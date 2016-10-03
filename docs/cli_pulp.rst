Scripts for Pulp
================

pulp-clear-repos
----------------

.. argparse::
   :module: releng_sop.pulp_clear_repos
   :func: get_parser
   :prog: pulp-clear-repos


Manual Steps
~~~~~~~~~~~~
Requirements:


Inputs:

* **commit** - Program performs a dry-run by default. Enable this option to apply the changes.
* **RELEASE_ID** - PDC release ID, for example 'fedora-24', 'fedora-24-updates'.
* **REPO_FAMILY** - It is repo family in PDC.
* **variant** - It is variant in PDC.
* **arch** - It is arch in PDC.

Steps:

#  ``pulp_clear_repos [--commit] RELEASE_ID REPO_FAMILY [--variant=] ... [--arch=] ...``
