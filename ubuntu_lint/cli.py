# Copyright 2026 Canonical Ltd.
# SPDX-License-Identifier: GPL-3.0-only

import argparse
import sys
import ubuntu_lint

from typing import Callable, Sequence, Any


class Runner:
    all_linters = {
        "distribution-invalid": ubuntu_lint.check_distribution_invalid,
        "missing-bug-references": ubuntu_lint.check_missing_bug_references,
        "missing-git-ubuntu-references": ubuntu_lint.check_missing_git_ubuntu_references,
        "missing-launchpad-bugs-fixed": ubuntu_lint.check_missing_launchpad_bugs_fixed,
        "missing-pending-changelog-entry": ubuntu_lint.check_missing_pending_changelog_entry,
        "missing-ubuntu-maintainer": ubuntu_lint.check_missing_ubuntu_maintainer,
        "ppa-version-string": ubuntu_lint.check_ppa_version_string,
        "sru-bug-missing-template": ubuntu_lint.check_sru_bug_missing_template,
        "sru-bug-missing-release-tasks": ubuntu_lint.check_sru_bug_missing_release_tasks,
        "sru-version-string-breaks-upgrades": ubuntu_lint.check_sru_version_string_breaks_upgrades,
        "sru-version-string-convention": ubuntu_lint.check_sru_version_string_convention,
    }

    # Default actions when linting development release.
    auto_devel = {
        "distribution-invalid": "fail",
        "missing-bug-references": "warn",
        "missing-git-ubuntu-references": "warn",
        "missing-launchpad-bugs-fixed": "warn",
        "missing-pending-changelog-entry": "warn",
        "missing-ubuntu-maintainer": "fail",
        "ppa-version-string": "fail",
        "sru-bug-missing-template": "off",
        "sru-bug-missing-release-tasks": "off",
        "sru-version-string-breaks-upgrades": "off",
        "sru-version-string-convention": "off",
    }

    # Default actions when linting stable releases.
    auto_stable = {
        "distribution-invalid": "fail",
        "missing-bug-references": "fail",
        "missing-git-ubuntu-references": "warn",
        "missing-launchpad-bugs-fixed": "fail",
        "missing-pending-changelog-entry": "fail",
        "missing-ubuntu-maintainer": "fail",
        "ppa-version-string": "fail",
        "sru-bug-missing-template": "warn",
        "sru-bug-missing-release-tasks": "warn",
        "sru-version-string-breaks-upgrades": "warn",
        "sru-version-string-convention": "warn",
    }

    def __init__(self):
        self._checks_by_name: dict = self.all_linters
        self._action_by_name: dict = {
            name: "auto" for name in self._checks_by_name.keys()
        }
        self._results: dict[str, list[tuple[str, str]]] = {}

        self.changes_file: str | None = None
        self.debian_changelog: str | None = None
        self.source_dir: str = "."
        self.verbose: bool = False

    def set_linter(
        self,
        name: str,
        fn: Callable[[ubuntu_lint.Context], None],
        failure_action: str,
    ) -> None:
        """Configure a linter on the runner."""

        if failure_action == "off":
            try:
                del self._checks_by_name[name]
                del self._action_by_name[name]
            except KeyError:
                pass

            return

        self._checks_by_name[name] = fn
        self._action_by_name[name] = failure_action

    def run(self, context: ubuntu_lint.Context) -> int:
        """Run the configured linters with the given context."""
        ret = 0

        if context.is_stable_release():
            auto = self.auto_stable
        else:
            auto = self.auto_devel

        for name, fn in self._checks_by_name.items():
            failure_action = self._action_by_name[name]

            if failure_action == "auto":
                try:
                    failure_action = auto[name]
                except KeyError:
                    # Do not run this linter by default in this context.
                    continue

            if failure_action == "off":
                # Should not happen, but just in case.
                continue

            if failure_action not in ("warn", "fail"):
                raise ValueError(f'invalid failure action "{failure_action}"')

            result: str = "OK"
            msg: str = ""
            print(f"Running {name}...", end="", flush=True)
            try:
                fn(context)
            except ubuntu_lint.LintFailure as e:
                result = failure_action.upper()
                msg = str(e)
                if failure_action == "fail" and ret <= 0:
                    ret = 1
            except ubuntu_lint.MissingContextException as e:
                if self._action_by_name[name] == "auto":
                    result = "SKIP"
                else:
                    result = "ERROR"
                    ret = 2

                msg = str(e)

            try:
                self._results[result].append((name, msg))
            except KeyError:
                self._results[result] = [(name, msg)]

            print(result)

        self.print_summary()

        return ret

    def print_summary(self):
        ran = 0

        # Print failure details
        for mode, results in self._results.items():
            num = len(results)
            ran += num

            if mode == "OK" or num == 0:
                continue

            if mode == "SKIP" and not self.verbose:
                continue

            if num == 1:
                print(f"\n{mode}: 1 issue")
            else:
                print(f"\n{mode}: {num} issues")

            for (name, msg) in results:
                print(f"    {name}: {msg}")

        stats = []
        for mode in ("OK", "FAIL", "WARN", "ERROR", "SKIP"):
            num = len(self._results.get(mode, []))
            stats.append(f"{mode}: {num}")
        short = ", ".join(stats)

        print(f"\nSummary: ran {ran} lint checks ({short})")


class ActionConfigureLinter(argparse.Action):
    def __call__(
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        values: str | Sequence[Any] | None,
        option_string: str | None = None,
    ) -> None:
        # '--linter-name' -> 'linter-name'
        assert option_string is not None
        name = option_string.lstrip("-")
        namespace.set_linter(name, namespace.all_linters[name], values)


def main():
    parser = argparse.ArgumentParser(
        prog="ubuntu-lint",
        description="Lint checker for Ubuntu package uploads",
    )
    parser.add_argument(
        "--verbose",
        help="Verbose output",
        action="store_true",
    )

    context_args = parser.add_argument_group(
        "context options",
        "Control package context for linters",
    )

    context_args.add_argument(
        "--source-dir",
        help="Path to debian source package",
        type=str,
    )
    context_args.add_argument(
        "--debian-changelog",
        help="Path to debian changelog",
        type=str,
    )
    context_args.add_argument(
        "--changes-file",
        help="Path to source changes file",
        type=str,
    )

    linter_args = parser.add_argument_group(
        "linter options", "Enable or disable specific lint checks"
    )
    for name, callback in Runner.all_linters.items():
        linter_args.add_argument(
            f"--{name}",
            type=str,
            choices=["auto", "off", "warn", "fail"],
            default="auto",
            action=ActionConfigureLinter,
        )

    runner = parser.parse_args(namespace=Runner())

    context = ubuntu_lint.Context(
        source_dir=runner.source_dir,
        debian_changelog=runner.debian_changelog,
        changes=runner.changes_file,
    )

    sys.exit(runner.run(context))
