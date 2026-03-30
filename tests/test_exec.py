# Copyright 2026 Canonical Ltd.
# SPDX-License-Identifier: GPL-3.0-only

import json
import os
import pytest
import subprocess


def get_testdata_dir() -> str:
    return os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "testdata",
    )


def get_ubuntu_lint_bin() -> str:
    return os.path.join(get_testdata_dir(), "../../ubuntu-lint")


def get_defined_testcases() -> list[str]:
    testcases = os.listdir(get_testdata_dir())

    try:
        testcases.remove("baseline")
    except ValueError:
        pass

    return testcases


def get_defined_testcases_with_data() -> list[tuple[str, str, str]]:
    testcases_with_data: list[tuple[str, str, str]] = []

    for name in get_defined_testcases():
        testdir = os.path.join(get_testdata_dir(), name)

        changes = os.path.join(testdir, "changes")
        if not os.path.exists(changes):
            changes = ""

        changelog = os.path.join(testdir, "changelog")
        if not os.path.exists(changelog):
            changelog = ""

        testcases_with_data.append((name, changes, changelog))

    return testcases_with_data


@pytest.mark.parametrize("name", get_defined_testcases())
def test_exec_cli(name: str):
    changes = os.path.join(get_testdata_dir(), "baseline/changes")
    changelog = os.path.join(get_testdata_dir(), "baseline/changelog")

    cmd = [
        get_ubuntu_lint_bin(),
        "--json",
        "--all=off",
        f"--{name}=fail",
        f"--changes-file={changes}",
        f"--debian-changelog={changelog}",
    ]

    r = subprocess.run(cmd, capture_output=True)
    assert r.returncode == 0

    out = json.loads(r.stdout.decode())
    assert out[name]["result"] == "OK"


@pytest.mark.parametrize(
    "name, changes, changelog",
    get_defined_testcases_with_data(),
    ids=get_defined_testcases(),
)
def test_exec_cli_expect_fail(name: str, changes: str, changelog: str):
    assert changes or changelog

    cmd = [
        get_ubuntu_lint_bin(),
        "--json",
        "--all=off",
        f"--{name}=fail",
    ]
    if changes:
        cmd.append(f"--changes-file={changes}")

    if changelog:
        cmd.append(f"--debian-changelog={changelog}")

    r = subprocess.run(cmd, capture_output=True)
    assert r.returncode != 0

    out = json.loads(r.stdout.decode())

    assert out[name]["result"] == "FAIL"
