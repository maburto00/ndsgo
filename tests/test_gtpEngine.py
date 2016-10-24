from unittest import TestCase

from board import Board
from gtp_engine import GtpEngine
from lookup_players import MCPlayerQ
from utils import Color


class TestGtpEngine(TestCase):
    def setUp(self):
        player = MCPlayerQ(3)
        player.load_Q('/home/mario/Dropbox/PycharmProjects/ndsgo/MC_Q_N3_G1000000_seed2.npy')
        self.gtp = GtpEngine(player)

    def test_gtp_session(self):
        pass

    def test_known_commands(self):
        pass
        # for e in self.gtp.known_commands:
        #    self.gtp
