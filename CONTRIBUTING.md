# Contributing to expfactory-deploy

Thanks for your interest in contributing! This project deploys Django-managed batteries of experiments. If you hit a snag or have a question, please open an issue at <https://github.com/expfactory/expfactory-deploy/issues>.

## Attribution

The structure and conventions of this document (branch prefixes, commit prefixes, fork + PR workflow) are adapted from the excellent [DataLad CONTRIBUTING guide](https://github.com/datalad/datalad/blob/maint/CONTRIBUTING.md). Thanks to the DataLad maintainers.

## Development setup

See `README.rst` for full local setup. In short: the project runs as a Docker Compose stack defined in `local.yml`; you will need a container runtime (Docker or Podman) and a few env files under `.envs/.local/`.

## Fork-based workflow

1. Fork `expfactory/expfactory-deploy` on GitHub.
2. Clone your fork locally as `origin`:
   ```bash
   git clone git@github.com:<your-username>/expfactory-deploy.git
   cd expfactory-deploy
   ```
3. Add the canonical repository as `upstream`:
   ```bash
   git remote add upstream https://github.com/expfactory/expfactory-deploy.git
   ```
4. Keep `main` tracking `upstream/main`:
   ```bash
   git fetch upstream
   git switch main
   git branch --set-upstream-to=upstream/main main
   ```
5. Create topic branches off `main`. See **Branch naming** below.
6. Push topic branches to your fork (`origin`) and open a PR against `expfactory/expfactory-deploy:main`.

## Branch naming

Use these prefixes on topic-branch names, lowercase and hyphen-separated:

| Prefix | Meaning          |
| ------ | ---------------- |
| `nf-`  | New feature      |
| `bf-`  | Bug fix          |
| `rf-`  | Refactor         |
| `doc-` | Documentation    |
| `bm-`  | Benchmarks       |

Examples: `nf-prolific-export`, `bf-preview-instructions-typo`, `doc-contributing`.

## Commit messages

Prefix the first line of each commit with one of these tags:

| Prefix | Meaning                 |
| ------ | ----------------------- |
| `NF:`  | New feature             |
| `BF:`  | Bug fix                 |
| `RF:`  | Refactor                |
| `DOC:` | Documentation           |
| `BM:`  | Benchmarks              |
| `TST:` | Tests only              |
| `CI:`  | Continuous integration  |
| `UX:`  | User-facing polish      |
| `BK:`  | Known breakage          |

Prefixes may be combined with `+`, e.g. `RF+DOC: rename battery model and update docs`.

You may scope a commit with parentheses, e.g. `BF(TST): fix flaky assertion in prolific view test`.

To auto-close an issue when the PR merges, add a footer: `Closes #123`.

## Before opening a PR

- [ ] `main` is up to date with `upstream/main`, and your topic branch is rebased or merged up to that tip.
- [ ] Pre-commit hooks pass (the repo has `.pre-commit-config.yaml` configured with ruff and other checks).
- [ ] Database migrations are included if you changed models.
- [ ] Tests pass locally:
  ```bash
  podman compose -f local.yml run --rm django ./manage.py test
  # or: docker compose -f local.yml run --rm django ./manage.py test
  ```

## Opening the PR

- **Base:** `expfactory/expfactory-deploy:main`.
- **Head:** `<your-username>:<branch-name>`.
- **Title:** start with the commit prefix that matches the dominant change (e.g., `BF: fix ...`).
- **Body:** short description of what and why; link any related issues.

## After merge

Once your PR merges:

1. Delete the topic branch from your fork (GitHub's UI offers a one-click delete after merge).
2. Sync your fork's `main`:
   ```bash
   git switch main
   git fetch upstream
   git reset --hard upstream/main
   git push --force-with-lease origin main
   ```
