load('{{ch_root}}/deployment-configuration/tilt-deploy.ext', 'deploy')
load('ext://uibutton', 'cmd_button')

config.define_bool('setup-infrastructure')
config.define_bool('watch')
cfg = config.parse()
setup_infrastructure = cfg.get('setup-infrastructure', False)
watch = cfg.get('watch', False)
if setup_infrastructure:
    # setup ingress
    print("Installing ingress controller")
    # local("cd infrastructure/cluster-configuration && source cluster-init.sh")
    local("kubectl get namespace ingress-nginx 2>/dev/null 1>/dev/null || bash -c 'helm upgrade --install ingress-nginx ingress-nginx --repo https://kubernetes.github.io/ingress-nginx --namespace ingress-nginx --create-namespace --version v4.2.5 && sleep 10'")
    # print("Let's wait a few seconds...")
    # local("sleep 30")
else:
    print("To setup the infrastructure (f.e. ingress controller)")
    print("run: tilt up -- --setup-infrastructure")

if not watch:
    print("To watch file changes, run: tilt up -- --watch")


# build images
{% for image in images -%}
docker_build(ref='{{image.image}}', context='{{image.context}}', dockerfile='{{image.docker.dockerfile}}', build_args={{image.docker.buildArgs}}{% if image.is_task %}, match_in_env_vars=True{% endif %})
{% endfor %}

extra_env = {}
{% for image in images -%}
{% if image.is_app -%}
extra_env.setdefault("{{ image.name }}", [])
{% for task in images -%}
{% if task.is_task and task.parent_app_name == image.name -%}
extra_env["{{ image.name }}"].append("{{ task.image }}")
{% endif -%}
{% endfor -%}
{% endif -%}
{% endfor %}

# deploy
deploy(name='{{name}}', namespace='{{namespace}}', extra_env=extra_env, watch=watch)

{% for app in apps -%}
# Add Tilt ui elements for: {{app.name}}
k8s_resource(
    '{{app.app_key}}',
    links=[link('http://{{app.name}}.{{domain}}', 'Open {{app.name}} page')]
)
cmd_button('{{app.app_key}}:set debug mode',
    argv=["sh", "-c", "kubectl -n {{namespace}} patch deployment {{app.app_key}} --patch '{\"spec\": {\"template\": {\"spec\": {\"containers\": [{\"name\": \"{{app.app_key}}\", \"command\": [\"/bin/bash\"], \"args\": [\"-c\", \"sleep infinity\"], \"livenessProbe\": null, \"readinessProbe\": null}]}}}}'"],
    resource='{{app.app_key}}',
    icon_name='bug_report',
    text='set debug mode',
)
{% endfor %}
