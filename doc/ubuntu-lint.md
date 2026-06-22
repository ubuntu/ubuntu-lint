---
title: ubuntu-lint
subtitle: "packaging linter for Ubuntu uploads"
section: 1
date: 2026-06-22
author: Canonical Ltd.
---

# NAME

ubuntu-lint — packaging linter for Ubuntu uploads

# SYNOPSIS

`ubuntu-lint [--help] [--verbose] [--json] [--source-dir DIR] [--changelog FILE] [--changes-file FILE] [--all=(auto|off|warn|fail)] [--<linter>=(auto|off|warn|fail)]...`

# DESCRIPTION

ubuntu-lint is a packaging linter focused on Ubuntu-specific policies and conventions. It inspects Debian source package directories, changelogs, and .changes files and runs modular lint checks.

If run with no explicit context flags and a `debian/` directory is present, ubuntu-lint will infer context from the changelog and the most recent .changes file. Context may be provided explicitly using the context options below.

Most lint checks have an associated `dput-ng` hook defined for easy linting at upload time.

# OPTIONS

`--help, -h`
: Show help and exit.

`--verbose`
: Enable verbose output.

`--json`
: Print results as JSON.

# CONTEXT OPTIONS

`--source-dir DIR`
: Path to Debian source package directory to use as context.

`--changelog FILE`
: Path to `debian/changelog` to use as context.

`--changes-file FILE`
: Path to a source .changes file to use as context.

# LINTER OPTIONS

Each lint has a corresponding flag `--<linter-name>=` which accepts one of: `auto`, `off`, `warn`, `fail`.

- auto — use the lint's default behavior depending on whether the target is a development or stable release.
- warn — treat detected issues as warnings.
- fail — treat detected issues as failures.
- off — disable the check.

`--all=` sets the default level for all linters. Any linter-specific flags that come after take precedence.

# AVAILABLE LINTERS

## distribution-invalid
Detects invalid or unsupported distribution field, such as incorrect distribution names.

## missing-bug-references
Detects when the upload is missing Launchpad bug references in the changelog.

## missing-launchpad-bugs-fixed
Detects when the upload is missing Launchpad bug references (i.e. the `Launchpad-Bugs-Fixed` field) in the .changes file.

## missing-git-ubuntu-references
Detects when changes file is missing `git-ubuntu` metadata (i.e. the `Vcs-Git`, `Vcs-Git-Commit`, `Vcs-Git-Ref` fields).

## git-ubuntu-references-mismatch
Checks that if present, the `git-ubuntu` metadata in the changes file is consistent with the remote.

## missing-pending-changelog-entry
Detects when an upload's changelog is missing the entry of a pending change, for example an upload that is still in `-proposed`.

## missing-ubuntu-maintainer
Detects when the changes file has not set the `Maintainer` field to `Ubuntu Developers <ubuntu-devel-discuss@lists.ubuntu.com>`.

## sru-bug-missing-template
For SRU uploads, checks if the associated bugs have filled out the SRU template.

## sru-bug-missing-release-tasks
For SRU uploads, checks if the associated bugs have the correct release tasks set.

## sru-version-string-breaks-upgrades
For SRU uploads, checks if the version string could break upgrade paths.

## sru-version-string-convention
For SRU uploads, checks if the version string follows Ubuntu and SRU conventions.

## release-mismatch
Attempts to detect inconsistencies in the version string and series name, e.g. `1.2.3-0ubuntu1~22.04.1` and `noble` (because the `~22.04.1` looks like it is meant for Ubuntu 22.04 LTS "Jammy Jellyfish", and `noble` refers to Ubuntu 24.04 LTS "Noble Numbat").

See `ubuntu-lint --help` for the complete list.

# DPUT-NG HOOKS

Most lint checks have an associated `dput-ng` hook which is shipped in `/etc/dput.d/hooks/<linter>.json`. If installed alongside `dpug-ng`, these hooks will be invoked with `dput-ng`'s context at upload time.

# EXAMPLES

Run in current directory (auto-detect context):

$ ubuntu-lint

Run against an explicit source directory:

$ ubuntu-lint --source-dir=/path/to/src

Disable a specific linter:

$ ubuntu-lint --missing-git-ubuntu-references=off

Force all checks to be warnings:

$ ubuntu-lint --all=warn

# AUTHOR

Canonical Ltd. — see project files for contributors.

# BUGS

Report issues to the project's issue tracker: https://github.com/ubuntu/ubuntu-lint/issues.

