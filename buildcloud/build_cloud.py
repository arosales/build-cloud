#!/usr/bin/env python

from argparse import ArgumentParser
from contextlib import contextmanager
from collections import namedtuple
import logging
import os
import shutil

from buildcloud.utility import (
    configure_logging,
    copytree_force,
    ensure_dir,
    get_juju_home,
    run_command,
    temp_dir,
)


def parse_args(argv=None):
    parser = ArgumentParser()
    parser.add_argument(
        'model', nargs='+', help='Name of models to use')
    parser.add_argument(
        'test_plan', help='File path to test plan.')
    parser.add_argument(
        '--bundle-args',
        help='Name of bundle file to deploy, if url points to a bundle '
             'containing multiple bundle files.',
        default=os.environ.get('bundle'))
    parser.add_argument(
        '--verbose', action='count', default=0)
    parser.add_argument(
        '--juju-home', help='Juju home directory.', default=get_juju_home())
    parser.add_argument('--log-dir', help='The directory to dump logs to.')
    args = parser.parse_args(argv)
    return args


@contextmanager
def temp_juju_home(juju_home):
    org_juju_home = os.environ.get('JUJU_HOME')
    os.environ["JUJU_HOME"] = juju_home
    try:
        yield
    finally:
        os.environ['JUJU_HOME'] = org_juju_home if org_juju_home else ''


@contextmanager
def env(args):
    with temp_dir() as root:
        tmp_juju_home = os.path.join(root, 'tmp_juju_home')
        shutil.copytree(args.juju_home, tmp_juju_home,
                        ignore=shutil.ignore_patterns('environments'))

        juju_repository = ensure_dir('juju_repository', parent=root)
        test_results = ensure_dir('results', parent=root)

        tmp = ensure_dir('tmp', parent=root)
        ssh_dir = os.path.join(tmp, 'ssh')
        os.mkdir(ssh_dir)
        shutil.copyfile(os.path.join(tmp_juju_home, 'staging-juju-rsa'),
                        os.path.join(ssh_dir, 'id_rsa'))
        ssh_path = os.path.join(tmp, 'ssh')

        Host = namedtuple(
            'Host',
            ['tmp_juju_home', 'juju_repository', 'test_results',
             'tmp', 'ssh_path', 'root'])
        host = Host(
            tmp_juju_home=tmp_juju_home, juju_repository=juju_repository,
            test_results=test_results, tmp=tmp, ssh_path=ssh_path, root=root)
        Container = namedtuple(
            'Container',
            ['user', 'name', 'home', 'ssh_home', 'juju_home', 'test_results',
             'juju_repository', 'test_plans'])
        container_user = 'ubuntu'
        container_home = os.path.join('/home', container_user)
        container_juju_home = os.path.join(container_home, '.juju')
        container_ssh_home = os.path.join(container_home, '.ssh')
        container_test_results = os.path.join(container_home, 'results')
        container_repository = os.path.join(container_home, 'charm-repo')
        container_test_plans = os.path.join(container_home, 'test_plans')
        container = Container(user=container_user,
                              name='seman/cwrbox',
                              home=container_home,
                              ssh_home=container_ssh_home,
                              juju_home=container_juju_home,
                              test_results=container_test_results,
                              juju_repository=container_repository,
                              test_plans=container_test_plans)
        yield host, container


@contextmanager
def juju(host, args):
    run_command('juju --version')
    logging.info("Juju home is set to {}".format(host.tmp_juju_home))
    for model in args.model:
        run_command(
            'juju bootstrap --show-log -e {} --constraints mem=4G'.format(
                model))
        run_command('juju set-constraints -e {} mem=2G'.format(model))
    try:
        yield
    finally:
        for model in args.model:
            run_command(
                'juju destroy-environment --force --yes {}'.format(model))


def run_container(host, container, args):
    logging.debug("Host data: ", host)
    logging.debug("Container data: ", container)
    run_command('sudo docker pull {}'.format(container.name))
    container_options = (
        '--rm '
        '-u {} '
        '-e Home={} '
        '-e JUJU_HOME={} '
        '-w {} '
        '-v {}:{} '   # Test result location
        '-v {}:{} '   # Temp Juju home
        '-v {}/.deployer-store-cache:{}.deployer-store-cache '
        '-v {}:{} '   # Repository location
        '-v {}:{} '   # Temp location.
        '-v {}:{} '   # Test plan
        '-t {} '.format(container.user,
                        container.home,
                        container.juju_home,
                        container.home,
                        host.test_results, container.test_results,
                        host.tmp_juju_home, container.juju_home,
                        host.tmp, container.juju_home,
                        host.juju_repository, container.juju_repository,
                        host.tmp, host.tmp,
                        os.path.dirname(args.test_plan), container.test_plans,
                        container.name))
    test_plan = os.path.join(
        container.test_plans, os.path.basename(args.test_plan))
    shell_options = (
        'sudo cwr -F -l DEBUG -v {} {}'.format(
            ' '.join(args.model), test_plan))
    command = ('sudo docker run {} sh -c'.format(
        container_options).split() + [shell_options])
    run_command(command)
    run_command('sudo chown -R {}:{} {}'.format(
        os.getegid(), os.getpgrp(), host.root))
    # Copy logs
    if args.log_dir:
        copytree_force(host.test_results, args.log_dir)


def main():
    args = parse_args()
    log_level = max(logging.WARN - args.verbose * 10, logging.DEBUG)
    configure_logging(log_level)
    with env(args) as (host, container):
        with temp_juju_home(host.tmp_juju_home):
            with juju(host, args):
                run_container(host, container, args)


if __name__ == '__main__':
    main()
