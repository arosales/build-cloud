#!/usr/bin/env python

from argparse import ArgumentParser
from collections import namedtuple
import os
import yaml

from jenkins import Jenkins


Credentials = namedtuple('Credentials', ['user', 'password'])


def parse_args(argv=None):
    parser = ArgumentParser()
    parser.add_argument(
        'test_plan_dir', help='File path to test plan directory.')
    parser.add_argument(
        '--user', default=os.environ.get('JENKINS_USER'))
    parser.add_argument(
        '--password', default=os.environ.get('JENKINS_PASSWORD'))
    parser.add_argument(
        '--cwr-test-token', default=os.environ.get('CWR_TEST_TOKEN'))
    parser.add_argument(
        'controllers', nargs='+', help='List of controllers. ')
    parser.add_argument(
        '--test_plans', nargs='+',
        help='List of test plan files.  Instead of scheduling all the tests, '
             'this can be use to restrict the test plan files. If this is '
             'not set, all the test will be scheduled.')
    args = parser.parse_args(argv)
    if not args.cwr_test_token:
        parser.error("Please set the cwr-test Jenkins job token by "
                     "exporting the CWR_TEST_TOKEN environment variable.")
    return args


def make_parameters(test_plan, args):
    with open(test_plan, 'r') as f:
        plan = yaml.load(f)
    parameters = {
        'test_plan': test_plan,
        'controllers': args.controllers,
        'bundle_name': plan['bundle_name'],
        'bundle_file': plan.get('bundle_file')
    }
    # Remove empty values
    parameters = {k: v for k, v in parameters.items() if v}
    return parameters


def make_jobs(args):
    test_plans = args.test_plans or os.listdir(args.test_plan_dir)
    for test_plan in test_plans:
        if not test_plan.endswith('.yaml'):
            continue
        test_plan = os.path.join(args.test_plan_dir, test_plan)
        yield make_parameters(test_plan, args)


def get_credentials(args):
    if None in (args.user, args.password):
        raise ValueError(
            'Jenkins username and/or password not supplied.')
    return Credentials(args.user, args.password)


def build_jobs(credentials, jobs):
    jenkins = Jenkins('http://localhost:8080', *credentials)
    for job in jobs:
        jenkins.build_job('cwr-test', job)


def main():
    args = parse_args()
    credentials = get_credentials(args)
    jobs = make_jobs(args)
    build_jobs(credentials, jobs)


if __name__ == '__main__':
    main()
