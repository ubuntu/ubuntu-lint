import ubuntu_lint

from dput.changes import Changes
from dput.exceptions import HookException
from dput.interfaces.cli import CLInterface
from typing import Callable


def call_lint_as_hook(
    lint: Callable[[ubuntu_lint.Context], None],
    changes: Changes,
    profile: dict,
    interface: CLInterface,
    can_ignore: bool = False,
):
    context = ubuntu_lint.Context(changes=changes.get_raw_changes())
    try:
        lint(context)
    except ubuntu_lint.LintFailure as e:
        msg = str(e)
        if can_ignore and interface.boolean("WARNING", f"{msg} - ignore?"):
            return
        raise HookException(f"ERROR: {msg}")


def dput_missing_launchpad_bugs_fixed(
    changes: Changes, profile: dict, interface: CLInterface
):
    """
    Hook wrapper around ubuntu_lint.check_missing_launchpad_bugs_fixed.
    """
    call_lint_as_hook(
        ubuntu_lint.check_missing_launchpad_bugs_fixed,
        changes,
        profile,
        interface,
        can_ignore=True,
    )


def dput_missing_ubuntu_maintainer(
    changes: Changes, profile: dict, interface: CLInterface
):
    """
    Hook wrapper around ubuntu_lint.check_missing_ubuntu_maintainer.
    """
    call_lint_as_hook(
        ubuntu_lint.check_missing_ubuntu_maintainer,
        changes,
        profile,
        interface,
    )


def dput_missing_git_ubuntu_references(
    changes: Changes, profile: dict, interface: CLInterface
):
    """
    Hook wrapper around ubuntu_lint.check_missing_git_ubuntu_references.
    """
    call_lint_as_hook(
        ubuntu_lint.check_missing_git_ubuntu_references,
        changes,
        profile,
        interface,
        can_ignore=True,
    )


def dput_missing_pending_changelog_entry(
    changes: Changes, profile: dict, interface: CLInterface
):
    """
    Hook wrapper around ubuntu_lint.check_missing_pending_changelog_entry.
    """
    call_lint_as_hook(
        ubuntu_lint.check_missing_pending_changelog_entry,
        changes,
        profile,
        interface,
        can_ignore=True,
    )


def dput_sru_bug_missing_template(
    changes: Changes, profile: dict, interface: CLInterface
):
    """
    Hook wrapper around ubuntu_lint.check_sru_bug_missing_template.
    """
    call_lint_as_hook(
        ubuntu_lint.check_sru_bug_missing_template,
        changes,
        profile,
        interface,
        can_ignore=True,
    )


def dput_sru_bug_missing_release_tasks(
    changes: Changes, profile: dict, interface: CLInterface
):
    """
    Hook wrapper around ubuntu_lint.check_sru_bug_missing_release_tasks.
    """
    call_lint_as_hook(
        ubuntu_lint.check_sru_bug_missing_release_tasks,
        changes,
        profile,
        interface,
        can_ignore=True,
    )
