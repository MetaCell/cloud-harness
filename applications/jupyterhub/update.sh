git clone -n git@github.com:jupyterhub/zero-to-jupyterhub-k8s.git
git checkout jupyterhub
git checkout chartpress.yaml
pip install chartpress
cd zero-to-jupyterhub-k8s
chartpress -t $1 
cd ..
cp -R zero-to-jupyterhub-k8s/jupyterhub/templates/* deploy/templates
cp zero-to-jupyterhub-k8s/jupyterhub/files/hub/* deploy/resources/hub
cp zero-to-jupyterhub-k8s/jupyterhub/values* deploy
cd deploy

rm -Rf templates/proxy/autohttps # Proxy is not used as node balancer
rm templates/ingress.yaml # Default cloudharness ingress is used
# Command to replace everything like files/hub/ inside deploy/templates with resources/jupyterhub/hub/
find templates -type f -exec sed -i 's/files\/hub/resources\/jupyterhub\/hub/g' {} \;

# replace .Values.hub. with .Values.hub.config with .Values.apps.jupyterhub.hub
find templates -type f -exec sed -i 's/.Values./.Values.apps.jupyterhub./g' {} \;

# replace .Values.apps.jupyterhub.hub.image with .Values.apps.jupyterhub.harness.deployment.image
find templates -type f -exec sed -i 's/{{ .Values.apps.jupyterhub.hub.image.name }}:{{ .Values.apps.jupyterhub.hub.image.tag }}/{{ .Values.apps.jupyterhub.harness.deployment.image }}/g' {} \;



find templates -type f -exec sed -i 's$.Template.BasePath "/hub$.Template.BasePath "/jupyterhub/hub$g' {} \;
find templates -type f -exec sed -i 's$.Template.BasePath "/proxy$.Template.BasePath "/jupyterhub/proxy$g' {} \;
find templates -type f -exec sed -i 's$.Template.BasePath "/scheduling$.Template.BasePath "/jupyterhub/scheduling$g' {} \;
