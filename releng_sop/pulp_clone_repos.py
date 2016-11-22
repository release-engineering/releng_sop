# -*- coding: utf-8 -*-

"""
Manual Steps
~~~~~~~~~~~~
Requirements:


Inputs:

* **commit** - Program performs a dry-run by default. Enable this option to apply the changes.
* **RELEASE_ID_FROM** - PDC release ID, for example 'fedora-24', 'fedora-24-updates'.
* **RELEASE_ID_TO** - PDC release ID, for example 'fedora-24', 'fedora-24-updates'.
* **REPO_FAMILY** - It is repo family in PDC.
* **variant** - It is variant in PDC.
* **arch** - It is arch in PDC.
* **skip-repo-check** - Repo_from and repo_to differ, fail instantly unless --skip-repo-check is set.

Steps:

#.  ``pulp-clone-repos FROM_RELEASE_ID TO_RELEASE_ID REPO_FAMILY [--commit] [--variant=] [--arch=] [--skip-repo-check] ...``
"""

from __future__ import print_function
from __future__ import unicode_literals
import getpass
import sys
import subprocess

from pdc_client import PDCClient
import argparse

from .common import Environment, Release, Error, UsageError
from .common_pulp import PulpAdminConfig


class PulpCloneRepos(object):
    """Clone Pulp repos.

    :param env:                Environment object to be used to execute the commands.
    :type env:                 Environment
    :note env:                 Keys 'pulp_server' and 'pdc_server' are used.

    :param release_from:       Release object from.
    :type release_from:        Release

    :param release_to:         Release object to.
    :type release_to:          Release

    :param repo_family:        Repo family to be cleared.
    :type repo_family:         string

    :param variants:           Variants to be filtered for.
    :type variant:             list of strings

    :param arches:             Architectures to be filtered for.
    :type arches:              list of strings

    :param content_category:   Content_category to be filtered for.
    :type content_category:    string

    :param skip_repo_check:    Repo_from and repo_to differ, fail instantly unless --skip-repo-check is set.
    :type skip_repo_check:     boolean
    """

    def __init__(self, env, release_from, release_to, repo_family, variants, arches, content_categories, skip_repo_check):  # noqa: D102
        self.env = env
        self.release_id_from = release_from.name
        self.release_from = release_from
        self.release_id_to = release_to.name
        self.release_to = release_to
        self.repo_family = repo_family
        self.variants = variants
        self.arches = arches
        self.pulp_config = PulpAdminConfig(self.env["pulp_server"])
        self.skip_repo_check = skip_repo_check
        self.content_categories = content_categories
        self.pulp_password = self.pulp_config["client"].get("password")

    def rearange(self, result):
        """Creating dictionary from repos and to repos."""
        rep = {}
        for x in result:
            key = (x['arch'], x['variant_uid'], x['content_category'])
            if key in rep:
                raise UsageError('Error same key in repos')
            rep[key] = x['name']
        return rep

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
        """Get name of pdc repo_from and pdc repo_to."""
        query_data_from = {
            "release_id": self.release_id_from,
            "service": "pulp",
            "repo_family": self.repo_family,
            "content_format": "rpm",
            "arch": self.arches,
            "variant_uid": self.variants,
            "content_category": self.content_categories,
            "shadow": False,
        }

        query_data_to = {
            "release_id": self.release_id_to,
            "service": "pulp",
            "repo_family": self.repo_family,
            "content_format": "rpm",
            "arch": self.arches,
            "variant_uid": self.variants,
            "content_category": self.content_categories,
            "shadow": False,
        }

        if self.release_id_from == self.release_id_to:
            raise UsageError('Release id is same')
        client = PDCClient(self.env["pdc_server"], develop=True)

        result_from = client['content-delivery-repos']._(page_size=0, **query_data_from)
        result_to = client['content-delivery-repos']._(page_size=0, **query_data_to)

        if (len(result_from) != len(result_to)) and (not self.skip_repo_check):
            raise UsageError('Error')

        rep_from = self.rearange(result_from)
        rep_to = self.rearange(result_to)

        self.cloned = []
        self.sameName = []
        self.missDest = []
        self.missSource = []

        while len(rep_from):
            map_key, name = rep_from.popitem()
            if map_key in rep_to:
                if name == rep_to[map_key]:
                    self.sameName.append({'from': name, 'to': rep_to[map_key]})
                else:
                    self.cloned.append({'from': name, 'to': rep_to[map_key]})
                del rep_to[map_key]
            else:
                self.missDest.append({'from': name})
        while len(rep_to):
            map_key, name = rep_to.popitem()
            self.missSource.append({'to': name})
        self.cloned = sorted(self.cloned, key=lambda x: sorted(x.values()))

    def details(self, commit=False):
        """
        Print details of command execution.

        :param commit: Flag to indicate if the command will be actually executed.
                       Line indicating "test mode" is printed, if this is False.
        :type  commit: boolean=False
        """
        self.query_repo()

        details = "Pulp clone repos\n"
        details += " * env name:                %s\n" % self.env.name
        details += " * env config:              %s\n" % self.env.config_path
        details += " * from release source:     %s\n" % self.release_from.config_path
        details += " * to release source:       %s\n" % self.release_to.config_path
        details += " * PDC server:              %s\n" % self.env["pdc_server"]
        details += " * release_id from:         %s\n" % self.release_id_from
        details += " * release_id to:           %s\n" % self.release_id_to
        if self.content_categories:
            details += " * content_categories:\n"
            for i in self.content_categories:
                details += "     %s\n" % i
        details += " * content_format:          %s\n" % 'rpm'
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
        details += " * repo from:\n"
        if not self.cloned:
            details += "     No repos found.\n"
        else:
            for x in self.cloned:
                details += "     %s\n" % x['from']
        details += " * repo to:\n"
        if not self.cloned:
            details += "     No repos found.\n"
        else:
            for x in self.cloned:
                details += "     %s\n" % x['to']
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
                       Prepend command with 'echo', if this is false
        :type commit: boolean=False

        :return: Pulp command
        :rtype:  list of strings
        """
        # password is added only if requested and this is commit action
        password = []
        if add_password and commit:
            password = ["--password=%s" % self.pulp_password]

        echo = []
        if not commit:
            echo = ['echo']

        commands = []
        for repo in self.cloned:
            cmd = []
            cmd.append("pulp-admin")
            cmd.append("--config=%s" % self.pulp_config.config_path)
            cmd.append("--user=%s" % self.pulp_config["client"]["user"])
            cmd = cmd + password
            cmd.append("repo")
            cmd.append("clone")
            cmd.append("--id=%s" % repo['from'])
            cmd.append("--clone_id=%s" % repo['to'])
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
        if self.sameName:
            for x in self.sameName:
                print('Source and destination is the same. Cloning "%s" skipped.' % x['from'])
        if self.missDest:
            for x in self.missDest:
                print('Missing destination repo. Cloning from "%s" skipped.' % x['to'])
        if self.missSource:
            for x in self.missSource:
                print('Missing source repo. Cloning from "%s" skipped.' % x['to'])


def get_parser():
    """Construct argument parser.

    :returns: ArgumentParser object with arguments set up.
    :rtype: argparse.ArgumentParser
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "from_release_id",
        metavar="FROM_RELEASE_ID",
        help="PDC release ID to clone from, for example 'fedora-24', 'fedora-24-updates'.",
    )
    parser.add_argument(
        "to_release_id",
        metavar="TO_RELEASE_ID",
        help="PDC release ID to clone to, for example 'fedora-24', 'fedora-24-updates'.",
    )
    parser.add_argument(
        "repo_family",
        metavar="REPO_FAMILY",
        help="PDC repo family to be considered for cloning.",
    )
    parser.add_argument(
        "--variant",
        metavar="VARIANT",
        dest="variants",
        action="append",
        help="PDC variant(s) to be considered for cloning.",
    )
    parser.add_argument(
        "--arch",
        metavar="ARCH",
        dest="arches",
        action="append",
        help="PDC architecture(s) to be considered for cloning.",
    )
    parser.add_argument(
        "--content-category",
        metavar="CON_CATEGORY",
        dest="content-categories",
        action="append",
        help="PDC content category to be considered for cloning.",
    )
    parser.add_argument(
        "--skip-repo-check",
        default=False,
        action="store_true",
        help="Skip checking if all the repos to clone from can be mapped to all the repos " +
             "to clone to. Will list repos not cloned due to missing destination or source.",
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
        release_from = Release(args.from_release_id)
        release_to = Release(args.to_release_id)
        clone = PulpCloneRepos(env, release_from, release_to, args.repo_family, args.variants,
                               args.arches, args.content_categories, args.skip_repo_check)
        clone.password_prompt(args.commit)
        clone.run(commit=args.commit)

    except Error:
        if not args.debug:
            sys.tracebacklimit = 0
        raise


if __name__ == "__main__":
    main()
