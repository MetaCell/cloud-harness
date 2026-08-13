# Use harness-generate to generate server and client stubs

To (re)generate the code for your applications, run `harness-generate`.
`harness-generate` is a command-line tool used to generate client code, server stubs, and model libraries for applications. It walks through the filesystem inside the `./applications` folder to create and update application scaffolding. The tool supports different generation modes and allows for both interactive and non-interactive usage.

## Usage

```sh
harness-generate [mode] [-h] [-i] [-a APP_NAME] [-cn CLIENT_NAME] [-t | -p] [path]
```

## harness-generate Arguments

- `path` *(optional)* – The base path of the application. If provided, the `-a/--app-name` flag is ignored.

## harness-generate Options

- `-h, --help` – Displays the help message and exits.
- `-i, --interactive` – Asks for confirmation before generating code, or before handling each project in `dependencies` mode.
- `-a APP_NAME, --app-name APP_NAME` – Specifies the application name to generate clients for.
- `-cn CLIENT_NAME, --client-name CLIENT_NAME` – Specifies a prefix for the client name.
- `-t, --ts-only` – Generates only TypeScript clients.
- `-p, --python-only` – Generates only Python clients.

## Generation Modes

`harness-generate` supports the following modes:

- **all** – Generates both server stubs and client libraries.
- **clients** – Generates only client libraries.
- **servers** – Generates only server stubs.
- **models** – Regenerates only model libraries.
- **dependencies** – Audits JavaScript dependencies and refreshes every lock file. Not included in **all**, which only regenerates checked in code and should not move third party versions.

## harness-generate Examples

### Generate Client and Server stubs for all applications

```sh
harness-generate all
```

### Generate Client and Server stubs for a Specific Application

```sh
harness-generate all -a myApp
```

### Generate Only Client Libraries

```sh
harness-generate clients
```

### Generate Only Server Stubs

```sh
harness-generate servers
```

### Regenerate Only Model Libraries (deprecated)

```sh
harness-generate models
```

### Generate TypeScript Clients Only and Server stubs

```sh
harness-generate all -t
```

### Generate Python Clients Only and Server stubs

```sh
harness-generate all -p
```

### Interactive Mode

```sh
harness-generate all -i
```

### Update dependencies and lock files

```sh
harness-generate dependencies
```

Every JavaScript project below the current path is discovered by the lock file sitting
next to its `package.json`, then audited and refreshed:

- **yarn projects** are re-resolved against the version ranges already declared in
  `package.json`, which is what picks up a patched release. Yarn has no `audit fix`
  equivalent, and a plain `yarn install` will not move a resolution that still satisfies
  its range, so the lock file is discarded and rebuilt.
- **npm projects** additionally get `npm audit fix`.

`package.json` is left untouched, and the
[dependency cooldown](../dependency-cooldown.md) applies throughout, so no version
published in the last 7 days is picked up. A directory holding both a `yarn.lock` and a
`package-lock.json` is updated once per package manager.

The command exits non-zero when vulnerabilities are still reported afterwards. Those
need a change an in-range update cannot make: `--upgrade` for a direct dependency, or a
`resolutions` entry in `package.json` for a transitive one.

Report vulnerabilities without writing anything:

```sh
harness-generate dependencies --audit-only
```

Also raise the version ranges declared in `package.json`. This can cross major versions
and introduce breaking changes, so review the resulting diff:

```sh
harness-generate dependencies --upgrade
```

Confirm each project before it is touched, which is the way to update one application
without moving the others:

```sh
harness-generate dependencies -i
```

```
Do you want to update /path/applications/samples/frontend [yarn]? (Y/n): y
Do you want to update /path/test/test-e2e [yarn]? (Y/n): n
INFO Skipping /path/test/test-e2e [yarn]
```

Declined projects are neither audited nor updated, and are not counted in the final
report. `-i` combines with `--audit-only` and `--upgrade`.

This mode needs neither java nor the openapi generator. It does need a yarn new enough to
read the lock files: if yours is too old it offers to run `corepack enable` for you before
touching anything, and falls back to printing that instruction when there is no terminal
to ask at. See [developer setup](../dependency-cooldown.md#developer-setup).

## harness-generate Notes

- The tool scans the `./applications` directory for available applications.
- If `path` is provided, `-a/--app-name` is ignored.
- The `models` mode is a special flag used when regenerating only model libraries (deprecated).
- The tool supports interactive mode to confirm before generating clients.
- Use either `-t` or `-p`, but not both simultaneously.
- The `dependencies` mode takes `-i/--interactive`, `--upgrade` and `--audit-only`; the other generation options do not apply to it.

For further details, run:

```sh
harness-generate --help
```
