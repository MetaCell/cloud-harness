# Use harness-application to create a new application

## Overview

`harness-application` is a command-line tool used to create new applications from predefined code templates. It allows users to quickly scaffold applications with backend, frontend, and database configurations.

## Usage

```sh
harness-application [name] [-t TEMPLATE]
```

## Arguments

- `name` *(required)* – The name of the application to be created.

## Options

- `-h, --help` – Displays the help message and exits.
- `-t TEMPLATES, --template TEMPLATES` – Specifies one or more templates to use when creating the application.

## Choosing Templates

When creating a new application, you can choose templates that define its structure and components. Running `harness-application --help` will list the currently available templates:

```sh
usage: harness-application [-h] [-t TEMPLATES] name
```

## Available Templates

### Base

- The `base` template is always included and serves as the foundation for any other template.

### Backend Templates

#### Flask Server

- The `flask-server` template consists of a backend built using [Flask](https://flask.palletsprojects.com/en/1.1.x/).
  - Uses [Connexion](https://github.com/zalando/connexion) to map OpenAPI definitions to Flask routes.
  - Served by [Gunicorn](https://gunicorn.org/) with 2 synchronous workers by default.
    - Supports customization of the worker count and type.

#### Django

- The `django-fastapi` consists of a backend based on [FastAPI](https://fastapi.tiangolo.com/) and [Django](https://www.djangoproject.com/).
  - Uses the [FastAPI code generator](https://github.com/koxudaxi/fastapi-code-generator) to map OpenAPI definitions.
  - Served by [Uvicorn](https://www.uvicorn.org/) with 2 workers by default.
- The `django-ninja` consists of a backend based on [Django Ninja](https://django-ninja.dev/)
  - Provides automatic OpenAPI schema generation.
  - Supports Django's built-in ORM for seamless database integration.
  - High performance due to Pydantic-based data validation.
  - Simplifies request parsing and authentication.

### Full-Stack Templates

#### Webapp

- The `webapp` template extends the `base` template by adding a [React](https://reactjs.org/) frontend.
  - The frontend bundle is served by the Python backend.
  - React is used by default, but other frontend technologies can be integrated.

#### Django with Microsoft Entra ID

- The `django-entra` template is a complete application: a [Django Ninja](https://django-ninja.dev/) backend,
  a [React](https://reactjs.org/) frontend served by the backend and a PostgreSQL database.
  - Users log in with [Microsoft Entra ID](https://learn.microsoft.com/entra/identity/) (OpenID Connect, single tenant)
    and are synchronized in Django at login; app roles of the Entra registration give access to the application and
    to the Django admin. API clients can use Entra access tokens.
  - Does not use Keycloak (`accounts`), Kafka (`events`), the gatekeeper or the CloudHarness base images: the
    CloudHarness Python libraries are vendored in the application (`libraries`).
  - Self-contained: it cannot be combined with other templates (`base` is not added).
  - See the README of the generated application to register it in Entra and configure the deployment.

### Database Templates

- `db-postgres` – [PostgreSQL](https://www.postgresql.org/), a relational database.
- `db-neo4j` – [Neo4J](https://neo4j.com/), a graph database.
- `db-mongo` – [MongoDB](https://www.mongodb.com/), a NoSQL document-based database.

## Examples

### Create a New Flask-Based Microservice Application

```sh
harness-application myapp
```

### Create a Full-Stack Web Application

```sh
harness-application myapp -t webapp
```

### Create a Web Application with a Mongo Database

```sh
harness-application myapp -t webapp -t db-mongo
```

### Create a Django Application Authenticated with Microsoft Entra ID

```sh
harness-application myapp -t django-entra
```

### Display Help Information

```sh
harness-application --help
```

## Notes

- Multiple templates can be specified by concatenating the `-t` parameter.
- The tool generates the necessary scaffolding for the chosen templates.
- Ensure you have the required dependencies installed before running the generated application.
- For more information, run `harness-application --help` or check out the additional documentation:
  - [Applications README](./docs/applications/README.md)
  - [Developer Guide](./docs/dev.md)
