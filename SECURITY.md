# Security Policy

Sweepito deletes files, so a bug that removes the wrong thing is a security issue.

## What counts as a vulnerability

Please report privately if you can make Sweepito:

- delete a **tracked** file, a file **outside the project root**, or anything inside `.git/`;
- follow a symlink or, on Windows, a junction out of the project root;
- delete something that is not git-ignored without `allow_untracked = true`;
- run a command from an untrusted configuration file;
- run a `high-impact` rule that was not selected with `--enable` or `--risk high-impact`.

A rule that is merely too aggressive for your project (for example a build folder you
wanted kept) is a normal bug. Please open a regular issue.

## Supported versions

Only the latest released version receives fixes.

## Reporting

Use GitHub's private vulnerability reporting: open the repository's **Security** tab and
choose **Report a vulnerability**. Please do not open a public issue for these reports.

Include the Sweepito version (`sweepito --version`), your operating system, the
configuration file, and the smallest repository layout that reproduces the problem.

You can expect an acknowledgement within a few days. Fixes are released as a patch version
and credited in the changelog unless you prefer otherwise.
