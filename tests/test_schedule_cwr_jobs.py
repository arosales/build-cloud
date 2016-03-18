from argparse import Namespace
from contextlib import contextmanager
import os
from unittest import TestCase

from mock import (
    patch,
    call,
)
import yaml

from buildcloud.schedule_cwr_jobs import (
    build_jobs,
    Credentials,
    get_credentials,
    make_jobs,
    make_parameters,
    parse_args
)
from buildcloud.utility import temp_dir


class TestSchedule(TestCase):

    def test_parse_args(self):
        with jenkins_env():
            args = parse_args(['test_dir', 'default-aws', 'default-azure'])
            expected = Namespace(
                controllers=['default-aws', 'default-azure'],
                cwr_test_token='fake_pass',
                password='bar',
                test_plan_dir='test_dir', test_plans=None, user='foo')
            self.assertEqual(args, expected)

    def test_make_parameters(self):
        with temp_dir() as test_dir:
            test_plan = self.fake_parameters(test_dir)
            args = Namespace(controllers=['default-aws'])
            parameters = make_parameters(test_plan, args)
            expected = {
                'controllers': ['default-aws'],
                'bundle_name': 'make_life_easy',
                'test_plan': test_plan}
            self.assertEqual(parameters, expected)

    def test_make_jobs(self):
        args = Namespace(controllers=['default-aws'], password='bar',
                         test_plan_dir='', test_plans=None, user='foo')
        with temp_dir() as test_dir:
            args.test_plan_dir = test_dir
            test_plan = self.fake_parameters(test_dir)
            test_plan_2 = self.fake_parameters(test_dir, 2)
            self.fake_parameters(test_dir, 3, ext='.py')
            parameters = list(make_jobs(args))
            expected = [
                {'controllers': ['default-aws'],
                 'bundle_name': 'make_life_easy',
                 'test_plan': test_plan},
                {'controllers': ['default-aws'],
                 'bundle_name': 'make_life_easy',
                 'test_plan': test_plan_2}]
            self.assertItemsEqual(parameters, expected)

    def test_get_credentials(self):
        args = Namespace(controllers=['default-aws'], password='bar',
                         test_plan_dir='', test_plans=None, user='foo')
        cred = get_credentials(args)
        self.assertEqual(cred.user, 'foo')
        self.assertEqual(cred.password, 'bar')

    def fake_parameters(self, test_dir, count=1, ext='.yaml'):
        test_plan = os.path.join(test_dir, 'test' + str(count) + ext)
        plan = {
            'bundle': 'make life easy',
            'bundle_name': 'make_life_easy',
            'bundle_file': ''
        }
        with open(test_plan, 'w') as f:
            yaml.dump(plan, f)
        return test_plan

    def test_build_jobs_credentials(self):
        credentials = Credentials('joe', 'pass')
        params = [
            {'controllers': ['default-aws'],
             'bundle_name': 'make_life_easy',
             'test_plan': 'test_plan'},
            {'controllers': ['default-aws'],
             'bundle_name': 'made life easy',
             'test_plan': 'test_plan_2'}]
        with patch('buildcloud.schedule_cwr_jobs.Jenkins',
                   autospec=True) as jenkins_mock:
            build_jobs(credentials, params)
        jenkins_mock.assert_called_once_with(
            'http://localhost:8080', 'joe', 'pass')
        calls = [
            call('cwr-test',
                 {'controllers': ['default-aws'],
                  'bundle_name': 'make_life_easy',
                  'test_plan': 'test_plan'}),
            call('cwr-test',
                 {'controllers': ['default-aws'],
                  'bundle_name': 'made life easy',
                  'test_plan': 'test_plan_2'})]
        self.assertEqual(
            jenkins_mock.return_value.build_job.call_args_list, calls)


@contextmanager
def jenkins_env():
    user = os.environ.get('JENKINS_USER')
    password = os.environ.get('JENKINS_PASSWORD')
    cwr_token = os.environ.get('CWR_TEST_TOKEN')
    os.environ["JENKINS_USER"] = 'foo'
    os.environ["JENKINS_PASSWORD"] = 'bar'
    os.environ["CWR_TEST_TOKEN"] = 'fake_pass'
    try:
        yield
    finally:
        os.environ["JENKINS_USER"] = user if user else ''
        os.environ["JENKINS_PASSWORD"] = password if password else ''
        os.environ["CWR_TEST_TOKEN"] = cwr_token if cwr_token else ''
