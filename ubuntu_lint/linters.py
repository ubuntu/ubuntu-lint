# Copyright 2026 Canonical Ltd.
# SPDX-License-Identifier: GPL-3.0-only

import distro_info
import re
import requests

from debian import changelog, debian_support
from ubuntu_lint import Context


def check_missing_ubuntu_maintainer(context: Context):
    """
    Check if the changes file has appropriately updated the Maintainer field to
    Ubuntu Developers <ubuntu-devel-discuss@lists.ubuntu.com>.
    """
    ubuntu_devel = "Ubuntu Developers <ubuntu-devel-discuss@lists.ubuntu.com>"

    if "ubuntu" not in str(context.get_package_version()):
        return

    if context.changes.get_as_string("Maintainer") != ubuntu_devel:
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
    dist = context.get_series()
    if not distro_info.UbuntuDistroInfo().valid(dist):
        context.lint_fail(f'"{dist}" is not a valid Ubuntu codename')


def check_missing_git_ubuntu_references(context: Context):
    """
    Check that the changes file contains the necessary Vcs headers
    for a git-ubuntu upload.
    """
    missing = []
    if not context.changes.get("Vcs-Git"):
        missing.append("Vcs-Git")
    if not context.changes.get("Vcs-Git-Commit"):
        missing.append("Vcs-Git-Commit")
    if not context.changes.get("Vcs-Git-Ref"):
        missing.append("Vcs-Git-Ref")

    if missing:
        context.lint_fail("changes file is missing {}".format(", ".join(missing)))


def check_git_ubuntu_references_mismatch(context: Context):
    """
    Check that the git-ubuntu Vcs headers, if present, match the remote.
    In particur, check that:

     - Vcs-Git is a valid URL pointing to a git-ubuntu repository
     - Vcs-Git-Commit is a valid object in that repository
     - Vcs-Git-Ref is a reference to the object given in Vcs-Git-Commit
    """
    if not (vcs_git := context.changes.get("Vcs-Git")):
        context.lint_skip("changes file does not have Vcs-Git")
    if not (vcs_git_commit := context.changes.get("Vcs-Git-Commit")):
        context.lint_skip("changes file does not have Vcs-Git-Commit")
    if not (vcs_git_ref := context.changes.get("Vcs-Git-Ref")):
        context.lint_skip("changes file does not have Vcs-Git-Ref")

    url = f"{vcs_git}/patch/?h={vcs_git_ref}"
    r = requests.get(url)
    if not r.ok:
        if r.status_code == 404:
            context.lint_error(f"{url} does not exist")

        elif r.status_code == 503:
            context.lint_skip("Launchpad git web is unavailable")

        else:
            context.lint_warn(f"failed to check {url} (status_code={r.status_code})")

    if not r.text.startswith(f"From {vcs_git_commit} "):
        context.lint_fail("Vcs-Git fields in changes file do not match the remote")


def check_missing_pending_changelog_entry(context: Context):
    """
    Checks if the changes file is missing pending changelog entries,
    i.e. entries for uploads which are still in -proposed. This is a warning
    for the development release, and an error for stable releases.
    """
    if context.is_unreleased():
        context.lint_skip("changelog is still UNRELEASED")

    dist = context.get_series()
    package = context.get_source_package_name()

    # Mangle the Changes field so that we can parse it like a changelog.
    s = context.changes.get_as_string("Changes")
    s = s.replace(f"\n .\n {package}", f"\n  --\n {package}")
    s = s + "\n  --\n"
    lines = ["" if v == " ." else v[1:] for v in s.splitlines()]

    ch = changelog.Changelog(lines, allow_empty_author=True)
    changes_versions = set([str(v) for v in ch.get_versions()])

    # Check Launchpad for pending package versions in -proposed.
    lp_ubuntu = context.lp.distributions["ubuntu"]
    series = lp_ubuntu.getSeries(name_or_version=dist)
    published = lp_ubuntu.main_archive.getPublishedSources(
        source_name=package, distro_series=series, exact_match=True
    )

    pending_versions = set()
    for v in published:
        # The published versions are sorted newest to oldest. Once we encounter
        # something that is not in -proposed, it was published somewhere that is not
        # "pending", so stop looking.
        if v.pocket != "Proposed":
            break

        # Conventionally, we would not expect someone to include the Debian changelog
        # entry, e.g. for an ubuntu1 upload fixing a sync that is stuck in -proposed.
        if "ubuntu" not in v.source_package_version:
            continue

        pending_versions.add(v.source_package_version)

    if not pending_versions:
        # There is not anything in -proposed, nothing more to do.
        return

    if not pending_versions <= changes_versions:
        # The versions listed in the changes file is not a superset
        # of the pending versions according to Launchpad.
        missing_versions = ",".join(pending_versions - changes_versions)

        context.lint_fail(
            "the following versions have been published in proposed "
            "but have not migrated, and are not included in the "
            "changes file: " + missing_versions
        )


def check_sru_bug_missing_template(context: Context):
    """
    For uploads to stable releases, checks that bugs referenced in the changes
    file have added an SRU template, and warns if it appears the template is
    incomplete.
    """
    if not context.is_stable_release():
        context.lint_skip("this check applies to SRUs only")

    bugs = context.changes.get("Launchpad-Bugs-Fixed", "").split()

    if not bugs:
        context.lint_fail("no bug references found, cannot check for SRU template")

    for n in bugs:
        try:
            bug = context.lp.bugs[n]
            desc = bug.description
        except KeyError:
            context.lint_fail(f"bug {n} does not exist or is not public")

        for section in ("impact", "test plan", "where problems could occur"):
            if not re.search(rf"\[\s*{section}\s*\]", desc.lower()):
                context.lint_fail(
                    f"bug {n} description is missing the [{section.title()}] section"
                    ", see: https://documentation.ubuntu.com/project/SRU/"
                    "reference/bug-template/#reference-sru-bug-template"
                )


def check_sru_bug_missing_release_tasks(context: Context):
    """
    For uploads to stable releases, checks if the referenced bugs are
    missing a task for the appropriate release, and warns if not.
    """
    if not context.is_stable_release():
        context.lint_skip("this check applies to SRUs only")

    if context.is_unreleased():
        context.lint_skip("changelog is still UNRELEASED")

    bugs = context.changes.get("Launchpad-Bugs-Fixed", "").split()

    if not bugs:
        context.lint_fail("no bug references found, cannot check for SRU template")

    dist = context.get_series()
    lp_ubuntu = context.lp.distributions["ubuntu"]
    series = lp_ubuntu.getSeries(name_or_version=dist)
    series_url = str(series)

    warn = []
    for n in bugs:
        try:
            bug = context.lp.bugs[n]
        except KeyError:
            context.lint_fail(f"bug {n} does not exist or is not public")

        for task in bug.bug_tasks:
            if str(task).startswith(series_url):
                break
        else:
            warn.append(f"LP: #{n}")

    if warn:
        context.lint_fail(
            "{} {} missing a bug task for {}".format(
                ", ".join(warn), "is" if len(warn) == 1 else "are", dist
            )
        )


def _rmadision_get_max_version_by_series(context: Context) -> dict[str, str]:
    """
    Construct a map of series -> highest version (excluding -backports). This can then
    be used to compare the target version against all newer releases, to ensure it
    sorts before them.
    """
    package = context.get_source_package_name()

    url = f"https://people.canonical.com/~ubuntu-archive/madison.cgi?package={package}&a=source&text=on"

    r = requests.get(url)
    if not r.ok:
        if r.status_code == 404:
            context.lint_error(f"{url} does not exist")
        else:
            context.lint_error(f"failed to check {url} (status_code={r.status_code})")

    max_version_by_series: dict[str, str] = {}
    for line in r.text.splitlines():
        # An rmadision line is formatted like:
        # <source_package> | <version> | <suite> | source
        values = [c.strip() for c in line.split("|")]

        if len(values) < 4:
            context.lint_error(f"Unexpected line from rmadison: {line}")

        version = values[1]
        suite = values[2]
        series, _, pocket = suite.partition("-")

        if pocket == "backports":
            # Exclude -backports, as different rules apply.
            continue

        try:
            if (
                debian_support.version_compare(version, max_version_by_series[series])
                > 0
            ):
                max_version_by_series[series] = version
        except KeyError:
            max_version_by_series[series] = version

    return max_version_by_series


def check_sru_version_string_breaks_upgrades(context: Context):
    """
    Examines the package version string, and the package version string in all
    series (from the target series through the development series), to ensure
    the ordering is correct.
    """
    if context.is_unreleased():
        context.lint_skip("changelog is still UNRELEASED")

    max_version_by_series = _rmadision_get_max_version_by_series(context)

    target_version = context.get_package_version()
    target_series = context.get_series()

    if target_series not in max_version_by_series.keys():
        context.lint_fail(f"{target_series} is not know by rmadison")

    try:
        compare_series = [
            d
            for d in distro_info.UbuntuDistroInfo().get_all()
            if d in max_version_by_series
        ]
        index = compare_series.index(target_series)
    except ValueError:
        context.lint_error(f"{target_series} is not known by distro-info")

    for s in compare_series[index + 1 :]:
        v = max_version_by_series[s]
        if debian_support.version_compare(target_version, v) > 0:
            context.lint_fail(
                f"{target_version} for {target_series} is greater than {v} for {s}, "
                "which breaks the upgrade path"
            )


def check_sru_version_string_convention(context: Context):
    """
    Examines the package version string to determine if it is appropriate for SRU.
    """
    docs = "https://documentation.ubuntu.com/project/how-ubuntu-is-made/concepts/version-strings"

    if context.is_unreleased():
        context.lint_skip("changelog is still UNRELEASED")

    next_version = context.get_package_version()
    prev_version = context.changelog_entry_by_index(1).version

    match = re.search(r"-[0-9]*", prev_version.full_version)
    if match:
        upstream_version, debian_revison, ubuntu_revision = str(prev_version).partition(
            match.group()
        )
    else:
        context.lint_skip(
            "check not implemented for native packages, "
            f"please check {docs} to ensure version string is correct"
        )

    series_version = distro_info.UbuntuDistroInfo().version(context.get_series())
    # Strip off " LTS" if needed.
    series_version = series_version.partition(" ")[0]

    if (
        debian_support.version_compare(
            next_version.upstream_version, prev_version.upstream_version
        )
        > 0
    ):
        # Handle new upstream version separately from the rest. This check could be
        # expanded in the future to cover more cases, but at the very least, the new
        # version should end in e.g. 24.04.1.
        if not str(next_version).endswith(f"{series_version}.1"):
            context.lint_fail(
                f"version string for new upstream should contain suffix {series_version}.1"
            )
        return

    # If the previous version is published across multiple series, then we expect e.g.
    # ubuntu24.04.x suffixes.
    max_version_by_series = _rmadision_get_max_version_by_series(context)
    series_with_version = list(max_version_by_series.values()).count(prev_version)

    suffix_extra: str = ""
    if series_with_version > 1:
        suffix_extra = f".{series_version}"

    expect: str = ""
    if not ubuntu_revision:
        # E.g. 2.0-1 -> 2.0-1ubuntu0.1
        expect = f"{upstream_version}{debian_revison}ubuntu0{suffix_extra}.1"
    elif "ubuntu" not in ubuntu_revision:
        # E.g. 2.0-1build1 -> 2.0-1ubuntu0.1
        expect = f"{upstream_version}{debian_revison}ubuntu0{suffix_extra}.1"
    elif "." not in ubuntu_revision:
        # E.g. 2.0-1ubuntu1 -> 2.0-1ubuntu1.1
        expect = f"{str(prev_version)}{suffix_extra}.1"
    elif suffix_extra:
        # All other cases where there multiple series with the same version.
        expect = f"{str(prev_version)}{suffix_extra}.1"
    else:
        # E.g. 2.0-1ubuntu1.1 -> 2.0-1ubuntu1.2
        try:
            parts = ubuntu_revision.split(".")
            parts[-1] = str(int(parts[-1]) + 1)
            new_ubuntu_revision = ".".join(parts)

            expect = f"{upstream_version}{debian_revison}{new_ubuntu_revision}"
        except ValueError:
            context.lint_error(f"cannot handle version string format {prev_version}")

    if str(next_version) != expect:
        context.lint_fail(
            f"{next_version} does not match expected version {expect}, "
            f"see {docs} for expected version string conventions"
        )
