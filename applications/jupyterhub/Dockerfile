FROM jupyterhub/k8s-hub:0.9.0
USER root
# COPY . .
# COPY deploy/resources/hub/* /etc/jupyterhub/

# RUN pip install -e ./kubespawner
USER jovyan
# CMD ["jupyterhub", "--config", "/srv/jupyterhub_config.py"]