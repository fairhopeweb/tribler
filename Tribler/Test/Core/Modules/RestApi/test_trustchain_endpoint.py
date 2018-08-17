import json

from nose.twistedtools import deferred
from twisted.internet.defer import inlineCallbacks

from Tribler.Core.Modules.wallet.tc_wallet import TrustchainWallet
from Tribler.pyipv8.ipv8.attestation.trustchain.block import TrustChainBlock
from Tribler.pyipv8.ipv8.attestation.trustchain.community import TrustChainCommunity
from Tribler.pyipv8.ipv8.test.mocking.ipv8 import MockIPv8
from Tribler.Test.Core.Modules.RestApi.base_api_test import AbstractApiTest


class TestTrustchainStatsEndpoint(AbstractApiTest):

    @inlineCallbacks
    def setUp(self):
        yield super(TestTrustchainStatsEndpoint, self).setUp()

        self.mock_ipv8 = MockIPv8(u"low",
                                  TrustChainCommunity,
                                  working_directory=self.session.config.get_state_dir())
        self.session.lm.trustchain_community = self.mock_ipv8.overlay
        self.session.lm.wallets['MB'] = TrustchainWallet(self.session.lm.trustchain_community)

    @inlineCallbacks
    def tearDown(self):
        yield self.mock_ipv8.unload()
        yield super(TestTrustchainStatsEndpoint, self).tearDown()

    @deferred(timeout=10)
    def test_get_statistics_no_community(self):
        """
        Testing whether the API returns error 404 if no trustchain community is loaded
        """
        del self.session.lm.wallets['MB']
        return self.do_request('trustchain/statistics', expected_code=404)

    @deferred(timeout=10)
    def test_get_statistics(self):
        """
        Testing whether the API returns the correct statistics
        """
        block = TrustChainBlock()
        block.public_key = self.session.lm.trustchain_community.my_peer.public_key.key_to_bin()
        block.link_public_key = "deadbeef".decode("HEX")
        block.link_sequence_number = 21
        block.type = 'tribler_bandwidth'
        block.transaction = {"up": 42, "down": 8, "total_up": 1024, "total_down": 2048, "type": "tribler_bandwidth"}
        block.sequence_number = 3
        block.previous_hash = "babecafe".decode("HEX")
        block.signature = "babebeef".decode("HEX")
        self.session.lm.trustchain_community.persistence.add_block(block)

        def verify_response(response):
            response_json = json.loads(response)
            self.assertTrue("statistics" in response_json)
            stats = response_json["statistics"]
            self.assertEqual(stats["id"], self.session.lm.trustchain_community.my_peer.
                             public_key.key_to_bin().encode("HEX"))
            self.assertEqual(stats["total_blocks"], 3)
            self.assertEqual(stats["total_up"], 1024)
            self.assertEqual(stats["total_down"], 2048)
            self.assertEqual(stats["peers_that_pk_helped"], 1)
            self.assertEqual(stats["peers_that_helped_pk"], 1)
            self.assertIn("latest_block", stats)
            self.assertNotEqual(stats["latest_block"]["insert_time"], "")
            self.assertEqual(stats["latest_block"]["hash"], block.hash.encode("HEX"))
            self.assertEqual(stats["latest_block"]["link_public_key"], "deadbeef")
            self.assertEqual(stats["latest_block"]["link_sequence_number"], 21)
            self.assertEqual(stats["latest_block"]["up"], 42)
            self.assertEqual(stats["latest_block"]["down"], 8)

        self.should_check_equality = False
        return self.do_request('trustchain/statistics', expected_code=200).addCallback(verify_response)

    @deferred(timeout=10)
    def test_get_statistics_no_data(self):
        """
        Testing whether the API returns the correct statistics
        """

        def verify_response(response):
            response_json = json.loads(response)
            self.assertTrue("statistics" in response_json)
            stats = response_json["statistics"]
            self.assertEqual(stats["id"], self.session.lm.trustchain_community.my_peer.
                             public_key.key_to_bin().encode("HEX"))
            self.assertEqual(stats["total_blocks"], 0)
            self.assertEqual(stats["total_up"], 0)
            self.assertEqual(stats["total_down"], 0)
            self.assertEqual(stats["peers_that_pk_helped"], 0)
            self.assertEqual(stats["peers_that_helped_pk"], 0)
            self.assertNotIn("latest_block", stats)

        self.should_check_equality = False
        return self.do_request('trustchain/statistics', expected_code=200).addCallback(verify_response)

    @deferred(timeout=10)
    def test_get_bootstrap_identity_no_community(self):
        """
        Testing whether the API returns error 404 if no trustchain community is loaded when bootstrapping a new identity
        """
        del self.session.lm.wallets['MB']
        return self.do_request('trustchain/bootstrap', expected_code=404)

    @deferred(timeout=10)
    def test_get_bootstrap_identity_all_tokens(self):
        """
        Testing whether the API return all available tokens when no argument is supplied
        """
        transaction = {'up': 100, 'down': 0, 'total_up': 100, 'total_down': 0}
        transaction2 = {'up': 100, 'down': 0}

        def verify_response(response):
            response_json = json.loads(response)
            self.assertEqual(response_json['transaction'], transaction2)

        test_block = TrustChainBlock()
        test_block.type = 'tribler_bandwidth'
        test_block.transaction = transaction
        test_block.public_key = self.session.lm.trustchain_community.my_peer.public_key.key_to_bin()
        self.session.lm.trustchain_community.persistence.add_block(test_block)

        self.should_check_equality = False
        return self.do_request('trustchain/bootstrap', expected_code=200).addCallback(verify_response)

    @deferred(timeout=10)
    def test_get_bootstrap_identity_partial_tokens(self):
        """
        Testing whether the API return partial available credit when argument is supplied
        """
        transaction = {'up': 100, 'down': 0, 'total_up': 100, 'total_down': 0}
        transaction2 = {'up': 50, 'down': 0}

        def verify_response(response):
            response_json = json.loads(response)
            self.assertEqual(response_json['transaction'], transaction2)

        test_block = TrustChainBlock()
        test_block.type = 'tribler_bandwidth'
        test_block.transaction = transaction
        test_block.public_key = self.session.lm.trustchain_community.my_peer.public_key.key_to_bin()
        self.session.lm.trustchain_community.persistence.add_block(test_block)

        self.should_check_equality = False
        return self.do_request('trustchain/bootstrap?amount=50', expected_code=200).addCallback(verify_response)

    @deferred(timeout=10)
    def test_get_bootstrap_identity_not_enough_tokens(self):
        """
        Testing whether the API returns error 400 if bandwidth is to low when bootstrapping a new identity
        """
        transaction = {'up': 100, 'down': 0, 'total_up': 100, 'total_down': 0}
        test_block = TrustChainBlock()
        test_block.type = 'tribler_bandwidth'
        test_block.transaction = transaction
        test_block.public_key = self.session.lm.trustchain_community.my_peer.public_key.key_to_bin()
        self.session.lm.trustchain_community.persistence.add_block(test_block)

        self.should_check_equality = False
        return self.do_request('trustchain/bootstrap?amount=200', expected_code=400)

    @deferred(timeout=10)
    def test_get_bootstrap_identity_not_enough_tokens_2(self):
        """
        Testing whether the API returns error 400 if bandwidth is to low when bootstrapping a new identity
        """
        transaction = {'up': 0, 'down': 100, 'total_up': 0, 'total_down': 100}
        test_block = TrustChainBlock()
        test_block.type = 'tribler_bandwidth'
        test_block.transaction = transaction
        test_block.public_key = self.session.lm.trustchain_community.my_peer.public_key.key_to_bin()
        self.session.lm.trustchain_community.persistence.add_block(test_block)

        self.should_check_equality = False
        return self.do_request('trustchain/bootstrap?amount=10', expected_code=400)

    @deferred(timeout=10)
    def test_get_bootstrap_identity_zero_amount(self):
        """
        Testing whether the API returns error 400 if amount is zero when bootstrapping a new identity
        """
        self.should_check_equality = False
        return self.do_request('trustchain/bootstrap?amount=0', expected_code=400)

    @deferred(timeout=10)
    def test_get_bootstrap_identity_negative_amount(self):
        """
        Testing whether the API returns error 400 if amount is negative when bootstrapping a new identity
        """
        self.should_check_equality = False
        return self.do_request('trustchain/bootstrap?amount=-1', expected_code=400)

    @deferred(timeout=10)
    def test_get_bootstrap_identity_string(self):
        """
        Testing whether the API returns error 400 if amount is string when bootstrapping a new identity
        """
        self.should_check_equality = False
        return self.do_request('trustchain/bootstrap?amount=aaa', expected_code=400)
