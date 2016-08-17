# -*- coding: utf-8 -*-


import os
import json

import xdg.BaseDirectory


__all__ = (
    "Environment",
    "Release",
)


class ConfigBase(object):

    # override in inherited classes
    config_subdir = None

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
        filename = "%s.json" % self.name
        for dirname in self.config_dirs:
            # resolve the default.conf symlink to real path
            path = os.path.realpath(os.path.join(dirname, filename))
            if os.path.exists(path):
                self.config_path = path
                return
        raise RuntimeError("Couldn't find config file '%s' in following locations:\n%s" % (filename, "\n".join(self.config_dirs)))

    def _read_config(self):
        """
        Read config file contents.
        """
        with open(self.config_path, "r") as f:
            self.config_data = json.load(f)

    def __getitem__(self, name):
        return self.config_data[name]

    def __iter__(self):
        for key in self.config_data:
            yield key


class Environment(ConfigBase):
    config_subdir = "environments"
    default_config = "default"


class Release(ConfigBase):
    config_subdir = "releases"
