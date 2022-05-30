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
```

**Available Attributes**

`auto`: If true, db will be automatically deployed in the cluster

`type`: Specifies which DB technology to use, allowed values: `mongo`, `postgres`, `neo4j`

`size`: Size of the persistent volume that the database container mounts, default is set to `1Gi`

`image_ref`: Optional setting, used for referencing an image from the build. The image name will automagically being generated from the values.yaml file. This setting overrides the image setting of the database setting.


## Configuring Backups

Per default, database backups are disabled. However, you can overwrite backups by overwriting the `values-template.yaml`, as described in [Extend CloudHarness](Extend-CloudHarness#overwrite-helm-chart-configuration).


**Example:**  `deployment-configuration/values-template.yaml`

```yaml
backup:
    active: true
```

You can find additional configuration fields for backups to overwrite in the generated `deployment/helm/values.yaml` once you deploy your applications.

Backups are defined for `mongo` and `postgres` database in form of a [K8s CronJob](https://kubernetes.io/docs/concepts/workloads/controllers/cron-jobs/) that creates a dump of the database and stores it in a different persistent volume on the same cluster.

This is done periodically according to a configurable schedule, per default once a day.



### MongoDB

`mongodump` is used to create a gzipped archive file of the complete database.

Further reading: [MongoDB archiving & compression](https://www.mongodb.com/blog/post/archiving-and-compression-in-mongodb-tools), [MongoDB Backup methods](https://docs.mongodb.com/manual/core/backups/), [mongodump](https://docs.mongodb.com/database-tools/mongodump/)


### Postgres

`pg_dumpall` is used to create for each database a gzipped script.

Further reading: [pg_dumpall docs](https://www.postgresql.org/docs/10/app-pg-dumpall.html)


### Neo4j

Not yet supported!
