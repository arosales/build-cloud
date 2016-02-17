#!/usr/bin/env python

from collections import namedtuple
import logging
import os
import subprocess
from argparse import ArgumentParser

from buildcloud.utility import (
    configure_logging,
    ensure_dir,
    get_juju_home,
    juju_run,
    run_command,
    temp_dir,
)


def parse_args(argv=None):
    parser = ArgumentParser()
    parser.add_argument(
        'env', help='The juju environment to use.')
    parser.add_argument(
        'test-plan', help='File path to test plan.')
    parser.add_argument(
        '--url',
        help='The url of the charm or bundle to test. The location must be '
             'public.',
        default=os.environ.get('url'))
    parser.add_argument(
        '--bundle-args',
        help='Name of bundle file to deploy, if url points to a bundle '
             'containing multiple bundle files.',
        default=os.environ.get('bundle'))
    parser.add_argument(
        '--verbose', action='count', default=0)
    parser.add_argument(
        '--juju-home', help='Juju home directory.', default=get_juju_home())
    parser.add_argument(
        '--docker-net', help='Docker network.')
    parser.add_argument(
        '--job_id', default=os.environ.get('job_id'))
    parser.add_argument(
        '--config', help='Description of the configuration.',
        default=os.environ.get('config'))
    parser.add_argument(
            '--bzr_user',
            default=os.environ.get('bzr_user'))
    parser.add_argument(
            '--bundle_args',
            help='Name of bundle file to deploy, if $url points to a bundle '
                 'containing multiple bundle files.',
            default=os.environ.get('bundle'))
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
    tmp_juju_home = os.path.join(root, 'tmp_juju_home')
    ensure_dir(tmp_juju_home)
    #todo: copy juju_home to tmp_juju_home
    juju_repository = os.path.join(root, 'juju_repository')
    ensure_dir(juju_repository)
    log_dest = os.path.join(root, 'log_dest')
    tmp = os.path.join(root, 'tmp')
    ensure_dir(tmp)
    charm_box = 'jujusolution/charmbox:latest'
    output = os.path.join(tmp, 'result.json')
    Env = namedtuple('Env', ['tmp_juju_home', 'juju_repository', 'log_dest',
                             'tmp' 'output', 'charm_box'])
    env = Env(tmp_juju_home=tmp_juju_home, juju_repository=juju_repository,
              log_dest=log_dest, tmp=tmp, output=output, charm_box=charm_box)
    return env


def run_docker(args, env):
    run_command('sudo docker pull {}'.format(env.charm_box))
    options = (
        '--rm {}  '
        '-u ubuntu '
        '-e "Home=/home/ubuntu" '
        '-e "JUJU_HOME=/home/ubuntu/.juju" '
        '-w "/home/ubuntu" '
        '-v {}:/home/ubuntu/.juju '
        '-v {}/.deployer-store-cache:/home/ubuntu/.juju/.deployer-store-cache '
        '-v {}:/home/ubuntu/charm-repo '
        '-v {}:{} '
        '-v {}/ssh:/home/ubuntu/.ssh '
        '-t {} '.format(args.docker_net, env.tmp_juju_home, env.tmp,
                        env.juju_repository, env.tmp, env.tmp. env.charm_box))
    run = ('  sh -c "bzr whoami \'{}\' && '
          'sudo cwr -F -e {} -t {} -l DEBUG -v -r json -o {} {}"'
           ''.format(args.bzr_user, args.env, args.url, env.output,
                     args.bundle_args))
    cmd = 'sudo docker run {}'.format(options)


def main():
    args = parse_args()
    log_level = max(logging.WARN - args.verbose * 10, logging.DEBUG)
    configure_logging(log_level)
    with temp_dir() as root:
        env = setup_env(root)
        run_docker(args, env)


if __name__ == '__main__':
    main()
