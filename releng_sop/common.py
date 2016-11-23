# -*- coding: utf-8 -*-
"""Common code and utilities."""


import os
import json
import logging
import subprocess

import xdg.BaseDirectory


__all__ = (
    "Environment",
    "Release",
    "get_logger",
    "Error",
    "ConfigError",
    "UsageError",
)


class Error(Exception):
    """Base class for releng-sop errors."""

    pass


class ConfigError(Error):
    """Error to be raised for configuration errors."""

    pass


class UsageError(Error):
    """Error to be raised for usage errors of scripts."""

    pass


class ConfigBase(object):
    """Base class for configurations."""

    # override in inherited classes
    config_subdir = None
    config_suffix = ".json"

    def __init__(self, name, config_dirs=None):
        self.name = name
        self._set_config_dirs(config_dirs)
        self._set_config_path()
        self._read_config()

    def _set_config_dirs(self, config_dirs=None):
        """
        Set list of config dirs in priority order.
        """
        self.config_dirs = []
        if config_dirs:
            # set user defined paths
            self.config_dirs += config_dirs
        else:
            # set userdir and system conf dirs
            self.config_dirs.append(os.path.join(xdg.BaseDirectory.xdg_config_home, "releng-sop", self.config_subdir))
            self.config_dirs.append(os.path.join("/etc", "releng-sop", self.config_subdir))

    def _set_config_path(self):
        """
        Find existing config in config dirs.
        """
        filename = "%s%s" % (self.name, self.config_suffix)
        for dirname in self.config_dirs:
            # resolve the default.conf symlink to real path
            path = os.path.realpath(os.path.join(dirname, filename))
            if os.path.exists(path):
                self.config_path = path
                return

        message = "Couldn't find config file '%s' in following locations:\n%s"
        raise ConfigError(message % (filename, "\n".join(self.config_dirs)))

    def _read_config(self):
        """
        Read config file contents.
        """
        with open(self.config_path, "r") as f:
            self.config_data = json.load(f)

    def __getitem__(self, name):
        return self.config_data[name]

    def __contains__(self, name):
        return name in self.config_data

    def __iter__(self):
        for key in self.config_data:
            yield key


class Environment(ConfigBase):
    """Environment configuration."""

    config_subdir = "environments"


class Release(ConfigBase):
    """Release configuration."""

    config_subdir = "releases"


class CommandBase(object):
    """Base class for commands.

    :param env:        Environment object to be used to execute the commands.
    :type env:         Environment

    :param release: Release object.
    :type release:  Release
    """

    def __init__(self, env, release):  # noqa: D102
        self.env = env
        self.release_id = release.name
        self.release = release

    def run(self, commit=False):
        """Print command details, get command and run it."""
        details = self.details(commit=commit)
        print(details)
        cmd = self.get_cmd(commit=commit)
        print(cmd)
        subprocess.check_output(cmd)


def get_logger(obj, log_level):
    """
    Return default logger with console output.
    """
    logger = logging.Logger(obj.__class__.__name__)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)-8s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))
    handler.setLevel(log_level)
    logger.addHandler(handler)
    return logger
