# __APP_NAME__

Django-Ninja/React-based web application.
This application is constructed to be deployed inside a cloud-harness Kubernetes.
It can be also run locally for development and test purpose.

The code is generated with the script `harness-application`.

## Configuration

### Accounts

The CloudHarness Django application template comes with a configuration that can retrieve user account updates from Keycloak (accounts)
To enable this feature:
* log in into the accounts admin interface
* select in the left sidebar Events
* select the `Config` tab
* enable "metacell-admin-event-listener" under the `Events Config` - `Event Listeners`

An other option is to enable the "metacell-admin-event-listener" through customizing the Keycloak realm.json from the CloudHarness repository.

## Develop

This application is composed of a Django-Ninja backend and a React frontend.

### Backend

Backend code is inside the *backend* directory.
See [backend/README.md#Develop]

### Frontend

Frontend code is inside the *frontend* directory.

Frontend is by default generated as a React web application, but no constraint about this specific technology.

See also [frontend/README.md]

#### Generate API client stubs
All the api stubs are automatically generated in the [frontend/rest](frontend/rest) directory by `harness-application`
and `harness-generate`.

To update frontend client stubs, run

```
harness-generate clients __APP_NAME__ -t
```

Stubs can also be updated using the `genapi.sh` from the api folder.

## Local build & run

### Install Python dependencies 
1 - Clone cloud-harness into your project root folder 

2 - Run the dev setup script
```
cd applications/__APP_NAME__
source dev-setup.sh
```

### Prepare backend

Create a Django local superuser account, this you only need to do on initial setup
```bash
cd backend
python3 manage.py migrate # to sync the database with the Django models
python3 manage.py collectstatic --noinput # to copy all assets to the static folder
python3 manage.py createsuperuser
# link the frontend dist to the django static folder, this is only needed once, frontend updates will automatically be applied
cd static/www
ln -s ../../../frontend/dist dist
```

### Run frontend

- `yarn dev` Local dev with no backend (no or mock data, cookie required)
- `yarn start` Local dev with backend on localhost:8000 -- see next paragraph (cookie required)
- `yarn start:dev` Local dev with backend on the remote dev deployment  (cookie required)
- `yarn start:local` Local dev with backend on the local dev deployment on mnp.local (cookie required)

To obtain the login cookie, login in the application with the forwarded backend, copy the `kc-access` cookie and set it into localhost:9000

### Run backend application

start the Django server

```bash
ACCOUNTS_ADMIN_PASSWORD=metacell ACCOUNTS_ADMIN_USERNAME=admin CH_CURRENT_APP_NAME=__APP_NAME__ CH_VALUES_PATH=../../../deployment/helm/values.yaml DJANGO_SETTINGS_MODULE=django_baseapp.settings KUBERNETES_SERVICE_HOST=a uvicorn --host 0.0.0.0 --port 8000 django_baseapp.asgi:application
```

Before running this backend, have to:
- Run `harness-deployment ... -n [NAMESPACE] -i __APP_NAME__` with the setup 
- port-forward keycloak and the database (see below)

### Running local with port forwardings to a kubernetes cluster
When you create port forwards to microservices in your k8s cluster you want to forced your local backend server to initialize
the AuthService and EventService services.
This can be done by setting the `KUBERNETES_SERVICE_HOST` environment variable to a dummy or correct k8s service host.
The `KUBERNETES_SERVICE_HOST` switch will activate the creation of the keycloak client and client roles of this microservice.

Run `port-forward.sh` to get the keycloak and database running.

To access those have to map to the hosts file:

```
127.0.0.1 accounts.[NAMESPACE] __APP_NAME__-db
```

After running the backend on port 8000, run `yarn start` to get a frontend to it

#### Vs code run configuration

Run configuration is automatically generated for VS code (__APP_NAME__ backend)