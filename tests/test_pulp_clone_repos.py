#!/usr/bin/python
# -*- coding: utf-8 -*-


"""Tests of PulpCloneRepo script.
"""


from __future__ import print_function, unicode_literals
import unittest
import os
import sys
from mock import Mock, patch, call
from releng_sop.common import UsageError

DIR = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(DIR, ".."))

from releng_sop.pulp_clone_repos import get_parser, PulpCloneRepos  # noqa
from tests.common import ParserTestBase  # noqa


class TestPulpCloneRepos(unittest.TestCase):
    """Tests of methods from KojiCloneTagForReleaseMilestone class."""

    data_from_all = {
        "release_id": 'rhel-7.1',
        "service": "pulp",
        "repo_family": 'htb',
        "content_format": 'rpm',
        "content_category": None,
        "arch": ['x86_64', 's390x'],
        "variant_uid": ['Server', 'Workstation'],
        "shadow": False,
    }

    data_to_all = {
        "release_id": 'rhel-6.1',
        "service": "pulp",
        "repo_family": 'htb',
        "content_format": 'rpm',
        "content_category": None,
        "arch": ['x86_64', 's390x'],
        "variant_uid": ['Server', 'Workstation'],
        "shadow": False,
    }

    release_spec_from = {
        'name': 'rhel-7.1',
        'config_path': 'some-rhel-7.1.json',
        'config_data': {},
        '__getitem__': lambda self, item: self.config_data[item],
    }

    release_spec_to = {
        'name': 'rhel-6.1',
        'config_path': 'some-rhel-6.1.json',
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
    details_base = """Pulp clone repos
 * env name:                {env[name]}
 * env config:              {env[config_path]}
 * release source           {release[config_path]}
 * PDC server:              pdc-test
 * release_id from:         {data_from[release_id]}
 * release_id to:           {data_to[release_id]}
""".format(env=env_spec, release=release_spec_from, data_from=data_from_all,
           data_to=data_to_all)

    details_base_conti = """
 * content_format:          {data_from[content_format]}
 * pulp config:             {pulp[config]}
 * pulp config path:        {pulp[config_path]}
 * pulp user:               {pulp[user]}
 * repo_family:             {data_from[repo_family]}
""".format(pulp=pulp_spec, data_from=data_from_all,
           data_to=data_to_all)

    details_with_one_repo = """ * repo from:
     rhel-6-workstation-htb-rpms
 * repo to:
     rhel-7-workstation-htb-rpms
"""

    details_with_more_repo = """ * repo from:
     rhel-6-server-htb-source-rpms
     rhel-6-workstation-htb-rpms
 * repo to:
     rhel-7-server-htb-source-rpms
     rhel-7-workstation-htb-rpms
"""

    details_no_repo = """ * repo from:
     No repos found.
 * repo to:
     No repos found.
"""

    details_arch = """ * arches:
     {arches}
""".format(arches="\n     ".join(data_from_all['arch']))

    details_variant = """ * variants:
     {variants}
""".format(variants="\n     ".join(data_from_all['variant_uid']))

    expected_query_from = {
        "release_id": "rhel-7.1",
        "service": "pulp",
        "repo_family": "htb",
        "content_format": "rpm",
        "shadow": False,
    }

    expected_query_to = {
        "release_id": "rhel-6.1",
        "service": "pulp",
        "repo_family": "htb",
        "content_format": "rpm",
        "shadow": False,
    }

    def setUp(self):
        """Set up variables before tests."""
        self.data_from_all['arch'] = []
        self.data_from_all['variant_uid'] = []

        self.env = Mock(spec_set=list(self.env_spec.keys()))
        self.env.configure_mock(**self.env_spec)

        self.release_from = Mock(spec_set=list(self.release_spec_from.keys()))
        self.release_from.configure_mock(**self.release_spec_from)

        self.release_to = Mock(spec_set=list(self.release_spec_to.keys()))
        self.release_to.configure_mock(**self.release_spec_to)

    def check_details(self, PDCClientClassMock, PulpAdminConfigClassMock, expected_details,
                      expected_query_from, expected_query_to, testMethod, query_result_from,
                      query_result_to, commit, skip_repo_check):
        """Check the expected and actual."""
        # get mock instance and configure return value for get_paged
        instance = PDCClientClassMock.return_value
        api = instance.__getitem__.return_value

        api._.side_effect = iter([query_result_from, query_result_to])

        pulpAdminConfig = PulpAdminConfigClassMock.return_value
        pulpAdminConfig.name = 'pulp-test'
        pulpAdminConfig.config_path = 'some_path.json'

        client = pulpAdminConfig.__getitem__.return_value
        client.__getitem__.return_value = 'admin'

        clone = PulpCloneRepos(self.env, self.release_from, self.release_to, self.data_from_all['repo_family'],
                               self.data_from_all['variant_uid'], self.data_from_all['arch'],
                               self.data_from_all['content_category'], skip_repo_check)
        actual = clone.details(commit=commit)

        # check that class constructor is called once with the value
        # of env['pdc_server']
        PDCClientClassMock.assert_called_once_with('pdc-test', develop=True)

        instance.__getitem__.assert_called_with('content-delivery-repos')
        # check that the API is called twice
        self.assertEquals(instance.__getitem__.call_count, 2)

        # assert_called_with behaves strangely, and making to
        # of these won't help. Instead we have to construct
        # a list of expected call objects, and check that
        # this list matches the actual call list that happened
        expected_calls = [
            call(page_size=0, **expected_query_from),
            call(page_size=0, **expected_query_to), ]

        self.assertEquals(api._.call_args_list, expected_calls)

        # check that there are exactly 2 queries made
        self.assertEquals(instance.__getitem__()._.call_count, 2)

        print(actual)
        print(expected_details)

        # check that the actual details are the same as the expected ones
        self.assertEquals(expected_details, actual, testMethod.__doc__)

    def check_details_error(self, PDCClientClassMock, PulpAdminConfigClassMock, expected_details,
                            expected_query_from, expected_query_to, testMethod, query_result_from,
                            query_result_to, commit, skip_repo_check):
        """Check the expected and actual."""
        # get mock instance and configure return value for get_paged
        instance = PDCClientClassMock.return_value
        api = instance.__getitem__.return_value

        api._.side_effect = iter([query_result_from, query_result_to])

        pulpAdminConfig = PulpAdminConfigClassMock.return_value
        pulpAdminConfig.name = 'pulp-test'
        pulpAdminConfig.config_path = 'some_path.json'

        client = pulpAdminConfig.__getitem__.return_value
        client.__getitem__.return_value = 'admin'

        clone = PulpCloneRepos(self.env, self.release_from, self.release_to, self.data_from_all['repo_family'],
                               self.data_from_all['variant_uid'], self.data_from_all['arch'],
                               self.data_from_all['content_category'], skip_repo_check)
        '''with self.assertRaises(UsageError) as context:
            clone.details(commit=commit)'''
        self.assertRaises(UsageError, clone.details, commit=commit)
        '''# check that class constructor is called once with the value
        # of env['pdc_server']
        PDCClientClassMock.assert_called_once_with('pdc-test', develop=True)

        instance.__getitem__.assert_called_with('content-delivery-repos')
        # check that the API is called twice
        self.assertEquals(instance.__getitem__.call_count, 2)

        # assert_called_with behaves strangely, and making to
        # of these won't help. Instead we have to construct
        # a list of expected call objects, and check that
        # this list matches the actual call list that happened
        expected_calls = [
            call(page_size=0, **expected_query_from),
            call(page_size=0, **expected_query_to), ]

        self.assertEquals(api._.call_args_list, expected_calls)

        # check that there are exactly 2 queries made
        self.assertEquals(instance.__getitem__()._.call_count, 2)'''

    @patch('releng_sop.pulp_clone_repos.PDCClient', autospec=True)
    @patch('releng_sop.pulp_clone_repos.PulpAdminConfig', autospec=True)
    def test_details_no_commit_one_repo(self, PulpAdminConfigClassMock, PDCClientClassMock):
        """Check details with one repo found and two arches and two variant and with skip-repo-check,
        while not commiting.
        """
        self.data_from_all['arch'] = ['x86_64', 's390x']
        self.data_from_all['variant_uid'] = ['Server', 'Workstation']
        self.data_from_all['content_category'] = 'source'

        query_result_from = [
            {
                'arch': 'x86_64',
                'variant_uid': 'Workstation',
                'content_category': 'source',
                'name': 'rhel-6-workstation-htb-rpms',
            }
        ]

        query_result_to = [
            {
                'arch': 'x86_64',
                'variant_uid': 'Server',
                'content_category': 'source',
                'name': 'rhel-7-server-htb-source-rpms',
            },
            {
                'arch': 'x86_64',
                'variant_uid': 'Workstation',
                'content_category': 'source',
                'name': 'rhel-7-workstation-htb-rpms',
            },

        ]

        expected_details = (self.details_base +
                            " * content_category:        %s" % self.data_from_all['content_category'] +
                            self.details_base_conti + self.details_arch + self.details_variant +
                            self.details_with_one_repo + "*** TEST MODE ***")
        expected_query_add = {
            'arch': self.data_from_all['arch'],
            'variant_uid': self.data_from_all['variant_uid'],
            'content_category': self.data_from_all['content_category'],
        }

        expected_query_from = dict(self.expected_query_from)
        expected_query_from.update(expected_query_add)

        expected_query_to = dict(self.expected_query_to)
        expected_query_to.update(expected_query_add)

        commit = False
        skip_repo_check = True

        testMethod = TestPulpCloneRepos.test_details_with_commit_one_repo
        self.check_details(PDCClientClassMock, PulpAdminConfigClassMock, expected_details,
                           expected_query_from, expected_query_to, testMethod, query_result_from,
                           query_result_to, commit, skip_repo_check)

    '''@patch('releng_sop.pulp_clone_repos.PDCClient', autospec=True)
    @patch('releng_sop.pulp_clone_repos.PulpAdminConfig', autospec=True)
    def test_details_no_commit_more_repo(self, PulpAdminConfigClassMock, PDCClientClassMock):
        """Check details with more repo found and two variants and without skip-repo-check,
        while not commiting.
        """
        self.data_from_all['variant_uid'] = ['Server', 'Workstation']
        self.data_from_all['content_category'] = 'source'
        query_result_from = [
            {
                'arch': 'x86_64',
                'variant_uid': 'Server',
                'content_category': 'source',
                'name': 'rhel-6-server-htb-source-rpms',
            },
            {
                'arch': 'x86_64',
                'variant_uid': 'Workstation',
                'content_category': 'source',
                'name': 'rhel-6-workstation-htb-rpms',
            }
        ]
        query_result_to = [
            {
                'arch': 'x86_64',
                'variant_uid': 'Workstation',
                'content_category': 'source',
                'name': 'rhel-7-workstation-htb-rpms',
            },
            {
                'arch': 'x86_64',
                'variant_uid': 'Server',
                'content_category': 'source',
                'name': 'rhel-7-server-htb-source-rpms',
            }
        ]

        expected_details = (self.details_base +
                            " * content_category:        %s" % self.data_from_all['content_category'] +
                            self.details_base_conti + self.details_variant +
                            self.details_with_more_repo + "*** TEST MODE ***")
        expected_query_add = {
            'arch': self.data_from_all['arch'],
            'variant_uid': self.data_from_all['variant_uid'],
            'content_category': self.data_from_all['content_category'],
        }

        expected_query_from = dict(self.expected_query_from)
        expected_query_from.update(expected_query_add)

        expected_query_to = dict(self.expected_query_to)
        expected_query_to.update(expected_query_add)

        commit = False
        skip_repo_check = False

        testMethod = TestPulpCloneRepos.test_details_no_commit_one_repo
        self.check_details(PDCClientClassMock, PulpAdminConfigClassMock, expected_details,
                           expected_query_from, expected_query_to, testMethod, query_result_from,
                           query_result_to, commit, skip_repo_check)'''

    @patch('releng_sop.pulp_clone_repos.PDCClient', autospec=True)
    @patch('releng_sop.pulp_clone_repos.PulpAdminConfig', autospec=True)
    def test_details_no_commit_no_repo(self, PulpAdminConfigClassMock, PDCClientClassMock):
        """Check details with no repo found and two arches and with skip-repo-check,
        while not commiting.
        """
        self.data_from_all['arch'] = ['x86_64', 's390x']
        self.data_from_all['content_category'] = 'source'

        query_result_from = []
        query_result_to = []

        expected_details = (self.details_base +
                            " * content_category:        %s" % self.data_from_all['content_category'] +
                            self.details_base_conti + self.details_arch +
                            self.details_no_repo + "*** TEST MODE ***")
        expected_query_add = {
            'arch': self.data_from_all['arch'],
            'variant_uid': self.data_from_all['variant_uid'],
            'content_category': self.data_from_all['content_category'],
        }

        expected_query_from = dict(self.expected_query_from)
        expected_query_from.update(expected_query_add)

        expected_query_to = dict(self.expected_query_to)
        expected_query_to.update(expected_query_add)

        commit = False
        skip_repo_check = True

        testMethod = TestPulpCloneRepos.test_details_with_commit_no_repo
        self.check_details(PDCClientClassMock, PulpAdminConfigClassMock, expected_details,
                           expected_query_from, expected_query_to, testMethod, query_result_from,
                           query_result_to, commit, skip_repo_check)

    @patch('releng_sop.pulp_clone_repos.PDCClient', autospec=True)
    @patch('releng_sop.pulp_clone_repos.PulpAdminConfig', autospec=True)
    def test_details_no_commit_error(self, PulpAdminConfigClassMock, PDCClientClassMock):
        """Check details with error and two variants and without skip-repo-check,
        while not commiting.
        """
        query_result_from = [
            {
                'arch': 'x86_64',
                'variant_uid': 'Server',
                'content_category': 'source',
                'name': 'rhel-6-server-htb-source-rpms'
            },
            {
                'arch': 'x86_64',
                'variant_uid': 'Workstation',
                'content_category': 'source',
                'name': 'rhel-6-workstation-htb-rpms'
            }
        ]
        query_result_to = [
            {
                'arch': 'x86_64',
                'variant_uid': 'Workstation',
                'content_category': 'source',
                'name': 'rhel-7-workstation-htb-rpms'
            }
        ]

        expected_details = "UsageError: Error"
        expected_query_add = {
            'arch': self.data_from_all['arch'],
            'variant_uid': self.data_from_all['variant_uid'],
        }

        expected_query_from = dict(self.expected_query_from)
        expected_query_from.update(expected_query_add)

        expected_query_to = dict(self.expected_query_to)
        expected_query_to.update(expected_query_add)

        commit = False
        skip_repo_check = False

        testMethod = TestPulpCloneRepos.test_details_no_commit_one_repo
        self.check_details_error(PDCClientClassMock, PulpAdminConfigClassMock, expected_details,
                                 expected_query_from, expected_query_to, testMethod, query_result_from,
                                 query_result_to, commit, skip_repo_check)

    @patch('releng_sop.pulp_clone_repos.PDCClient', autospec=True)
    @patch('releng_sop.pulp_clone_repos.PulpAdminConfig', autospec=True)
    def test_details_with_commit_one_repo(self, PulpAdminConfigClassMock, PDCClientClassMock):
        """Check details with one repo found and two arches and two variant and with skip-repo-check,
        when not commiting.
        """
        self.data_from_all['arch'] = ['x86_64', 's390x']
        self.data_from_all['variant_uid'] = ['Server', 'Workstation']
        self.data_from_all['content_category'] = 'source'

        query_result_from = [
            {
                'arch': 'x86_64',
                'variant_uid': 'Workstation',
                'content_category': 'source',
                'name': 'rhel-6-workstation-htb-rpms',
            }
        ]

        query_result_to = [
            {
                'arch': 'x86_64',
                'variant_uid': 'Server',
                'content_category': 'source',
                'name': 'rhel-7-server-htb-source-rpms',
            },
            {
                'arch': 'x86_64',
                'variant_uid': 'Workstation',
                'content_category': 'source',
                'name': 'rhel-7-workstation-htb-rpms',
            },

        ]

        expected_details = (self.details_base +
                            " * content_category:        %s" % self.data_from_all['content_category'] +
                            self.details_base_conti + self.details_arch + self.details_variant +
                            self.details_with_one_repo)
        expected_query_add = {
            'arch': self.data_from_all['arch'],
            'variant_uid': self.data_from_all['variant_uid'],
            'content_category': self.data_from_all['content_category'],
        }

        expected_query_from = dict(self.expected_query_from)
        expected_query_from.update(expected_query_add)

        expected_query_to = dict(self.expected_query_to)
        expected_query_to.update(expected_query_add)

        commit = True
        skip_repo_check = True

        testMethod = TestPulpCloneRepos.test_details_with_commit_one_repo
        self.check_details(PDCClientClassMock, PulpAdminConfigClassMock, expected_details,
                           expected_query_from, expected_query_to, testMethod, query_result_from,
                           query_result_to, commit, skip_repo_check)

    '''@patch('releng_sop.pulp_clone_repos.PDCClient', autospec=True)
    @patch('releng_sop.pulp_clone_repos.PulpAdminConfig', autospec=True)
    def test_details_with_commit_more_repo(self, PulpAdminConfigClassMock, PDCClientClassMock):
        """Check details with more repo found and two variants and without skip-repo-check,
        when commiting.
        """
        self.data_from_all['variant_uid'] = ['Server', 'Workstation']
        self.data_from_all['content_category'] = 'source'
        query_result_from = [
            {
                'arch': 'x86_64',
                'variant_uid': 'Server',
                'content_category': 'source',
                'name': 'rhel-6-server-htb-source-rpms',
            },
            {
                'arch': 'x86_64',
                'variant_uid': 'Workstation',
                'content_category': 'source',
                'name': 'rhel-6-workstation-htb-rpms',
            }
        ]
        query_result_to = [
            {
                'arch': 'x86_64',
                'variant_uid': 'Workstation',
                'content_category': 'source',
                'name': 'rhel-7-workstation-htb-rpms',
            },
            {
                'arch': 'x86_64',
                'variant_uid': 'Server',
                'content_category': 'source',
                'name': 'rhel-7-server-htb-source-rpms',
            }
        ]

        expected_details = (self.details_base +
                            " * content_category:        %s" % self.data_from_all['content_category'] +
                            self.details_base_conti + self.details_variant +
                            self.details_with_more_repo)
        expected_query_add = {
            'arch': self.data_from_all['arch'],
            'variant_uid': self.data_from_all['variant_uid'],
            'content_category': self.data_from_all['content_category'],
        }

        expected_query_from = dict(self.expected_query_from)
        expected_query_from.update(expected_query_add)

        expected_query_to = dict(self.expected_query_to)
        expected_query_to.update(expected_query_add)

        commit = True
        skip_repo_check = False

        testMethod = TestPulpCloneRepos.test_details_no_commit_one_repo
        self.check_details(PDCClientClassMock, PulpAdminConfigClassMock, expected_details,
                           expected_query_from, expected_query_to, testMethod, query_result_from,
                           query_result_to, commit, skip_repo_check)'''

    @patch('releng_sop.pulp_clone_repos.PDCClient', autospec=True)
    @patch('releng_sop.pulp_clone_repos.PulpAdminConfig', autospec=True)
    def test_details_with_commit_no_repo(self, PulpAdminConfigClassMock, PDCClientClassMock):
        """Check details with no repo found and two arches and with skip-repo-check,
        when commiting.
        """
        self.data_from_all['arch'] = ['x86_64', 's390x']
        self.data_from_all['content_category'] = 'source'

        query_result_from = []
        query_result_to = []

        expected_details = (self.details_base +
                            " * content_category:        %s" % self.data_from_all['content_category'] +
                            self.details_base_conti + self.details_arch +
                            self.details_no_repo)
        expected_query_add = {
            'arch': self.data_from_all['arch'],
            'variant_uid': self.data_from_all['variant_uid'],
            'content_category': self.data_from_all['content_category'],
        }

        expected_query_from = dict(self.expected_query_from)
        expected_query_from.update(expected_query_add)

        expected_query_to = dict(self.expected_query_to)
        expected_query_to.update(expected_query_add)

        commit = True
        skip_repo_check = True

        testMethod = TestPulpCloneRepos.test_details_with_commit_no_repo
        self.check_details(PDCClientClassMock, PulpAdminConfigClassMock, expected_details,
                           expected_query_from, expected_query_to, testMethod, query_result_from,
                           query_result_to, commit, skip_repo_check)

    @patch('releng_sop.pulp_clone_repos.PDCClient', autospec=True)
    @patch('releng_sop.pulp_clone_repos.PulpAdminConfig', autospec=True)
    def test_details_with_commit_error(self, PulpAdminConfigClassMock, PDCClientClassMock):
        """Check details with error and two variants and without skip-repo-check,
        when commiting.
        """
        query_result_from = [
            {
                'arch': 'x86_64',
                'variant_uid': 'Server',
                'content_category': 'source',
                'name': 'rhel-6-server-htb-source-rpms'
            },
            {
                'arch': 'x86_64',
                'variant_uid': 'Workstation',
                'content_category': 'source',
                'name': 'rhel-6-workstation-htb-rpms'
            }
        ]
        query_result_to = [
            {
                'arch': 'x86_64',
                'variant_uid': 'Workstation',
                'content_category': 'source',
                'name': 'rhel-7-workstation-htb-rpms'
            }
        ]

        expected_details = "UsageError: Error"
        expected_query_add = {
            'arch': self.data_from_all['arch'],
            'variant_uid': self.data_from_all['variant_uid'],
        }

        expected_query_from = dict(self.expected_query_from)
        expected_query_from.update(expected_query_add)

        expected_query_to = dict(self.expected_query_to)
        expected_query_to.update(expected_query_add)

        commit = True
        skip_repo_check = False

        testMethod = TestPulpCloneRepos.test_details_with_commit_error
        self.check_details_error(PDCClientClassMock, PulpAdminConfigClassMock, expected_details,
                                 expected_query_from, expected_query_to, testMethod, query_result_from,
                                 query_result_to, commit, skip_repo_check)

    def check_get_cmd(self, PulpAdminConfigClassMock, expected, commit, testMethod, cloned,
                      skip_repo_check, password, addPassword):
        """Check the expected and actual."""
        clone = PulpCloneRepos(self.env, self.release_from, self.release_to,
                               self.data_from_all['repo_family'], self.data_from_all['variant_uid'],
                               self.data_from_all['arch'], self.data_from_all['content_category'],
                               skip_repo_check)

        clone.cloned = cloned
        clone.pulp_password = password

        pulpAdminConfig = PulpAdminConfigClassMock.return_value
        pulpAdminConfig.name = 'pulp-test'
        pulpAdminConfig.config_path = 'some_path.json'

        client = pulpAdminConfig.__getitem__.return_value
        client.__getitem__.return_value = 'admin'

        actual = clone.get_cmd(add_password=addPassword, commit=commit)

        self.assertEqual(actual, expected, testMethod.__doc__)

    @patch('releng_sop.pulp_clone_repos.PulpAdminConfig', autospec=True)
    def test_get_cmd_no_commit_no_repo(self, PulpAdminConfigClassMock):
        """Get command with no repo, while not commiting."""
        cloned = []
        expected_cmd = []
        password = 'like'
        expected = []
        for repo in cloned:
            expected_cmd = "pulp-admin --config={config} --user={username} --password={passwd}".format(
                config=self.env_spec['config_path'],
                username=self.pulp_spec['user'],
                passwd=password).split()
            expected_cmd += "repo clone --id={id_from} --clone_id={id_to}".format(
                id_from=repo['from'],
                id_to=repo['to']).split()
            expected.append(expected_cmd)
        commit = False
        skip_repo_check = True
        addPassword = True

        testMethod = TestPulpCloneRepos.test_get_cmd_no_commit_no_repo
        self.check_get_cmd(PulpAdminConfigClassMock, expected_cmd, commit, testMethod, cloned,
                           skip_repo_check, password, addPassword)

    @patch('releng_sop.pulp_clone_repos.PulpAdminConfig', autospec=True)
    def test_get_cmd_with_commit_one_repo(self, PulpAdminConfigClassMock):
        """Get command with one repo, when commiting."""
        cloned = [{'from': 'rhel-7-workstation-htb-rpms', 'to': 'rhel-7-server-htb-source-rpms'}]
        expected_cmd = []
        password = 'like'
        expected = []
        for repo in cloned:
            expected_cmd = "pulp-admin --config={config} --user={username} --password={passwd}".format(
                config=self.env_spec['config_path'],
                username=self.pulp_spec['user'],
                passwd=password).split()
            expected_cmd += "repo clone --id={id_from} --clone_id={id_to}".format(
                id_from=repo['from'],
                id_to=repo['to']).split()
            expected.append(expected_cmd)
        commit = True
        skip_repo_check = False
        addPassword = True

        testMethod = TestPulpCloneRepos.test_get_cmd_with_commit_one_repo
        self.check_get_cmd(PulpAdminConfigClassMock, expected, commit, testMethod, cloned,
                           skip_repo_check, password, addPassword)

    @patch('releng_sop.pulp_clone_repos.PulpAdminConfig', autospec=True)
    def test_get_cmd_with_commit_two_repo(self, PulpAdminConfigClassMock):
        """Get command with two repos when commiting."""
        cloned = [{'from': 'rhel-7-workstation-htb-rpms', 'to': 'rhel-7-server-htb-source-rpms'},
                  {'from': 'rhel-6-workstation-htb-rpms', 'to': 'rhel-6-server-htb-source-rpms'}]
        password = ''
        expected = []
        for repo in cloned:
            expected_cmd = "pulp-admin --config={config} --user={username}".format(
                config=self.env_spec['config_path'],
                username=self.pulp_spec['user'],
                passwd=password).split()
            expected_cmd += "repo clone --id={id_from} --clone_id={id_to}".format(
                id_from=repo['from'],
                id_to=repo['to']).split()
            expected.append(expected_cmd)
        commit = True
        addpassword = False
        skip_repo_check = True

        testMethod = TestPulpCloneRepos.test_get_cmd_with_commit_two_repo
        self.check_get_cmd(PulpAdminConfigClassMock, expected, commit, testMethod, cloned,
                           skip_repo_check, password, addpassword)


class TestPulpCloneReposParser(ParserTestBase, unittest.TestCase):
    """Set Arguments and Parser for Test generator."""

    ARGUMENTS = {
        'envHelp': {
            'arg': '--env ENV',
            'env_default': ['rhel-7.1', 'rhel-7.0', 'htb'],
            'env_set': ['rhel-7.1', 'rhel-7.0', 'htb', '--commit', "--env", "some_env"],
        },
        'helpFromReleaseId': {
            'arg': 'FROM_RELEASE_ID',
        },
        'helpToReleaseId': {
            'arg': 'TO_RELEASE_ID',
        },
        'commitHelp': {
            'arg': '--commit',
            'commit_default': ['rhel-7.1', 'rhel-7.0', 'htb'],
            'commit_set': ['rhel-7.1', 'rhel-7.0', 'htb', '--commit'],
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
        'skipCheckRepoHelp': {
            'arg': '--skip-repo-check',
        },
    }

    PARSER = get_parser()


if __name__ == "__main__":
    unittest.main()
