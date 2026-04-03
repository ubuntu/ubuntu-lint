# Copyright 2026 Canonical Ltd.
# SPDX-License-Identifier: GPL-3.0-only

import json
import os
import pytest
import shutil
import subprocess
import tempfile


def get_testdata_dir() -> str:
    return os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "testdata",
    )


def get_top_level_dir() -> str:
    return os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..",
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


def get_defined_testscase_with_changes() -> list[tuple[str, str]]:
    testcases_with_changes = [
        (name, changes)
        for name, changes, _ in get_defined_testcases_with_data()
        if changes
    ]

    return testcases_with_changes


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
        f"--changelog={changelog}",
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
        cmd.append(f"--changelog={changelog}")

    r = subprocess.run(cmd, capture_output=True)
    assert r.returncode != 0

    out = json.loads(r.stdout.decode())

    assert out[name]["result"] == "FAIL"


@pytest.mark.skipif(shutil.which("dput") is None, reason="dput-ng is not installed")
@pytest.mark.parametrize(
    "name", [name for name, _ in get_defined_testscase_with_changes()]
)
def test_dput_hook(name: str):
    changes = os.path.join(get_testdata_dir(), "baseline/changes")

    with tempfile.TemporaryDirectory() as tmpdir:
        dput_hooks_dir = os.path.join(tmpdir, ".dput.d/hooks")
        dput_profiles_dir = os.path.join(tmpdir, ".dput.d/profiles")

        os.makedirs(dput_hooks_dir, exist_ok=True)
        os.makedirs(dput_profiles_dir, exist_ok=True)

        hook = os.path.join(get_top_level_dir(), f"dput.d/hooks/{name}.json")
        shutil.copy2(hook, dput_hooks_dir)

        changes_file = os.path.join(tmpdir, "test.changes")
        shutil.copy2(changes, changes_file)

        with open(os.path.join(dput_profiles_dir, "ubuntu.json"), "w") as f:
            f.write(f'{{"hooks": [ "{name}" ] }}')

        r = subprocess.run(
            [
                "dput",
                "--check-only",  # Perform pre-upload hooks only
                "--unchecked",  # Do not check signature
                "ubuntu",
                changes_file,
            ],
            capture_output=True,
            env={
                "HOME": tmpdir,
                "PYTHONPATH": get_top_level_dir(),
            },
        )
        assert r.returncode == 0
        assert f"running {name}:" in r.stderr.decode()


@pytest.mark.skipif(shutil.which("dput") is None, reason="dput-ng is not installed")
@pytest.mark.parametrize("name, changes", get_defined_testscase_with_changes())
def test_dput_hook_expect_fail(name: str, changes: str):
    with tempfile.TemporaryDirectory() as tmpdir:
        dput_hooks_dir = os.path.join(tmpdir, ".dput.d/hooks")
        dput_profiles_dir = os.path.join(tmpdir, ".dput.d/profiles")

        os.makedirs(dput_hooks_dir, exist_ok=True)
        os.makedirs(dput_profiles_dir, exist_ok=True)

        hook = os.path.join(get_top_level_dir(), f"dput.d/hooks/{name}.json")
        shutil.copy2(hook, dput_hooks_dir)

        changes_file = os.path.join(tmpdir, "test.changes")
        shutil.copy2(changes, changes_file)

        with open(os.path.join(dput_profiles_dir, "ubuntu.json"), "w") as f:
            f.write(f'{{"hooks": [ "{name}" ] }}')

        r = subprocess.run(
            [
                "dput",
                "--check-only",  # Perform pre-upload hooks only
                "--unchecked",  # Do not check signature
                "ubuntu",
                changes_file,
            ],
            capture_output=True,
            env={
                "HOME": tmpdir,
                "PYTHONPATH": get_top_level_dir(),
            },
        )
        assert r.returncode != 0

        out = r.stderr.decode()
        assert f"running {name}:" in out
        assert "ERROR:" in out
