# Application Volume

Application Volumes are defined at `harness.deployment.volume`.
At the time of writing this documentation CloudHarness supports only one volume per deployment.

The Application Volume will be mounted in the container at a specific path at **deployment** time.

A Volume can be mounted by one or more pods (shared Volume). Be careful: only one of the deployments
should create the Volume, the other deployment should only mount it.

This can be established through setting the `auto` attribute (default false) of the Volume object
auto: true --> auto create the volume and mount
auto: false --> only mount the volume

Shared volumes are handy when you have e.g. 2 deployments for one app: frontend & backend deployment
in such a case it could be helpfull that the frontend can access files stored by the backend.
E.g. user uploaded media files

**Example**

```yaml
harness:
  ...
  deployment:
    ...
    volume:
      name: myFirstVolume
      mountpath: /usr/src/app/myvolume
      auto: true
      size: 5Gi
```
