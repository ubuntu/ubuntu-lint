import distro_info
import requests

from ubuntu_lint import Context


def check_missing_ubuntu_maintainer(context: Context):
    """
    Check if the changes file has appropriately updated the Maintainer field to
    Ubuntu Developers <ubuntu-devel-discuss@lists.ubuntu.com>.
    """
    ubuntu_devel = "Ubuntu Developers <ubuntu-devel-discuss@lists.ubuntu.com>"

    if "ubuntu" not in context.changes.get("Version"):
        return

    if context.changes.get("Maintainer") != ubuntu_devel:
        context.lint_fail(f"Maintainer field is not set to {ubuntu_devel}")


def check_missing_launchpad_bugs_fixed(context: Context):
    """
    Check if at least one bug is being fixed by this upload, by checking
    the Launchpad-Bugs-Fixed field of the changes file.
    """
    if context.changes.get("Launchpad-Bugs-Fixed"):
        return

    context.lint_fail("no Launchpad bugs are marked as fixed by this upload")


def check_missing_bug_references(context: Context):
    """
    Check that the debian/changelog entry contains at least one bug reference.
    """
    if context.changelog_entry.lp_bugs_closed:
        return

    context.lint_fail("no Launchpad bugs are referenced in the changelog entry")


def check_distribution_invalid(context: Context):
    """
    Check that the debian/changelog entry uses a valid Ubuntu release name.
    """
    dist = context.changelog_entry.distributions
    if not distro_info.UbuntuDistroInfo().valid(dist):
        context.lint_fail(f'"{dist} is not a valid Ubuntu codename')


def check_missing_git_ubuntu_references(context: Context):
    """
    Check that the changes file is suitable for git-ubuntu uploads.

    In particular, check that:

     - Vcs-Git is a valid URL pointing to a git-ubuntu repository
     - Vcs-Git-Commit is a valid object in that repository
     - Vcs-Git-Ref is a reference to the object given in Vcs-Git-Commit
    """
    missing = []
    if not (vcs_git := context.changes.get("Vcs-Git")):
        missing.append("Vcs-Git")
    if not (vcs_git_commit := context.changes.get("Vcs-Git-Commit")):
        missing.append("Vcs-Git-Commit")
    if not (vcs_git_ref := context.changes.get("Vcs-Git-Ref")):
        missing.append("Vcs-Git-Ref")

    if missing:
        context.lint_fail("changes file is missing {}".format(", ".join(missing)))

    r = requests.get(f"{vcs_git}/patch/?h={vcs_git_ref}")
    if r.ok and r.text.startswith(f"From {vcs_git_commit} "):
        return

    context.lint_fail("Vcs-Git fields in changes file do not match the remote")
