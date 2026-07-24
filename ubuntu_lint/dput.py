# Copyright 2026 Canonical Ltd.
# SPDX-License-Identifier: GPL-3.0-only

import re
import sys
import ubuntu_lint

from dput.changes import Changes
from dput.core import logger
from dput.exceptions import HookException
from dput.interfaces.cli import CLInterface
from pathlib import Path
from typing import Callable
from ubuntu_lint.cli import format_error, format_warning


def call_lint_as_hook(
    lint: Callable[[ubuntu_lint.Context], None],
    changes: Changes,
    profile: dict,
    interface: CLInterface,
    can_ignore: bool = False,
    stable_can_ignore: bool = False,
):

    raw_changes = changes.get_raw_changes()
    source = raw_changes.get_as_string("Source")

    # The epoch is stripped from the build artifact filenames, if present.
    version_no_epoch = raw_changes.get_as_string("Version").split(":")[-1]

    debian_tar: Path | None = None
    for f in changes.get_files():
        p = Path(f)

        if re.match(
            rf"^{source}_{re.escape(version_no_epoch)}(?:\.debian)?\.tar\.(?:xz|gz|bz2|lzma)$",
            p.name,
        ):
            debian_tar = p
            break

    if debian_tar is None:
        raise HookException(
            format_error("ERROR: could not find source package tarball")
        )

    context = ubuntu_lint.Context(
        changes=raw_changes,
        debian_tar=debian_tar,
    )
    try:
        lint(context)
    except ubuntu_lint.LintException as e:
        msg = str(e)

        if e.result == ubuntu_lint.LintResult.SKIP:
            logger.debug(f"skipping {lint.__name__}: {msg}")
            return

        if (
            can_ignore or (stable_can_ignore and context.is_stable_release())
        ) and sys.stdin.isatty():
            if interface.boolean(
                format_warning("WARNING"),
                format_warning(f"{msg} - ignore?"),
            ):
                return

        raise HookException(format_error(f"ERROR: {msg}"))


def dput_ppa_version_string(changes: Changes, profile: dict, interface: CLInterface):
    """
    For any upload to the archive, check that ~ppa is not present in the
    version string. For uploads to PPAs, check that ~ppa is present.
    """
    version_contains_ppa = re.match(r".*\w*ppa\d*$", changes["Version"])
    target = profile.get("name")

    if target == "ppa":
        if version_contains_ppa:
            return

        msg = "upload to ppa does not include ~ppa in version string"
        if sys.stdin.isatty():
            if interface.boolean(
                format_warning("WARNING"),
                format_warning(f"{msg} - ignore?"),
            ):
                return

        raise HookException(format_error(f"ERROR: {msg}"))
    else:
        if version_contains_ppa:
            raise HookException(
                format_error("ERROR: upload to archive includes ~ppa in version string")
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
        can_ignore=True,
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


def dput_release_mismatch(changes: Changes, profile: dict, interface: CLInterface):
    """
    Hook wrapper around ubuntu_lint.check_release_mismatch.
    """
    call_lint_as_hook(
        ubuntu_lint.check_release_mismatch,
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


def dput_missing_version_suffix(
    changes: Changes, profile: dict, interface: CLInterface
):
    """
    Hook wrapper around ubuntu_lint.check_missing_version_suffix.
    """
    call_lint_as_hook(
        ubuntu_lint.check_missing_version_suffix,
        changes,
        profile,
        interface,
        stable_can_ignore=True,
    )


def dput_merge_missing_new_debian_changelog(
    changes: Changes, profile: dict, interface: CLInterface
):
    """
    Hook wrapper around ubuntu_lint.check_merge_missing_new_debian_changelog.
    """
    call_lint_as_hook(
        ubuntu_lint.check_merge_missing_new_debian_changelog,
        changes,
        profile,
        interface,
        can_ignore=True,
    )


def dput_sru_version_string_convention(
    changes: Changes, profile: dict, interface: CLInterface
):
    """
    Hook wrapper around ubuntu_lint.check_sru_version_string_convention.
    """
    call_lint_as_hook(
        ubuntu_lint.check_sru_version_string_convention,
        changes,
        profile,
        interface,
        can_ignore=True,
    )
