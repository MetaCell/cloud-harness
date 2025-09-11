load('{{ch_root}}/deployment-configuration/tilt-deploy.ext', 'deploy')
load('ext://uibutton', 'cmd_button')

config.define_bool('setup-infrastructure')
cfg = config.parse()
setup_infrastructure = cfg.get('setup-infrastructure', False)
if setup_infrastructure:
    # setup ingress
    print("Installing ingress controller")
    local("cd infrastructure/cluster-configuration && source cluster-init.sh")
    print("Let's wait a few seconds...")
    local("sleep 30")
else:
    print("To setup the infrastructure (f.e. ingress controller)")
    print("run: tilt up -- --setup-infrastructure")

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
deploy(name='{{name}}', namespace='{{namespace}}', extra_env=extra_env)

{% for app in apps -%}
# Add Tilt ui elements for: {{app.name}}
k8s_resource(
    '{{app.name}}',
    links=[link('http://{{app.name}}.{{domain}}', 'Open {{app.name}} page')]
)
cmd_button('{{app.name}}:set debug mode',
    argv=["sh", "-c", "kubectl patch deployment {{app.name}} -n {{namespace}} --type='json' -p='[{\"op\": \"replace\", \"path\": \"/spec/template/spec/containers/0/command\", \"value\": [\"/bin/bash\", \"-c\", \"sleep infinity\"]}]'"],
    resource='{{app.name}}',
    icon_name='bug_report',
    text='set debug mode',
)
{% endfor %}
