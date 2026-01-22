import argparse
import os
import sys
import ubuntu_lint

from typing import Callable


class Runner:
    all_linters = {
        "distribution-invalid": ubuntu_lint.check_distribution_invalid,
        "missing-bug-references": ubuntu_lint.check_missing_bug_references,
        "missing-git-ubuntu-references": ubuntu_lint.check_missing_git_ubuntu_references,
        "missing-launchpad-bugs-fixed": ubuntu_lint.check_missing_launchpad_bugs_fixed,
        "missing-pending-changelog-entry": ubuntu_lint.check_missing_pending_changelog_entry,
        "missing-ubuntu-maintainer": ubuntu_lint.check_missing_ubuntu_maintainer,
    }

    # Default actions when linting development release.
    auto_devel = {
        "distribution-invalid": "fail",
        "missing-bug-references": "warn",
        "missing-git-ubuntu-references": "warn",
        "missing-launchpad-bugs-fixed": "warn",
        "missing-pending-changelog-entry": "warn",
        "missing-ubuntu-maintainer": "fail",
    }

    # Default actions when linting stable releases.
    auto_stable = {
        "distribution-invalid": "fail",
        "missing-bug-references": "fail",
        "missing-git-ubuntu-references": "warn",
        "missing-launchpad-bugs-fixed": "fail",
        "missing-pending-changelog-entry": "fail",
        "missing-ubuntu-maintainer": "fail",
    }

    def __init__(self):
        self._checks_by_name: dict = self.all_linters
        self._action_by_name: dict = {
            name: "auto" for name in self._checks_by_name.keys()
        }

    def set_linter(
        self,
        name: str,
        fn: Callable[ubuntu_lint.Context, []],
        failure_action: str,
    ) -> None:
        """Configure a linter on the runner."""

        if failure_action == "off":
            try:
                del self._checks_by_name[name]
                del self._action_by_name[name]
            except KeyError:
                pass
            finally:
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

            print(f"Running {name}...", end="")

            try:
                fn(context)
                print("OK")
            except ubuntu_lint.LintFailure as e:
                print(f"[{failure_action}] {name}: {e}")

                if failure_action == "fail" and ret <= 0:
                    ret = 1
            except RuntimeError as e:
                print(f"[error] {name}: {e}")
                ret = 2

        return ret


class ActionConfigureLinter(argparse.Action):
    def __call__(
        self,
        parser,
        namespace,
        values,
        option_string,
    ):
        # '--linter-name' -> 'linter-name'
        name = option_string.lstrip("-")
        namespace.set_linter(name, namespace.all_linters[name], values)


def main():
    parser = argparse.ArgumentParser(
        prog="ubuntu-lint",
        description="Lint checker for Ubuntu package uploads",
    )

    context_args = parser.add_argument_group(
        "context options",
        "Control package context for linters",
    )

    context_args.add_argument(
        "--source-dir",
        help="Path to debian source package",
        type=str,
        default=".",
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

    if runner.debian_changelog is None:
        runner.debian_changelog = os.path.join(runner.source_dir, "debian/changelog")

    context = ubuntu_lint.Context(
        debian_changelog=runner.debian_changelog,
        changes=runner.changes_file,
    )

    if not runner.run(context):
        sys.exit(1)


if __name__ == "__main__":
    main()
