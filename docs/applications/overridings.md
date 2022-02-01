# How to override an application

Solutions built upon Cloudharness can use the default applications as they are or override them to customize for example the configuration, the image or the theming.

To override an application in your solution, can create an application with the same name.

## Configuration changes
The `values.yaml` file values from the original application will be overridden by the new ones.

For instance:

cloud-harness/applications/accounts/deploy/values.yaml:

```yaml
harness:
  subdomain: accounts
  secured: false
  deployment:
    auto: true
    port: 8080
```

my-solution/applications/accounts/deploy/values.yaml:

```yaml
harness:
  deployment:
    port: 8000
```

Resulting configuration after calling `harness-deployment cloud-harness my-solution`:

```yaml
harness:
  subdomain: accounts
  secured: false
  deployment:
    auto: true
    port: 8000
```

> Notice: the precedence of the applications is defined by the order of the paths given
> to the `harness-deployment` command (latter overrides the former). Calling `harness-deployment my-solution cloud-harness` would have resulted in no overridings.

## Other files changes

Files included as resources or copied in the Dockerfile can also be overridden.
Differently from the values file, no merging strategy is applied to other files.
New files will replace the original file.

A special case is when the `Dockerfile` is overridden:
by default, original application files are not included in the deployment of the overridden application in so if any of the original file is required, can either 
copy all the required files in the overridden application or use the `--merge` (`-m`)
parameter when calling `harness-deployment`.

For instance, calling 
`harness-deployment cloud-harness . -m build` all the files pertaining to the build process are copied in the `./build` directory: at first, applications from cloud-harness are copied, then applications from the current directory are copied, so eventually overriding previously existing files.