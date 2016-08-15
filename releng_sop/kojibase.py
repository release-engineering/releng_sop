# -*- coding: utf-8 -*-

import subprocess

from .common import Release

class KojiBase(object):
    def __init__(self, env, release_id, packages):
        self.env = env
        self.release_id = release_id
        self.release = Release(self.release_id)
        self.packages = sorted(packages)

    def run(self, commit=False):
        self.print_details(commit=commit)
        cmd = self.get_cmd(commit=commit)
        print(cmd)
        subprocess.check_output(cmd)
