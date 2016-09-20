# -*- coding: utf-8 -*-


"""
Sign packages in a release tag.

Then import the signed headers to koji
and write signed copies in koji.
"""


from __future__ import print_function
from __future__ import unicode_literals
import sys

import argparse
import logging

from .common import Environment, Release, Error, ConfigError
from .koji_sign import KojiSignRPMs, get_rpmsign_class


class KojiSignRPMsInRelease(object):
    """
    Sign RPMs and import them to a koji instance.

    :param env: Environment object.
    :type  env: releng_sop.common.Environment
    :param release: Release object.
    :type  release: releng_sop.common.Release
    :param level: Signing level: 'beta' or 'gold'
    :type  level: str
    :param packages: List of packages to be signed (optional).
    :type  packages: list=None
    :param just_sign: Just sign RPMs, don't write RPMs from sigcache.
    :type  just_sign: bool=False
    :param just_write: Just write RPMs from sigcache, don't sign anything.
    :type  just_write: bool=False
    """

    def __init__(self, env, release, level, packages=None, just_sign=False, just_write=False):  # noqa: D102
        self.env = env
        self.release = release
        self.release_id = self.release.name
        self.koji_tag = self._get_koji_tag()
        self.level = level
        self.sigkeys = self._get_sigkeys()
        self.just_sign = just_sign
        self.just_write = just_write
        self.rpmsign_class = get_rpmsign_class(self.env)
        self.packages = sorted(packages or [])

    def _get_koji_tag(self):
        """
        Return tag name associated to a release.

        Return compose tag if exists.
        Return release tag if compose tag is not available.
        """
        result = self.release["koji"].get("tag_compose")
        if not result:
            result = self.release["koji"].get("tag_release")
        if result:
            return result
        raise ConfigError("Neither compose or release tag is set for release: %s" % self.release_id)

    def _get_sigkeys(self):
        """
        Get list of sigkeys according to the signing level.
        """
        if self.level == "beta":
            return [self.release["signing"]["sigkey_beta"], self.release["signing"]["sigkey_gold"]]
        elif self.level == "gold":
            return [self.release["signing"]["sigkey_gold"]]
        raise ConfigError("Unknown level: %s" % self.level)

    def details(self, commit=False):
        """
        Return details about command execution.

        :param commit: Disable dry-run, apply changes for real.
        :type  commit: bool=False
        :returns: List of text lines with command execution details
        :rtype:   list
        """
        result = [
            "Signing RPMs in a release",
            " * env name:                %s" % self.env.name,
            " * env config:              %s" % self.env.config_path,
            " * release source:          %s" % self.release.config_path,
            " * koji profile:            %s" % self.env["koji_profile"],
            " * release_id:              %s" % self.release_id,
            " * tag:                     %s" % self.koji_tag,
            " * level:                   %s" % self.level,
            " * sigkeys:                 %s" % ", ".join(self.sigkeys),
            " * just_sign:               %s" % self.just_sign,
            " * just_write:              %s" % self.just_write,
            " * signing class:           %s.%s" % (self.rpmsign_class.__module__, self.rpmsign_class.__name__),
        ]
        if self.packages:
            result += [" * packages:"]
            for i in self.packages:
                result += ["     - %s" % i]

        if not commit:
            result += ["*** TEST MODE ***"]
        return result

    def run(self, commit=False):
        """
        Print command details, get command and run it.

        :param commit: Disable dry-run, apply changes for real.
        :type  commit: bool=False
        """
        sign = KojiSignRPMs(self.env["koji_profile"], self.rpmsign_class, log_level=logging.DEBUG)

        for i in self.details(commit=commit):
            sign.logger.info(i)

        msg = "Reading RPM information from koji"
        sign.logger.info(msg)
        rpm_info_list = sign.get_latest_tagged_rpms(self.koji_tag)
        if self.packages:
            rpm_info_list = sign.filter_rpm_info_list_by_packages(rpm_info_list, self.packages)

        sign.sign(rpm_info_list, self.sigkeys, just_sign=self.just_sign, just_write=self.just_write, commit=commit)


def get_parser():
    """
    Construct argument parser.

    :returns: ArgumentParser object with arguments set up.
    :rtype:   argparse.ArgumentParser
    """
    parser = argparse.ArgumentParser(description="Sign RPMs in a koji tag that maps to given release.")
    parser.add_argument(
        "release_id",
        metavar="RELEASE_ID",
        help="PDC release ID, for example 'fedora-24', 'fedora-24-updates'.",
    )
    parser.add_argument(
        "level",
        choices=["beta", "gold"],
        help="Signature level. Allowed values: beta, gold.",
    )
    parser.add_argument(
        "--package",
        dest="packages",
        action="append",
        help="Specify packages to be signed",
    )

    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--just-sign",
        action="store_true",
        help="Just sign RPMs, don't write RPMs from sigcache.",
    )
    group.add_argument(
        "--just-write",
        action="store_true",
        help="Just write RPMs from sigcache, don't sign anything.",
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
    return parser


def main():
    """
    Main function.
    """
    try:
        parser = get_parser()
        args = parser.parse_args()
        env = Environment(args.env)
        release = Release(args.release_id)
        sign = KojiSignRPMsInRelease(env, release, args.level, packages=args.packages, just_sign=args.just_sign, just_write=args.just_write)
        sign.run(commit=args.commit)

    except Error:
        if not args.debug:
            sys.tracebacklimit = 0
        raise


if __name__ == "__main__":
    main()
