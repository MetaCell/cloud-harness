# __APP_NAME__

FastAPI/Django/React-based web application.
This application is constructed to be deployed inside a cloud-harness Kubernetes.
It can be also run locally for development and test purpose.

The code is generated with the script `harness-application` and is in part automatically generated 
from [openapi definition](./api/openapi.yaml).

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

This application is composed of a FastAPI Django backend and a React frontend.

### Backend

Backend code is inside the *backend* directory.
See [backend/README.md#Develop]

### Frontend

Backend code is inside the *frontend* directory.

Frontend is by default generated as a React web application, but no constraint about this specific technology.

#### Call the backend apis
All the api stubs are automatically generated in the [frontend/rest](frontend/rest) directory by `harness-application`
and `harness-generate`.

#### Update the backend apis from openapi.yaml
THe backend openapi models and main.py can be updated using the `genapi.sh` from the api folder.

## Local build & run

### Install dependencies 
1 - Clone cloud-harness into your project root folder 

2 - Install cloud-harness requirements
```
cd cloud-harness
bash install.sh
```

3 - Install cloud-harness common library
```
cd libraries/cloudharness-common
pip install -e .
```

4 - Install cloud-harness common library
```
cd libraries/cloudharness-common
pip install -e .
```

5 - Install cloud-harness django library
```
cd ../cloudharness-django
pip install -e .
```

6 - Install cloud-harness fastapi requirements
```
cd ../fastapi
pip install -r requirements.txt
```

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

Compile the frontend
```bash
cd frontend
npm install
npm run build
```


sync the Django models with the database and collect all other assets
```bash
cd ../backend
python3 manage.py migrate # to sync the database with the Django models
python3 manage.py collectstatic --noinput # to copy all assets to the static folder
```

start the FastAPI server
```bash
uvicorn --workers 2 --host 0.0.0.0 --port 8000 main:app
```
