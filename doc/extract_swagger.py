import json
from asyncio import get_event_loop
from io import StringIO
from unittest.mock import Mock

import aiohttp

from tribler_core.config.tribler_config import TriblerConfig
from tribler_core.restapi.rest_manager import RESTManager

import yaml


async def extract_swagger(destination_fn):
    session = Mock()
    session.config = TriblerConfig()
    session.config.api.key = 'apikey'
    session.config.api.http_enabled = False
    session.config.api.https_enabled = False
    api_manager = RESTManager(session)
    await api_manager.start()

    fp = StringIO()
    proto = aiohttp.web_protocol.RequestHandler(api_manager.runner._server, loop=get_event_loop())
    proto.connection_made(Mock(is_closing=lambda: False, write=lambda b: fp.write(b.decode())))
    proto.data_received(b'GET /docs/swagger.json HTTP/1.1\r\n'
                        b'Connection: close\r\n\r\n')
    await proto.start()
    api_spec = json.loads(fp.getvalue().split('\r\n\r\n')[1])

    # All responses should have a description
    for _, path in api_spec['paths'].items():
        for _, spec in path.items():
            for _, response in spec['responses'].items():
                if 'description' not in response:
                    response['description'] = ''
    # Convert to yaml
    with open(destination_fn, 'w') as destination_fp:
        destination_fp.write(yaml.dump(api_spec))


if __name__ == '__main__':
    loop = get_event_loop()
    loop.run_until_complete(extract_swagger('restapi/swagger.yaml'))
