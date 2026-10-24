# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project identity and purpose

- This repository, `magalu-cloud-collection`, contains an Ansible collection for managing and inspecting Magalu Cloud resources.
- The current development collection identifier is `dennisurtubia.magalu_cloud` (`namespace` and `name` in `galaxy.yml`).
- `dennisurtubia` is a personal namespace. Do not represent it as an official Magalu Cloud namespace.
- Do not publish or register the collection under the intended official namespace without explicit authorization.

## Reference conventions

- Use `amazon.aws` and `google.cloud` as references for Ansible interface design, usability, module documentation, and conventions.
- Never assume Magalu Cloud has the same API behavior, resource capabilities, defaults, or lifecycle semantics as AWS or GCP.
- Magalu Cloud's official API documentation is the authoritative source for Magalu-specific API contracts. Use the relevant product reference under `https://docs.magalu.cloud/api/`, for example https://docs.magalu.cloud/api/database.
- Use the official Magalu Cloud guides at https://docs.magalu.cloud/docs/ for additional product context and operational guidance.
- The official Magalu Cloud CLI may help discover capabilities but is not authoritative evidence of HTTP API contracts.
- Do not use unofficial SDKs, blogs, forums, or undocumented assumptions to define API behavior.
- When official sources are missing or contradictory, document the gap and ask for clarification rather than inventing a contract.

## Scope and technical constraints

- Do not assume an API supports creation, modification, deletion, restart, state transitions, or any other operation without evidence.
- Avoid speculative abstractions and unnecessary generalization.
- Do not add third-party Python runtime dependencies without an explicit technical justification and approval.
- Use Ansible-supported Python module utilities (`ansible.module_utils.urls`) for HTTP communication where appropriate.

## Language and maintainability

- Write source code, module documentation, tests, and project guidance in English.
- Preserve established repository conventions when they do not conflict with these definitions.
- Keep documentation accurate and consistent with implemented behavior.

## Development and testing

- `ansible-test` only runs from a checkout whose physical path ends in `ansible_collections/dennisurtubia/magalu_cloud/`. It resolves the working directory with `os.getcwd()`, so reaching the checkout through a symlink at that path is not enough.
- `ansible-core` and `ansible-lint` are installed globally with `uv tool install`. They are not project dependencies, and the repository has no Python project files.
- Run `ansible-test` with `--docker default` when a container runtime is available, otherwise with `--venv`. Unit-test requirements (pytest, pytest-mock) come from `ansible-test`.
- Never run integration tests without explicit approval: they create real, billable Magalu Cloud resources.
- Pull requests that change existing content under `plugins/` need a fragment in `changelogs/fragments/` (antsibull-changelog format). New modules are detected from `version_added` and need none.
- Releases are cut by pushing a tag equal to the `galaxy.yml` version after running `antsibull-changelog release`. The release workflow publishes to Ansible Galaxy only after approval in the `release` environment.

```bash
ansible-galaxy collection build   # dennisurtubia-magalu_cloud-<version>.tar.gz
ansible-lint
ansible-test sanity --venv -v
ansible-test sanity --venv -v --test validate-modules plugins/modules/<module>.py
ansible-test units --venv -v
ansible-test units --venv -v tests/unit/plugins/modules/test_<module>.py
antsibull-changelog lint
```
