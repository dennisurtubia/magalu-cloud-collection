# Ansible Collection - dennisurtubia.magalu_cloud

[![CI](https://github.com/dennisurtubia/magalu-cloud-collection/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/dennisurtubia/magalu-cloud-collection/actions/workflows/ci.yml)

Documentation for the collection.

## Development

### Tests

`ansible-test` must run from a checkout whose path ends in `ansible_collections/dennisurtubia/magalu_cloud/`.

```bash
ansible-lint
ansible-test sanity --venv -v
ansible-test units --venv -v
antsibull-changelog lint
```

CI runs sanity and unit tests against every supported ansible-core branch, plus `devel` as a non-blocking job.
It also runs `ansible-lint` and builds the collection to check it with the Galaxy importer.
Integration tests are not part of CI because they create real, billable Magalu Cloud resources.

### Changelog

The changelog is managed with [antsibull-changelog](https://ansible.readthedocs.io/projects/antsibull-changelog/).
A pull request that changes existing content under `plugins/` must add a fragment to `changelogs/fragments/`.
New modules do not need a fragment, because they are detected from `version_added` at release time.
Maintainers can apply the `skip-changelog` label when a change does not affect users.

### Release

1. Set `version` in `galaxy.yml`.
2. Add a `release_summary` fragment and run `antsibull-changelog release`.
3. Commit, then push a tag that matches the version, for example `1.0.0`.

The release workflow runs CI, builds the collection, waits for approval in the `release` environment, publishes to
Ansible Galaxy, and creates a GitHub release with the collection artifact.
