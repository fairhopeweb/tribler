from unittest.mock import Mock

import pytest

from tribler_common.simpledefs import MAX_LIBTORRENT_RATE_LIMIT

from tribler_core.modules.libtorrent.download_config import DownloadConfig
from tribler_core.modules.libtorrent.download_manager import DownloadManager
from tribler_core.restapi.base_api_test import do_request
from tribler_core.utilities.path_util import Path


def verify_settings(settings_dict):
    """
    Verify that the expected sections are present.
    """
    check_section = ['libtorrent', 'general', 'torrent_checking',
                     'tunnel_community', 'api', 'trustchain', 'watch_folder']

    assert settings_dict['settings']
    assert Path(settings_dict['settings']['download_defaults']['saveas'])
    for section in check_section:
        assert settings_dict['settings'][section]


@pytest.mark.asyncio
async def test_unicode_chars(enable_api, session):
    """
    Test setting watch_folder to a unicode path.
    """
    post_data = {'watch_folder': {'directory': '\u2588'}}

    await do_request(session, 'settings', expected_code=200, request_type='POST', post_data=post_data)

    settings = await do_request(session, 'settings')

    watch_folder = settings['settings']['watch_folder']['directory']
    assert watch_folder == post_data['watch_folder']['directory']


@pytest.mark.asyncio
async def test_get_settings(enable_api, session):
    """
    Testing whether the API returns a correct settings dictionary when the settings are requested
    """
    response = await do_request(session, 'settings', expected_code=200)
    verify_settings(response)


@pytest.mark.asyncio
async def test_set_settings_invalid_dict(enable_api, session):
    """
    Testing whether an error is returned if we are passing an invalid dictionary that is too deep
    """
    post_data = {'a': {'b': {'c': 'd'}}}
    response_dict = await do_request(session, 'settings', expected_code=500, request_type='POST', post_data=post_data)
    assert 'error' in response_dict


@pytest.mark.asyncio
async def test_set_settings_no_key(enable_api, session):
    """
    Testing whether an error is returned when we try to set a non-existing key
    """
    def verify_response(response_dict):
        assert 'error' in response_dict

    post_data = {'general': {'b': 'c'}}
    verify_response(await do_request(session, 'settings', expected_code=500, request_type='POST', post_data=post_data))

    post_data = {'Tribler': {'b': 'c'}}
    verify_response(await do_request(session, 'settings', expected_code=500, request_type='POST', post_data=post_data))


@pytest.mark.asyncio
async def test_set_settings(enable_api, mock_dlmgr, session):
    """
    Testing whether settings in the API can be successfully set
    """
    dcfg = DownloadConfig()
    download = Mock()
    download.config = dcfg
    session.dlmgr.get_downloads = lambda: [download]

    post_data = {'download_defaults': {'seeding_mode': 'ratio',
                                       'seeding_ratio': 3,
                                       'seeding_time': 123}}
    await do_request(session, 'settings', expected_code=200, request_type='POST', post_data=post_data)
    assert session.config.download_defaults.seeding_mode == 'ratio'
    assert session.config.download_defaults.seeding_ratio == 3
    assert session.config.download_defaults.seeding_time == 123


@pytest.mark.asyncio
async def test_set_rate_settings(enable_api, mock_dlmgr, session):
    """
    Testing whether libtorrent rate limits works for large number without overflow error.
    """

    dcfg = DownloadConfig()
    download = Mock()
    download.config = dcfg
    session.dlmgr.get_downloads = lambda: [download]

    extra_rate = 1024 * 1024 * 1024  # 1GB/s
    post_data = {
        'libtorrent': {
            'max_download_rate': MAX_LIBTORRENT_RATE_LIMIT + extra_rate,
            'max_upload_rate': MAX_LIBTORRENT_RATE_LIMIT + extra_rate
        }
    }
    await do_request(session, 'settings', expected_code=200, request_type='POST', post_data=post_data)

    assert DownloadManager.get_libtorrent_max_download_rate(session.config) == MAX_LIBTORRENT_RATE_LIMIT
    assert DownloadManager.get_libtorrent_max_upload_rate(session.config) == MAX_LIBTORRENT_RATE_LIMIT
