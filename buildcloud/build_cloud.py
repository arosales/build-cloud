#!/usr/bin/env python

import logging
import os
import subprocess
from argparse import ArgumentParser

from buildcloud.utility import (
    configure_logging,
    ensure_dir,
    get_juju_home,
    juju_run,
)


def parse_args(argv=None):
    parser = ArgumentParser()
    parser.add_argument('env', help='The juju environment to use.')
    parser.add_argument('--verbose', action='count', default=0)
    parser.add_argument('--juju-home', help='Juju home directory.',
                        default=get_juju_home())
    parser.add_argument('--docker-net', help='Docker network.')
    args = parser.parse_args(argv)
    if (args.docker_net is None and (
            args.env == "charm-testing-lxc" or
            args.env == "charm-testing-power8-maas")):
        args.docker_net = '--net=host'
    return args


def clean_up(args):
    try:
        juju_run('destroy-environment --force {}'.format(args.env))
    except subprocess.CalledProcessError:
        pass


def setup_env(root):
    juju_repository = os.path.join(root, 'juju_repository')
    ensure_dir(juju_repository)
    tmp = os.path.join(root, 'tmp')
    ensure_dir(tmp)


def main():
    args = parse_args()
    log_level = max(logging.WARN - args.verbose * 10, logging.DEBUG)
    configure_logging(log_level)


if __name__ == '__main__':
    main()
