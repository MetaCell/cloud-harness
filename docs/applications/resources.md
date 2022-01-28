# Resources

Resources files can be added in a `resources` folder inside the `deploy` folder.

Resources will be mounted in the container at a specific path at **deployment** time.

Currently, we support `json` and `yaml` resource files.

Resources are defined at `harness.resources`.
Each resource must consist of a `name`, a `src` path and a `dst` path.

**Example**

```yaml
harness:
  ...
  resources:
    - name: my-config
      src: "myConfig.json"
      dst: "/tmp/resources/myConfig.json"
    - name: example
      src: "example.yaml"
      dst: "/usr/src/app/important_config.yaml"
```