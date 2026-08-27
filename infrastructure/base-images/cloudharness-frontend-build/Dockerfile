FROM node:22-alpine

# The bundled classic yarn (1.22) has no release-age gate; that setting needs yarn >= 4.10.
# Pinned so CI and developer machines agree on one version.
ENV COREPACK_ENABLE_DOWNLOAD_PROMPT=0
RUN corepack enable && corepack prepare yarn@4.18.0 --activate

# Keep the classic node_modules layout: vite, eslint and jest resolve through it.
ENV YARN_NODE_LINKER=node-modules

# Supply chain cooldown: ignore package versions published less than 7 days ago,
# mirroring the pip --uploaded-prior-to=P7D quarantine window. Yarn's own default is 1 day.
# Exempt a package with npmPreapprovedPackages in the application .yarnrc.yml.
ENV YARN_NPM_MINIMAL_AGE_GATE=7d
