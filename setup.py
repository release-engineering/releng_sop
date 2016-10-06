# -*- coding: utf-8 -*-
"""Packaging logic for releng-sop."""

from setuptools import setup, find_packages


setup(
    name="releng-sop",
    version="0.1",
    description="Release Engineering Standard Operating Procedures",
    url="https://github.com/release-engineering/releng-sop.git",
    author="Daniel Mach",
    author_email="dmach@redhat.com",
    license="MIT",
    install_requires=[
        "pyxdg",
        "productmd",
        "six",
        "pdc-client"
    ],
    packages=find_packages(),
    include_package_data=True,
    scripts=[
        "bin/koji-block-package-in-release",
        "bin/koji-create-package-in-release",
        "bin/koji-clone-tag-for-release-milestone",
        "bin/pulp-clear-repos"
    ],
    test_suite="tests",
    tests_require=["mock", "six", "pdc-client"]
)
