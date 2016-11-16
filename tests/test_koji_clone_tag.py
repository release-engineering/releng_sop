#!/usr/bin/python
# -*- coding: utf-8 -*-


"""Tests of KojiCloneTagForReleaseMilestone script.
"""


import unittest
import os
import sys
from mock import Mock, patch

DIR = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(DIR, ".."))

from releng_sop.common import Environment, Release  # noqa
from releng_sop.koji_clone_tag_for_release_milestone import get_parser, KojiCloneTagForReleaseMilestone  # noqa
from tests.common import ParserTestBase  # noqa


class TestKojiCloneTag(unittest.TestCase):
    """Tests of methods from KojiCloneTagForReleaseMilestone class."""

    env_spec = {
        'name': 'default',
        'config_data': {
            'koji_profile': 'test'
        },
        '__getitem__': lambda self, item: self.config_data[item]
    }

    release_spec = {
        'name': 'test-release',
        'config_data': {
            'koji': {
                'tag_release': 'test',
                'tag_compose': 'test-compose'
            }
        },
        '__getitem__': lambda self, item: self.config_data[item]
    }

    milestone = "Beta-1.0"
    milestone_tag = '{0}-{1}-set'.format(
        release_spec['config_data']['koji']['tag_release'],
        milestone.lower().split(".")[0])

    # Expected details text
    details = """Cloning package set for a release milestone
 * koji profile:            {env[config_data][koji_profile]}
 * release_id:              {release[name]}
 * milestone:               {milestone}
 * compose tag (source):    {release[config_data][koji][tag_compose]}
 * milestone tag (target):  {milestone_tag}
""".format(env=env_spec, release=release_spec, milestone=milestone, milestone_tag=milestone_tag)

    # Expected command
    cmd = "koji --profile={profile} clone-tag --verbose {tag_compose} {milestone_tag}".format(
        profile=env_spec['config_data']['koji_profile'],
        tag_compose=release_spec['config_data']['koji']['tag_compose'],
        milestone_tag=milestone_tag).split()

    @classmethod
    def setUpClass(cls):
        """Set up variables before tests."""
        cls.env = Mock(spec_set=list(cls.env_spec.keys()))
        cls.env.configure_mock(**cls.env_spec)

        cls.release = Mock(spec_set=list(cls.release_spec.keys()))
        cls.release.configure_mock(**cls.release_spec)

        with patch('releng_sop.koji_clone_tag_for_release_milestone.verify_milestone') as verify_milestone:
            verify_milestone.return_value = cls.milestone
            cls.clone = KojiCloneTagForReleaseMilestone(cls.env, cls.release, cls.milestone)

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
        expected = self.cmd + ["--test"]
        self.assertEqual(actual, expected, self.test_get_cmd_no_commit.__doc__)

    def test_get_cmd_with_commit(self):
        """Get command when commiting."""
        actual = self.clone.get_cmd(commit=True)
        expected = self.cmd
        self.assertEqual(actual, expected, self.test_get_cmd_with_commit.__doc__)

    def test_invalid_milestone(self):
        """Test invalid milestone."""
        with patch('releng_sop.koji_clone_tag_for_release_milestone.verify_milestone') as verify_milestone:
            verify_milestone.side_effect = ValueError
            self.assertRaises(ValueError, KojiCloneTagForReleaseMilestone, self.env, self.release, self.milestone)


class TestKojiCloneTagParser(ParserTestBase, unittest.TestCase):
    """Set Arguments and Parser for Test generator."""

    ARGUMENTS = {
        'envHelp': {
            'arg': '--env ENV',
            'env_default': ['fedora-24', 'bash'],
            'env_set': ['fedora-24', 'bash', "--env", "some_env"],
        },
        'commitHelp': {
            'arg': '--commit',
            'commit_default': ['fedora-24', 'bash'],
            'commit_set': ['fedora-24', 'bash', "--commit"],
        },
        'helpReleaseId': {
            'arg': 'RELEASE_ID',
        },
        'helpMilestone': {
            'arg': 'MILESTONE',
        },
    }

    PARSER = get_parser()


if __name__ == "__main__":
    unittest.main()
