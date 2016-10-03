#!/usr/bin/python
# -*- coding: utf-8 -*-


"""Tests of KojiCloneTagForReleaseMilestone script.
"""


import unittest
import os
import sys
from six import with_metaclass
from mock import Mock, patch

DIR = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(DIR, ".."))

from releng_sop.pulp_clear_repos import get_parser, PulpClearRepos  # noqa
#from tests.common import ParserTestBase  # noqa


class TestPulpClearRepos(unittest.TestCase):
    """Tests of methods from KojiCloneTagForReleaseMilestone class."""

    data = {
        "release_id": 'rhel-7.1',
        "service": 'pulp',
        "repo_family": 'htb',
        "repo_family_bad": 'ht',
        "content_format": 'rpm',
        "arch": 'x86_64',
        "variant_uid": 'Server',
    }

    repo_name = ('rhel-7-workstation-htb-rpms', 'rhel-7-workstation-htb-debug-rpms', 'rhel-7-workstation-htb-source-rpms')
    repo_one_name = repo_name[0]

    '''client_spec = {
        'name': 'dev',
        'get_paged': lambda resource, **query: data,
        '__getitem__': lambda self, item: Mock(spec_set=['_'])
    }'''

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

    repos = ['rhel-7-workstation-htb-rpms', 'rhel-7-server-htb-source-rpms']

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

    details_bad_repo = """ * repo_family:             {data[repo_family_bad]}
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

    @patch('releng_sop.pulp_clear_repos.PulpAdminConfig')
    def setUp(self, PulpAdminConfig):
        """Set up variables before tests."""
        self.env = Mock(spec_set=list(self.env_spec.keys()))
        self.env.configure_mock(**self.env_spec)

        self.release = Mock(spec_set=list(self.release_spec.keys()))
        self.release.configure_mock(**self.release_spec)

    def detail_client_mock(self, PDCClientClassMock, PulpAdminConfigClassMock, expected, expected_query_base, expected_query_add, nameFunction, result, commit):
        """Check the expected and actual."""
        # get mock instance and configure return value for get_paged
        instance = PDCClientClassMock.return_value
        api = instance.__getitem__.return_value

        api._.return_value = result

        pulpAdminConfig = PulpAdminConfigClassMock.return_value
        pulpAdminConfig.name = 'pulp-test'
        pulpAdminConfig.config_path = 'some_path.json'

        client = pulpAdminConfig.__getitem__.return_value
        client.__getitem__.return_value = 'admin'

        clear = PulpClearRepos(self.env, self.release, self.data['repo_family'], self.data['variant_uid'], self.data['arch'])
        actual = clear.details(commit)

        # check that class constructor is called once with the value
        # of env['pdc_server']
        PDCClientClassMock.assert_called_once_with('pdc-test', develop=True)

        # check that the right resource is accessed
        instance.__getitem__.assert_called_once_with('content-delivery-repos')
        # check that mock instance is called once, with the correct
        # parameters
        expected_query = expected_query_base
        expected_query.update(expected_query_add)
        instance.__getitem__()._.assert_called_once_with(page_size=0, **expected_query)
        # check that the actual details are the same as the expected ones
        self.assertEquals(expected, actual, nameFunction.__doc__)

    @patch('releng_sop.pulp_clear_repos.PDCClient', autospec=True)
    @patch('releng_sop.pulp_clear_repos.PulpAdminConfig', autospec=True)
    def test_details_no_commit_one_repo(self, PulpAdminConfigClassMock, PDCClientClassMock):
        """Get details, while not commiting."""
        self.data['repo_family'] = 'htb'
        self.data['arch'] = []
        self.data['variant_uid'] = []

        result = [
            {
                'name': 'rhel-7-workstation-htb-rpms',
            }
        ]

        expected = self.details_base + self.details_good_repo + self.details_with_one_repo + "*** TEST MODE ***"
        expected_query_add = {
            'arch': self.data['arch'],
            'variant_uid': self.data['variant_uid'],
        }

        commit = False
        nameFunction = TestPulpClearRepos.test_details_no_commit_one_repo
        self.detail_client_mock(PDCClientClassMock, PulpAdminConfigClassMock, expected, self.expected_query, expected_query_add, nameFunction, result, commit)

    @patch('releng_sop.pulp_clear_repos.PDCClient', autospec=True)
    @patch('releng_sop.pulp_clear_repos.PulpAdminConfig', autospec=True)
    def test_details_no_commit_more_repo(self, PulpAdminConfigClassMock, PDCClientClassMock):
        """Get details, while not commiting."""
        self.data['repo_family'] = 'htb'
        self.data['arch'] = []
        self.data['variant_uid'] = []

        result = [
            {
                'name': 'rhel-7-workstation-htb-rpms\n     rhel-7-server-htb-source-rpms',
            }
        ]

        expected = self.details_base + self.details_good_repo + self.details_with_more_repo + "*** TEST MODE ***"
        expected_query_add = {
            'arch': self.data['arch'],
            'variant_uid': self.data['variant_uid'],
        }

        commit = False
        nameFunction = TestPulpClearRepos.test_details_no_commit_more_repo
        self.detail_client_mock(PDCClientClassMock, PulpAdminConfigClassMock, expected, self.expected_query, expected_query_add, nameFunction, result, commit)

    @patch('releng_sop.pulp_clear_repos.PDCClient', autospec=True)
    @patch('releng_sop.pulp_clear_repos.PulpAdminConfig', autospec=True)
    def test_details_no_commit_no_repo(self, PulpAdminConfigClassMock, PDCClientClassMock):
        """Get details, while not commiting."""
        self.data['repo_family'] = 'ht'
        self.data['arch'] = []
        self.data['variant_uid'] = []

        result = [
            {
                'name': 'No repos found.',
            }
        ]

        expected = self.details_base + self.details_bad_repo + self.details_no_repo + "*** TEST MODE ***"
        expected_query_add = {
            'arch': self.data['arch'],
            'variant_uid': self.data['variant_uid'],
        }

        commit = False
        nameFunction = TestPulpClearRepos.test_details_no_commit_no_repo
        self.detail_client_mock(PDCClientClassMock, PulpAdminConfigClassMock, expected, self.expected_query_no_repo, expected_query_add, nameFunction, result, commit)

    @patch('releng_sop.pulp_clear_repos.PDCClient', autospec=True)
    @patch('releng_sop.pulp_clear_repos.PulpAdminConfig', autospec=True)
    def test_details_with_commit_one_repo(self, PulpAdminConfigClassMock, PDCClientClassMock):
        """Get details when commiting."""
        self.data['repo_family'] = 'htb'
        self.data['arch'] = []
        self.data['variant_uid'] = []

        result = [
            {
                'name': 'rhel-7-workstation-htb-rpms',
            }
        ]

        expected = self.details_base + self.details_good_repo + self.details_with_one_repo
        expected_query_add = {
            'arch': self.data['arch'],
            'variant_uid': self.data['variant_uid'],
        }

        commit = True
        nameFunction = TestPulpClearRepos.test_details_with_commit_one_repo
        self.detail_client_mock(PDCClientClassMock, PulpAdminConfigClassMock, expected, self.expected_query, expected_query_add, nameFunction, result, commit)

    @patch('releng_sop.pulp_clear_repos.PDCClient', autospec=True)
    @patch('releng_sop.pulp_clear_repos.PulpAdminConfig', autospec=True)
    def test_details_with_commit_more_repo(self, PulpAdminConfigClassMock, PDCClientClassMock):
        """Get details when commiting."""
        self.data['repo_family'] = 'htb'
        self.data['arch'] = []
        self.data['variant_uid'] = []

        result = [
            {
                'name': 'rhel-7-workstation-htb-rpms\n     rhel-7-server-htb-source-rpms',
            }
        ]

        expected = self.details_base + self.details_good_repo + self.details_with_more_repo
        expected_query_add = {
            'arch': self.data['arch'],
            'variant_uid': self.data['variant_uid'],
        }

        commit = True
        nameFunction = TestPulpClearRepos.test_details_with_commit_more_repo
        self.detail_client_mock(PDCClientClassMock, PulpAdminConfigClassMock, expected, self.expected_query, expected_query_add, nameFunction, result, commit)

    @patch('releng_sop.pulp_clear_repos.PDCClient', autospec=True)
    @patch('releng_sop.pulp_clear_repos.PulpAdminConfig', autospec=True)
    def test_details_with_commit_no_repo(self, PulpAdminConfigClassMock, PDCClientClassMock):
        """Get details when commiting."""
        self.data['repo_family'] = 'ht'
        self.data['arch'] = []
        self.data['variant_uid'] = []

        result = [
            {
                'name': 'No repos found.',
            }
        ]

        expected = self.details_base + self.details_bad_repo + self.details_no_repo
        expected_query_add = {
            'arch': self.data['arch'],
            'variant_uid': self.data['variant_uid'],
        }

        commit = True
        nameFunction = TestPulpClearRepos.test_details_with_commit_no_repo
        self.detail_client_mock(PDCClientClassMock, PulpAdminConfigClassMock, expected, self.expected_query_no_repo, expected_query_add, nameFunction, result, commit)

    @patch('releng_sop.pulp_clear_repos.PDCClient', autospec=True)
    @patch('releng_sop.pulp_clear_repos.PulpAdminConfig', autospec=True)
    def test_details_arch_no_commit_one_repo(self, PulpAdminConfigClassMock, PDCClientClassMock):
        """Get details, while not commiting."""
        self.data['repo_family'] = 'htb'
        self.data['arch'] = ['x86_64']
        self.data['variant_uid'] = []

        result = [
            {
                'name': 'rhel-7-workstation-htb-rpms',
            }
        ]

        expected = self.details_base + self.details_good_repo + self.details_arch + self.details_with_one_repo + "*** TEST MODE ***"
        expected_query_add = {
            'arch': self.data['arch'],
            'variant_uid': self.data['variant_uid'],
        }

        commit = False
        nameFunction = TestPulpClearRepos.test_details_arch_no_commit_one_repo
        self.detail_client_mock(PDCClientClassMock, PulpAdminConfigClassMock, expected, self.expected_query, expected_query_add, nameFunction, result, commit)

    @patch('releng_sop.pulp_clear_repos.PDCClient', autospec=True)
    @patch('releng_sop.pulp_clear_repos.PulpAdminConfig', autospec=True)
    def test_details_arch_no_commit_more_repo(self, PulpAdminConfigClassMock, PDCClientClassMock):
        """Get details, while not commiting."""
        self.data['repo_family'] = 'htb'
        self.data['arch'] = ['x86_64']
        self.data['variant_uid'] = []

        result = [
            {
                'name': 'rhel-7-workstation-htb-rpms\n     rhel-7-server-htb-source-rpms',
            }
        ]

        expected = self.details_base + self.details_good_repo + self.details_arch + self.details_with_more_repo + "*** TEST MODE ***"
        expected_query_add = {
            'arch': self.data['arch'],
            'variant_uid': self.data['variant_uid'],
        }

        commit = False
        nameFunction = TestPulpClearRepos.test_details_arch_no_commit_one_repo
        self.detail_client_mock(PDCClientClassMock, PulpAdminConfigClassMock, expected, self.expected_query, expected_query_add, nameFunction, result, commit)

    @patch('releng_sop.pulp_clear_repos.PDCClient', autospec=True)
    @patch('releng_sop.pulp_clear_repos.PulpAdminConfig', autospec=True)
    def test_details_arch_no_commit_no_repo(self, PulpAdminConfigClassMock, PDCClientClassMock):
        """Get details, while not commiting."""
        self.data['repo_family'] = 'ht'
        self.data['arch'] = ['x86_64']
        self.data['variant_uid'] = []

        result = [
            {
                'name': 'No repos found.',
            }
        ]

        expected = self.details_base + self.details_bad_repo + self.details_arch + self.details_no_repo + "*** TEST MODE ***"
        expected_query_add = {
            'arch': self.data['arch'],
            'variant_uid': self.data['variant_uid'],
        }

        commit = False
        nameFunction = TestPulpClearRepos.test_details_arch_no_commit_one_repo
        self.detail_client_mock(PDCClientClassMock, PulpAdminConfigClassMock, expected, self.expected_query_no_repo, expected_query_add, nameFunction, result, commit)

    @patch('releng_sop.pulp_clear_repos.PDCClient', autospec=True)
    @patch('releng_sop.pulp_clear_repos.PulpAdminConfig', autospec=True)
    def test_details_arch_with_commit_one_repo(self, PulpAdminConfigClassMock, PDCClientClassMock):
        """Get details when commiting."""
        self.data['repo_family'] = 'htb'
        self.data['arch'] = ['x86_64']
        self.data['variant_uid'] = []

        result = [
            {
                'name': 'rhel-7-workstation-htb-rpms',
            }
        ]

        expected = self.details_base + self.details_good_repo + self.details_arch + self.details_with_one_repo
        expected_query_add = {
            'arch': self.data['arch'],
            'variant_uid': self.data['variant_uid'],
        }

        commit = True
        nameFunction = TestPulpClearRepos.test_details_arch_with_commit_one_repo
        self.detail_client_mock(PDCClientClassMock, PulpAdminConfigClassMock, expected, self.expected_query, expected_query_add, nameFunction, result, commit)

    @patch('releng_sop.pulp_clear_repos.PDCClient', autospec=True)
    @patch('releng_sop.pulp_clear_repos.PulpAdminConfig', autospec=True)
    def test_details_arch_with_commit_more_repo(self, PulpAdminConfigClassMock, PDCClientClassMock):
        """Get details when commiting."""
        self.data['repo_family'] = 'htb'
        self.data['arch'] = ['x86_64']
        self.data['variant_uid'] = []

        result = [
            {
                'name': 'rhel-7-workstation-htb-rpms\n     rhel-7-server-htb-source-rpms',
            }
        ]

        expected = self.details_base + self.details_good_repo + self.details_arch + self.details_with_more_repo
        expected_query_add = {
            'arch': self.data['arch'],
            'variant_uid': self.data['variant_uid'],
        }

        commit = True
        nameFunction = TestPulpClearRepos.test_details_arch_with_commit_more_repo
        self.detail_client_mock(PDCClientClassMock, PulpAdminConfigClassMock, expected, self.expected_query, expected_query_add, nameFunction, result, commit)

    @patch('releng_sop.pulp_clear_repos.PDCClient', autospec=True)
    @patch('releng_sop.pulp_clear_repos.PulpAdminConfig', autospec=True)
    def test_details_arch_with_commit_no_repo(self, PulpAdminConfigClassMock, PDCClientClassMock):
        """Get details when commiting."""
        self.data['repo_family'] = 'ht'
        self.data['arch'] = ['x86_64']
        self.data['variant_uid'] = []

        result = [
            {
                'name': 'No repos found.',
            }
        ]

        expected = self.details_base + self.details_bad_repo + self.details_arch + self.details_no_repo
        expected_query_add = {
            'arch': self.data['arch'],
            'variant_uid': self.data['variant_uid'],
        }

        commit = True
        nameFunction = TestPulpClearRepos.test_details_arch_with_commit_no_repo
        self.detail_client_mock(PDCClientClassMock, PulpAdminConfigClassMock, expected, self.expected_query_no_repo, expected_query_add, nameFunction, result, commit)

    @patch('releng_sop.pulp_clear_repos.PDCClient', autospec=True)
    @patch('releng_sop.pulp_clear_repos.PulpAdminConfig', autospec=True)
    def test_details_variant_no_commit_one_repo(self, PulpAdminConfigClassMock, PDCClientClassMock):
        """Get details, while not commiting."""
        self.data['repo_family'] = 'htb'
        self.data['variant_uid'] = ['Server']
        self.data['arch'] = []

        result = [
            {
                'name': 'rhel-7-workstation-htb-rpms',
            }
        ]

        expected = self.details_base + self.details_good_repo + self.details_variant + self.details_with_one_repo + "*** TEST MODE ***"
        expected_query_add = {
            'arch': self.data['arch'],
            'variant_uid': self.data['variant_uid'],
        }

        commit = False
        nameFunction = TestPulpClearRepos.test_details_variant_no_commit_one_repo
        self.detail_client_mock(PDCClientClassMock, PulpAdminConfigClassMock, expected, self.expected_query, expected_query_add, nameFunction, result, commit)

    @patch('releng_sop.pulp_clear_repos.PDCClient', autospec=True)
    @patch('releng_sop.pulp_clear_repos.PulpAdminConfig', autospec=True)
    def test_details_variant_no_commit_more_repo(self, PulpAdminConfigClassMock, PDCClientClassMock):
        """Get details, while not commiting."""
        self.data['repo_family'] = 'htb'
        self.data['variant_uid'] = ['Server']
        self.data['arch'] = []

        result = [
            {
                'name': 'rhel-7-workstation-htb-rpms\n     rhel-7-server-htb-source-rpms',
            }
        ]

        expected = self.details_base + self.details_good_repo + self.details_variant + self.details_with_more_repo + "*** TEST MODE ***"
        expected_query_add = {
            'arch': self.data['arch'],
            'variant_uid': self.data['variant_uid'],
        }

        commit = False
        nameFunction = TestPulpClearRepos.test_details_variant_no_commit_more_repo
        self.detail_client_mock(PDCClientClassMock, PulpAdminConfigClassMock, expected, self.expected_query, expected_query_add, nameFunction, result, commit)

    @patch('releng_sop.pulp_clear_repos.PDCClient', autospec=True)
    @patch('releng_sop.pulp_clear_repos.PulpAdminConfig', autospec=True)
    def test_details_variant_no_commit_no_repo(self, PulpAdminConfigClassMock, PDCClientClassMock):
        """Get details, while not commiting."""
        self.data['repo_family'] = 'ht'
        self.data['variant_uid'] = ['Server']
        self.data['arch'] = []

        result = [
            {
                'name': 'No repos found.',
            }
        ]

        expected = self.details_base + self.details_bad_repo + self.details_variant + self.details_no_repo + "*** TEST MODE ***"
        expected_query_add = {
            'arch': self.data['arch'],
            'variant_uid': self.data['variant_uid'],
        }

        commit = False
        nameFunction = TestPulpClearRepos.test_details_variant_no_commit_no_repo
        self.detail_client_mock(PDCClientClassMock, PulpAdminConfigClassMock, expected, self.expected_query_no_repo, expected_query_add, nameFunction, result, commit)

    @patch('releng_sop.pulp_clear_repos.PDCClient', autospec=True)
    @patch('releng_sop.pulp_clear_repos.PulpAdminConfig', autospec=True)
    def test_details_variant_with_commit_one_repo(self, PulpAdminConfigClassMock, PDCClientClassMock):
        """Get details when commiting."""
        self.data['repo_family'] = 'htb'
        self.data['variant_uid'] = ['Server']
        self.data['arch'] = []

        result = [
            {
                'name': 'rhel-7-workstation-htb-rpms',
            }
        ]

        expected = self.details_base + self.details_good_repo + self.details_variant + self.details_with_one_repo
        expected_query_add = {
            'arch': self.data['arch'],
            'variant_uid': self.data['variant_uid'],
        }

        commit = True
        nameFunction = TestPulpClearRepos.test_details_variant_with_commit_one_repo
        self.detail_client_mock(PDCClientClassMock, PulpAdminConfigClassMock, expected, self.expected_query, expected_query_add, nameFunction, result, commit)

    @patch('releng_sop.pulp_clear_repos.PDCClient', autospec=True)
    @patch('releng_sop.pulp_clear_repos.PulpAdminConfig', autospec=True)
    def test_details_variant_with_commit_more_repo(self, PulpAdminConfigClassMock, PDCClientClassMock):
        """Get details when commiting."""
        self.data['repo_family'] = 'htb'
        self.data['variant_uid'] = ['Server']
        self.data['arch'] = []

        result = [
            {
                'name': 'rhel-7-workstation-htb-rpms\n     rhel-7-server-htb-source-rpms',
            }
        ]

        expected = self.details_base + self.details_good_repo + self.details_variant + self.details_with_more_repo
        expected_query_add = {
            'arch': self.data['arch'],
            'variant_uid': self.data['variant_uid'],
        }

        commit = True
        nameFunction = TestPulpClearRepos.test_details_variant_with_commit_more_repo
        self.detail_client_mock(PDCClientClassMock, PulpAdminConfigClassMock, expected, self.expected_query, expected_query_add, nameFunction, result, commit)

    @patch('releng_sop.pulp_clear_repos.PDCClient', autospec=True)
    @patch('releng_sop.pulp_clear_repos.PulpAdminConfig', autospec=True)
    def test_details_variant_with_commit_no_repo(self, PulpAdminConfigClassMock, PDCClientClassMock):
        """Get details when commiting."""
        self.data['repo_family'] = 'ht'
        self.data['variant_uid'] = ['Server']
        self.data['arch'] = []

        result = [
            {
                'name': 'No repos found.',
            }
        ]

        expected = self.details_base + self.details_bad_repo + self.details_variant + self.details_no_repo
        expected_query_add = {
            'arch': self.data['arch'],
            'variant_uid': self.data['variant_uid'],
        }

        commit = True
        nameFunction = TestPulpClearRepos.test_details_variant_with_commit_no_repo
        self.detail_client_mock(PDCClientClassMock, PulpAdminConfigClassMock, expected, self.expected_query_no_repo, expected_query_add, nameFunction, result, commit)

    @patch('releng_sop.pulp_clear_repos.PDCClient', autospec=True)
    @patch('releng_sop.pulp_clear_repos.PulpAdminConfig', autospec=True)
    def test_details_arch_variant_no_commit_one_repo(self, PulpAdminConfigClassMock, PDCClientClassMock):
        """Get details, while not commiting."""
        self.data['repo_family'] = 'htb'
        self.data['arch'] = ['x86_64']
        self.data['variant_uid'] = ['Server']

        result = [
            {
                'name': 'rhel-7-workstation-htb-rpms',
            }
        ]

        expected = self.details_base + self.details_good_repo + self.details_variant_arch + self.details_with_one_repo + "*** TEST MODE ***"
        expected_query_add = {
            'arch': self.data['arch'],
            'variant_uid': self.data['variant_uid'],
        }

        commit = False
        nameFunction = TestPulpClearRepos.test_details_arch_variant_no_commit_one_repo
        self.detail_client_mock(PDCClientClassMock, PulpAdminConfigClassMock, expected, self.expected_query, expected_query_add, nameFunction, result, commit)

    @patch('releng_sop.pulp_clear_repos.PDCClient', autospec=True)
    @patch('releng_sop.pulp_clear_repos.PulpAdminConfig', autospec=True)
    def test_details_arch_variant_no_commit_more_repo(self, PulpAdminConfigClassMock, PDCClientClassMock):
        """Get details, while not commiting."""
        self.data['repo_family'] = 'htb'
        self.data['arch'] = ['x86_64']
        self.data['variant_uid'] = ['Server']

        result = [
            {
                'name': 'rhel-7-workstation-htb-rpms\n     rhel-7-server-htb-source-rpms',
            }
        ]

        expected = self.details_base + self.details_good_repo + self.details_variant_arch + self.details_with_more_repo + "*** TEST MODE ***"
        expected_query_add = {
            'arch': self.data['arch'],
            'variant_uid': self.data['variant_uid'],
        }

        commit = False
        nameFunction = TestPulpClearRepos.test_details_arch_variant_no_commit_more_repo
        self.detail_client_mock(PDCClientClassMock, PulpAdminConfigClassMock, expected, self.expected_query, expected_query_add, nameFunction, result, commit)

    @patch('releng_sop.pulp_clear_repos.PDCClient', autospec=True)
    @patch('releng_sop.pulp_clear_repos.PulpAdminConfig', autospec=True)
    def test_details_arch_variant_no_commit_no_repo(self, PulpAdminConfigClassMock, PDCClientClassMock):
        """Get details, while not commiting."""
        self.data['repo_family'] = 'ht'
        self.data['arch'] = ['x86_64']
        self.data['variant_uid'] = ['Server']

        result = [
            {
                'name': 'No repos found.',
            }
        ]

        expected = self.details_base + self.details_bad_repo + self.details_variant_arch + self.details_no_repo + "*** TEST MODE ***"
        expected_query_add = {
            'arch': self.data['arch'],
            'variant_uid': self.data['variant_uid'],
        }

        commit = False
        nameFunction = TestPulpClearRepos.test_details_arch_variant_no_commit_no_repo
        self.detail_client_mock(PDCClientClassMock, PulpAdminConfigClassMock, expected, self.expected_query_no_repo, expected_query_add, nameFunction, result, commit)

    @patch('releng_sop.pulp_clear_repos.PDCClient', autospec=True)
    @patch('releng_sop.pulp_clear_repos.PulpAdminConfig', autospec=True)
    def test_details_arch_variant_with_commit_one_repo(self, PulpAdminConfigClassMock, PDCClientClassMock):
        """Get details when commiting."""
        self.data['repo_family'] = 'htb'
        self.data['arch'] = ['x86_64']
        self.data['variant_uid'] = ['Server']

        result = [
            {
                'name': 'rhel-7-workstation-htb-rpms',
            }
        ]

        expected = self.details_base + self.details_good_repo + self.details_variant_arch + self.details_with_one_repo
        expected_query_add = {
            'arch': self.data['arch'],
            'variant_uid': self.data['variant_uid'],
        }

        commit = True
        nameFunction = TestPulpClearRepos.test_details_arch_variant_with_commit_one_repo
        self.detail_client_mock(PDCClientClassMock, PulpAdminConfigClassMock, expected, self.expected_query, expected_query_add, nameFunction, result, commit)

    @patch('releng_sop.pulp_clear_repos.PDCClient', autospec=True)
    @patch('releng_sop.pulp_clear_repos.PulpAdminConfig', autospec=True)
    def test_details_arch_variant_with_commit_more_repo(self, PulpAdminConfigClassMock, PDCClientClassMock):
        """Get details when commiting."""
        self.data['repo_family'] = 'htb'
        self.data['arch'] = ['x86_64']
        self.data['variant_uid'] = ['Server']

        result = [
            {
                'name': 'rhel-7-workstation-htb-rpms\n     rhel-7-server-htb-source-rpms',
            }
        ]

        expected = self.details_base + self.details_good_repo + self.details_variant_arch + self.details_with_more_repo
        expected_query_add = {
            'arch': self.data['arch'],
            'variant_uid': self.data['variant_uid'],
        }

        commit = True
        nameFunction = TestPulpClearRepos.test_details_arch_variant_with_commit_more_repo
        self.detail_client_mock(PDCClientClassMock, PulpAdminConfigClassMock, expected, self.expected_query, expected_query_add, nameFunction, result, commit)

    @patch('releng_sop.pulp_clear_repos.PDCClient', autospec=True)
    @patch('releng_sop.pulp_clear_repos.PulpAdminConfig', autospec=True)
    def test_details_arch_variant_with_commit_no_repo(self, PulpAdminConfigClassMock, PDCClientClassMock):
        """Get details when commiting."""
        self.data['repo_family'] = 'ht'
        self.data['arch'] = ['x86_64']
        self.data['variant_uid'] = ['Server']

        result = [
            {
                'name': 'No repos found.',
            }
        ]

        expected = self.details_base + self.details_bad_repo + self.details_variant_arch + self.details_no_repo
        expected_query_add = {
            'arch': self.data['arch'],
            'variant_uid': self.data['variant_uid'],
        }

        commit = True
        nameFunction = TestPulpClearRepos.test_details_arch_variant_with_commit_no_repo
        self.detail_client_mock(PDCClientClassMock, PulpAdminConfigClassMock, expected, self.expected_query_no_repo, expected_query_add, nameFunction, result, commit)

    def share_get_cmd(self, PulpAdminConfigClassMock, expected, commit, nameFunction):
        """Check the expected and actual."""
        clear = PulpClearRepos(self.env, self.release, self.data['repo_family'], self.data['variant_uid'], self.data['arch'])
        clear.repos = self.repos
        pulpAdminConfig = PulpAdminConfigClassMock.return_value
        pulpAdminConfig.name = 'pulp-test'
        pulpAdminConfig.config_path = 'some_path.json'

        client = pulpAdminConfig.__getitem__.return_value
        client.__getitem__.return_value = 'admin'
        if commit:
            actual = [' '.join(cmdlist) for cmdlist in clear.get_cmd(commit=True)]
        else:
            actual = [' '.join(cmdlist) for cmdlist in clear.get_cmd()]

        self.assertEqual(actual, expected, self.test_get_cmd_no_commit.__doc__)

    @patch('releng_sop.pulp_clear_repos.PulpAdminConfig', autospec=True)
    def test_get_cmd_no_commit(self, PulpAdminConfigClassMock):
        """Get command, while not commiting."""
        expected = []
        for repo in self.repos:
            expected_cmd = ["echo"]
            expected_cmd += "pulp-admin --config={config} --user={username} rpm repo remove rpm --filters='{filters}' --repo-id {repo}".format(
                config=self.env_spec['config_path'],
                username=self.pulp_spec['user'],
                passwd=self.pulp_spec['password'],
                filters='{}',
                repo=repo).split()
            expected.append(' '.join(expected_cmd))
        commit = False

        nameFunction = TestPulpClearRepos.test_get_cmd_no_commit
        self.share_get_cmd(PulpAdminConfigClassMock, expected, commit, nameFunction)

    @patch('releng_sop.pulp_clear_repos.PulpAdminConfig', autospec=True)
    def test_get_cmd_with_commit(self, PulpAdminConfigClassMock):
        """Get command when commiting."""
        expected = []
        for repo in self.repos:
            expected_cmd = "pulp-admin --config={config} --user={username} rpm repo remove rpm --filters='{filters}' --repo-id {repo}".format(
                config=self.env_spec['config_path'],
                username=self.pulp_spec['user'],
                passwd=self.pulp_spec['password'],
                filters='{}',
                repo=repo).split()
            expected.append(' '.join(expected_cmd))
        commit = True

        nameFunction = TestPulpClearRepos.test_get_cmd_no_commit
        self.share_get_cmd(PulpAdminConfigClassMock, expected, commit, nameFunction)


class HelpNotEmptyMeta(type):
    """Test generator whether some help is empty."""

    def __new__(meta, name, bases, dct):
        """Create new test."""
        def gen_test(a):
            def test(self):
                for line in self.HELPTEXT:
                    if line.strip().startswith(a):
                        helpAtr = line.replace(a, '').strip()
                        self.assertNotEqual(len(helpAtr), 0, 'Help in %s argument is empty.' % a)
                        return
                self.assertTrue(False, '%s not in help text.' % a)
            return test

        for tname, a in dct.get('ARGUMENTS', dict()).items():
            test_name = "test_%s" % tname
            dct[test_name] = gen_test(a["arg"])
        return type.__new__(meta, name, bases, dct)


class ParserTestBase(with_metaclass(HelpNotEmptyMeta), object):
    """SetUpClass and tearDownClass for test generator whether some help is empty."""

    @classmethod
    def setUpClass(cls):
        """Set up variables before tests."""
        with open('test.txt', 'w') as f:
            cls.PARSER.print_help(f)

        cls.HELPTEXT = open('test.txt').read().split('\n')
        os.remove('test.txt')

    def test_commit_default(self):
        """Test whether --commit have default value False."""
        arguments = self.ARGUMENTS["commitHelp"]["commit_default"]
        args = self.PARSER.parse_args(arguments)
        self.assertTrue(hasattr(args, "commit"), 'commit argument is missing')
        self.assertFalse(args.commit, 'Default value for commit should be False')

    def test_commit_set(self):
        """Test whether --commit is set."""
        arguments = self.ARGUMENTS["commitHelp"]["commit_set"]
        args = self.PARSER.parse_args(arguments)
        self.assertTrue(args.commit, 'Value for commit should be True')


class TestKojiCloneTagParser(ParserTestBase, unittest.TestCase):
    """Set Arguments and Parser for Test generator."""

    ARGUMENTS = {
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
