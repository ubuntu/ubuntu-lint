# Copyright 2026 Canonical Ltd.
# SPDX-License-Identifier: GPL-3.0-only

import copy
import pytest
import ubuntu_lint
import re
import textwrap

from debian import deb822, changelog

basic_changes_no_ubuntu_delta = deb822.Changes("""
Format: 1.8
Date: Wed, 16 Apr 2025 11:50:00 +0200
Source: hello
Built-For-Profiles: noudeb
Architecture: source
Version: 2.10-5
Distribution: unstable
Urgency: medium
Maintainer: John Doe <john.doe@example.com>
Changed-By: John Doe <john.doe@example.com>
Closes: 1103293
Changes:
 hello (2.10-5) unstable; urgency=medium
 .
   * Testing
Checksums-Sha1:
 e8a7a0d2e631c572c507ffd4ee475863ffec39d4 1198 hello_2.10-5.dsc
 36142446c0da8522c7c354ada53ea920d45621a5 13092 hello_2.10-5.debian.tar.xz
 5b335e8f8604d0e44cf2ac7955203af1169a3f16 5943 hello_2.10-5_source.buildinfo
Checksums-Sha256:
 b30084f91b8ec6259bad06da8a071801baa209b6ee72d1f69d1f270f92e953c7 1198 hello_2.10-5.dsc
 b6ace4322d10d434c7515c5d80511f7583ddf04a7c8dda87f7f5f50a490f7182 13092 hello_2.10-5.debian.tar.xz
 98ffbea3cf19ef26ae1c4d4e7418606d46eaee3226639fc58dfdcc4b1e4e4ab4 5943 hello_2.10-5_source.buildinfo
Files:
 121de8e534b189a3e3ddcc584557e29b 1198 devel optional hello_2.10-5.dsc
 d80440ea5a0018680cedcff7160df211 13092 devel optional hello_2.10-5.debian.tar.xz
 c16ad903c1291cb24da33abd6a782419 5943 devel optional hello_2.10-5_source.buildinfo
""")

basic_changelog_no_ubuntu_delta = changelog.Changelog(file="""
hello (2.10-5) unstable; urgency=medium

  * Testing

 -- John Doe <john.doe@example.com>  Mon, 26 Jan 2026 15:13:02 -0500
""")

basic_changes_ubuntu_delta = deb822.Changes("""
Format: 1.8
Date: Mon, 26 Jan 2026 15:13:02 -0500
Source: hello
Built-For-Profiles: noudeb
Architecture: source
Version: 2.10-5ubuntu1
Distribution: resolute
Urgency: medium
Maintainer: Ubuntu Developers <ubuntu-devel-discuss@lists.ubuntu.com>
Changed-By: John Doe <john.doe@example.com>
Launchpad-Bugs-Fixed: 12345678
Changes:
 hello (2.10-5ubuntu1) resolute; urgency=medium
 .
   * Testing (LP: #12345678)
Checksums-Sha1:
 4e2e0717e96715704d311a89b7b7b7e4677b3726 1305 hello_2.10-5ubuntu1.dsc
 7328d4a18da70228074e05e21109dd998f61a539 13228 hello_2.10-5ubuntu1.debian.tar.xz
 1bce5b30cd93da2aa711705ae8354506aeaff759 5971 hello_2.10-5ubuntu1_source.buildinfo
Checksums-Sha256:
 c1eabb9f56c1bcb7f736a51641ae6d0cd2bc33364d0664303178e77152d33a86 1305 hello_2.10-5ubuntu1.dsc
 8136bb2298cd2ab40a333ed58848ccff067315dd872e59056177e55a5727c460 13228 hello_2.10-5ubuntu1.debian.tar.xz
 944f72673ac9b04d7fecd3c317bbdd66551df8eb20a74faa79a104f590926b45 5971 hello_2.10-5ubuntu1_source.buildinfo
Files:
 f6ae5ebd0add2f6510e985d591100c3b 1305 devel optional hello_2.10-5ubuntu1.dsc
 a12ce1144993b3e0910b552dbb7b5ab6 13228 devel optional hello_2.10-5ubuntu1.debian.tar.xz
 c7d4f3688fa4fde9388a5a2fef0065e6 5971 devel optional hello_2.10-5ubuntu1_source.buildinfo
Original-Maintainer: Santiago Vila <sanvila@debian.org>
Vcs-Git: https://git.launchpad.net/~ubuntu-core-dev/ubuntu/+source/hello
Vcs-Git-Commit: 6e591bb3a2bbc44dcb6f49499dc7dbee400ce5b9
Vcs-Git-Ref: refs/heads/testing
""")

basic_changelog_ubuntu_delta = changelog.Changelog(file="""
hello (2.10-5ubuntu1) resolute; urgency=medium

  * Testing (LP: #12345678)

 -- John Doe <john.doe@example.com>  Tue, 27 Jan 2026 15:13:02 -0500

hello (2.10-5) unstable; urgency=medium

  * Testing

 -- John Doe <john.doe@example.com>  Mon, 26 Jan 2026 15:13:02 -0500
""")

basic_changes_ubuntu_extra_changelog = deb822.Changes("""
Format: 1.8
Date: Mon, 26 Jan 2026 15:13:02 -0500
Source: hello
Built-For-Profiles: noudeb
Architecture: source
Version: 2.10-5ubuntu2
Distribution: resolute
Urgency: medium
Maintainer: Ubuntu Developers <ubuntu-devel-discuss@lists.ubuntu.com>
Changed-By: John Doe <john.doe@example.com>
Launchpad-Bugs-Fixed: 12345678
Changes:
 hello (2.10-5ubuntu2) resolute; urgency=medium
 .
   * Fix mistake in previous upload
 .
 hello (2.10-5ubuntu1) resolute; urgency=medium
 .
   * Fix a bug (LP: #12345678)
Checksums-Sha1:
 4e2e0717e96715704d311a89b7b7b7e4677b3726 1305 hello_2.10-5ubuntu1.dsc
 7328d4a18da70228074e05e21109dd998f61a539 13228 hello_2.10-5ubuntu1.debian.tar.xz
 1bce5b30cd93da2aa711705ae8354506aeaff759 5971 hello_2.10-5ubuntu1_source.buildinfo
Checksums-Sha256:
 c1eabb9f56c1bcb7f736a51641ae6d0cd2bc33364d0664303178e77152d33a86 1305 hello_2.10-5ubuntu1.dsc
 8136bb2298cd2ab40a333ed58848ccff067315dd872e59056177e55a5727c460 13228 hello_2.10-5ubuntu1.debian.tar.xz
 944f72673ac9b04d7fecd3c317bbdd66551df8eb20a74faa79a104f590926b45 5971 hello_2.10-5ubuntu1_source.buildinfo
Files:
 f6ae5ebd0add2f6510e985d591100c3b 1305 devel optional hello_2.10-5ubuntu1.dsc
 a12ce1144993b3e0910b552dbb7b5ab6 13228 devel optional hello_2.10-5ubuntu1.debian.tar.xz
 c7d4f3688fa4fde9388a5a2fef0065e6 5971 devel optional hello_2.10-5ubuntu1_source.buildinfo
Original-Maintainer: Santiago Vila <sanvila@debian.org>
Vcs-Git: https://git.launchpad.net/~ubuntu-core-dev/ubuntu/+source/hello
Vcs-Git-Commit: 6e591bb3a2bbc44dcb6f49499dc7dbee400ce5b9
Vcs-Git-Ref: refs/heads/testing
""")

basic_changelog_ubuntu_extra_changelog = changelog.Changelog(file="""
hello (2.10-5ubuntu2) resolute; urgency=medium

  * Fix mistake in previous upload

 -- John Doe <john.doe@example.com>  Tue, 27 Jan 2026 18:13:02 -0500

hello (2.10-5ubuntu1) resolute; urgency=medium

  * Testing (LP: #12345678)

 -- John Doe <john.doe@example.com>  Tue, 27 Jan 2026 15:13:02 -0500

hello (2.10-5) unstable; urgency=medium

  * Testing

 -- John Doe <john.doe@example.com>  Mon, 26 Jan 2026 15:13:02 -0500
""")

basic_changes_sru = deb822.Changes("""
Format: 1.8
Date: Wed, 11 Mar 2026 16:01:41 -0400
Source: hello
Built-For-Profiles: noudeb
Architecture: source
Version: 2.10-3ubuntu0.1
Distribution: noble
Urgency: medium
Maintainer: Ubuntu Developers <ubuntu-devel-discuss@lists.ubuntu.com>
Changed-By: John Doe <john.doe@example.com>
Launchpad-Bugs-Fixed: 12345678
Changes:
 hello (2.10-3ubuntu0.1) noble; urgency=medium
 .
   * Fix a bug (LP: #12345678)
Checksums-Sha1:
 f69ac22584593891440e320777ccb038568c6809 1298 hello_2.10-3ubuntu0.1.dsc
 5eea7226f111d7a874b0b2a7d4586dee3bb9707a 12876 hello_2.10-3ubuntu0.1.debian.tar.xz
 d503db0bad6eb221f1cb96d8fea3d396dc4c2e01 6025 hello_2.10-3ubuntu0.1_source.buildinfo
Checksums-Sha256:
 fe698e4496f18a6575fdbb2bc79bd97289b26d1838da88271f285b9c2a625d84 1298 hello_2.10-3ubuntu0.1.dsc
 37df32119bebf1af5ae8cd793f85a712233b1a5e055d0a517c3a483074255735 12876 hello_2.10-3ubuntu0.1.debian.tar.xz
 03c853b26f1fe5d8ec43831462ceea0d714e0b77f1f253909419f8dc1667c449 6025 hello_2.10-3ubuntu0.1_source.buildinfo
Files:
 1d4d7dc915ed16973febc95ae80d73ed 1298 devel optional hello_2.10-3ubuntu0.1.dsc
 2be6a13bd3827fa7a051fb1b52d37672 12876 devel optional hello_2.10-3ubuntu0.1.debian.tar.xz
 2b095557f297d3f85e85a72363dd1019 6025 devel optional hello_2.10-3ubuntu0.1_source.buildinfo
Original-Maintainer: Santiago Vila <sanvila@debian.org>
""")

basic_changelog_sru = changelog.Changelog(file="""
hello (2.10-3ubuntu0.1) noble; urgency=medium

  * Fix a bug (LP: #12345678)

 -- John Doe <john.doe@example.com>  Tue, 27 Jan 2026 18:13:02 -0500

hello (2.10-3) unstable; urgency=medium

  * Testing

 -- John Doe <john.doe@example.com>  Mon, 26 Jan 2026 15:13:02 -0500
""")

basic_changes_merge = deb822.Changes("""
Format: 1.8
Date: Wed, 11 Mar 2026 16:01:41 -0400
Source: hello
Built-For-Profiles: noudeb
Architecture: source
Version: 2.12-1ubuntu1
Distribution: resolute
Urgency: medium
Maintainer: Ubuntu Developers <ubuntu-devel-discuss@lists.ubuntu.com>
Changed-By: John Doe <john.doe@example.com>
Launchpad-Bugs-Fixed: 12345678
Changes:
 hello (2.12-1ubuntu1) resolute; urgency=medium
 .
   * Merge from Debian unstable (LP: #12345678)
 .
 hello (2.12-1) unstable; urgency=medium
 .
   * New upstream release
 .
 hello (2.11-2) unstable; urgency=medium
 .
   * Fix a bug
 .
 hello (2.11-1) unstable; urgency=medium
 .
   * New upstream release
Checksums-Sha1:
 f69ac22584593891440e320777ccb038568c6809 1298 hello_2.12-1ubuntu1.dsc
 5eea7226f111d7a874b0b2a7d4586dee3bb9707a 12876 hello_2.12-1ubuntu1.debian.tar.xz
 d503db0bad6eb221f1cb96d8fea3d396dc4c2e01 6025 hello_2.12-1ubuntu1_source.buildinfo
Checksums-Sha256:
 fe698e4496f18a6575fdbb2bc79bd97289b26d1838da88271f285b9c2a625d84 1298 hello_2.12-1ubuntu1.dsc
 37df32119bebf1af5ae8cd793f85a712233b1a5e055d0a517c3a483074255735 12876 hello_2.12-1ubuntu1.debian.tar.xz
 03c853b26f1fe5d8ec43831462ceea0d714e0b77f1f253909419f8dc1667c449 6025 hello_2.12-1ubuntu1_source.buildinfo
Files:
 1d4d7dc915ed16973febc95ae80d73ed 1298 devel optional hello_2.12-1ubuntu1.dsc
 2be6a13bd3827fa7a051fb1b52d37672 12876 devel optional hello_2.12-1ubuntu1.debian.tar.xz
 2b095557f297d3f85e85a72363dd1019 6025 devel optional hello_2.12-1ubuntu1_source.buildinfo
Original-Maintainer: Joe Schmoe <joe.schmoe@debian.org>
""")

basic_changelog_merge = changelog.Changelog(file="""
hello (2.12-1ubuntu1) resolute; urgency=medium

  * Merge from Debian unstable (LP: #12345678)

 -- John Doe <john.doe@example.com>  Mon, 26 Jan 2026 15:13:02 -0500

hello (2.12-1) unstable; urgency=medium

  * New upstream release

 -- Joe Schmoe <joe.schmoe@debian.org>  Mon, 19 Jan 2026 15:13:02 -0500

hello (2.11-2) unstable; urgency=medium

  * Fix a bug

 -- Joe Schmoe <joe.schmoe@debian.org>  Mon, 12 Jan 2026 15:13:02 -0500

hello (2.11-1) unstable; urgency=medium

  * New upstream release

 -- Joe Schmoe <joe.schmoe@debian.org>  Mon, 05 Jan 2026 15:13:02 -0500

hello (2.10-2ubuntu2) resolute; urgency=medium

  * Fix a bug (LP: #12345679)

 -- John Doe <john.doe@example.com>  Mon, 26 Jan 2026 15:13:02 -0500
""")


def test_check_missing_ubuntu_maintainer():
    ubuntu_lint.check_missing_ubuntu_maintainer(
        ubuntu_lint.Context(changes=basic_changes_no_ubuntu_delta)
    )
    ubuntu_lint.check_missing_ubuntu_maintainer(
        ubuntu_lint.Context(changes=basic_changes_ubuntu_delta)
    )

    changes_missing_ubuntu_maintainer = copy.deepcopy(basic_changes_ubuntu_delta)
    changes_missing_ubuntu_maintainer["Maintainer"] = "John Doe <john.doe@example.com>"
    with pytest.raises(ubuntu_lint.LintException):
        ubuntu_lint.check_missing_ubuntu_maintainer(
            ubuntu_lint.Context(changes=changes_missing_ubuntu_maintainer)
        )


def test_check_missing_launchpad_bugs_fixed():
    ubuntu_lint.check_missing_launchpad_bugs_fixed(
        ubuntu_lint.Context(changes=basic_changes_ubuntu_delta)
    )

    changes_missing_lp_bugs_fixed = copy.deepcopy(basic_changes_ubuntu_delta)
    del changes_missing_lp_bugs_fixed["Launchpad-Bugs-Fixed"]
    with pytest.raises(ubuntu_lint.LintException):
        ubuntu_lint.check_missing_launchpad_bugs_fixed(
            ubuntu_lint.Context(changes=changes_missing_lp_bugs_fixed)
        )


def test_check_missing_git_ubuntu_references(requests_mock):
    ubuntu_lint.check_missing_git_ubuntu_references(
        ubuntu_lint.Context(changes=basic_changes_ubuntu_delta)
    )

    # Refs missing from changes file completely
    changes_missing_git_ubuntu_refs = copy.deepcopy(basic_changes_ubuntu_delta)
    for field in ("Vcs-Git", "Vcs-Git-Commit", "Vcs-Git-Ref"):
        del changes_missing_git_ubuntu_refs[field]

    with pytest.raises(ubuntu_lint.LintException):
        ubuntu_lint.check_missing_git_ubuntu_references(
            ubuntu_lint.Context(changes=changes_missing_git_ubuntu_refs)
        )


def test_check_git_ubuntu_references_mismatch(requests_mock):
    vcs_git = basic_changes_ubuntu_delta.get("Vcs-Git")
    vcs_git_ref = basic_changes_ubuntu_delta.get("Vcs-Git-Ref")
    vcs_git_commit = basic_changes_ubuntu_delta.get("Vcs-Git-Commit")

    requests_mock.get(
        f"{vcs_git}/patch/?h={vcs_git_ref}",
        text=f"From {vcs_git_commit} Mon Sep 17 00:00:00 2001",
    )
    ubuntu_lint.check_git_ubuntu_references_mismatch(
        ubuntu_lint.Context(changes=basic_changes_ubuntu_delta)
    )

    # Simulate local commit hash != remote commit hash.
    requests_mock.get(
        f"{vcs_git}/patch/?h={vcs_git_ref}",
        status_code=404,
    )
    with pytest.raises(ubuntu_lint.LintException):
        ubuntu_lint.check_git_ubuntu_references_mismatch(
            ubuntu_lint.Context(changes=basic_changes_ubuntu_delta)
        )


def test_check_missing_bug_references():
    dch = changelog.Changelog(file="""
hello (2.10-5ubuntu1) resolute; urgency=medium

  * Testing (LP: #12345678)

 -- John Doe <john.doe@example.com>  Mon, 26 Jan 2026 15:13:02 -0500
""")

    ubuntu_lint.check_missing_bug_references(
        context=ubuntu_lint.Context(debian_changelog=dch)
    )

    dch = changelog.Changelog(file="""
hello (2.10-5ubuntu1) resolute; urgency=medium

  * Testing

 -- John Doe <john.doe@example.com>  Mon, 26 Jan 2026 15:13:02 -0500
""")

    with pytest.raises(ubuntu_lint.LintException):
        ubuntu_lint.check_missing_bug_references(
            context=ubuntu_lint.Context(debian_changelog=dch)
        )


def test_check_distribution_invalid():
    dch = changelog.Changelog(file="""
hello (2.10-5ubuntu1) resolute; urgency=medium

  * Testing (LP: #12345678)

 -- John Doe <john.doe@example.com>  Mon, 26 Jan 2026 15:13:02 -0500
""")

    ubuntu_lint.check_distribution_invalid(
        context=ubuntu_lint.Context(debian_changelog=dch)
    )

    dch = changelog.Changelog(file="""
hello (2.10-5ubuntu1) uffda; urgency=medium

  * Testing (LP: #12345678)

 -- John Doe <john.doe@example.com>  Mon, 26 Jan 2026 15:13:02 -0500
""")

    with pytest.raises(ubuntu_lint.LintException):
        ubuntu_lint.check_distribution_invalid(
            context=ubuntu_lint.Context(debian_changelog=dch)
        )


def test_check_sru_version_string_breaks_upgrades(requests_mock):
    package = basic_changes_sru.get("Source")

    rmadison_tmpls = [
        # Package in main
        textwrap.dedent("""hello | 2.8-4         | trusty          | source
               hello | 2.10-1        | xenial          | source
               hello | 2.10-1build1  | bionic          | source
               hello | 2.10-1build3  | bionic-security | source
               hello | 2.10-1build3  | bionic-updates  | source
               hello | 2.10-2ubuntu2 | focal           | source
               hello | 2.10-2ubuntu4 | jammy           | source
               hello | 2.10-3build1  | noble           | source
               hello | 2.10-5        | questing        | source
               hello | 2.10-5build1  | resolute        | source
        """),
        # Package in universe
        textwrap.dedent("""hello | 2.8-4         | trusty/universe          | source
               hello | 2.10-1        | xenial/universe          | source
               hello | 2.10-1build1  | bionic/universe          | source
               hello | 2.10-1build3  | bionic-security/universe | source
               hello | 2.10-1build3  | bionic-updates/universe  | source
               hello | 2.10-2ubuntu2 | focal/universe           | source
               hello | 2.10-2ubuntu4 | jammy/universe           | source
               hello | 2.10-3build1  | noble/universe           | source
               hello | 2.10-5        | questing/universe        | source
               hello | 2.10-5build1  | resolute/universe        | source
        """),
    ]

    for tmpl in rmadison_tmpls:
        requests_mock.get(
            f"https://people.canonical.com/~ubuntu-archive/madison.cgi?package={package}&a=source&text=on",
            text=tmpl,
        )
        ubuntu_lint.check_sru_version_string_breaks_upgrades(
            ubuntu_lint.Context(changes=basic_changes_sru)
        )

        # Simulate a version bump in noble that is greater than questing.
        changes_bad_version = copy.deepcopy(basic_changes_sru)
        changes_bad_version["Version"] = "2.10-5ubuntu0.1"
        with pytest.raises(ubuntu_lint.LintException):
            ubuntu_lint.check_sru_version_string_breaks_upgrades(
                ubuntu_lint.Context(changes=changes_bad_version)
            )


def test_check_sru_version_string_convention(requests_mock):
    changelog_tmpl = """hello ({next_version}) noble; urgency=medium

  * Fix a bug (LP: #12345678)

 -- John Doe <john.doe@example.com>  Wed, 11 Mar 2026 16:01:41 -0400

hello ({prev_version}) noble; urgency=high

  * No change rebuild for 64-bit time_t and frame pointers.

 -- John Doe <john.doe@example.com>  Mon, 08 Apr 2024 17:58:52 +0200
"""

    rmadison_tmpls = [
        textwrap.dedent("""hello | 2.8-4         | trusty          | source
               hello | 2.10-1        | xenial          | source
               hello | 2.10-1build1  | bionic          | source
               hello | 2.10-1build3  | bionic-security | source
               hello | 2.10-1build3  | bionic-updates  | source
               hello | 2.10-2ubuntu2 | focal           | source
               hello | 2.10-2ubuntu4 | jammy           | source
               hello | {prev_version}| noble           | source
               hello | 2.10-5        | questing        | source
               hello | 2.10-5build1  | resolute        | source
        """),
        # Same version in two releases
        textwrap.dedent("""hello | 2.8-4         | trusty          | source
               hello | 2.10-1        | xenial          | source
               hello | 2.10-1build1  | bionic          | source
               hello | 2.10-1build3  | bionic-security | source
               hello | 2.10-1build3  | bionic-updates  | source
               hello | 2.10-2ubuntu2 | focal           | source
               hello | 2.10-2ubuntu4 | jammy           | source
               hello | {prev_version}| noble           | source
               hello | {prev_version}| questing        | source
               hello | 2.10-5build1  | resolute        | source
        """),
    ]

    # (prev_version, next_version, expect_pass)
    testcases_list = [
        [
            # 2.10-3 -> "2.10-3ubuntu0.1"
            ("2.10-3", "2.10-3ubuntu0.1", True),
            ("2.10-3", "2.10-3ubuntu1", False),
            ("2.10-3", "2.10-4", False),
            # 2.10-3ubuntu0.1 -> "2.10-3ubuntu0.2"
            ("2.10-3ubuntu0.1", "2.10-3ubuntu0.2", True),
            ("2.10-3ubuntu0.1", "2.10-3ubuntu1", False),
            # 2.10-3ubuntu2 -> "2.10-3ubuntu2.1"
            ("2.10-3ubuntu2", "2.10-3ubuntu2.1", True),
            ("2.10-3ubuntu2", "2.10-3ubuntu3", False),
            # 2.10-3ubuntu2.1 -> "2.10-3ubuntu2.2"
            ("2.10-3ubuntu2.1", "2.10-3ubuntu2.2", True),
            ("2.10-3ubuntu2.1", "2.10-3ubuntu3", False),
            # 2.10-3build1 -> 2.10-3ubuntu0.1
            ("2.10-3build1", "2.10-3ubuntu0.1", True),
            ("2.10-3build1", "2.10-3build2", False),
            ("2.10-3build1", "2.10-3ubuntu1", False),
            # 2.10-3ubuntu0.24.04.1 -> 2.10-3ubuntu0.24.04.2
            ("2.10-3ubuntu0.24.04.1", "2.10-3ubuntu0.24.04.2", True),
            ("2.10-3ubuntu0.24.04.1", "2.10-3ubuntu1", False),
        ],
        [
            # 2.10-5 in two releases -> 2.10-5ubuntu0.24.04.1
            ("2.10-5", "2.10-5ubuntu0.24.04.1", True),
            ("2.10-5", "2.10-5ubuntu0.1", False),
            ("2.10-5", "2.10-5ubuntu1", False),
            ("2.10-5", "2.10-6", False),
            # 2.10-5build1 in two releases -> 2.10-5ubuntu0.24.04.1
            ("2.10-5build1", "2.10-5ubuntu0.24.04.1", True),
            ("2.10-5build1", "2.10-5ubuntu0.1", False),
            ("2.10-5build1", "2.10-5ubuntu1", False),
            ("2.10-5build1", "2.10-5build2", False),
            # 2.10-5ubuntu1 in two releases -> 2.10-5ubuntu1.24.04.1
            ("2.10-5ubuntu1", "2.10-5ubuntu1.24.04.1", True),
            ("2.10-5ubuntu1", "2.10-5ubuntu1.1", False),
            ("2.10-5ubuntu1", "2.10-5ubuntu2", False),
            # 2.10-5ubuntu1.1 in two releases -> 2.10-5ubuntu1.1.24.04.1
            ("2.10-5ubuntu1.1", "2.10-5ubuntu1.1.24.04.1", True),
            ("2.10-5ubuntu1.1", "2.10-5ubuntu1.2", False),
            ("2.10-5ubuntu1.1", "2.10-5ubuntu2", False),
        ],
    ]

    for i in range(len(testcases_list)):
        rmadison_tmpl = rmadison_tmpls[i]
        testcases = testcases_list[i]

        for prev_version, next_version, expect_pass in testcases:
            requests_mock.get(
                "https://people.canonical.com/~ubuntu-archive/madison.cgi?package=hello&a=source&text=on",
                text=rmadison_tmpl.format(prev_version=prev_version),
            )
            debian_changelog = changelog.Changelog(
                changelog_tmpl.format(
                    prev_version=prev_version,
                    next_version=next_version,
                )
            )
            context = ubuntu_lint.Context(debian_changelog=debian_changelog)

            if expect_pass:
                ubuntu_lint.check_sru_version_string_convention(context)
            else:
                with pytest.raises(
                    ubuntu_lint.LintException,
                    match=f"{next_version} does not match expected version",
                ):
                    ubuntu_lint.check_sru_version_string_convention(context)

    # Test cases for new upstream version
    testcases = [
        # 2.10-3ubuntu1 -> 2.11-0ubuntu0.24.04.1 (new upstream)
        ("2.10-3ubuntu1", "2.11-0ubuntu0.24.04.1", True),
        ("2.10-3ubuntu1", "2.11-0ubuntu0.1", False),
        # 2.10-3ubuntu1 -> 2.11-0ubuntu0~24.04.1 (new upstream)
        ("2.10-3ubuntu1", "2.11-0ubuntu0~24.04.1", True),
        # 2.10-3ubuntu1 -> 2.11-1ubuntu2~24.04.1 (devel backport)
        ("2.10-3ubuntu1", "2.11-1ubuntu2~24.04.1", True),
        ("2.10-3ubuntu1", "2.11-1ubuntu2", False),
    ]

    for prev_version, next_version, expect_pass in testcases:
        requests_mock.get(
            "https://people.canonical.com/~ubuntu-archive/madison.cgi?package=hello&a=source&text=on",
            text=rmadison_tmpls[0].format(prev_version=prev_version),
        )
        debian_changelog = changelog.Changelog(
            changelog_tmpl.format(
                prev_version=prev_version,
                next_version=next_version,
            )
        )
        context = ubuntu_lint.Context(debian_changelog=debian_changelog)

        if expect_pass:
            ubuntu_lint.check_sru_version_string_convention(context)
        else:
            with pytest.raises(
                ubuntu_lint.LintException,
                match="version string for new upstream should contain suffix",
            ):
                ubuntu_lint.check_sru_version_string_convention(context)


def test_check_release_mismatch():
    changelog_tmpl = """hello ({version}) {distribution}; urgency=medium

  * Fix a bug (LP: #12345678)

 -- John Doe <john.doe@example.com>  Wed, 11 Mar 2026 16:01:41 -0400
 """

    testcases_list = [
        ("2.10-3~24.04.1", "noble", True, "", ""),
        ("2.10-3~24.04.1", "focal", False, "24.04", "20.04"),
        ("2.10-3ubuntu0.24.04.1", "noble", True, "", ""),
        ("2.10-3ubuntu0.24.04.1", "focal", False, "24.04", "20.04"),
        ("2.10-3ubuntu1.1.24.04.1", "noble", True, "", ""),
        ("2.10-3ubuntu1.1.24.04.1", "focal", False, "24.04", "20.04"),
        ("2.11-1ubuntu2~24.04.1", "noble", True, "", ""),
        ("2.11-1ubuntu2~24.04.1", "focal", False, "24.04", "20.04"),
    ]

    for (
        version,
        target_series,
        expect_pass,
        given_version,
        target_version,
    ) in testcases_list:
        debian_changelog = changelog.Changelog(
            changelog_tmpl.format(version=version, distribution=target_series)
        )

        context = ubuntu_lint.Context(debian_changelog=debian_changelog)

        if expect_pass:
            ubuntu_lint.check_release_mismatch(context)
        else:
            with pytest.raises(
                ubuntu_lint.LintException,
                match=f"ubuntu version {version} contains {given_version} which does not match target \\({target_series} {target_version}\\)",
            ):
                ubuntu_lint.check_release_mismatch(context)


@pytest.mark.parametrize(
    "version, expect_pass",
    [
        # Pass
        ("1.2.3-0ubuntu1", True),
        ("1.2.3-0ubuntu1.1", True),
        ("1.2.3-1ubuntu2", True),
        ("1.2.3-1ubuntu2~22.04.1", True),
        ("1.0ubuntu", True),
        ("1.2.3-0build1", True),
        ("1.2.3-1build2", True),
        ("20200505dfsg0-5ubuntu1", True),
        ("2.3+dfsg-1ubuntu2", True),
        ("2.3.7+git20230731.5fc64cde+dfsg-4ubuntu1", True),
        ("2.0ubuntu.build1", True),
        ("1.0build1", True),
        # Fail
        ("1.2.3-1", False),
        ("1.2.3-0ubunut1.1", False),
        ("1.2.3-1ubunt2", False),
        ("1.2.3-1ubuntuu2~22.04.1", False),
        ("1.0", False),
        ("1.2.3-0maysync1", False),
        ("20200505dfsg0-5", False),
        ("2.3.7+git20230731.5fc64cde+dfsg-4", False),
        ("1.0build", False),
        ("1.2-3ubuntu", False),
    ],
)
def test_check_missing_version_suffix(version: str, expect_pass: bool):
    changelog_tmpl = """hello ({version}) resolute; urgency=medium

  * Fix a bug (LP: #12345678)

 -- John Doe <john.doe@example.com>  Wed, 11 Mar 2026 16:01:41 -0400
 """
    debian_changelog = changelog.Changelog(changelog_tmpl.format(version=version))
    context_changelog = ubuntu_lint.Context(debian_changelog=debian_changelog)

    changes = copy.deepcopy(basic_changes_ubuntu_delta)
    changes["Version"] = version
    context_changes = ubuntu_lint.Context(changes=changes)

    if expect_pass:
        ubuntu_lint.check_missing_version_suffix(context_changelog)
        ubuntu_lint.check_missing_version_suffix(context_changes)
    else:
        with pytest.raises(
            ubuntu_lint.LintException,
            match=re.escape(
                f"version {version} is missing a proper 'ubuntuX' or 'buildX' suffix"
            ),
        ):
            ubuntu_lint.check_missing_version_suffix(context_changelog)
            ubuntu_lint.check_missing_version_suffix(context_changes)


def test_check_missing_version_suffix_debian_upload():
    changelog_tmpl = """hello (1.2.3-4) unstable; urgency=medium

  * Fix a bug (Closes: #12345678)

 -- John Doe <john.doe@example.com>  Wed, 11 Mar 2026 16:01:41 -0400
 """
    context_changelog = ubuntu_lint.Context(
        debian_changelog=changelog.Changelog(changelog_tmpl)
    )
    context_changes = ubuntu_lint.Context(changes=basic_changes_no_ubuntu_delta)

    with pytest.raises(
        ubuntu_lint.LintException,
        match="upload is not targeting an Ubuntu series",
    ) as e:
        ubuntu_lint.check_missing_version_suffix(context_changelog)
        ubuntu_lint.check_missing_version_suffix(context_changes)

    assert e.value.result == ubuntu_lint.LintResult.SKIP


@pytest.fixture
def mock_lp_handle(mocker):
    mock_lp = mocker.MagicMock()
    mock_series = mocker.MagicMock()

    mock_lp.distributions.__getitem__.return_value = mock_lp
    mock_lp.getSeries.return_value = mock_series
    mock_lp.main_archive = mocker.MagicMock()

    return mock_lp


@pytest.fixture
def add_published_source_mock(mocker):
    def _add_published_source_mock(version, pocket="Release", status="Published"):
        mock_published = mocker.MagicMock()
        mock_published.pocket = pocket
        mock_published.status = status
        mock_published.source_package_version = version
        return mock_published

    return _add_published_source_mock


def test_check_missing_pending_changelog_entry(
    mock_lp_handle, add_published_source_mock
):
    mock_lp_handle.main_archive.getPublishedSources.return_value = [
        add_published_source_mock("2.10-5ubuntu1", pocket="Proposed"),
    ]
    # This changes file includes the changelog entry for version already in -proposed
    ubuntu_lint.check_missing_pending_changelog_entry(
        ubuntu_lint.Context(
            changes=basic_changes_ubuntu_extra_changelog,
            launchpad_handle=mock_lp_handle,
        )
    )

    mock_lp_handle.main_archive.getPublishedSources.return_value = [
        add_published_source_mock("2.10-4ubuntu2", pocket="Proposed"),
    ]
    with pytest.raises(
        ubuntu_lint.LintException,
        match=r"published in proposed but have not migrated.*2.10-4ubuntu2",
    ):
        # This changes file does NOT include the changelog entry for the version in
        # -proposed
        ubuntu_lint.check_missing_pending_changelog_entry(
            ubuntu_lint.Context(
                changes=basic_changes_ubuntu_delta,
                launchpad_handle=mock_lp_handle,
            )
        )


def test_check_missing_pending_changelog_entry_skips_deleted(
    mock_lp_handle, add_published_source_mock
):
    mock_lp_handle.main_archive.getPublishedSources.return_value = [
        add_published_source_mock("2.10-4ubuntu2", pocket="Proposed", status="Deleted"),
    ]
    # This changes file does not include the changelog entry that was in -proposed,
    # because it was deleted from the archive
    ubuntu_lint.check_missing_pending_changelog_entry(
        ubuntu_lint.Context(
            changes=basic_changes_ubuntu_delta,
            launchpad_handle=mock_lp_handle,
        )
    )


def test_check_missing_pending_changelog_entry_nothing_in_proposed(
    mock_lp_handle, add_published_source_mock
):
    mock_lp_handle.main_archive.getPublishedSources.return_value = [
        add_published_source_mock("2.10-4ubuntu2"),
    ]
    # The previous upload migrated already
    ubuntu_lint.check_missing_pending_changelog_entry(
        ubuntu_lint.Context(
            changes=basic_changes_ubuntu_delta,
            launchpad_handle=mock_lp_handle,
        )
    )


def test_check_missing_pending_changelog_entry_ignore_syncs(
    mock_lp_handle, add_published_source_mock
):
    mock_lp_handle.main_archive.getPublishedSources.return_value = [
        add_published_source_mock("2.10-5", pocket="Proposed"),
    ]
    # This changes file does NOT include the changelog entry for the version in
    # -proposed, because the previous version was a sync from Debian.
    ubuntu_lint.check_missing_pending_changelog_entry(
        ubuntu_lint.Context(
            changes=basic_changes_ubuntu_delta,
            launchpad_handle=mock_lp_handle,
        )
    )


@pytest.fixture
def add_bug_mock(mocker):
    def _add_bug_mock(bug_id, description="", bug_tasks=None):
        mock_bug = mocker.MagicMock()
        mock_bug.description = description
        mock_bug.bug_tasks = bug_tasks or []
        return mock_bug

    return _add_bug_mock


def test_check_sru_bug_missing_template(mock_lp_handle, add_bug_mock):
    bug_number = basic_changes_sru["Launchpad-Bugs-Fixed"].split()[0]

    impact = """
[Impact]
The application crashes on startup.
"""
    test_plan = """
[Test Plan]
1. Install the package
2. Run the application
3. Verify it starts without crashing
"""

    where_problems_could_occur = """
[Where Problems Could Occur]
Any code that initializes the application could be affected.
"""

    for impact_stanza, test_plan_stanza, where_problems_could_occur_stanza in [
        (impact, test_plan, where_problems_could_occur),
        (impact, test_plan, ""),
        (impact, "", ""),
        ("", "", ""),
    ]:
        bug_description = (
            f"{impact_stanza}\n{test_plan_stanza}\n{where_problems_could_occur_stanza}"
        )

        mock_bug = add_bug_mock(bug_number, description=bug_description)
        mock_lp_handle.bugs = {bug_number: mock_bug}

        if not all(
            (impact_stanza, test_plan_stanza, where_problems_could_occur_stanza)
        ):
            if not impact_stanza:
                section = "Impact"
            elif not test_plan_stanza:
                section = "Test Plan"
            else:
                section = "Where Problems Could Occur"

            with pytest.raises(
                ubuntu_lint.LintException,
                match=re.escape(
                    f"bug {bug_number} description is missing the [{section}] section"
                ),
            ):
                ubuntu_lint.check_sru_bug_missing_template(
                    ubuntu_lint.Context(
                        changes=basic_changes_sru, launchpad_handle=mock_lp_handle
                    )
                )
        else:
            ubuntu_lint.check_sru_bug_missing_template(
                ubuntu_lint.Context(
                    changes=basic_changes_sru, launchpad_handle=mock_lp_handle
                )
            )


def test_check_sru_bug_missing_release_tasks(mock_lp_handle, add_bug_mock):
    bug_number = basic_changes_sru["Launchpad-Bugs-Fixed"].split()[0]
    dist = basic_changes_sru["Distribution"]
    package = basic_changes_sru["Source"]

    mock_series = mock_lp_handle.getSeries.return_value
    series_url = f"https://api.launchpad.net/1.0/ubuntu/{dist}"
    mock_series.__str__.return_value = series_url

    mock_bug_with_task = add_bug_mock(
        bug_number,
        bug_tasks=[
            f"https://api.launchpad.net/1.0/ubuntu/{dist}/+source/{package}/+bug/{bug_number}"
        ],
    )
    mock_lp_handle.bugs = {bug_number: mock_bug_with_task}

    ubuntu_lint.check_sru_bug_missing_release_tasks(
        ubuntu_lint.Context(changes=basic_changes_sru, launchpad_handle=mock_lp_handle)
    )

    mock_bug_missing_task = add_bug_mock(bug_number, bug_tasks=[])
    mock_lp_handle.bugs = {bug_number: mock_bug_missing_task}

    with pytest.raises(
        ubuntu_lint.LintException,
        match=re.escape(f"LP: #{bug_number} is missing a bug task for noble"),
    ):
        ubuntu_lint.check_sru_bug_missing_release_tasks(
            ubuntu_lint.Context(
                changes=basic_changes_sru, launchpad_handle=mock_lp_handle
            )
        )


def test_check_merge_missing_new_debian_changelog():
    ubuntu_lint.check_merge_missing_new_debian_changelog(
        ubuntu_lint.Context(
            changes=basic_changes_merge,
            debian_changelog=basic_changelog_merge,
        )
    )

    # Trim the changes, it should now fail.
    bad_changes = copy.deepcopy(basic_changes_merge)
    bad_changes["Changes"] = """
 hello (2.12-1ubuntu1) resolute; urgency=medium
 .
   * Merge from Debian unstable (LP: #12345678)"""

    with pytest.raises(
        ubuntu_lint.LintException,
        match="source package should be built with -v2.10-2ubuntu2",
    ):
        ubuntu_lint.check_merge_missing_new_debian_changelog(
            ubuntu_lint.Context(
                changes=bad_changes,
                debian_changelog=basic_changelog_merge,
            )
        )


@pytest.mark.parametrize(
    "changes, debian_changelog",
    [
        (basic_changes_no_ubuntu_delta, basic_changelog_no_ubuntu_delta),
        (basic_changes_ubuntu_delta, basic_changelog_ubuntu_delta),
        (basic_changes_ubuntu_extra_changelog, basic_changelog_ubuntu_extra_changelog),
        (basic_changes_sru, basic_changelog_sru),
    ],
    ids=[
        "no_delta",
        "delta",
        "extra_changelog",
        "sru",
    ],
)
def test_check_merge_missing_new_debian_changelog_skip(
    changes: deb822.Changes,
    debian_changelog: changelog.Changelog,
):
    with pytest.raises(
        ubuntu_lint.LintException,
        match="upload does not look like a merge",
    ) as e:
        ubuntu_lint.check_merge_missing_new_debian_changelog(
            ubuntu_lint.Context(changes=changes, debian_changelog=debian_changelog)
        )

    assert e.value.result == ubuntu_lint.LintResult.SKIP
