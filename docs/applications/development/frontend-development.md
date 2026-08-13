# Develop in the frontend with CloudHarness

## Set up yarn

CloudHarness frontends are built with yarn 4, pinned through the `packageManager` field
of each `package.json`. The `yarn` shipped with Node is still 1.22 and cannot read the
lock files, so enable [corepack](https://yarnpkg.com/corepack) once:

```bash
corepack enable
```

Until you do, yarn refuses to run and prints this same instruction. Never use npm for a
frontend.

Installs are subject to the 7 day [dependency cooldown](../../dependency-cooldown.md):
a package version published in the last week will not be resolved. Use
`harness-generate dependencies` to audit and refresh the lock files.

## Base images and libraries
TODO 

## Create a default Frontend with React and Openapi

Can use a webapp application template, see [here](../harness-application.md).

## Authentication and Authorization

The preferred method is to use and configure a [gatekeeper](../../accounts#configure-a-gatekeeper).

Another option is using the [Keycloak Javascript adapter](https://www.npmjs.com/package/keycloak-js).
