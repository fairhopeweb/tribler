import logging
from hashlib import sha1

from tribler_core.utilities.libtorrent_helper import libtorrent as lt
from tribler_core.utilities.path_util import Path

logger = logging.getLogger(__name__)


def commonprefix(paths_list):
    # this unlike the os path .commonprefix version always returns path prefixes as it compares
    # path component wise.
    base_set = set(paths_list[0].parents)
    for p in paths_list[1:]:
        base_set.intersection_update(set(p.parents))

    return sorted(base_set, reverse=True)[0]


def _existing_files(path_list):
    for path in path_list:
        path = Path(path)
        if not path.exists():
            raise OSError(f'Path does not exist: {path}')
        elif path.is_file():
            yield path


def create_torrent_file(file_path_list, params, torrent_filepath=None):
    fs = lt.file_storage()

    # filter all non-files
    path_list = list(_existing_files(file_path_list))

    # get the directory where these files are in. If there are multiple files, take the common directory they are in
    base_path = commonprefix(path_list).parent if len(path_list) > 1 else path_list[0].parent
    base_path = base_path.absolute()
    for path in path_list:
        relative = path.relative_to(base_path)
        fs.add_file(str(relative), path.size())

    if params.get(b'piece length'):
        piece_size = params[b'piece length']
    else:
        piece_size = 0

    flags = lt.create_torrent_flags_t.optimize

    # This flag doesn't exist anymore in libtorrent V1.1.0
    if hasattr(lt.create_torrent_flags_t, 'calculate_file_hashes'):
        flags |= lt.create_torrent_flags_t.calculate_file_hashes

    params = {k: (v.decode('utf-8') if isinstance(v, bytes) else v) for k, v in params.items()}

    torrent = lt.create_torrent(fs, piece_size=piece_size, flags=flags)
    # Python2 wants binary, python3 want unicode
    if params.get(b'comment'):
        torrent.set_comment(params[b'comment'])
    if params.get(b'created by'):
        torrent.set_creator(params[b'created by'])
    # main tracker
    if params.get(b'announce'):
        torrent.add_tracker(params[b'announce'])
    # tracker list
    if params.get(b'announce-list'):
        tier = 1
        for tracker in params[b'announce-list']:
            torrent.add_tracker(tracker, tier=tier)
            tier += 1
    # DHT nodes
    # http://www.bittorrent.org/beps/bep_0005.html
    if params.get(b'nodes'):
        for node in params[b'nodes']:
            torrent.add_node(*node)
    # HTTP seeding
    # http://www.bittorrent.org/beps/bep_0017.html
    if params.get(b'httpseeds'):
        torrent.add_http_seed(params[b'httpseeds'])

    # Web seeding
    # http://www.bittorrent.org/beps/bep_0019.html
    if len(file_path_list) == 1:
        if params.get(b'urllist', False):
            torrent.add_url_seed(params[b'urllist'])

    # read the files and calculate the hashes
    lt.set_piece_hashes(torrent, str(base_path))

    t1 = torrent.generate()
    torrent = lt.bencode(t1)

    if torrent_filepath:
        with open(torrent_filepath, 'wb') as f:
            f.write(torrent)

    return {
        'success': True,
        'base_path': base_path,
        'base_dir': base_path.parent,
        'torrent_file_path': torrent_filepath,
        'metainfo': torrent,
        'infohash': sha1(lt.bencode(t1[b'info'])).digest()
    }


def get_info_from_handle(handle):
    # In libtorrent 0.16.18, the torrent_handle.torrent_file method is not available.
    # this method checks whether the torrent_file method is available on a given handle.
    # If not, fall back on the deprecated get_torrent_info
    try:
        if hasattr(handle, 'torrent_file'):
            return handle.torrent_file()
        return handle.get_torrent_info()
    except AttributeError as ae:
        logger.warning("No torrent info found from handle: %s", str(ae))
        return None
    except RuntimeError as e:  # This can happen when the torrent handle is invalid.
        logger.warning("Got exception when fetching info from handle: %s", str(e))
        return None
