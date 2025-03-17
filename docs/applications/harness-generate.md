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

## harness-generate Notes

- The tool scans the `./applications` directory for available applications.
- If `path` is provided, `-a/--app-name` is ignored.
- The `models` mode is a special flag used when regenerating only model libraries (deprecated).
- The tool supports interactive mode to confirm before generating clients.
- Use either `-t` or `-p`, but not both simultaneously.

For further details, run:

```sh
harness-generate --help
```
