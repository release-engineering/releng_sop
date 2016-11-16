# -*- coding: utf-8 -*-

"""Base class for koji commands."""

import subprocess


class CommandBase(object):
    """Base class for koji commands.

    :param env:        Environment object to be used to execute the commands.
    :type env:         Environment

    :param release: Release object.
    :type release:  Release
    """

    def __init__(self, env, release):  # noqa: D102
        self.env = env
        self.release_id = release.name
        self.release = release

    def run(self, commit=False):
        """Print command details, get command and run it."""
        details = self.details(commit=commit)
        print(details)
        cmd = self.get_cmd(commit=commit)
        print(cmd)
        subprocess.check_output(cmd)
