import copy
import pytest
import ubuntu_lint

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


def test_check_missing_ubuntu_maintainer():
    ubuntu_lint.check_missing_ubuntu_maintainer(
        ubuntu_lint.Context(changes=basic_changes_no_ubuntu_delta)
    )
    ubuntu_lint.check_missing_ubuntu_maintainer(
        ubuntu_lint.Context(changes=basic_changes_ubuntu_delta)
    )

    changes_missing_ubuntu_maintainer = copy.deepcopy(basic_changes_ubuntu_delta)
    changes_missing_ubuntu_maintainer["Maintainer"] = "John Doe <john.doe@example.com>"
    with pytest.raises(ubuntu_lint.LintFailure):
        ubuntu_lint.check_missing_ubuntu_maintainer(
            ubuntu_lint.Context(changes=changes_missing_ubuntu_maintainer)
        )


def test_check_missing_launchpad_bugs_fixed():
    ubuntu_lint.check_missing_launchpad_bugs_fixed(
        ubuntu_lint.Context(changes=basic_changes_ubuntu_delta)
    )

    changes_missing_lp_bugs_fixed = copy.deepcopy(basic_changes_ubuntu_delta)
    del changes_missing_lp_bugs_fixed["Launchpad-Bugs-Fixed"]
    with pytest.raises(ubuntu_lint.LintFailure):
        ubuntu_lint.check_missing_launchpad_bugs_fixed(
            ubuntu_lint.Context(changes=changes_missing_lp_bugs_fixed)
        )


def test_check_missing_git_ubuntu_references(requests_mock):
    vcs_git = basic_changes_ubuntu_delta.get("Vcs-Git")
    vcs_git_ref = basic_changes_ubuntu_delta.get("Vcs-Git-Ref")
    vcs_git_commit = basic_changes_ubuntu_delta.get("Vcs-Git-Commit")

    requests_mock.get(
        f"{vcs_git}/patch/?h={vcs_git_ref}",
        text=f"From {vcs_git_commit} Mon Sep 17 00:00:00 2001",
    )
    ubuntu_lint.check_missing_git_ubuntu_references(
        ubuntu_lint.Context(changes=basic_changes_ubuntu_delta)
    )

    # Simulate local commit hash != remote commit hash.
    requests_mock.get(
        f"{vcs_git}/patch/?h={vcs_git_ref}",
        status_code=404,
    )
    with pytest.raises(ubuntu_lint.LintFailure):
        ubuntu_lint.check_missing_git_ubuntu_references(
            ubuntu_lint.Context(changes=basic_changes_ubuntu_delta)
        )

    # Refs missing from changes file completely
    changes_missing_git_ubuntu_refs = copy.deepcopy(basic_changes_ubuntu_delta)
    for field in ("Vcs-Git", "Vcs-Git-Commit", "Vcs-Git-Ref"):
        del changes_missing_git_ubuntu_refs[field]

    with pytest.raises(ubuntu_lint.LintFailure):
        ubuntu_lint.check_missing_git_ubuntu_references(
            ubuntu_lint.Context(changes=changes_missing_git_ubuntu_refs)
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

    with pytest.raises(ubuntu_lint.LintFailure):
        ubuntu_lint.check_missing_bug_references(
            context=ubuntu_lint.Context(debian_changelog=dch)
        )
