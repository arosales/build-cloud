import os
from unittest import TestCase

from mock import patch

from buildcloud.utility import (
    juju_run,
    run_command,
    temp_dir,
)


class TestUtility(TestCase):

    def test_temp_dir(self):
        with temp_dir() as d:
            self.assertTrue(os.path.isdir(d))
        self.assertFalse(os.path.exists(d))

    def test_temp_dir_contents(self):
        with temp_dir() as d:
            self.assertTrue(os.path.isdir(d))
            open(os.path.join(d, "a-file"), "w").close()
        self.assertFalse(os.path.exists(d))

    def test_temp_dir_parent(self):
        with temp_dir() as p:
            with temp_dir(parent=p) as d:
                self.assertTrue(os.path.isdir(d))
                self.assertEqual(p, os.path.dirname(d))
            self.assertFalse(os.path.exists(d))
        self.assertFalse(os.path.exists(p))

    def test_run_command(self):
        with patch('subprocess.check_output') as co_mock:
            run_command(['foo', 'bar'])
        args, kwargs = co_mock.call_args
        self.assertEqual((['foo', 'bar'], ), args)

    def test_run_command_str(self):
        with patch('subprocess.check_output') as co_mock:
            run_command('foo bar')
        args, kwargs = co_mock.call_args
        self.assertEqual((['foo', 'bar'], ), args)

    def test_run_command_verbose(self):
        with patch('subprocess.check_output'):
            with patch('buildcloud.utility.print_now') as p_mock:
                run_command(['foo', 'bar'], verbose=True)
                self.assertEqual(2, p_mock.call_count)

    def test_juju_run(self):
        with patch('subprocess.check_output') as co_mock:
            juju_run(['foo', 'bar'])
        args, kwargs = co_mock.call_args
        self.assertEqual((['juju', 'foo', 'bar'], ), args)
