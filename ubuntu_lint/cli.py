# Copyright 2026 Canonical Ltd.
# SPDX-License-Identifier: GPL-3.0-only

import argparse
import json
import os
import sys
import ubuntu_lint

from typing import Callable, Sequence, Any


class LinterConfiguration:
    def __init__(
        self,
        name: str,
        fn: Callable[[ubuntu_lint.Context], None],
        default_level_devel: ubuntu_lint.LintResult | None,
        default_level_stable: ubuntu_lint.LintResult | None,
        level: ubuntu_lint.LintResult | None = None,
        requires: set[str] = set(),
    ):
        self.name = name
        self.fn = fn
        self.level = level
        self.default_level_devel = default_level_devel
        self.default_level_stable = default_level_stable
        self.requires = requires

    def get_level(self, is_stable: bool) -> ubuntu_lint.LintResult | None:
        if self.level is not None:
            return self.level

        return self.default_level_stable if is_stable else self.default_level_devel

    def is_auto(self) -> bool:
        return self.level is None


all_linters = [
    LinterConfiguration(
        name="distribution-invalid",
        fn=ubuntu_lint.check_distribution_invalid,
        default_level_devel=ubuntu_lint.LintResult.FAIL,
        default_level_stable=ubuntu_lint.LintResult.FAIL,
    ),
    LinterConfiguration(
        name="git-ubuntu-references-mismatch",
        fn=ubuntu_lint.check_git_ubuntu_references_mismatch,
        default_level_devel=ubuntu_lint.LintResult.FAIL,
        default_level_stable=ubuntu_lint.LintResult.FAIL,
        requires={"changes"},
    ),
    LinterConfiguration(
        name="missing-bug-references",
        fn=ubuntu_lint.check_missing_bug_references,
        default_level_devel=ubuntu_lint.LintResult.WARN,
        default_level_stable=ubuntu_lint.LintResult.FAIL,
        requires={"changelog"},
    ),
    LinterConfiguration(
        name="missing-git-ubuntu-references",
        fn=ubuntu_lint.check_missing_git_ubuntu_references,
        default_level_devel=ubuntu_lint.LintResult.WARN,
        default_level_stable=ubuntu_lint.LintResult.WARN,
        requires={"changes"},
    ),
    LinterConfiguration(
        name="missing-launchpad-bugs-fixed",
        fn=ubuntu_lint.check_missing_launchpad_bugs_fixed,
        default_level_devel=ubuntu_lint.LintResult.WARN,
        default_level_stable=ubuntu_lint.LintResult.FAIL,
        requires={"changes"},
    ),
    LinterConfiguration(
        name="missing-pending-changelog-entry",
        fn=ubuntu_lint.check_missing_pending_changelog_entry,
        default_level_devel=ubuntu_lint.LintResult.WARN,
        default_level_stable=ubuntu_lint.LintResult.FAIL,
        requires={"changes"},
    ),
    LinterConfiguration(
        name="missing-ubuntu-maintainer",
        fn=ubuntu_lint.check_missing_ubuntu_maintainer,
        default_level_devel=ubuntu_lint.LintResult.FAIL,
        default_level_stable=ubuntu_lint.LintResult.FAIL,
        requires={"changes"},
    ),
    LinterConfiguration(
        name="sru-bug-missing-template",
        fn=ubuntu_lint.check_sru_bug_missing_template,
        default_level_devel=None,
        default_level_stable=ubuntu_lint.LintResult.WARN,
    ),
    LinterConfiguration(
        name="sru-bug-missing-release-tasks",
        fn=ubuntu_lint.check_sru_bug_missing_release_tasks,
        default_level_devel=None,
        default_level_stable=ubuntu_lint.LintResult.WARN,
    ),
    LinterConfiguration(
        name="sru-version-string-breaks-upgrades",
        fn=ubuntu_lint.check_sru_version_string_breaks_upgrades,
        default_level_devel=None,
        default_level_stable=ubuntu_lint.LintResult.WARN,
    ),
    LinterConfiguration(
        name="sru-version-string-convention",
        fn=ubuntu_lint.check_sru_version_string_convention,
        default_level_devel=None,
        default_level_stable=ubuntu_lint.LintResult.WARN,
        requires={"changelog"},
    ),
    LinterConfiguration(
        name="release-mismatch",
        fn=ubuntu_lint.check_release_mismatch,
        default_level_devel=ubuntu_lint.LintResult.WARN,
        default_level_stable=ubuntu_lint.LintResult.WARN,
    ),
]
all_linters_by_name = {linter.name: linter for linter in all_linters}


class Runner:
    def __init__(self):
        self._checks_by_name: dict = {linter.name: linter for linter in all_linters}
        self._results: dict[ubuntu_lint.LintResult, list[tuple[str, str]]] = {}

        self.changes_file: str | None = None
        self.debian_changelog: str | None = None
        self.source_dir: str | None = None
        self.verbose: bool = False
        self.print_json: bool = False

    def set_linter_level(
        self,
        name: str,
        level: str,
    ) -> None:
        """Configure a linter on the runner."""

        if name not in self._checks_by_name:
            self._checks_by_name[name] = all_linters_by_name[name]

        if level == "off":
            try:
                del self._checks_by_name[name]
            except KeyError:
                pass
        elif level == "auto":
            self._checks_by_name[name].level = None
        else:
            self._checks_by_name[name].level = ubuntu_lint.LintResult[level.upper()]

    def set_level_all(self, level: str):
        for name in list(self._checks_by_name):
            self.set_linter_level(name, level)

    def run(self, context: ubuntu_lint.Context) -> int:
        """Run the configured linters with the given context."""
        ret = 0

        context_sources = set()
        try:
            if context.changes:
                context_sources.add("changes")
        except ubuntu_lint.MissingContextException:
            pass

        try:
            if context.changelog_entry:
                context_sources.add("changelog")
        except ubuntu_lint.MissingContextException:
            pass

        for name, linter in self._checks_by_name.items():
            level = linter.get_level(context.is_stable_release())
            if level is None:
                continue

            if not linter.requires <= context_sources:
                continue

            result = ubuntu_lint.LintResult.OK
            msg: str = ""
            if not self.print_json:
                print(f"Running {name}...", end="", flush=True)
            try:
                linter.fn(context)
            except ubuntu_lint.LintException as e:
                result = e.result

                # If the level for this check was explicitly configured,
                # downgrade the level if needed.
                if level.value < result.value:
                    result = level

                msg = str(e)
                if level == ubuntu_lint.LintResult.FAIL and ret <= 0:
                    ret = 1

            except ubuntu_lint.MissingContextException as e:
                if linter.is_auto():
                    result = ubuntu_lint.LintResult.SKIP
                else:
                    result = ubuntu_lint.LintResult.ERROR
                    ret = 2

                msg = str(e)

            try:
                self._results[result].append((name, msg))
            except KeyError:
                self._results[result] = [(name, msg)]

            if not self.print_json:
                print(result.name)

        self.print_summary()

        return ret

    def print_summary(self):
        if self.print_json:
            output = {}

            for level, results in self._results.items():
                for name, msg in results:
                    output[name] = {"result": level.name}
                    if level != ubuntu_lint.LintResult.OK:
                        output[name]["reason"] = msg

            print(json.dumps(output, indent=4))
            return

        # Print failure details
        ran = 0
        for level, results in self._results.items():
            num = len(results)
            ran += num

            if level == ubuntu_lint.LintResult.OK or num == 0:
                continue

            if level == ubuntu_lint.LintResult.SKIP and not self.verbose:
                continue

            if num == 1:
                print(f"\n{level.name}: 1 issue")
            else:
                print(f"\n{level.name}: {num} issues")

            for name, msg in results:
                print(f"    {name}: {msg}")

        stats = []
        for level in ubuntu_lint.LintResult:
            num = len(self._results.get(level, []))
            stats.append(f"{level.name}: {num}")
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
        if name == "all":
            # Special key for setting level of all linters.
            namespace.set_level_all(values)
        else:
            namespace.set_linter_level(name, values)


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
    parser.add_argument(
        "--json",
        help="Print results as JSON",
        action="store_true",
        dest="print_json",
    )

    context_args = parser.add_argument_group(
        "context options",
        "Control package context for linters. If ubuntu-lint is run without "
        "any arguments and the current working directory looks like a "
        "Debian source package, it will use the changelog and the most recent "
        "changes file as context, if available."
        "\n\n"
        "Alternatively, context can be given explicitly using the flags below.",
    )

    context_args.add_argument(
        "--source-dir",
        help="Path to debian source package",
        type=str,
    )
    context_args.add_argument(
        "--changelog",
        help="Path to debian changelog",
        type=str,
        dest="debian_changelog",
    )
    context_args.add_argument(
        "--changes-file",
        help="Path to source changes file",
        type=str,
    )

    linter_args = parser.add_argument_group(
        "linter options",
        "Configure individual lint checks. Setting to 'off' disables the "
        "check entirely, while setting to 'warn' or 'fail' controls how a "
        "failure should be treated. For example, if a lint check returns "
        "'fail', but 'warn' was set for that check, the failure is downgraded "
        "to a warning. Setting to 'auto' lets the default take effect.",
    )
    linter_args.add_argument(
        "--all",
        help=(
            "Set the level for all lint checks. Settings for specific lint "
            "checks that come after this flag will take precedence."
        ),
        type=str,
        choices=["auto", "off", "warn", "fail"],
        default="auto",
        action=ActionConfigureLinter,
    )
    for linter in all_linters:
        linter_args.add_argument(
            f"--{linter.name}",
            type=str,
            choices=["auto", "off", "warn", "fail"],
            default="auto",
            action=ActionConfigureLinter,
        )

    runner = parser.parse_args(namespace=Runner())

    if not any(
        (
            runner.source_dir,
            runner.debian_changelog,
            runner.changes_file,
        )
    ):
        if os.path.exists("debian"):
            runner.source_dir = "."
        else:
            parser.error(
                "must specify a combination of changelog, changes file, or source directory"
            )

    context = ubuntu_lint.Context(
        source_dir=runner.source_dir,
        debian_changelog=runner.debian_changelog,
        changes=runner.changes_file,
    )

    sys.exit(runner.run(context))
