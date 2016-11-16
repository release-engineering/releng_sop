#!/usr/bin/python
# -*- coding: utf-8 -*-


"""Tests of KojiCreatePackageInRelease script.
"""


import unittest
import os
import sys
from mock import Mock

DIR = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(DIR, ".."))

from releng_sop.common import Environment, Release, UsageError  # noqa
from releng_sop.koji_create_package_in_release import get_parser, KojiCreatePackageInRelease  # noqa
# from releng_sop.koji_create_package_in_release import _handle_scl  # noqa
from tests.common import ParserTestBase  # noqa


class TestKojiCreatePackage(unittest.TestCase):
    """Tests of methods from KojiCreatePackageInRelease class."""

    env_spec = {
        'name': 'default',
        'config_path': 'some/file.json',
        'config_data': {
            'koji_profile': 'test'
        },
        '__getitem__': lambda self, item: self.config_data[item],
    }

    release_spec = {
        'name': 'test-release',
        'config_path': 'some.json',
        'config_data': {
            'koji': {
                'tag_release': 'test'
            },
        },
        '__contains__': lambda self, item: item in self.config_data,
        '__getitem__': lambda self, item: self.config_data[item],
    }

    packages = ['bash']
    owner = 'test'

    # Expected details text
    details = """Creating packages in a release
 * env name:                {env[name]}
 * env config:              {env[config_path]}
 * release source           {release[config_path]}
 * koji profile:            {env[config_data][koji_profile]}
 * release_id:              {release[name]}
 * owner:                   {owner}
 * tag:                     {release[config_data][koji][tag_release]}
 * packages:
     {packages}
""".format(env=env_spec, owner=owner, release=release_spec, packages="\n     ".join(packages))

    # Expected command
    cmd = "koji --profile={profile} add-pkg --owner={owner} {release_tag} {packages}".format(
        profile=env_spec['config_data']['koji_profile'],
        owner=owner,
        release_tag=release_spec['config_data']['koji']['tag_release'],
        packages=" ".join(packages)).split()

    @classmethod
    def setUpClass(cls):
        """Set up variables before tests."""
        env = Mock(spec_set=list(cls.env_spec.keys()))
        env.configure_mock(**cls.env_spec)

        release = Mock(spec_set=list(cls.release_spec.keys()))
        release.configure_mock(**cls.release_spec)

        cls.clone = KojiCreatePackageInRelease(env, release, cls.packages, cls.owner)

    def test_details_no_commit(self):
        """Get details, while not commiting."""
        actual = self.clone.details()
        expected = self.details + "*** TEST MODE ***"
        self.assertEqual(actual, expected, self.test_details_no_commit.__doc__)

    def test_details_with_commit(self):
        """Get details when commiting."""
        actual = self.clone.details(commit=True)
        expected = self.details
        self.assertEqual(actual, expected, self.test_details_with_commit.__doc__)

    def test_get_cmd_no_commit(self):
        """Get command, while not commiting."""
        actual = self.clone.get_cmd()
        expected = ["echo"] + self.cmd
        self.assertEqual(actual, expected, self.test_get_cmd_no_commit.__doc__)

    def test_get_cmd_with_commit(self):
        """Get command when commiting."""
        actual = self.clone.get_cmd(commit=True)
        expected = self.cmd
        self.assertEqual(actual, expected, self.test_get_cmd_with_commit.__doc__)


class TestHandleScl(unittest.TestCase):
    """Test handling of --scl option."""

    def setUp(self):
        """Set up Release object spec."""
        self.release_spec = {
            'config_path': 'testscl.json',
            'config_data': {
                'scls': ['python27', 'bash']
            },
            '__contains__': lambda self, item: item in self.config_data,
            '__getitem__': lambda self, item: self.config_data[item]
        }
        self.handle_scl = KojiCreatePackageInRelease._handle_scl

    def _get_release_mock(self):
        release = Mock(spec_set=list(self.release_spec.keys()))
        release.configure_mock(**self.release_spec)
        return release

    def test_unexpected_scl(self):
        """
        Raise UsageError in case there is no scls data, but scl is specified.
        """
        # remove scls data from release
        self.release_spec['config_data'].pop('scls')
        release = self._get_release_mock()
        scl = 'none'
        packages = list()

        self.assertRaises(UsageError, self.handle_scl, release, scl, packages)

    def test_missing_scl(self):
        """
        Raise UsageError in case the is scls data, but scl is not specified.
        """
        release = self._get_release_mock()
        scl = None
        packages = list()

        self.assertRaises(UsageError, self.handle_scl, release, scl, packages)

    def test_incorrect_scl(self):
        """
        Raise UsageError in case scl is not in scls data.
        """
        release = self._get_release_mock()
        scl = 'perl'
        packages = list()

        self.assertRaises(UsageError, self.handle_scl, release, scl, packages)

    def test_none_scl(self):
        """
        Package names are not prefixed when there is scls data and scl is none.
        """
        release = self._get_release_mock()
        scl = 'none'
        packages_in = ['kernel', 'productmd']

        # work with a copy of packages_in
        packages_out = self.handle_scl(release, scl, list(packages_in))

        self.assertEqual(packages_in, packages_out, self.test_none_scl.__doc__)

    def test_correct_scl(self):
        """
        Package names are prefixed when there is scls data and scl is selected.
        """
        release = self._get_release_mock()
        scl = 'bash'
        packages_in = ['poke', 'mon']

        # work with a copy of packages_in
        packages_out = self.handle_scl(release, scl, list(packages_in))
        packages_expected = ['%s-%s' % (scl, package) for package in packages_in]

        self.assertEqual(packages_expected, packages_out, self.test_correct_scl.__doc__)

    def test_scl_data_empty(self):
        """
        'none' can be still selected as scl when scls data is empty.
        """
        # set scls data empty
        self.release_spec['config_data']['scls'] = list()
        release = self._get_release_mock()
        scl = 'none'
        packages_in = ['lindy', 'hop']

        # work with a copy of packages_in
        packages_out = self.handle_scl(release, scl, list(packages_in))

        self.assertEqual(packages_in, packages_out, self.test_scl_data_empty.__doc__)


class TestKojiCreatePackageParser(ParserTestBase, unittest.TestCase):
    """Set Arguments and Parser for Test generator."""

    ARGUMENTS = {
        'envHelp': {
            'arg': '--env ENV',
            'env_default': ['fedora-24', 'test', 'bash'],
            'env_set': ['fedora-24', 'test', 'bash', "--env", "some_env"],
        },
        'commitHelp': {
            'arg': '--commit',
            'commit_default': ['fedora-24', 'test', 'bash'],
            'commit_set': ['fedora-24', 'test', 'bash', '--commit'],
        },
        'helpReleaseId': {
            'arg': 'RELEASE_ID',
        },
        'helpPackage': {
            'arg': 'PACKAGE',
        },
        'helpOwner': {
            'arg': 'OWNER',
        },
        'helpScl': {
            'arg': '--scl',
        },
    }

    PARSER = get_parser()


if __name__ == "__main__":
    unittest.main()
