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

#### Call the backend apis
All the api stubs are automatically generated in the [frontend/rest](frontend/rest) directory by `harness-application`
and `harness-generate`.

## Local build & run

### Install dependencies 
1 - Clone cloud-harness into your project root folder 

2 - Run the dev setup script
```
cd applications/__APP_NAME__
bash dev-setup.sh
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

### Build frontend

Compile the frontend
```bash
cd frontend
npm install
npm run build
```

### Run backend application

start the Django server
```bash
uvicorn --workers 2 --host 0.0.0.0 --port 8000 django_baseapp.asgi:application
```


### Running local with port forwardings to a kubernetes cluster
When you create port forwards to microservices in your k8s cluster you want to forced your local backend server to initialize
the AuthService and EventService services.
This can be done by setting the `KUBERNETES_SERVICE_HOST` environment variable to a dummy or correct k8s service host.
The `KUBERNETES_SERVICE_HOST` switch will activate the creation of the keycloak client and client roles of this microservice.
