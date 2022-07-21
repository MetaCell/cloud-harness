# Use harness-application to create a new application from templates

## Choosing Templates

If you create a new application, you can choose templates that are used to generate the application scaffold.

Running `harness-application --help` will list the currently available templates:

```
usage: harness-application [-h] [-t TEMPLATES] name

Creates a new Application.

positional arguments:
  name                  Application name

optional arguments:
  -h, --help            show this help message and exit
  -t TEMPLATES, --template TEMPLATES
                        Add a template name. Available templates: - base (always included) - server (backend flask app based on openapi) - webapp (webapp including backend and frontend) - db-postgres - db-neo4j - db-mongo - django-app (fastapi django backend based on openapi)
```

## Available Templates

### Base

* The `base` template is always included and used as foundation for any other template.

### Server
* It consists of a single backend, a Python [Flask](https://flask.palletsprojects.com/en/1.1.x/) application. 
* The [Connexion](https://github.com/zalando/connexion) library maps the OpenAPI definition to Flask routing.
* Per default, [Gunicorn](https://gunicorn.org/) serves the Flask app with 2 synchronous workers. Depending on the application requirements, you can update the number of workers or choose a different [worker type](https://docs.gunicorn.org/en/stable/design.html).  


### Webapp

* The `webapp` template consists builds upon the `base` template extends it by a [React](https://reactjs.org/) frontend application.
* The generated frontend bundle is served by the Python backend.
* Per default, React is used as a frontend application, but you are free to choose a different frontend technology. 


### Databases

Additionally, you can choose one of the following database templates:
* `db-postgres` - [PostgreSQL](https://www.postgresql.org/), a relational database
* `db-neo4j`- [Neo4J](https://neo4j.com/), a graph database
* `db-mongo` - [MongoDB](https://www.mongodb.com/), a NoSQL document-based database

### Django
* It consists of a single backend, a Python [FastAPI](https://fastapi.tiangolo.com/) application. 
* The [FastAPI code generator](https://github.com/koxudaxi/fastapi-code-generator) maps the OpenAPI definition to FastAPI routing.
* The [Django framework](https://www.djangoproject.com/) encourages rapid development and clean, pragmatic design.
* Per default, [Uvicorn](https://www.uvicorn.org/) serves the FastAPI app with 2 workers. Depending on the application requirements, you can update the number of workers.
