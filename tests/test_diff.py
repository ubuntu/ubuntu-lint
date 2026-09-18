# Copyright 2026 Canonical Ltd.
# SPDX-License-Identifier: GPL-3.0-only

"""
Tests for debian/source/format 1.0 support, i.e. packages that ship their
Debian packaging as a ".diff.gz" instead of a ".debian.tar.xz" (or similar).
"""

import gzip
import pytest
import ubuntu_lint

from debian import deb822
from ubuntu_lint.dput import call_lint_as_hook

CHANGELOG_TEXT = (
    "hello (1.0-1) unstable; urgency=low\n"
    "\n"
    "  * Initial release.\n"
    "\n"
    " -- Test Maintainer <test@example.com>  "
    "Mon, 01 Jan 2024 00:00:00 +0000\n"
)


class FakeChanges:
    """A minimal stand-in for dput.changes.Changes."""

    def __init__(self, raw_changes, files):
        self._raw_changes = raw_changes
        self._files = files

    def get_raw_changes(self):
        return self._raw_changes

    def get_files(self):
        return self._files


def make_diff_gz(tmp_path, name, changelog_text, wholly_new=True):
    lines = changelog_text.splitlines()

    diff = "--- old/debian/changelog\n"
    diff += "+++ new/debian/changelog\n"
    diff += f"@@ -0,0 +1,{len(lines)} @@\n"
    if wholly_new:
        diff += "".join(f"+{line}\n" for line in lines)
    else:
        # Simulate a diff that isn't a wholly new file, e.g. it has
        # context/removed lines, which is not something we support
        # reconstructing without access to the original file.
        diff += " " + lines[0] + "\n"
        diff += "".join(f"+{line}\n" for line in lines[1:])

    path = tmp_path / name
    with gzip.open(path, "wt") as f:
        f.write(diff)

    return path


def test_context_with_diff_gz_debian_tar(tmp_path):
    diff_gz = make_diff_gz(tmp_path, "hello_1.0-1.diff.gz", CHANGELOG_TEXT)

    context = ubuntu_lint.Context(debian_tar=diff_gz)

    assert context.debian_tar == diff_gz
    assert context.changelog_entry.package == "hello"
    assert str(context.changelog_entry.version) == "1.0-1"


def test_context_with_diff_gz_not_wholly_new_file(tmp_path):
    diff_gz = make_diff_gz(
        tmp_path, "hello_1.0-1.diff.gz", CHANGELOG_TEXT, wholly_new=False
    )

    with pytest.raises(ValueError):
        ubuntu_lint.Context(debian_tar=diff_gz)


def test_context_with_diff_gz_missing_changelog(tmp_path):
    path = tmp_path / "hello_1.0-1.diff.gz"
    with gzip.open(path, "wt") as f:
        f.write("--- old/debian/control\n+++ new/debian/control\n@@ -0,0 +1 @@\n+x\n")

    with pytest.raises(ValueError):
        ubuntu_lint.Context(debian_tar=path)


def test_call_lint_as_hook_finds_diff_gz_as_tarball(tmp_path):
    """
    debian/source/format 1.0 packages ship a .diff.gz instead of a
    .debian.tar.xz (or similar); make sure call_lint_as_hook can still
    locate and use it.
    """
    diff_gz = make_diff_gz(tmp_path, "hello_1.0-1.diff.gz", CHANGELOG_TEXT)
    orig = tmp_path / "hello_1.0.orig.tar.gz"
    orig.write_bytes(b"")

    raw_changes = deb822.Changes("Source: hello\nVersion: 1.0-1\n")
    changes = FakeChanges(raw_changes, [str(orig), str(diff_gz)])

    seen = {}

    def lint(context):
        seen["context"] = context

    call_lint_as_hook(lint, changes, {}, None)

    assert seen["context"].debian_tar == diff_gz
    assert seen["context"].changelog_entry.package == "hello"
