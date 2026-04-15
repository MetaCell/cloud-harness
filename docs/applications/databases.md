## Configuring a Database

See [Application Templates](Application-Templates) for a list of supported databases.

The database can be configured in the application's values.yaml located in `applications/<your-application>/deploy/values.yaml`.


**Example**

```yaml
harness:
    ...
    database:
      auto: true
      type: mongo
      image_ref: myownpgimage'
      resources:
        requests:
          memory: "512Mi"
          cpu: "100m"
        limits:
          memory: "2Gi"
          cpu: "1000m"
```

**Available Attributes**

`auto`: If true, db will be automatically deployed in the cluster

`type`: Specifies which DB technology to use, allowed values: `mongo`, `postgres`, `neo4j`

`size`: Size of the persistent volume that the database container mounts, default is set to `1Gi`

`resources`: Set the database pod resources

`image_ref`: Optional setting, used for referencing a base/static image from the build. The complete image name with tag will automagically being generated from the values.yaml file. This setting overrides the `image` setting specific for the database type (e.g. postgres/image). Note: the referenced image must be included as a build dependency in order to be built by the pipelines.

`expose`: This option allows you to expose the database port through a load balancer.
Do not use on production!


### Specific database settings

Specific database settings are defined using the database key:

```yaml
harness:
    ...
    database:
      [mongo/postgres/neo4j]:
        image:
        ports:
```

**Common settings**

`image`: specifies the default static image (must be a publicly available image with full tag)

`ports`: specify one or more ports that are exposed by the database

#### MongoDB

Defaults:

```yaml
harness
  database:
    mongo:
      image: mongo:5
      ports:
        - name: http
          port: 27017
```



#### Postgres

Defaults:

```yaml
harness
  database:
    postgres:
      image: postgres:13
      initialdb: cloudharness
      operator: false
      instances: 1
      apiServerCidr: []
      ports:
        - name: http
          port: 5432
```

`initialdb` is the default database used

`operator`: When set to `true`, uses the [CloudNative-PG operator](https://github.com/cloudnative-pg/cloudnative-pg) instead of a plain Kubernetes Deployment. This provides advanced features like automated failover and cluster management. **Backups are not configured by default by this chart; you must define CNPG backup resources (for example, `Backup` and/or `ScheduledBackup` objects) or use another backup mechanism separately.** **Requires the CNPG operator to be pre-installed in the cluster.**

To install the CNPG operator:
```bash
helm repo add cloudnative-pg https://cloudnative-pg.github.io/charts
helm repo update
helm install cnpg cloudnative-pg/cloudnative-pg
```

`instances`: Number of PostgreSQL instances (replicas) managed by the CNPG operator. Only used when `operator: true`. Default is 1.

`apiServerCidr`: List of CIDRs allowed for CNPG database pods to reach the Kubernetes API server on port 443. **Resolved automatically at deploy time** by looking up the `kubernetes` Service and Endpoints in the `default` namespace. The explicit list is only used as a fallback when lookup returns nothing (e.g. `helm template` dry-run). Leave empty (`[]`) for auto-detection; set explicitly only for air-gapped or restricted environments.


#### Neo4j

Defaults:
```yaml
harness
  database:
    neo4j:
      dbms_security_auth_enabled: "false"
      image: neo4j:5
      memory:
        heap: { initial: 64M, max: 128M }
        pagecache: { size: 64M }
        size: 256M
        ports:
          - { name: http, port: 7474 }
          - { name: bolt, port: 7687 }
```

Not that the default resource values are not optimized and increasing the default memory is recommended for production.
Mapping memory configuration with Kubernetes resource requests is also recommended.

## Programmatic API

The programmatic API allows you to get the connection string used to configure the database driver (e.g. psycopg2)

Example:

from cloudharness import applications
db_connection_string = applications.get_current_configuration().get_db_connection_string()

## Configuring Backups

Per default, database backups are disabled. However, you can overwrite backups by overwriting the `values-template.yaml`, as described in [Extend CloudHarness](Extend-CloudHarness#overwrite-helm-chart-configuration).


**Example:**  `deployment-configuration/values-template.yaml`

```yaml
backup:
  active: true
```

See all the default values [here](../../deployment-configuration/helm/values.yaml).
You can find additional configuration fields for backups to overwrite in the generated `deployment/helm/values.yaml` once you deploy your applications.

Backups are defined for `mongo` and `postgres` database in form of a [K8s CronJob](https://kubernetes.io/docs/concepts/workloads/controllers/cron-jobs/) that creates a dump of the database and stores it in a different persistent volume on the same cluster.

This is done periodically according to a configurable schedule, per default every 5 minutes.

A smart retention strategy is used for backups, by default:
- all current days backups
- one per day, last 7 days
- one per week, last 4 weeks
- one per month, last 6 months

Implementation of backups and retention is based on https://github.com/prodrigestivill/docker-postgres-backup-local.

#### How to monitor and restore backups

Backups are stored in a Kubernetes volume named `db-backups`.

Can mount the volume to your database pod by adding the following to your db deployment:

```yaml
...
spec:
  template:
    spec:
      containers:
      - ...
        volumeMounts:
        - name: "db-backups"
          mountPath: /backups
          readOnly: true
      ...
      volumes:
      ...
      - name: "db-backups"
        persistentVolumeClaim:
          claimName: "db-backups"
```



### MongoDB


`mongodump` is used to create a gzipped archive file of the complete database.

Further reading: [MongoDB archiving & compression](https://www.mongodb.com/blog/post/archiving-and-compression-in-mongodb-tools), [MongoDB Backup methods](https://docs.mongodb.com/manual/core/backups/), [mongodump](https://docs.mongodb.com/database-tools/mongodump/)


### Postgres

`pg_dumpall` is used to create for each database a gzipped script.

Further reading: [pg_dumpall docs](https://www.postgresql.org/docs/10/app-pg-dumpall.html)



