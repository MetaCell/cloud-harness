# Application dependencies

Application dependencies can be specified in the main application configuration
file (deploy/values.yaml), in the `harness` section.

Example:
```yaml
harness:
  dependencies:
    build:
    - cloudharness-base
    soft:
    - app1
    hard:
    - accounts
    git:
    - url: https://github.com/a/b.git
      branch_tag: master
```

## Build dependencies

Build dependencies specify which images must be built before the current one.
Currently only base images and common images can be used as a build dependency.

See also [base and common images documentation](../base-common-images.md).

## Soft dependencies

Soft dependencies specify other applications (from your app or cloudharness) that
must be included in the deployment together with your application,
but are not a prerequisite for the application to bootstrap and serve basic functionality.

Soft dependencies are implicitly chained: if *A1* depends on *A2* and *A2* depends on *A3*,
all *A1*, *A2*, *A3* are included in the deployment if A1 is requested (say with
`harness-deployment ... -i A1`).

## Hard dependencies

Hard dependencies work similarly to soft dependencies but they are required for the 
application declaring the dependency to start and provide even basic functionality.

With a hard dependency, we are allowed to assume that the other application exists in the
configuration and during the runtime.

Note that Cloud Harness does not guarantee the the other application starts before the
application declaring the dependency because that's how Kubernetes works. The application
is supposed to crash in the absence of its dependency and Kubernetes will start the crash
loop until both applications are settled.

## Git (repository) dependencies

Git dependencies allow us to build and deploy applications that are defined in another repository.
This functionality is an alternative to the otherwise monorepo-centric view of CloudHarness-based
applications.

The repository is cloned before the build within skaffold build and the CI/CD inside the 
`dependencies` directory at the same level of the Dockerfile.

Hence, in the Dockerfile we are allowed to `COPY` or `ADD` the repository.

For instance, given the following configuration:
```yaml
harness:
  dependencies:
    git:
    - url: https://github.com/a/b.git
      branch_tag: master
    - url: https://github.com/c/d.git
      branch_tag: v1.0.0
      path: myrepo
```
> Note that the path parameter is optional and unnecessary unless name clashes occur, like same repo and different branches

The directory structure will be as following:
```
Dockerfile
dependencies
  b
  myrepo
   d
  .dockerignore
```

Hence, inside the Dockerfile we expect to see something like

```dockerfile
COPY dependencies .
```
or
```dockerfile
COPY dependencies/b/src .
COPY dependencies/myrepo/d .
```

> Note that Cloud Harness does not add the COPY/ADD statements to the Dockerfile