# -*- coding: utf-8 -*-


"""
Manual Steps
~~~~~~~~~~~~
Requirements:


Inputs:

* **commit** - Program performs a dry-run by default. Enable this option to apply the changes.
* **RELEASE_ID** - PDC release ID, for example 'fedora-24', 'fedora-24-updates'.
* **REPO_FAMILY** - It is repo family in PDC.
* **variant** - It is variant in PDC.
* **arch** - It is arch in PDC.

Steps:

#  ``pulp_clear_repos [--commit] RELEASE_ID REPO_FAMILY [--variant=] ... [--arch=] ...``
"""

from __future__ import print_function, unicode_literals
import getpass
import sys
import subprocess

from pdc_client import PDCClient
import argparse

from .common import Environment, Release, Error, UsageError
from .common_pulp import PulpAdminConfig
from .kojibase import KojiBase


class PulpClearRepos(KojiBase):
    """Clear Pulp repos.

    :param env:                Environment object to be used to execute the commands.
    :type env:                 Environment
    :note env:                 Keys 'pulp_server' and 'pdc_server' are used.

    :param release:            Release object.
    :type release:             Release

    :param repo_family:        Repo family to be cleared.
    :type repo_family:         string

    :param variants:           Variants to be filtered for.
    :type variant:             list of strings

    :param arch:               Architectures to be filtered for.
    :type arch:                list of strings
    """

    def __init__(self, env, release, repo_family, variants, arches):  # noqa: D102
        super(PulpClearRepos, self).__init__(env, release)
        self.repo_family = repo_family
        self.variants = variants
        self.arches = arches
        self.repos = []
        self.pulp_config = PulpAdminConfig(self.env["pulp_server"])
        self.pulp_password = self.pulp_config["client"].get("password")

    def password_prompt(self, force=False, commit=False):
        """Get password to authenticate with Pulp.

        :param force:    Always ask for password, even if present in Pulp config
        :type force:     Boolean

        :param commit:   Flag to indicate if password is required for a commit action.
                         If not set, password will not be asked for.
        :type commit:    Boolean
        """
        if not commit:
            return

        result = self.pulp_password

        if force:
            result = ""

        while not result:
            msg = "Enter Pulp password for %s@%s: "
            prompt = msg % (self.pulp_config["client"]["user"], self.pulp_config.name)
            result = getpass.getpass(prompt=prompt)

        self.pulp_password = result

    def query_repo(self):
        """Get list names of pdc repo."""
        if self.repo_family == 'dist':
            raise UsageError('REPO_FAMILY must never be \"dist\"')

        client = PDCClient(self.env["pdc_server"], develop=True)

        data = {
            "release_id": self.release_id,
            "service": "pulp",
            "repo_family": self.repo_family,
            "content_format": "rpm",
            "arch": self.arches,
            "variant_uid": self.variants,
        }

        result = client['content-delivery-repos']._(page_size=0, **data)
        self.repos = [i['name'] for i in result]

    def details(self, commit=False):
        """
        Print details of command execution.

        :param commit: Flag to indicate if the command will be actually executed.
                       Line indicating "test mode" is printed, if this is False.
        :type  commit: boolean=False
        """
        self.query_repo()

        details = "Pulp clear repos\n"
        details += " * env name:                %s\n" % self.env.name
        details += " * env config:              %s\n" % self.env.config_path
        details += " * release source           %s\n" % self.release.config_path
        details += " * PDC server:              %s\n" % self.env["pdc_server"]
        details += " * release_id:              %s\n" % self.release_id
        details += " * pulp config:             %s\n" % self.pulp_config.name
        details += " * pulp config path:        %s\n" % self.pulp_config.config_path
        details += " * pulp user:               %s\n" % self.pulp_config["client"]["user"]
        details += " * repo_family:             %s\n" % self.repo_family
        if self.arches:
            details += " * arches:\n"
            for i in self.arches:
                details += "     %s\n" % i
        if self.variants:
            details += " * variants:\n"
            for i in self.variants:
                details += "     %s\n" % i
        details += " * repos:\n"
        if not self.repos:
            details += "     No repos found.\n"
        for i in self.repos:
            details += "     %s\n" % i
        if not commit:
            details += "*** TEST MODE ***"
        return details

    def get_cmd(self, add_password=False, commit=False):
        """
        Construct the Pulp commands.

        :param add_password: Flag to indicate wether password should be added
                             to the commands.
        :type add_password:  Boolean (default: False)

        :param commit: Flag to indicate if the command will be actually executed.
                       Prepend command with 'echo', if this is false.
        :type commit: boolean=False

        :return: Pulp commands
        :rtype:  list of list of strings
        """
        # password is added only if requested and this is commit action
        password = []
        if add_password and commit:
            password = ["--password=%s" % self.pulp_password]

        # echo is added if this is not a commit action
        echo = []
        if not commit:
            echo = ['echo']

        commands = []
        for repo in self.repos:
            cmd = []
            cmd.append("pulp-admin")
            cmd.append("--config=%s" % self.pulp_config.config_path)
            cmd.append("--user=%s" % self.pulp_config["client"]["user"])
            cmd = cmd + password
            cmd.append("rpm")
            cmd.append("repo")
            cmd.append("remove")
            cmd.append("rpm")
            cmd.append("--filters='{}'")
            cmd.append("--repo-id")
            cmd.append(repo)
            cmd = echo + cmd
            commands.append(cmd)
        return commands

    def run(self, commit=False):
        """Print command details, get command and run it."""
        details = self.details(commit=commit)
        print(details)
        commands_exec = self.get_cmd(add_password=True, commit=commit)
        commands_print = self.get_cmd(add_password=False, commit=commit)
        for cmd_exec, cmd_print in zip(commands_exec, commands_print):
            print(cmd_print)
            subprocess.check_call(cmd_exec)


def get_parser():
    """
    Construct argument parser.

    :returns: ArgumentParser object with arguments set up.
    :rtype: argparse.ArgumentParser
    """
    parser = argparse.ArgumentParser(
        description="Clear pulp repos associated with a release.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "release_id",
        metavar="RELEASE_ID",
        help="PDC release ID, for example 'fedora-24', 'fedora-24-updates'.",
    )
    parser.add_argument(
        "repo_family",
        metavar="REPO_FAMILY",
        help="Repo family to be cleared, for example 'beta'. Should never be 'dist'.",
    )
    parser.add_argument(
        "--variant",
        metavar="VARIANT",
        dest="variants",
        action="append",
        help="Filter repos to be cleared to match variants.",
    )
    parser.add_argument(
        "--arch",
        metavar="ARCH",
        dest="arches",
        action="append",
        help="Filter repos to be cleared to match architectures.",
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
        clear = PulpClearRepos(env, release, args.repo_family, args.variants, args.arches)
        clear.password_prompt(args.commit)
        clear.run(commit=args.commit)

    except Error:
        if not args.debug:
            sys.tracebacklimit = 0
        raise


if __name__ == "__main__":
    main()
