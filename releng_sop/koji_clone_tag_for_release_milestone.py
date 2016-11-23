# -*- coding: utf-8 -*-

"""
Manual Steps
~~~~~~~~~~~~
Requirements:

* **koji** package
* package with a koji profile (if needed)

Inputs:

* **profile** - koji instance in which the change will be made
* **compose_tag** - release (a.k.a. main) koji tag name for a release
* **milestone_tag** - main release tag + name of milestone + milestone major version + "-set" suffix, for example f24-beta-1-set

Steps:

#. ``koji --profile=<profile> clone-tag --verbose <compose_tag> <milestone_tag>``
"""


from __future__ import print_function
from __future__ import unicode_literals
import sys

import argparse

from productmd.composeinfo import verify_label as verify_milestone

from .common import Environment, Release, Error, CommandBase


class KojiCloneTagForReleaseMilestone(CommandBase):
    """
    Clone tag for release milestone.

    :param env:        Environment object to be used to execute the commands.
    :type env:         Environment

    :param release: Release object.
    :type release:  Release

    :param milestone: Milestone name and version, for example: Beta-1.0
    :type milestone: str
    """

    def __init__(self, env, release, milestone):
        """
        Adding milestone_tag and compose_tag.
        """
        super(KojiCloneTagForReleaseMilestone, self).__init__(env, release)
        self.milestone = milestone
        self.compose_tag = self.release["koji"]["tag_compose"]
        self.milestone_tag = self._get_milestone_tag(milestone)

    def _get_milestone_tag(self, milestone):
        """
        Verify milestone and created name of milestone_tag.

        :param milestone: Milestone name and version, for example: Beta-1.0
        :type  milestone: str
        :rtype: str
        """
        verify_milestone(milestone)
        result = "%s-%s-set" % (self.release["koji"]["tag_release"], self.milestone.lower().split(".")[0])
        return result

    def details(self, commit=False):
        """
        Print details of command execution.

        :param commit: Flag to indicate if the command will be actually executed.
                       Line indicating "test mode" is printed, if this is False.
        :type  commit: boolean=False
        """
        details = "Cloning package set for a release milestone\n"
        details += " * koji profile:            %s\n" % self.env["koji_profile"]
        details += " * release_id:              %s\n" % self.release_id
        details += " * milestone:               %s\n" % self.milestone
        details += " * compose tag (source):    %s\n" % self.compose_tag
        details += " * milestone tag (target):  %s\n" % self.milestone_tag
        if not commit:
            details += "*** TEST MODE ***"
        return details

    def get_cmd(self, commit=False):
        """
        Construct the koji command.

        :param commit: Flag to indicate if the command will be actually executed.
                       Add "--test" to the command, if this is False.
        :type commit: boolean=False
        :return: Koji command
        :rtype: list of strings
        """
        cmd = []
        cmd.append("koji")
        cmd.append("--profile=%s" % self.env["koji_profile"])
        cmd.append("clone-tag")
        cmd.append("--verbose")
        cmd.append(self.compose_tag)
        cmd.append(self.milestone_tag)
        if not commit:
            cmd.append('--test')
        return cmd


def get_parser():
    """
    Construct argument parser.

    :returns: ArgumentParser object with arguments set up.
    :rtype: argparse.ArgumentParser
    """
    parser = argparse.ArgumentParser(
        description="Clone tag for release milestone.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "release_id",
        metavar="RELEASE_ID",
        help="PDC release ID, for example 'fedora-24', 'fedora-24-updates'.",
    )
    parser.add_argument(
        "milestone",
        metavar="MILESTONE",
        help="Milestone name and version, for example: 'Beta-1.0'.",
    )
    parser.add_argument(
        "--commit",
        action="store_true",
        help="Program performs a dry-run by default. Enable this option to apply the changes.",
    )
    parser.add_argument(
        "--env",
        default="default",
        help="Select environment in which the program will make changes.",
    )
    parser.add_argument(
        "-d", "--debug",
        action="store_true",
        help="Print traceback for exceptions. By default only exception messages are displayed.",
    )
    return parser


def main():
    """Main function."""
    try:
        parser = get_parser()
        args = parser.parse_args()

        env = Environment(args.env)
        release = Release(args.release_id)
        clone = KojiCloneTagForReleaseMilestone(env, release, args.milestone)
        clone.run(commit=args.commit)

    except Error:
        if not args.debug:
            sys.tracebacklimit = 0
        raise


if __name__ == "__main__":
    main()
