# Copyright 2026 Canonical Ltd.
# SPDX-License-Identifier: GPL-3.0-only

import sys
import ubuntu_lint

from dput.changes import Changes
from dput.exceptions import HookException
from dput.interfaces.cli import CLInterface
import re
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
    except ubuntu_lint.LintException as e:
        msg = str(e)

        if e.result == ubuntu_lint.LintResult.SKIP:
            interface.message("SKIP", str(e))
            return

        if sys.stdin.isatty():
            if can_ignore and interface.boolean("WARNING", f"{msg} - ignore?"):
                return
        raise HookException(f"ERROR: {msg}")


def dput_ppa_version_string(changes: Changes, profile: dict, interface: CLInterface):
    """
    For any upload to the archive, check that ~ppa is not present in the
    version string. For uploads to PPAs, check that ~ppa is present.
    """
    version_contains_ppa = re.match(r".*\w*ppa\d*$", changes["Version"])
    target = profile.get("name")

    if target == "ppa":
        if not version_contains_ppa:
            raise HookException(
                "ERROR: upload to ppa does not include ~ppa in version string"
            )
    else:
        if version_contains_ppa:
            raise HookException(
                "ERROR: upload to archive includes ~ppa in version string"
            )


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


def dput_sru_version_string_breaks_upgrades(
    changes: Changes, profile: dict, interface: CLInterface
):
    """
    Hook wrapper around ubuntu_lint.check_sru_version_string_breaks_upgrades.
    """
    call_lint_as_hook(
        ubuntu_lint.check_sru_version_string_breaks_upgrades,
        changes,
        profile,
        interface,
        can_ignore=True,
    )
