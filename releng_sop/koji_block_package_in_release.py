# -*- coding: utf-8 -*-

"""Block packages in a release.

Constructs the koji command

    koji --profile=KOJI_PROFILE block-pkg RELEASE_TAG PACKAGES...

KOJI_PROFILE is obtained from the environment settings.

RELEASE_TAG is the "tag_release" key from the release configuration
    corresponding to the release id.
"""

from __future__ import print_function
from __future__ import unicode_literals
import sys

import argparse

from .common import Environment, Release, Error
from .kojibase import KojiBase


class KojiBlockPackageInRelease(KojiBase):
    """Block packages in a release.

    :param env:        Environment object to be used to execute the commands.
    :type env:         Environment

    :param release: Release object.
    :type release:  Release

    :param packages: name of package to be created in a release
    :type packages:  list of str
    """

    def __init__(self, env, release, packages):
        """Adding packages to block."""
        super(KojiBlockPackageInRelease, self).__init__(env, release)
        self.packages = sorted(packages)

    def details(self, commit=False):
        """Print details of command execution.

        :param commit: Flag to indicate if the command will be actually executed.
                       Line indicating "test mode" is printed, if this is False.
        :type commit:  boolean; default False
        """
        details = "Blocking packages in a release\n"
        details += " * env name:                %s\n" % self.env.name
        details += " * env config:              %s\n" % self.env.config_path
        details += " * release source           %s\n" % self.release.config_path
        details += " * koji profile:            %s\n" % self.env["koji_profile"]
        details += " * release_id:              %s\n" % self.release_id
        details += " * tag:                     %s\n" % self.release["koji"]["tag_release"]
        details += " * packages:\n"
        for i in self.packages:
            details += "     %s\n" % i
        if not commit:
            details += "*** TEST MODE ***"
        return details

    def get_cmd(self, commit=False):
        """Construct the koji command.

        :param commit: Flag to indicate if the command will be actually executed.
                       "echo" is prepended to the command, if this is False.
        :type commit:  boolean; default False
        :returns:      Koji command.
        :rtype:        list of strings
        """
        cmd = []
        cmd.append("koji")
        cmd.append("--profile=%s" % self.env["koji_profile"])
        cmd.append("block-pkg")
        cmd.append(self.release["koji"]["tag_release"])
        cmd.extend(self.packages)
        if not commit:
            cmd = ["echo"] + cmd
        return cmd


def get_parser():
    """Construct argument parser.

    :returns: ArgumentParser object with arguments set up.
    """
    parser = argparse.ArgumentParser(
        description="Block packages in a koji tag that maps to given release.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "release_id",
        metavar="RELEASE_ID",
        help="PDC release ID, for example 'fedora-24', 'fedora-24-updates'.",
    )
    parser.add_argument(
        "packages",
        metavar="PACKAGE",
        nargs="+",
        help="Koji package, for example 'bash', 'kernel'.",
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
        clone = KojiBlockPackageInRelease(env, release, args.packages)
        clone.run(commit=args.commit)

    except Error as e:
        if not args.debug:
            sys.tracebacklimit = 0
        raise e


if __name__ == "__main__":
    main()
