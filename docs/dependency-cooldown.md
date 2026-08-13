# Dependency cooldown

CloudHarness ignores third party package versions published in the last **7 days**.

Most malicious releases are detected and pulled within hours of being published, so
refusing to install anything newer than a week filters out the smash and grab attacks
that dominate registry compromises. The cost is that a genuine upgrade is available a
week later than it otherwise would be.

The window is applied by the package managers themselves, on both stacks.

## Python

Every `pip install` carries `--uploaded-prior-to=P7D`:

```dockerfile
RUN pip install --uploaded-prior-to=P7D -r requirements.txt
```

Add the flag to any new `pip install` you write, in Dockerfiles, `dev-setup.sh` scripts
and CI configuration alike.

**The one exception is `pip install --upgrade pip`.** That line bootstraps the pip that
understands the flag, so it cannot carry it. It stays unpinned by necessity, and it must
come *before* any flagged install:

```dockerfile
RUN python -m pip install --upgrade pip &&\
    pip install --uploaded-prior-to=P7D -r requirements.txt --prefer-binary
```

### Application lock files

Each application that installs a `requirements.txt` also carries a
[PEP 751](https://peps.python.org/pep-0751/) `pylock.toml` beside it, pinning the whole
resolved tree with hashes. Regenerate them with
[`harness-generate dependencies`](./applications/harness-generate.md#update-dependencies-and-lock-files).

The lock is generated inside a **throwaway container from the application's own base
image** — `cloudharness-flask` for a flask application, resolved from the `FROM` line of
its Dockerfile. The known base images are scanned from the `infrastructure` folders of
the repository and of a `cloud-harness` checkout beside it, so images a downstream
repository defines itself are covered without configuration. The requirements are installed there first and the freeze of that
environment constrains the lock, so resolution happens on top of the packages the base
image really provides instead of from an empty environment, and the pinned wheels match
the deploy platform by construction. The cooldown applies at both steps; nothing of the
lock toolchain ends up in a deploy image.

Generating locks therefore needs Docker and the base images built: run
`harness-deployment` to generate the build configuration, then `skaffold build`. The
built images are named through the generated `skaffold.yaml` (harness-deployment
prefixes them with the deployment name, e.g. `cloud-harness/cloudharness-flask`), and
the lock generation resolves through the same file, so the names always agree. Point
`--registry`/`--tag` at existing images to use those instead.

**Only applications are locked.** Base images, `libraries/` and `tools/` install into the
base images and stay unlocked on purpose, so every application keeps inheriting their
updates instead of pinning a copy of them.

The application Dockerfiles install from the lock rather than from `requirements.txt`:

```dockerfile
COPY ./pylock.toml /usr/src/app/
RUN pip3 install --no-cache-dir -r pylock.toml
```

**Do not add `--uploaded-prior-to` to a lock install.** pip treats the lock as the index,
and an index with no upload-time metadata cannot answer the cooldown question, so the
install fails outright with *"Index pylock.toml does not provide upload-time metadata"*.
The window was already applied when the lock was written, which is the whole point: this
is the second deliberate exception to the flag, after `pip install --upgrade pip`. The
`pip install -e .` that follows still carries it, because that one does resolve.

Two properties of these files are worth knowing:

- **They are single-platform.** `pip lock` records no `environments` or markers, and pins
  the concrete wheels of the image it ran in — amd64, CPython 3.12. Building an
  application image on another platform will fail rather than silently resolve something
  else, and a lock generated from a different base image would pin different wheels.
- **A stale lock silently pins old versions.** Editing `requirements.txt` no longer
  changes what an image installs until the lock is regenerated. Run
  `harness-generate dependencies` and commit both files together.

### Requirements

- The `P7D` duration form needs **pip >= 26.1**, which needs **Python >= 3.10**.
  (`--uploaded-prior-to` first appeared in pip 26.0, accepting only absolute datetimes.)
  An image or CI runner below Python 3.10 has to be upgraded, not flagged.
- The flag only works against indexes that publish upload time metadata. PyPI does.
  Pointing pip at a private mirror that does not would silently void the cooldown.

## JavaScript

Yarn applies the window through [`npmMinimalAgeGate`](https://yarnpkg.com/configuration/yarnrc#npmMinimalAgeGate),
which needs **yarn >= 4.10**. Yarn Classic (1.x) has no equivalent, so the repository
pins yarn 4 through the `packageManager` field in every `package.json`.

The setting is configured in two places, and nowhere else:

| Where | What it covers |
| --- | --- |
| [`.yarnrc.yml`](../.yarnrc.yml) at the repository root | Developer machines. Yarn merges rc files from ancestor directories, so one file covers every JavaScript project in the repo. |
| `YARN_NPM_MINIMAL_AGE_GATE` in the [cloudharness-frontend-build](../infrastructure/base-images/cloudharness-frontend-build/Dockerfile) base image | Every frontend container build, including applications generated into downstream repositories. |

Do not add per-project `.yarnrc.yml` files. If `yarn install` creates one during a
migration, delete it: yarn writes `approvedGitRepositories: "**"` into it, which allows
any git repository as a dependency source and works against the point of the exercise.

`test/test-e2e` repeats the base image settings inline in its own Dockerfile, because it
builds from the puppeteer runtime rather than from `cloudharness-frontend-build`.

### Developer setup

The `yarn` on your PATH is probably still 1.22, which cannot read the repository lock
files. Enable [corepack](https://yarnpkg.com/corepack) once and it will pick up the yarn
version pinned in `package.json`:

```bash
corepack enable
```

Until you do, yarn refuses to run and points you at this same command. It does not
corrupt anything. `harness-generate dependencies` detects an old yarn before it touches
anything and offers to run `corepack enable` for you; it only asks when attached to a
terminal, so an unattended run fails with the instruction rather than hanging on a prompt.

Corepack installs its shims next to the `node` binary. If that directory is not writable,
run the command with sudo or pass `--install-directory <dir on your PATH>`. If a different
yarn sits earlier in your PATH it will keep shadowing the shim, and the tool says so.

### Exempting a package

When the cooldown blocks a version you genuinely need, list the package under
`npmPreapprovedPackages` in the root `.yarnrc.yml` rather than lowering the window.

## Keeping dependencies current

`harness-generate dependencies` audits every JavaScript project and refreshes its lock
files within the cooldown. See
[harness-generate](./applications/harness-generate.md#update-dependencies-and-lock-files).

## Where the cooldown does and does not apply

Container builds install from a committed lock file with `--immutable` (yarn) or from
pinned requirements, so they resolve nothing and the cooldown never has to make a
decision. It applies wherever a *new* version gets chosen: `yarn add`, `yarn up`,
`harness-generate dependencies`, and any unpinned `pip install`.

Two gaps are worth knowing about:

- `pip install --upgrade pip` has no window, as described above.
- `test/test-e2e` is installed with npm by `harness-test` and with yarn by its Dockerfile,
  so it carries both a `package-lock.json` and a `yarn.lock`. Neither is stale; do not
  delete either. The npm side has no cooldown, because npm only gained `min-release-age`
  in 11.10.0.
