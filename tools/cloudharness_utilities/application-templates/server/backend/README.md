# __APP_NAME__

## Run
```bash
pip install -r requirements.txt
pip install -e .
python __main__.py
```

## Develop
The backend is a Python Flask application.
Connexion library maps the apis from the openapi definition to the Flask routing.

### Implement api functions
Api functions are all defined inside [__APP_NAME__/controllers](__APP_NAME__/controllers).
Function stubs are automatically generated: just replace your function body with the desired code.
Since the stubs are automatically generated, using other modules outside the controllers as helpers and services to 
implement the code logic is recommended.

### Add api functions

1. Edit [../api/openapi.yaml](api/openapi.yaml) as needed
1. Remove/comment the controllers exclusion on [.openapi-generator-ignore](.openapi-generator-ignore) file
1. Run `harness-generate .` from your deployment root
1. Merge the files inside [__APP_NAME__/controllers](__APP_NAME__/controllers). For instance, you can 
   use git or ide history)
1. Restore the [.openapi-generator-ignore](.openapi-generator-ignore) file