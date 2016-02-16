from __future__ import print_function

from contextlib import contextmanager
import errno
import logging
import os
from shutil import rmtree
import subprocess
import sys
from tempfile import mkdtemp


@contextmanager
def temp_dir(parent=None):
    directory = mkdtemp(dir=parent)
    try:
        yield directory
    finally:
        rmtree(directory)


def s3_cmd(params, drop_output=False):
    s3cfg_path = os.path.join(
        os.environ['HOME'], 'cloud-city/juju-qa.s3cfg')
    command = ['s3cmd', '-c', s3cfg_path, '--no-progress'] + params
    if drop_output:
        return subprocess.check_call(
            command, stdout=open('/dev/null', 'w'))
    else:
        return subprocess.check_output(command)


def configure_logging(log_level):
    logging.basicConfig(
        level=log_level, format='%(asctime)s %(levelname)s %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S')


def ensure_dir(path):
    try:
        os.mkdir(path)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise


def ensure_deleted(path):
    try:
        os.unlink(path)
    except OSError as e:
        if e.errno != errno.ENOENT:
            raise


def run_command(command, verbose=False):
    """Execute a command and maybe print the output."""
    if isinstance(command, str):
        command = command.split()
    if verbose:
        print_now('Executing: {}'.format(command))
    output = subprocess.check_output(command)
    if verbose:
        print_now(output)


def juju_run(command):
    command = command.split() if isinstance(command, str) else command
    return run_command(['juju'] + command)


def print_now(string):
    print(string)
    sys.stdout.flush()


def get_juju_home():
    home = os.environ.get('JUJU_HOME')
    if home is None:
        home = os.path.join(os.environ.get('HOME'), 'cloud-city')
    return home
