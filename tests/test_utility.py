import os
import subprocess
from unittest import TestCase

from mock import patch

from buildcloud.utility import (
    copytree_force,
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
        proc = FakeProc()
        cmd = ['foo', 'bar']
        with patch('subprocess.Popen', autospec=True,
                   return_value=proc) as p_mock:
                run_command(cmd)
        p_mock.assert_called_once_with(cmd, stdout=subprocess.PIPE)

    def test_run_command_str(self):
        proc = FakeProc()
        cmd = ['foo bar']
        with patch('subprocess.Popen', autospec=True,
                   return_value=proc) as p_mock:
            with patch('buildcloud.utility.print_now'):
                run_command(cmd, verbose=True)
        p_mock.assert_called_once_with(cmd, stdout=subprocess.PIPE)

    def test_run_command_verbose(self):
        proc = FakeProc()
        cmd = ['foo', 'bar']
        with patch('subprocess.Popen', autospec=True,
                   return_value=proc) as p_mock:
            with patch('buildcloud.utility.print_now') as pr_mock:
                run_command(cmd, verbose=True)
        p_mock.assert_called_once_with(cmd, stdout=subprocess.PIPE)
        pr_mock.assert_called_once_with("Executing: ['foo', 'bar']")

    def test_copytree_force(self):
        with temp_dir() as src:
            with temp_dir() as dst:
                sub_src_dir = os.path.join(src, 'tmp')
                os.mkdir(sub_src_dir)
                sub_dst_dir = os.path.join(dst, 'tmp')
                os.mkdir(sub_dst_dir)
                copytree_force(src, dst)
                self.assertTrue(os.path.exists(sub_dst_dir))


class FakeProc:

    returncode = 0

    def poll(self):
        return True
