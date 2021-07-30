from ipv8.bootstrapping.bootstrapper_interface import Bootstrapper
from ipv8.peer import Peer
from ipv8.peerdiscovery.discovery import RandomWalk
from ipv8_service import IPv8
from tribler_core.awaitable_resources import BANDWIDTH_ACCOUNTING_COMMUNITY, IPV8_SERVICE, MY_PEER, IPV8_BOOTSTRAPPER, \
    REST_MANAGER, UPGRADER

from tribler_core.modules.bandwidth_accounting.community import (
    BandwidthAccountingCommunity,
    BandwidthAccountingTestnetCommunity,
)
from tribler_core.modules.component import Component
from tribler_core.restapi.rest_manager import RESTManager


class BandwidthAccountingComponent(Component):
    role = BANDWIDTH_ACCOUNTING_COMMUNITY

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._rest_manager = None

    async def run(self, mediator):
        await super().run(mediator)
        await mediator.optional[UPGRADER]._resource_initialized_event.wait()
        config = mediator.config

        ipv8 = await self.use(mediator, IPV8_SERVICE)
        peer = await self.use(mediator, MY_PEER)
        bootstrapper = await self.use(mediator, IPV8_BOOTSTRAPPER)
        rest_manager = self._rest_manager = await self.use(mediator, REST_MANAGER)

        bandwidth_cls = BandwidthAccountingTestnetCommunity if config.general.testnet or config.bandwidth_accounting.testnet else BandwidthAccountingCommunity

        community = bandwidth_cls(peer, ipv8.endpoint, ipv8.network,
                                  settings=config.bandwidth_accounting,
                                  database=config.state_dir / "sqlite" / "bandwidth.db")
        ipv8.strategies.append((RandomWalk(community), 20))

        community.bootstrappers.append(bootstrapper)

        ipv8.overlays.append(community)
        self.provide(mediator, community)

        rest_manager.get_endpoint('trustview').bandwidth_db = community.database
        rest_manager.get_endpoint('bandwidth').bandwidth_community = community

    async def shutdown(self, mediator):
        self._rest_manager.get_endpoint('trustview').bandwidth_db = None
        self._rest_manager.get_endpoint('bandwidth').bandwidth_community = None
        await self._provided_object.unload()

        await super().shutdown(mediator)
