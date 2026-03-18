# Copyright 2026 Canonical Ltd.
# SPDX-License-Identifier: GPL-3.0-only

import distro_info
import os

from debian import (
    deb822,
    debian_support,
    changelog,
)
from launchpadlib.launchpad import Launchpad
from typing import Any


class LintFailure(Exception):
    """
    This exception is raised when a linter calls Context.lint_fail. Callers of
    linters should handle this exception to determine why a specific linter
    failed.
    """

    pass


class MissingContextException(Exception):
    """
    This exception is raised when a linter tries to use context (e.g. changelog or
    changes file), but it is not initialized for this Context instance.
    """

    pass


class InconsistentContextException(Exception):
    """
    This exception is raised when one or more context sources have inconsistent
    data for the same information.
    """
    def __init__(self, what: str, from_changes: Any, from_changelog: Any):
        self.what = what
        self.from_changes = from_changes
        self.from_changelog = from_changelog

        super().__init__(
            f"conflicting data for {what}: changes data ({from_changes}) does not "
            f"match changelog data ({from_changelog})"
        )


class Context:
    """
    A class to encapsulate the context of a source package, or package upload
    for a linter. Instances of Context are passed to linters.
    """

    def __init__(
        self,
        changes: str | deb822.Changes | None = None,
        debian_changelog: str | changelog.Changelog | None = None,
        launchpad_handle: Launchpad | None = None,
        source_dir: str | None = None,
    ):
        self._source_dir: str | None = None
        if source_dir:
            self.source_dir = source_dir

            if debian_changelog is None:
                debian_changelog = os.path.join(self.source_dir, "debian/changelog")

        self._changes: deb822.Changes | None = None
        if isinstance(changes, str):
            with open(changes, "r") as f:
                self._changes = deb822.Changes(f)

        elif isinstance(changes, deb822.Changes):
            self._changes = changes

        elif changes is not None:
            raise ValueError("invalid type for changes")

        self._changelog: changelog.Changelog | None = None
        if isinstance(debian_changelog, str):
            with open(debian_changelog, "r") as f:
                self._changelog = changelog.Changelog(f)

        elif isinstance(debian_changelog, changelog.Changelog):
            self._changelog = debian_changelog

        elif debian_changelog is not None:
            raise ValueError("invalid type for changelog")

        if not any((self._changes, self._changelog)):
            raise ValueError("context requires at least one of changes or changelog")

        self._lp: Launchpad | None = None
        if launchpad_handle is not None:
            self._lp = launchpad_handle

    @property
    def changes(self) -> deb822.Changes:
        if not self._changes:
            raise MissingContextException("missing context for changes file")
        assert self._changes is not None

        return self._changes

    def changelog_entry_by_index(self, index: int) -> changelog.ChangeBlock:
        if not self._changelog:
            raise MissingContextException("missing context for changelog entry")
        assert self._changelog is not None

        return self._changelog[index]

    @property
    def changelog_entry(self) -> changelog.ChangeBlock:
        return self.changelog_entry_by_index(0)

    @property
    def lp(self) -> Launchpad:
        if not self._lp:
            self._lp = Launchpad.login_anonymously("ubuntu-lint", "production")

        return self._lp

    @property
    def source_dir(self) -> str:
        if not self._source_dir:
            raise MissingContextException("missing context for source dir")
        assert self._source_dir is not None

        return self._source_dir

    @source_dir.setter
    def source_dir(self, source_dir: str):
        if not os.path.isdir(os.path.join(source_dir, "debian")):
            raise ValueError(f"{source_dir} does not look like a debian source package")

        self._source_dir = source_dir

    def lint_fail(self, msg: str):
        raise LintFailure(msg)

    def _ensure_get[T](
        self,
        what: str,
        from_changes: T | None,
        from_changelog: T | None,
    ) -> T:
        if (from_changes, from_changelog) == (None, None):
            raise MissingContextException(f"missing required context for {what}")

        if None not in (from_changes, from_changelog) and from_changes != from_changelog:
            raise InconsistentContextException(what, from_changes, from_changelog)

        ret = from_changes or from_changelog
        assert ret is not None

        return ret

    def get_distribution(self) -> str:
        """
        Return the name of the distribution associated with the change, e.g.
        noble, noble-security, etc.
        """
        try:
            from_changes = self.changes.get("Distribution")
        except MissingContextException:
            from_changes = None
        try:
            from_changelog = str(self.changelog_entry.distributions)
        except MissingContextException:
            from_changelog = None

        return self._ensure_get("distribution", from_changes, from_changelog)

    def get_series(self) -> str:
        """
        Return the name of the series associated with the change, e.g.
        noble, resolute, etc.
        """
        return self.get_distribution().partition('-')[0]

    def is_stable_release(self) -> bool:
        """
        Returns True if the context represents an upload targeting a stable
        release.
        """
        di = distro_info.UbuntuDistroInfo()
        stable = set(di.supported() + di.supported_esm()) - set([di.devel()])

        return self.get_series() in stable

    def get_launchpad_bugs_fixed(self) -> list[str]:
        """
        Returns the list of bugs fixed by this upload, according to
        changes file or most recent changelog entry.
        """
        try:
            from_changes = self.changes.get("Launchpad-Bugs-Fixed", "").split()
        except MissingContextException:
            from_changes = None

        try:
            from_changelog = [str(n) for n in self.changelog_entry.lp_bugs_closed]
        except MissingContextException:
            from_changelog = None

        return self._ensure_get("launchpad bugs fixed", from_changes, from_changelog)

    def get_package_version(self) -> debian_support.Version:
        """
        Returns the current package version, according to changes
        file or most recent changelog entry.
        """
        try:
            from_changes = debian_support.Version(self.changes.get("Version"))
        except MissingContextException:
            from_changes = None

        try:
            from_changelog = self.changelog_entry.version
        except MissingContextException:
            from_changelog = None

        return self._ensure_get("version", from_changes, from_changelog)

    def get_source_package_name(self):
        try:
            from_changes = self.changes.get("Source")
        except MissingContextException:
            from_changes = None

        try:
            from_changelog = self.changelog_entry.package
        except MissingContextException:
            from_changelog = None

        return self._ensure_get("source name", from_changes, from_changelog)
