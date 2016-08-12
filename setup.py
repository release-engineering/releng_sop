# -*- coding: utf-8 -*-


from setuptools import setup, find_packages


setup(
    name="releng-sop",
    version="0.1",
    description="Release Enginering Standard Operating Procedures",
    url="https://github.com/release-engineering/releng-sop.git",
    author="Daniel Mach",
    author_email="dmach@redhat.com",
    license="MIT",
    install_requires=[
        "pyxdg"
    ],
    packages=find_packages(),
    include_package_data=True,
    scripts=[
        "bin/koji-block-package-in-release",
        "bin/koji-create-package-in-release",
    ],
    test_suite="tests",
)
