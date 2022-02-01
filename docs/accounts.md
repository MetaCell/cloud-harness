## Manage user accounts
A user account must be provided to access to the MNP secured applications.

1. Login to the administration console on https://accounts.MYDOMAIN with user `admin`:`metacell`. 

> Change the password immediately if you are on a production environment!
2. Add a user (menu Users on the left)
1. Set a password to the user (tab credentials). Set temporary as *off*
1. On Role Mappings, assign all roles to the user

## Configure a Gatekeeper

To put a gatekeeper in front of your application, set `harness/secured` to `true`
in the application's values.yaml.

To assign paths and roles, set `uri_role_mapping` as you would do in the [gatekeeper configuration file resources](https://github.com/gogatekeeper/gatekeeper/blob/master/docs/user-guide.md#configuration-options).

Example:

```yaml
harness:
  ...
  secured: true
  uri_role_mapping:
  - uri: /*
    roles:
    - administrator
```

See the [Gogatekeeper official documentation](https://github.com/gogatekeeper/gatekeeper/blob/master/docs/user-guide.md) for more.