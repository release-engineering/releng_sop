#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Tests for configuration data.
"""
from __future__ import unicode_literals

import unittest

import os
import sys

DIR = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(DIR, ".."))

from releng_sop.common import Environment, Release, ConfigError  # noqa: E402


RELEASES_DIR = os.path.join(DIR, "releases")
ENVIRONMENTS_DIR = os.path.join(DIR, "environments")


class TestReleaseData(unittest.TestCase):
    """Test release configuration data found in RELEASES_DIR."""

    longMessage = True

    def _get_releases(self):
        result = []
        for fn in os.listdir(RELEASES_DIR):
            if not fn.endswith(".json"):
                continue
            result.append(fn[:-5])
        return result

    def test_releases(self):
        """Read all json files from RELEASES_DIR, and check data structure."""
        releases = self._get_releases()
        for release_id in releases:
            release = Release(release_id, config_dirs=[RELEASES_DIR])

            # check top-level sections
            expected = [
                "distgit",
                "koji",
                "scls",
                "signing",
            ]
            actual = sorted(release)
            if "scls" not in actual:
                # optional, may not be available
                expected.remove("scls")
            self.assertEqual(actual, expected, "\n\nrelease_id: %s" % release_id)

            # check distgit data
            expected = [
                "branch",
            ]
            self.assertEqual(sorted(release["distgit"]), expected, "\n\nrelease_id: %s" % release_id)

            # check koji data
            expected = [
                "tag_bootstrap",
                "tag_build",
                "tag_buildrequires",
                "tag_candidate",
                "tag_compose",
                "tag_override",
                "tag_pending",
                "tag_release",
                "tag_temp_override",
                "target",
            ]
            self.assertEqual(sorted(release["koji"]), expected, "\n\nrelease_id: %s" % release_id)

            # check signing data
            expected = [
                "sigkey_beta",
                "sigkey_gold",
            ]
            self.assertEqual(sorted(release["signing"]), expected, "\n\nrelease_id: %s" % release_id)


class TestEnvironmentData(unittest.TestCase):
    """Test environment configuration data found in ENVIRONMENTS_DIR."""

    longMessage = True

    def _get_environments(self):
        result = []
        for fn in os.listdir(ENVIRONMENTS_DIR):
            if not fn.endswith(".json"):
                continue
            result.append(fn[:-5])
        return result

    def test_environments(self):
        """Read all json files from ENVIRONMENTS_DIR, and check data structure."""
        environments = self._get_environments()
        for env_id in environments:
            env = Environment(env_id, config_dirs=[ENVIRONMENTS_DIR])

            expected = [
                "distgit_server",
                "koji_profile",
                "pdc_server",
                "pulp_server",
                "rpmsign_class",
            ]
            self.assertEqual(sorted(env), expected, "\n\nenv_id: %s" % env_id)


class TestConfigDataNotFound(unittest.TestCase):
    """RuntimeError raised if config data is not found."""

    def test_release_not_found(self):
        """Raise RuntimeError when release data no found."""
        release_id = "no-such-release"

        self.assertRaises(ConfigError,
                          Release, release_id, config_dirs=[RELEASES_DIR])

    def test_environment_not_found(self):
        """Raise RuntimeError when environment configuration no found."""
        env_id = "no-such-environment"

        self.assertRaises(ConfigError,
                          Environment, env_id, config_dirs=[ENVIRONMENTS_DIR])


if __name__ == "__main__":
    unittest.main()
