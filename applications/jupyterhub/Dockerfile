FROM jupyterhub/k8s-hub:0.9.0
USER root

# COPY deploy/resources/hub/* /etc/jupyterhub/
# COPY src/jupyterhub/jupyterhub/handlers/* /usr/local/lib/python3.6/dist-packages/jupyterhub/handlers/
# COPY ./src/kubespawner /usr/local/lib/python3.6/dist-packages/
COPY src src
RUN pip install ./src/harness_jupyter
RUN chmod 777 /usr/local/lib/python3.6/dist-packages/  -R
USER jovyan


# CMD ["jupyterhub", "--config", "/srv/jupyterhub_config.py"]