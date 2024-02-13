
### The first thing to check

> Make sure you have JDK installed in your WSL system. Without this, the code is not generated! (with harness-application command). A bunch of errors that I had was solved by this step. In addition, test if you have all the basic requirements needed for the Cloud-Harness + other requirements needed to set up.

Please check if you are running **Kubernetes with Docker Desktop.**

If you have Codecloud VS extension, make sure to check that you have docker-desktop ACTIVE. You can also check the namespace which by default is set to `default`

### Setting namespaces and with `docker-desktop` context

> The commands related to minikube from the tutorial are not needed in the case of docker-desktop.

We create namespaces inside docker-desktop… for our case of following the tutorial, it is azathoth

```
kubectl create ns azathoth
```

If want to change the namespace while keeping the context same (i.e. docker-desktop) then the following is the command. This is because the default namespace is `default`

```
kubectl config set-context --current --namespace=azathoth
```

### Deployment command distinction

Use the following command when you want your application installed inside the cloud-harness directory (very less likely; that one would use this)

```
harness-deployment . -u -dtls -l -d azathoth.local -e local -n azathoth
```

Otherwise (mostly how we use it)

```
harness-deployment cloud-harness . -u -dtls -l -d azathoth.local -e local -n azathoth
```

### About host file issue

To be able to visit links like - [http://clockdate.azathoth.local/](http://clockdate.azathoth.local/), or [http://clockdate.azathoth.local/api/ping](http://clockdate.azathoth.local/api/ping), we need to update the host file. Make note that the host file is of Windows (and not for the subsystem), which can be found here:

```
C:\Windows\System32\drivers\etc\hosts
```

(NOTE: We might be able to work with Linux hosts if we enable - *_Add the .docker.internal names to the host's etc/hosts file (Requires password)_ in the General settings of docker desktop. But I haven’t tested that. )

### If Running CLOUD HARNESS for the first time!

There are certain scripts that need to be run when running the CloudHarness and its dependent applications for the first time in a system. These are `sc.yaml` and `cluster-init.sh` which can be found in the following path w.r.t. cloud-harness.

```
kubectl apply -f cloud-harness/deployment/sc.yaml
```

```
cd cloud-harness/infrastructure/cluster-configuration && bash cluster-init.sh
```

These are one-time setup scripts needed to be run.

### About Frontend issues

If the [clockdate.azathoth.local](http://clockdate.azathoth.local/) doesn’t return the frontend part!

When the frontend is generated through the “harness-application”, the package-lock.json is required which is not mentioned in the docs. Therefore one must have to do the `npm i —legacy-peer-deps` before proceeding with the “scaffold run” command.


