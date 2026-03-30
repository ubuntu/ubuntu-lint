# ubuntu-lint

`ubuntu-lint` is a packaging linter for Ubuntu development. It is intended as a supplement to tools like `lintian`, and focuses on linting Ubuntu specific processes and conventions that arise frequently in code review. It can lint multiple types of input, including Debian source package directories, changelogs, and changes files.

There are a few ways to interact with `ubuntu-lint`:

* On the CLI with `ubuntu-lint`
* Directly in Python with the `ubuntu_lint` module
* As `dput-ng` hooks, which call into the Python module

## `ubuntu-lint` CLI

The easiest way to get started is to run `ubuntu-lint` with no arguments from a Debian source package directory:

```bash
$ ubuntu-lint
```

When other arguments are passed, `ubuntu-lint` will infer context using the current directory, changelog, and a recently built changes file if present. Input context can be specified explicitly using the `--changes-file=`, `--source-dir` and `--changelog` flags. By default, `ubuntu-lint` will automatically select which lints to run. For example, if the target series of an upload is a stable release, additional SRU checks will run.

For each lint, `foo-bar`, there is a corresponding flag `--foo-bar=` to control how that lint will run. It accepts one of `auto, off, warn, fail`. If set to `off`, it will not run at all. If set to `warn` or `fail`, the check will run, and detected issues will be treated as a warning or failure, respectively. The default is `auto`.

## Python module

The [`ubuntu_lint`](ubuntu_lint) Python module implements each lint, which is a function that accepts a single `Context` object. To indicate an issue, the lint raises a `LintException` by calling `Context.lint_fail`, `Context.lint_error`, `Context.lint_warn`, or `Context.lint_skip` with a message describing the issue. The `LintException` object has a `result` attribute with a `LintResult` to indicate the result of the lint.


## `dput-ng` hooks

Lints that operate on a changes file can trivially be used as a dput-ng hook. The [`ubuntu_lint.dput`](ubuntu_lint/dput.py) module provides simple wrappers that conform to `dput-ng`'s excpectations, and the necessary JSON snippets are in [`dput.d`](dput.d).
