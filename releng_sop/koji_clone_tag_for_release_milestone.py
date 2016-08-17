# -*- coding: utf-8 -*-
"""Clone tag for release milestone.

Constructs the koji command

    koji --profile=<koji_profile> clone-tag --verbose <compose_tag> <milestone_tag>

koji_profile is obtained from the environment settings.

compose_tag is compose koji tag name for a release

milestone_tag is main release tag + name of milestone + milestone major version +
    '-set' suffix, for example f24-beta-1-set
"""

from __future__ import print_function

import argparse
import subprocess

from productmd.composeinfo import verify_label as verify_milestone

from .common import Environment, Release


class KojiCloneTagForReleaseMilestone(object):
    """Clone tag for release milestone."""

    def __init__(self, env, release_id, milestone):
        """Init.

        Patameters
        ----------
        env: str
            name of the environment to be used to execute the commands
        release_id: str
        milestone: str

        """
        self.env = env
        self.release_id = release_id
        self.release = Release(self.release_id)
        self.milestone = milestone
        self.compose_tag = self.release["koji"]["tag_compose"]
        self.milestone_tag = self._get_milestone_tag(milestone)

    def _get_milestone_tag(self, milestone):
        verify_milestone(milestone)
        result = "%s-%s-set" % (self.release["koji"]["tag_release"], self.milestone.lower().split(".")[0])
        return result

    def print_details(self, commit=False):
        """Print details of command execution.

        Parameters
        ----------
        commit: boolean (optional; default False)
            Flag to indicate if the command will be actually executed.
            Line indicating "test mode" is printed, if this is False.
        """
        print("Cloning package set for a release milestone")
        print(" * koji profile:            %s" % self.env["koji_profile"])
        print(" * release_id:              %s" % self.release_id)
        print(" * milestone:               %s" % self.milestone)
        print(" * compose tag (source):    %s" % self.compose_tag)
        print(" * milestone tag (target):  %s" % self.milestone_tag)
        if not commit:
            print("*** TEST MODE ***")

    def get_cmd(self, commit=False):
        """Construct the koji command.

        Parameters
        ----------
        commit: boolean (optional; default False)
            Flag to indicate if the command will be actually executed.
            Add "--test" to the command, if this is False.

        Returns
        -------
        koji command as a list of strings.
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

    def run(self, commit=False):
        """Print command details, get command and run it."""
        self.print_details(commit=commit)
        cmd = self.get_cmd(commit=commit)
        print(cmd)
        subprocess.check_output(cmd)


def get_parser():
    """Construct argument parser.

    Returns
    -------
    ArgumentParser object with arguments set up.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "release_id",
        metavar="RELEASE_ID",
        help="",
    )
    parser.add_argument(
        "milestone",
        metavar="MILESTONE",
        help="milestone name and version, for example: Beta-1.0",
    )
    parser.add_argument(
        "--commit",
        action="store_true",
        default=False,
        help="apply the changes",
    )
    parser.add_argument(
        "--env",
        help="Select environment in which the program will make changes.",
    )
    return parser


def main():
    """Main function."""
    parser = get_parser()
    args = parser.parse_args()
    env = Environment(args.env)
    clone = KojiCloneTagForReleaseMilestone(env, args.release_id, args.milestone)
    clone.run(commit=args.commit)


if __name__ == "__main__":
    main()
