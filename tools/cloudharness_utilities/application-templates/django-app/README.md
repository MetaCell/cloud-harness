# __APP_NAME__

Flask/React-based web application.
This application is constructed to be deployed inside a cloud-harness Kubernetes.
It can be also run locally for development and test purpose.

The code is generated with the script `harness-application` and is in part automatically generated 
from [openapi definition](./api/config.json).

## Run with Docker

```bash
docker build . -t __APP_NAME__
docker run -it -p 8080:8080 __APP_NAME__
```

Prerequisite: the cloudharness-frontend-build image must be built first:

```bash
cd [CLOUDHARNESS_ROOT]
docker build . -f infrastructure/base-images/cloudharness-frontend-build/Dockerfile -t cloudharness-frontend-build 
```

## Develop

This application is composed of a Flask backend and a React frontend.

### Backend

Backend code is inside the *backend* directory.
See [backend/README.md#Develop]

### Frontend

Backend code is inside the *frontend* directory.

Frontend is by default generated as a React web application, but no constraint about this specific technology.

#### Build and run

To run in development mode:
```bash
cd frontend
npm install
npm run start
```
This setup will start the application at http://localhost:9000. use the backend running at http://localhost:5000.
The backend can be either started from code or from Docker.
In that case the launch command needs to match the port with:

```bash
docker run -it -p 5000:8080 __APP_NAME__
```

#### Call the backend apis
All the api stubs are automatically generated in the [frontend/rest](frontend/rest) directory by `harness-application`
and `harness-generate`.

## Local run
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
