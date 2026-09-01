# Dockerfile with ARG/FROM and an ARG not used by a FROM
ARG mybase=foo:bar
ARG mybase2=spam:egg
ARG mybase3=not:referenced

FROM ${mybase}
FROM $mybase2
