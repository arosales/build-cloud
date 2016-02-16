import os
from argparse import Namespace
from unittest import TestCase

from mock import patch

from buildcloud.build_cloud import (
    clean_up,
    parse_args,
)
from tests.common_test import (
    setup_test_logging,
)


class TestCloudBuild(TestCase):

    def setUp(self):
        self.temp_home = '/tmp/home'
        home_original = os.environ['HOME']
        os.environ['HOME'] = self.temp_home
        self.addCleanup(self.restore_home, home_original)
        setup_test_logging(self)

    def restore_home(self, home_original):
        os.environ['HOME'] = home_original

    def test_parse_args(self):
        args = parse_args(['juju-env'])
        expected = Namespace(docker_net=None, env='juju-env',
                             juju_home='/tmp/home/cloud-city', verbose=0)
        self.assertEqual(args, expected)

    def test_parse_args_lxc(self):
        args = parse_args(['charm-testing-lxc'])
        expected = Namespace(docker_net='--net=host', env='charm-testing-lxc',
                             juju_home='/tmp/home/cloud-city', verbose=0)
        self.assertEqual(args, expected)

    def test_parse_args_maas(self):
        args = parse_args(['charm-testing-power8-maas'])
        expected = Namespace(docker_net='--net=host',
                             env='charm-testing-power8-maas',
                             juju_home='/tmp/home/cloud-city', verbose=0)
        self.assertEqual(args, expected)

    def test_clean_up(self):
        with patch('subprocess.check_output') as co_mock:
            args = self.get_args()
            clean_up(args)
        co_mock.assert_called_once_with(
            ['juju', 'destroy-environment', '--force', 'juju-env'])

    def get_args(self):
        return Namespace(env='juju-env')
