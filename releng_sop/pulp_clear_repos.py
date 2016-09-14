# -*- coding: utf-8 -*-

"""Pulp clear repos.

Construct command
    pulp_clear_repos [--commit] RELEASE_ID REPO_FAMILY [--variant=] [--arch=]

"""

from __future__ import print_function
from __future__ import unicode_literals
import getpass
import sys
import subprocess

from pdc_client import PDCClient
import argparse

from .common import Environment, Release, Error
from .common_pulp import PulpAdminConfig
from .kojibase import KojiBase


class PulpClearRepos(KojiBase):
    """Pulp clear repos.

    :param release_id:          Name of release.
    :type release_id:           string

    :param service:             Name of service.
    :type service:              string

    :param repo_family:         Name of repo_family.
    :type repo_family:          string

    :param content_format:      Name of content_format.
    :type content_format:       string

    :param variant_uid:         Name of variant_uid.
    :type variant_uid:          string

    :param arch:                Name of arch.
    :type arch:                 string

    :param client:              Client object.
    :type client:               PDCClient
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
        """Get password."""
        if commit:
            result = self.pulp_password

            if force:
                result = ""

            while not result:
                prompt = "Enter Pulp password for %s@%s: " % (self.pulp_config["client"]["user"], self.pulp_config.name)
                result = getpass.getpass(prompt=prompt)

            self.pulp_password = result
        pass

    def query_repo(self):
        """Get list names of pdc repo."""
        if self.repo_family == 'dist':
            raise ValueError('REPO_FAMILY must never be \"dist\"')

        client = PDCClient(self.env["pdc_server"], develop=True)

        data = {
            "release_id": self.release_id,
            "service": "pulp",
            "repo_family": self.repo_family,
            "content_format": "rpm",
            "arch": self.arches,
            "variant_uid": self.variants,
        }

        '''result = client.get_paged(client['content-delivery-repos']._, **data)'''
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

        '''details = [
        "Pulp clear repos",
        " * env name:                %s" % self.env.name,
        " * env config:              %s" % self.env.config_path,
        " * release source           %s" % self.release.config_path,
        " * release_id:              %s" % self.release_id,
        " * repo_family:             %s" % self.repo_family,
        " * PDC server:              %s" % self.env["pdc_server"],
        ]
        if self.arches:
            details += [" * arches:"]
            for i in self.arches:
                details += ["     %s" % i]
        if self.variants:
            details += [" * variants:"]
            for i in self.variants:
                details += ["     %s" % i]
        details += [" * repos:"]
        if not self.repos:
            details += ["     No repos found."]
        for i in self.repos:
            details += ["     %s" % i]
        if not commit:
            details += ["*** TEST MODE ***"]
        return details'''

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
        Construct the koji command.

        :param commit: Flag to indicate if the command will be actually executed.
                       Add "--test" to the command, if this is False.
        :type commit: boolean=False
        :return: Pulp command
        :rtype: list of strings
        """
        commands = []
        for repo in self.repos:
            cmd = []
            cmd.append("pulp-admin")
            cmd.append("--config=%s" % self.pulp_config.config_path)
            cmd.append("--user=%s" % self.pulp_config["client"]["user"])
            if add_password:
                cmd.append("--password=%s" % self.pulp_password)
            cmd.append("rpm repo remove rpm")
            cmd.append("--filters='{}'")
            cmd.append("--repo-id %s" % repo)
            commands.append(cmd)
        return commands

    def run(self, commit=False):
        """Print command details, get command and run it."""
        details = self.details(commit=commit)
        print(details)
        commands = self.get_cmd(commit=commit)
        commands_print = self.get_cmd(add_password=True, commit=commit)
        for cmd, cmd_print in zip(commands, commands_print):
            print(cmd_print)
            print(cmd)
            if commit:
                subprocess.check_call(cmd)


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
        "repo_family",
        metavar="REPO_FAMILY",
        help="It is repo family in PDC.",
    )
    parser.add_argument(
        "--variant",
        metavar="VARIANT",
        dest="variants",
        action="append",
        help="It is variant in PDC.",
    )
    parser.add_argument(
        "--arch",
        metavar="ARCH",
        dest="arches",
        action="append",
        help="It is arch in PDC.",
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
