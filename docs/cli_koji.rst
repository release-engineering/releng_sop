Koji
====

koji-block-package-in-release
-----------------------------

.. argparse::
   :module: releng_sop.koji_block_package_in_release
   :func: get_parser
   :prog: koji-block-package-in-release


Manual Steps
~~~~~~~~~~~~
Requirements:

* **koji** package
* package with a koji profile (if needed)

Inputs:

* **profile** - koji instance in which the change will be made
* **tag** - release (a.k.a. main) koji tag name for a release
* **package** - name of package to be blocked in a release

Steps:

#. ``koji --profile=<profile> block-pkg <tag> <package> [package] ...``


koji-create-package-in-release
------------------------------

.. argparse::
   :module: releng_sop.koji_create_package_in_release
   :func: get_parser
   :prog: koji-create-package-in-release


Manual Steps
~~~~~~~~~~~~
Requirements:

* **koji** package
* package with a koji profile (if needed)

Inputs:

* **profile** - koji instance in which the change will be made
* **owner** - package owner
* **tag** - release (a.k.a. main) koji tag name for a release
* **package** - name of package to be created in a release

Steps:

#. ``koji --profile=<profile> add-pkg --owner=<owner> <tag> <package> [package] ...``


koji-clone-tag-for-release-milestone
------------------------------------

Clone a tag if you want to freeze package set for a milesone.
Then make a milestone compose. If a respin is needed, tag/untag builds
and respin the compose with increased minor version of the milestone
(Beta-1.0 -> Beta-1.1).


.. argparse::
   :module: releng_sop.koji_clone_tag_for_release_milestone
   :func: get_parser
   :prog: koji-clone-tag-for-release-milestone


Example::

    koji_clone_tag_for_release_milestone.py [--commit] fedora-24 Beta-1.2

    Cloning package set for a release milestone
     * koji profile:            test
     * release_id:              fedora-24
     * milestone:               Beta-1.2
     * compose tag (source):    f24-compose
     * milestone tag (target):  f24-beta-1-set
    *** TEST MODE ***
    ['koji', u'--profile=koji', 'clone-tag', '--verbose', u'f24-compose', u'f24-beta-1-set', '--test']
    ...


Manual Steps
~~~~~~~~~~~~
Requirements:

* **koji** package
* package with a koji profile (if needed)

Inputs:

* **profile** - koji instance in which the change will be made
* **compose_tag** - release (a.k.a. main) koji tag name for a release
* **milestone_tag** - main release tag + name of milestone + milestone major version + "-set" suffix, for example f24-beta-1-set

Steps:

#. ``koji --profile=<profile> clone-tag --verbose <compose_tag> <milestone_tag>``
