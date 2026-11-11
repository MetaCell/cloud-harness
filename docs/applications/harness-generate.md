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
- `-i, --interactive` – Asks for confirmation before generating code.
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
- **ci-cd** – Generates the CI/CD pipelines (Codefresh, GitHub Actions), see [below](#generate-the-cicd-pipelines).

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

### Generate the CI/CD pipelines

```sh
harness-generate ci-cd [paths ...] [-i APP ...] [-ex APP ...] [-e ENV ...] [--name NAME] [-u] [-rsn SECRET]
```

`paths` are the deployment layers, lowest priority first, as `harness-deployment` takes them (omit them to use
the subdirectories with a `deployment-configuration`, then the current directory). A pipeline is generated for
each environment with a template in the `deployment-configuration` of the last path:

- `codefresh-template-[ENV].yaml` → `deployment/ci--[NAME]--[ENV].yaml`
- `github-template-[ENV].yaml` → `.github/workflows/ci--[NAME]--[ENV].yaml` (and
  `.github/workflows/ci--[NAME]--promote.yaml` when the template has a `cloudharness.promote` workflow)

The templates of the other layers (e.g. cloud-harness) are merged in, but a pipeline is only generated for an
environment the project has a template file for, even an empty one. `[NAME]` is `--name`, by default the
included applications joined with dashes (`all` when there is no `-i`). `-e` restricts the environments; combine
several with dashes (`-e research-dev`), each needing its template. For example, from the cloud-harness root:

```sh
harness-generate ci-cd . -i samples
```

## harness-generate Notes

- The tool scans the `./applications` directory for available applications (`ci-cd` takes its own arguments,
  `-i` there selects the applications to deploy).
- If `path` is provided, `-a/--app-name` is ignored.
- The `models` mode is a special flag used when regenerating only model libraries (deprecated).
- The tool supports interactive mode to confirm before generating clients.
- Use either `-t` or `-p`, but not both simultaneously.

For further details, run:

```sh
harness-generate --help
```
