# Contributing Guidelines

Thank you for your interest in contributing to Project Lockdown. Whether it's a bug report, new feature, correction, or additional documentation, we appreciate feedback and contributions from our community.

Please read through this document before submitting any issues or pull requests to ensure we have all the necessary information to effectively respond to your bug report or contribution.

## Submitting an Issue (Bug Report)

- Before submitting an issue please review the current open and closed issues for duplicates.
- Please provide as many details as possible so that we can properly address the bug and accurately reproduce on our end.

## Submitting a Pull Request

- Please open a GitHub issue before working on any new functionality for Project Lockdown and then tie the Pull Request to the issue.
- We request that you [fork](https://docs.github.com/en/free-pro-team@latest/github/getting-started-with-github/fork-a-repo) Project Lockdown and then submit a Pull Request on your fork. This helps us better review open PRs, expedite the review process, and keep the repository clean by not having stale branches.
- Each Pull Request requires two approvals from code owners.

To submit a PR:
- Verify tests pass successfully by executing `make test` locally. 
- Commit the code coverage svg in your branch after tests pass.

Once submitted our Github Actions will run automated tests and report back the findings to the PR. If the tests fail, please review the findings and make the appropriate updates. 
