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
    """
    Clone tag for release milestone.

    :param env: name of the environment to be used to execute the commands.
    :type  env: str
    :param release_id: PDC release ID, for example 'fedora-24', 'fedora-24-updates'.
    :type release_id: str
    :param milestone: Milestone name and version, for example: Beta-1.0
    :type milestone: str
    """

    def __init__(self, env, release_id, milestone):  # noqa: D102
        self.env = env
        self.release_id = release_id
        self.release = Release(self.release_id)
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

    def print_details(self, commit=False):
        """
        Print details of command execution.

        :param commit: Flag to indicate if the command will be actually executed.
                       Line indicating "test mode" is printed, if this is False.
        :type  commit: boolean=False
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

    def run(self, commit=False):
        """Print command details, get command and run it."""
        self.print_details(commit=commit)
        cmd = self.get_cmd(commit=commit)
        print(cmd)
        subprocess.check_output(cmd)


def get_parser():
    """
    Construct argument parser.

    :returns: ArgumentParser object with arguments set up.
    :rtype: argparse.ArgumentParser
    """
    parser = argparse.ArgumentParser()
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
