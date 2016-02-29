from __future__ import print_function

from contextlib import contextmanager
import errno
import logging
import os
from shutil import (
    copytree,
    rmtree,
)
import subprocess
import sys
from tempfile import mkdtemp


@contextmanager
def temp_dir(parent=None):
    directory = mkdtemp(dir=parent, prefix='cwr_tst_')
    try:
        yield directory
    finally:
        rmtree(directory)


def configure_logging(log_level):
    logging.basicConfig(
        level=log_level, format='%(asctime)s %(levelname)s %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S')


def ensure_dir(path, parent=None):
    path = os.path.join(parent, path) if parent else path
    try:
        os.mkdir(path)
        return path
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise


def run_command(command, verbose=True):
    """Execute a command and maybe print the output."""
    if isinstance(command, str):
        command = command.split()
    if verbose:
        print_now('Executing: {}'.format(command))
    proc = subprocess.Popen(command, stdout=subprocess.PIPE)
    while proc.poll() is None:
        status = proc.stdout.readline()
        if status:
            print_now(status)
    if proc.returncode != 0 and proc.returncode is not None:
        output, error = proc.communicate()
        print_now("ERROR: run_command failed: {}".format(error))
        e = subprocess.CalledProcessError(proc.returncode, command, error)
        e.stderr = error
        raise e


def print_now(string):
    print(string)
    sys.stdout.flush()


def get_juju_home():
    home = os.environ.get('JUJU_HOME')
    if home is None:
        home = os.path.join(os.environ.get('HOME'), 'cloud-city')
    return home

def copytree_force(src, dst, ignore=None):
    if os.path.exists(dst):
        rmtree(dst)
    copytree(src, dst, ignore=ignore)
