from enum import Enum, unique
from unittest.mock import sentinel

"""
We use the sentinel class from mock package here instead of enums, 
because it does not require a class prefix, and looks better in debug traces.
Also, we purposefully do not put the identifiers into the component classes,
to avoid unnecessary and circular imports.
"""

EXCEPTION_HANDLER = sentinel.EXCEPTION_HANDLER
REST_MANAGER = sentinel.REST_MANAGER
IPV8_SERVICE = sentinel.IPV8_SERVICE
TUNNELS_COMMUNITY = sentinel.TUNNELS_COMMUNITY
BANDWIDTH_ACCOUNTING_COMMUNITY = sentinel.BANDWIDTH_ACCOUNTING_COMMUNITY
MY_PEER = sentinel.MY_PEER
DHT_DISCOVERY_COMMUNITY = sentinel.DHT_DISCOVERY_COMMUNITY
DOWNLOAD_MANAGER = sentinel.DOWNLOAD_MANAGER
IPV8_BOOTSTRAPPER = sentinel.IPV8_BOOTSTRAPPER
METADATA_STORE = sentinel.METADATA_STORE
DISCOVERY_COMMUNITY = sentinel.DISCOVERY_COMMUNITY



