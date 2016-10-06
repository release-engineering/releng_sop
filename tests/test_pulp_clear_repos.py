#!/usr/bin/python
# -*- coding: utf-8 -*-


"""Tests of PulpClearRepo script.
"""


from __future__ import print_function, unicode_literals
import unittest
import os
import sys
from mock import Mock, patch

DIR = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(DIR, ".."))

from releng_sop.pulp_clear_repos import get_parser, PulpClearRepos  # noqa
from tests.common import ParserTestBase  # noqa


class TestPulpClearRepos(unittest.TestCase):
    """Tests of methods from KojiCloneTagForReleaseMilestone class."""

    data = {
        "release_id": 'rhel-7.1',
        "service": 'pulp',
        "repo_family": 'htb',
        "repo_family_diff": 'ht',
        "content_format": 'rpm',
        "arch": 'x86_64\n     s390x',
        "variant_uid": 'Server\n     Workstation',
    }

    release_spec = {
        'name': 'rhel-7.1',
        'config_path': 'some.json',
        'config_data': {},
        '__getitem__': lambda self, item: self.config_data[item],
    }

    env_spec = {
        "name": 'default',
        'config_path': 'some_path.json',
        'config_data': {
            'pdc_server': 'pdc-test',
            'pulp_server': 'pulp_test',
        },
        '__getitem__': lambda self, item: self.config_data[item]
    }

    pulp_spec = {
        'user': 'admin',
        'password': 'pass',
        'config': 'pulp-test',
        'config_path': 'some_path.json',
    }

    # Expected details text
    details_base = """Pulp clear repos
 * env name:                {env[name]}
 * env config:              {env[config_path]}
 * release source           {release[config_path]}
 * PDC server:              pdc-test
 * release_id:              {release[name]}
 * pulp config:             {pulp[config]}
 * pulp config path:        {pulp[config_path]}
 * pulp user:               {pulp[user]}
""".format(env=env_spec, release=release_spec, pulp=pulp_spec)

    details_good_repo = """ * repo_family:             {data[repo_family]}
""".format(data=data)

    details_diff_repo = """ * repo_family:             {data[repo_family_diff]}
""".format(data=data)

    details_with_one_repo = """ * repos:
     rhel-7-workstation-htb-rpms
""".format(data=data)

    details_with_more_repo = """ * repos:
     rhel-7-workstation-htb-rpms
     rhel-7-server-htb-source-rpms
""".format(data=data)

    details_no_repo = """ * repos:
     No repos found.
""".format(data=data)

    details_arch = """ * arches:
     {data[arch]}
""".format(data=data)

    details_variant = """ * variants:
     {data[variant_uid]}
""".format(data=data)

    details_variant_arch = """ * arches:
     {data[arch]}
 * variants:
     {data[variant_uid]}
""".format(data=data)

    expected_query = {
        "release_id": "rhel-7.1",
        "service": "pulp",
        "repo_family": "htb",
        "content_format": "rpm",
    }

    expected_query_no_repo = {
        "release_id": "rhel-7.1",
        "service": "pulp",
        "repo_family": "ht",
        "content_format": "rpm",
    }

    def setUp(self):
        """Set up variables before tests."""
        self.data['arch'] = []
        self.data['variant_uid'] = []

        self.env = Mock(spec_set=list(self.env_spec.keys()))
        self.env.configure_mock(**self.env_spec)

        self.release = Mock(spec_set=list(self.release_spec.keys()))
        self.release.configure_mock(**self.release_spec)

    def check_details(self, PDCClientClassMock, PulpAdminConfigClassMock, expected_details,
                      expected_query, testMethod, query_result, commit):
        """Check the expected and actual."""
        # get mock instance and configure return value for get_paged
        instance = PDCClientClassMock.return_value
        api = instance.__getitem__.return_value

        api._.return_value = query_result

        pulpAdminConfig = PulpAdminConfigClassMock.return_value
        pulpAdminConfig.name = 'pulp-test'
        pulpAdminConfig.config_path = 'some_path.json'

        client = pulpAdminConfig.__getitem__.return_value
        client.__getitem__.return_value = 'admin'

        clear = PulpClearRepos(self.env, self.release, self.data['repo_family'],
                               self.data['variant_uid'], self.data['arch'])
        actual = clear.details(commit=commit)

        # check that class constructor is called once with the value
        # of env['pdc_server']
        PDCClientClassMock.assert_called_once_with('pdc-test', develop=True)

        # check that the right resource is accessed
        instance.__getitem__.assert_called_once_with('content-delivery-repos')
        # check that mock instance is called once, with the correct
        # parameters
        instance.__getitem__()._.assert_called_once_with(page_size=0, **expected_query)
        # check that the actual details are the same as the expected ones
        self.assertEquals(expected_details, actual, testMethod.__doc__)

    @patch('releng_sop.pulp_clear_repos.PDCClient', autospec=True)
    @patch('releng_sop.pulp_clear_repos.PulpAdminConfig', autospec=True)
    def test_details_no_commit_one_repo(self, PulpAdminConfigClassMock, PDCClientClassMock):
        """Check details with one repo found and two variants, while not commiting."""
        self.data['repo_family'] = 'htb'
        self.data['variant_uid'] = ['Server', 'Workstation']

        query_result = [
            {
                'name': 'rhel-7-workstation-htb-rpms',
            }
        ]

        expected_details = (self.details_base + self.details_good_repo +
                            self.details_variant + self.details_with_one_repo + "*** TEST MODE ***")
        expected_query_add = {
            'arch': self.data['arch'],
            'variant_uid': self.data['variant_uid'],
        }

        expected_query = dict(self.expected_query)
        expected_query.update(expected_query_add)

        commit = False
        testMethod = TestPulpClearRepos.test_details_no_commit_one_repo
        self.check_details(PDCClientClassMock, PulpAdminConfigClassMock, expected_details,
                           expected_query, testMethod, query_result, commit)

    @patch('releng_sop.pulp_clear_repos.PDCClient', autospec=True)
    @patch('releng_sop.pulp_clear_repos.PulpAdminConfig', autospec=True)
    def test_details_no_commit_more_repo(self, PulpAdminConfigClassMock, PDCClientClassMock):
        """Check details with two repos found and two arches, while not commiting."""
        self.data['repo_family'] = 'htb'
        self.data['arch'] = ['x86_64', 's390x']

        query_result = [
            {
                'name': 'rhel-7-workstation-htb-rpms',
            },
            {
                'name': 'rhel-7-server-htb-source-rpms',
            }
        ]

        expected_details = (self.details_base + self.details_good_repo +
                            self.details_arch + self.details_with_more_repo + "*** TEST MODE ***")
        expected_query_add = {
            'arch': self.data['arch'],
            'variant_uid': self.data['variant_uid'],
        }

        expected_query = dict(self.expected_query)
        expected_query.update(expected_query_add)

        commit = False
        testMethod = TestPulpClearRepos.test_details_no_commit_more_repo
        self.check_details(PDCClientClassMock, PulpAdminConfigClassMock, expected_details,
                           expected_query, testMethod, query_result, commit)

    @patch('releng_sop.pulp_clear_repos.PDCClient', autospec=True)
    @patch('releng_sop.pulp_clear_repos.PulpAdminConfig', autospec=True)
    def test_details_no_commit_no_repo(self, PulpAdminConfigClassMock, PDCClientClassMock):
        """Check details with no repo found and two variants and two arches, while not commiting."""
        self.data['repo_family'] = 'ht'
        self.data['arch'] = ['x86_64', 's390x']
        self.data['variant_uid'] = ['Server', 'Workstation']

        query_result = []

        expected_details = (self.details_base + self.details_diff_repo +
                            self.details_arch + self.details_variant + self.details_no_repo +
                            "*** TEST MODE ***")
        expected_query_add = {
            'arch': self.data['arch'],
            'variant_uid': self.data['variant_uid'],
        }

        expected_query = dict(self.expected_query_no_repo)
        expected_query.update(expected_query_add)

        commit = False
        testMethod = TestPulpClearRepos.test_details_no_commit_no_repo
        self.check_details(PDCClientClassMock, PulpAdminConfigClassMock, expected_details,
                           expected_query, testMethod, query_result, commit)

    @patch('releng_sop.pulp_clear_repos.PDCClient', autospec=True)
    @patch('releng_sop.pulp_clear_repos.PulpAdminConfig', autospec=True)
    def test_details_with_commit_one_repo(self,
                                          PulpAdminConfigClassMock, PDCClientClassMock):
        """Check details with one repo found and two variants and two arches, when commiting."""
        self.data['repo_family'] = 'htb'
        self.data['arch'] = ['x86_64', 's390x']
        self.data['variant_uid'] = ['Server', 'Workstation']

        query_result = [
            {
                'name': 'rhel-7-workstation-htb-rpms',
            }
        ]

        expected_details = (self.details_base + self.details_good_repo +
                            self.details_arch + self.details_variant + self.details_with_one_repo)
        expected_query_add = {
            'arch': self.data['arch'],
            'variant_uid': self.data['variant_uid'],
        }

        expected_query = dict(self.expected_query)
        expected_query.update(expected_query_add)

        commit = True
        testMethod = TestPulpClearRepos.test_details_with_commit_one_repo
        self.check_details(PDCClientClassMock, PulpAdminConfigClassMock, expected_details,
                           expected_query, testMethod, query_result, commit)

    @patch('releng_sop.pulp_clear_repos.PDCClient', autospec=True)
    @patch('releng_sop.pulp_clear_repos.PulpAdminConfig', autospec=True)
    def test_details_with_commit_more_repo(self, PulpAdminConfigClassMock, PDCClientClassMock):
        """Check details with two repos found and two variants, when commiting."""
        self.data['repo_family'] = 'htb'
        self.data['variant_uid'] = ['Server', 'Workstation']

        query_result = [
            {
                'name': 'rhel-7-workstation-htb-rpms',
            },
            {
                'name': 'rhel-7-server-htb-source-rpms',
            }
        ]

        expected_details = (self.details_base + self.details_good_repo +
                            self.details_variant + self.details_with_more_repo)
        expected_query_add = {
            'arch': self.data['arch'],
            'variant_uid': self.data['variant_uid'],
        }

        expected_query = dict(self.expected_query)
        expected_query.update(expected_query_add)

        commit = True
        testMethod = TestPulpClearRepos.test_details_with_commit_more_repo
        self.check_details(PDCClientClassMock, PulpAdminConfigClassMock, expected_details,
                           expected_query, testMethod, query_result, commit)

    @patch('releng_sop.pulp_clear_repos.PDCClient', autospec=True)
    @patch('releng_sop.pulp_clear_repos.PulpAdminConfig', autospec=True)
    def test_details_with_commit_no_repo(self, PulpAdminConfigClassMock, PDCClientClassMock):
        """Check details with no repo found and two arches, when commiting."""
        self.data['repo_family'] = 'ht'
        self.data['arch'] = ['x86_64', 's390x']

        query_result = []

        expected_details = (self.details_base + self.details_diff_repo +
                            self.details_arch + self.details_no_repo)
        expected_query_add = {
            'arch': self.data['arch'],
            'variant_uid': self.data['variant_uid'],
        }

        expected_query = dict(self.expected_query_no_repo)
        expected_query.update(expected_query_add)

        commit = True
        testMethod = TestPulpClearRepos.test_details_with_commit_no_repo
        self.check_details(PDCClientClassMock, PulpAdminConfigClassMock, expected_details,
                           expected_query, testMethod, query_result, commit)

    def check_get_cmd(self, PulpAdminConfigClassMock, expected, commit, testMethod, repos, password, addpassword):
        """Check the expected and actual."""
        clear = PulpClearRepos(self.env, self.release, self.data['repo_family'],
                               self.data['variant_uid'], self.data['arch'])
        clear.repos = repos
        clear.pulp_password = password

        pulpAdminConfig = PulpAdminConfigClassMock.return_value
        pulpAdminConfig.name = 'pulp-test'
        pulpAdminConfig.config_path = 'some_path.json'

        client = pulpAdminConfig.__getitem__.return_value
        client.__getitem__.return_value = 'admin'

        actual = clear.get_cmd(add_password=addpassword, commit=commit)

        self.assertEqual(actual, expected, testMethod.__doc__)

    @patch('releng_sop.pulp_clear_repos.PulpAdminConfig', autospec=True)
    def test_get_cmd_no_commit_no_repo(self, PulpAdminConfigClassMock):
        """Get command with no repo and password, while not commiting."""
        repos = []
        password = 'like'
        expected = []
        for repo in repos:
            expected_cmd = ["echo"]
            expected_cmd += "pulp-admin --config={config} --user={username} --password={passwd}".format(
                config=self.env_spec['config_path'],
                username=self.pulp_spec['user'],
                passwd=password).split()
            expected_cmd += "rpm repo remove rpm --filters='{filters}' --repo-id {repo}".format(
                filters='{}',
                repo=repo).split()
            expected.append(expected_cmd)
        commit = False
        addpassword = True

        testMethod = TestPulpClearRepos.test_get_cmd_no_commit_no_repo
        self.check_get_cmd(PulpAdminConfigClassMock, expected, commit, testMethod, repos, password, addpassword)

    @patch('releng_sop.pulp_clear_repos.PulpAdminConfig', autospec=True)
    def test_get_cmd_with_commit_one_repo(self, PulpAdminConfigClassMock):
        """Get command with one repo and password, when commiting."""
        repos = ['rhel-7-workstation-htb-rpms']
        password = 'like'
        expected = []
        for repo in repos:
            expected_cmd = "pulp-admin --config={config} --user={username} --password={passwd}".format(
                config=self.env_spec['config_path'],
                username=self.pulp_spec['user'],
                passwd=password).split()
            expected_cmd += "rpm repo remove rpm \
                --filters='{filters}' --repo-id {repo}".format(
                filters='{}',
                repo=repo).split()
            expected.append(expected_cmd)
        commit = True
        addpassword = True

        testMethod = TestPulpClearRepos.test_get_cmd_with_commit_one_repo
        self.check_get_cmd(PulpAdminConfigClassMock, expected, commit, testMethod, repos, password, addpassword)

    @patch('releng_sop.pulp_clear_repos.PulpAdminConfig', autospec=True)
    def test_get_cmd_with_commit_two_repo(self, PulpAdminConfigClassMock):
        """Get command with two repos when commiting."""
        repos = ['rhel-7-workstation-htb-rpms', 'rhel-7-server-htb-source-rpms']
        password = ''
        expected = []
        for repo in repos:
            expected_cmd = "pulp-admin --config={config} --user={username} rpm repo remove rpm".format(
                config=self.env_spec['config_path'],
                username=self.pulp_spec['user']).split()
            expected_cmd += "--filters='{filters}' --repo-id {repo}".format(
                filters='{}',
                repo=repo).split()
            expected.append(expected_cmd)
        commit = True
        addpassword = False

        testMethod = TestPulpClearRepos.test_get_cmd_with_commit_two_repo
        self.check_get_cmd(PulpAdminConfigClassMock, expected, commit, testMethod, repos, password, addpassword)


class TestKojiCloneTagParser(ParserTestBase, unittest.TestCase):
    """Set Arguments and Parser for Test generator."""

    ARGUMENTS = {
        'envHelp': {
            'arg': '--env ENV',
            'env_default': ['rhel-7.1', 'htb'],
            'env_set': ['rhel-7.1', 'htb', '--commit', "--env", "some_env"],
        },
        'helpReleaseId': {
            'arg': 'RELEASE_ID',
        },
        'commitHelp': {
            'arg': '--commit',
            'commit_default': ['rhel-7.1', 'htb'],
            'commit_set': ['rhel-7.1', 'htb', '--commit'],
        },
        'helpRepoFamily': {
            'arg': 'REPO_FAMILY',
        },
        'helpVariant': {
            'arg': '--variant',
        },
        'helpArch': {
            'arg': '--arch',
        },
    }

    PARSER = get_parser()

if __name__ == "__main__":
    unittest.main()
