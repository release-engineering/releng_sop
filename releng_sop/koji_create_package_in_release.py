# -*- coding: utf-8 -*-
"""
Manual Steps
~~~~~~~~~~~~

Requirements:

* **koji** package
* package with a koji profile (if needed)

Inputs:

* **profile** - koji instance in which the change will be made
* **owner** - package owner
* **tag** - release (a.k.a. main) koji tag name for a release
* **package** - name of package to be created in a release

Steps:

#. ``koji --profile=<profile> add-pkg --owner=<owner> <tag> <package> [package] ...``

"""

from __future__ import print_function
from __future__ import unicode_literals
import sys

import argparse

from .common import Environment, Release, UsageError, Error
from .kojibase import CommandBase


class KojiCreatePackageInRelease(CommandBase):
    """
    Create packages in a release.

    :param env:        Environment object to be used to execute the commands.
    :type env:         Environment

    :param release: Release object.
    :type release:  Release

    :param packages: name of package to be created in a release
    :type packages:  list of str

    :param owner:   package owner
    :type owner:    str
    """

    def __init__(self, env, release, packages, owner, scl=None):
        """Adding packages for create and owner as an aditional member."""
        super(KojiCreatePackageInRelease, self).__init__(env, release)
        self.packages = self._handle_scl(release, scl, sorted(packages))
        self.owner = owner

    def details(self, commit=False):
        """Print details of command execution.

        :param commit: Flag to indicate if the command will be actually executed.
                       Line indicating "test mode" is printed, if this is False.
        :type commit:  boolean; default False
        """
        details = "Creating packages in a release\n"
        details += " * env name:                %s\n" % self.env.name
        details += " * env config:              %s\n" % self.env.config_path
        details += " * release source           %s\n" % self.release.config_path
        details += " * koji profile:            %s\n" % self.env["koji_profile"]
        details += " * release_id:              %s\n" % self.release_id
        details += " * owner:                   %s\n" % self.owner
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
        cmd.append("add-pkg")
        cmd.append("--owner=%s" % self.owner)
        cmd.append(self.release["koji"]["tag_release"])
        cmd.extend(self.packages)
        if not commit:
            cmd = ["echo"] + cmd
        return cmd

    @staticmethod
    def _handle_scl(release, scl, packages):
        """Check SCL and update package names accordingly.

        :param release: Release object.
        :type release:  Release

        :param scl:     Software Collection in which packages belong
        :type scl:    str

        :param packages: name of package to be created in a release
        :type packages:  list of str
        """
        scl_required = 'scls' in release

        def scl_correct():
            return (scl is not None and (
                    scl in release['scls'] or scl.lower() == 'none'))

        if scl_required and scl is None:
            message = "Option --scl required! Valid values as found in '%s' are:\n%s"
            raise UsageError(message %
                             (release.config_path,
                              '\n'.join(release['scls'] + ['none'])))

        if scl_required and not scl_correct():
            message = "Incorrect SCL selection. Valid values as found in '%s' are:\n%s"
            raise UsageError(message %
                             (release.config_path,
                              '\n'.join(release['scls'] + ['none'])))

        if not scl_required and scl is not None:
            message = "'%s' has no SCL data, --scl option should not be used."
            raise UsageError(message % (release.config_path))

        if scl_required and scl.lower() != 'none':
            packages = ["%s-%s" % (scl, package) for package in packages]

        return packages


def get_parser():
    """Construct argument parser.

    :returns: ArgumentParser object with arguments set up.
    """
    parser = argparse.ArgumentParser(
        description="Create packages in a koji tag that maps to given release.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "release_id",
        metavar="RELEASE_ID",
        help="PDC release ID, for example 'fedora-24', 'fedora-24-updates'.",
    )
    parser.add_argument(
        "owner",
        metavar="OWNER",
        help="Package owner.",
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
        "--scl",
        metavar="SCL",
        default=argparse.SUPPRESS,
        help="""Software Collection for which packages are created.
        Required when release has SCL data.
        'none' can be used when none of the SCLs specifed should be used."""
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

        # hackish way to suppress 'default' text in help text,
        # but keep scl in the namespace
        if not hasattr(args, 'scl'):
            args.scl = None

        env = Environment(args.env)
        release = Release(args.release_id)
        clone = KojiCreatePackageInRelease(
            env, release, args.packages, args.owner, args.scl)
        clone.run(commit=args.commit)

    except Error:
        if not args.debug:
            sys.tracebacklimit = 0
        raise


if __name__ == "__main__":
    main()
