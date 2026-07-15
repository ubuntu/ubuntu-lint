# Copyright 2026 Canonical Ltd.
# SPDX-License-Identifier: GPL-3.0-only

import glob
import json
import os
import pytest
import shutil
import subprocess
import tempfile


def get_cli_testdata_dir() -> str:
    return os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "testdata/cli",
    )


def get_dput_testdata_dir() -> str:
    return os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "testdata/dput",
    )


def get_top_level_dir() -> str:
    return os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..",
    )


def get_ubuntu_lint_bin() -> str:
    if os.getenv("TEST_AUTOPKGTEST") == "1":
        return "/usr/bin/ubuntu-lint"

    return os.path.join(get_top_level_dir(), "ubuntu-lint")


def get_dput_dir() -> str:
    if os.getenv("TEST_AUTOPKGTEST") == "1":
        return "/etc/dput.d"

    return os.path.join(get_top_level_dir(), "dput.d")


def get_defined_cli_testcases() -> list[str]:
    testcases = os.listdir(get_cli_testdata_dir())

    try:
        testcases.remove("baseline")
    except ValueError:
        pass

    return testcases


def get_cli_testcases() -> list[tuple[str, str, str]]:
    testcases_with_data: list[tuple[str, str, str]] = []

    for name in get_defined_cli_testcases():
        testdir = os.path.join(get_cli_testdata_dir(), name)

        changes = os.path.join(testdir, "changes")
        if not os.path.exists(changes):
            changes = ""

        changelog = os.path.join(testdir, "changelog")
        if not os.path.exists(changelog):
            changelog = ""

        testcases_with_data.append((name, changes, changelog))

    return testcases_with_data


def get_dput_testcases() -> list[str]:
    testcases = os.listdir(get_dput_testdata_dir())

    try:
        testcases.remove("baseline")
    except ValueError:
        pass

    return testcases


@pytest.mark.parametrize("name", get_defined_cli_testcases())
def test_exec_cli(name: str):
    changes = os.path.join(get_cli_testdata_dir(), f"baseline/{name}.changes")
    if not os.path.exists(changes):
        changes = os.path.join(get_cli_testdata_dir(), "baseline/changes")

    changelog = os.path.join(get_cli_testdata_dir(), f"baseline/{name}.changelog")
    if not os.path.exists(changelog):
        changelog = os.path.join(get_cli_testdata_dir(), "baseline/changelog")

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
    get_cli_testcases(),
    ids=get_defined_cli_testcases(),
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


def run_dput_hook_with_tmpdir(name: str, changes: str) -> subprocess.CompletedProcess:
    with tempfile.TemporaryDirectory() as tmpdir:
        # Copy the hook under test to the temporary .dput.d
        dput_hooks_dir = os.path.join(tmpdir, ".dput.d/hooks")
        os.makedirs(dput_hooks_dir, exist_ok=True)
        hook = os.path.join(get_dput_dir(), f"hooks/{name}.json")
        shutil.copy2(hook, dput_hooks_dir)

        # Create the temporary ubuntu.json profile
        dput_profile = os.path.join(tmpdir, ".dput.d/profiles/ubuntu.json")
        os.makedirs(os.path.dirname(dput_profile), exist_ok=True)
        with open(dput_profile, "w") as f:
            f.write(f'{{"hooks": [ "{name}" ] }}')

        # Prepare environment for dput-ng
        dput_env = os.environ.copy()
        dput_env["HOME"] = tmpdir

        if os.getenv("TEST_AUTOPKGTEST") != "1":
            dput_env["PYTHONPATH"] = get_top_level_dir()

        return subprocess.run(
            [
                "dput",
                "--check-only",  # Perform pre-upload hooks only
                "--unchecked",  # Do not check signature
                "ubuntu",
                changes,
            ],
            capture_output=True,
            env=dput_env,
        )


@pytest.mark.skipif(shutil.which("dput") is None, reason="dput-ng is not installed")
@pytest.mark.parametrize("name", get_dput_testcases())
def test_dput_hook(name: str):
    r = run_dput_hook_with_tmpdir(
        name,
        os.path.join(
            get_dput_testdata_dir(), "baseline/hello_2.12.3-1ubuntu1_source.changes"
        ),
    )

    out = r.stderr.decode()
    if r.returncode != 0:
        pytest.fail(f"running {name} hook failed: {out}")

    assert f"running {name}:" in out


@pytest.mark.skipif(shutil.which("dput") is None, reason="dput-ng is not installed")
@pytest.mark.parametrize("name", get_dput_testcases())
def test_dput_hook_expect_fail(name: str):
    matches = glob.glob(f"{get_dput_testdata_dir()}/{name}/*.changes")
    assert len(matches) == 1

    r = run_dput_hook_with_tmpdir(name, matches[0])

    assert r.returncode != 0

    out = r.stderr.decode()
    assert f"running {name}:" in out
    assert "ERROR:" in out
