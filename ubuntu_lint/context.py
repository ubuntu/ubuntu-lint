import distro_info

from debian import deb822, changelog
from launchpadlib.launchpad import Launchpad


class LintFailure(Exception):
    """
    This exception is raised when a linter calls Context.lint_fail. Callers of
    linters should handle this exception to determine why a specific linter
    failed.
    """

    pass


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
    ):
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

        if launchpad_handle is not None:
            self._lp = launchpad_handle

    @property
    def changes(self) -> deb822.Changes:
        if not self._changes:
            self.lint_error("missing context for changes file")
        assert self._changes is not None

        return self._changes

    @property
    def changelog_entry(self) -> changelog.ChangeBlock:
        if not self._changelog:
            self.lint_error("missing context for changelog entry")
        assert self._changelog is not None

        return self._changelog[0]

    @property
    def lp(self) -> Launchpad:
        if not self._lp:
            self._lp = Launchpad.login_anonymously("ubuntu-lint", "production")

        return self._lp

    def lint_fail(self, msg: str):
        raise LintFailure(msg)

    def lint_error(self, msg: str):
        raise RuntimeError(msg)

    def is_stable_release(self) -> bool:
        """
        Returns True if the context represents an upload targeting a stable
        release.
        """
        if self._changes:
            dist = self.changes.get("Distribution", "").partition("-")[0]
        elif self.changelog_entry:
            dist = self.changelog_entry.distributions
        else:
            raise ValueError("missing required context, require changelog or changes")

        return dist in distro_info.UbuntuDistroInfo().supported()
