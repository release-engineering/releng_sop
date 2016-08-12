# -*- coding: utf-8 -*-


from __future__ import print_function
from __future__ import unicode_literals

import argparse
import subprocess

from .common import Environment, Release


class KojiCreatePackageInRelease(object):
    def __init__(self, env, owner, release_id, packages):
        self.env = env
        self.release_id = release_id
        self.release = Release(self.release_id)
        self.packages = sorted(packages)
        self.owner = owner

    def print_details(self, commit=False):
        print("Blocking packages in a release")
        print(" * env name:                %s" % self.env.name)
        print(" * env config:              %s" % self.env.config_path)
        print(" * release source           %s" % self.release.config_path)
        print(" * koji profile:            %s" % self.env["koji_profile"])
        print(" * release_id:              %s" % self.release_id)
        print(" * owner:                   %s" % self.owner)
        print(" * tag:                     %s" % self.release["koji"]["tag_release"])
        print(" * packages:")
        for i in self.packages:
            print("     %s" % i)
        if not commit:
            print("*** TEST MODE ***")

    def get_cmd(self, commit=False):
        cmd = []
        cmd.append("koji")
        cmd.append("--profile=%s" % self.env["koji_profile"])
        cmd.append("add-pkg")
        cmd.append("--owner=%s" %self.owner)
        cmd.append(self.release["koji"]["tag_release"])
        cmd.extend(self.packages)
        if not commit:
            cmd = ["echo"] + cmd
        return cmd

    def run(self, commit=False):
        self.print_details(commit=commit)
        cmd = self.get_cmd(commit=commit)
        print(cmd)
        subprocess.check_output(cmd)


def get_parser():
    parser = argparse.ArgumentParser(description="Create packages in a koji tag that maps to given release.")
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
        "--owner",
        required=True,
        help="Package owner",
    )
    parser.add_argument(
        "--env",
        help="Select environment in which the program will make changes.",
    )
    return parser


def main():
    parser = get_parser()
    args = parser.parse_args()
    env = Environment(args.env)
    clone = KojiCreatePackageInRelease(env, args.owner, args.release_id, args.packages)
    clone.run(commit=args.commit)


if __name__ == "__main__":
    main()
