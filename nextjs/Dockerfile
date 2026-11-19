ARG NODE_IMAGE
FROM ${NODE_IMAGE} AS build
WORKDIR /srv/build
COPY nextjs/package.json nextjs/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY nextjs/next.config.mjs ./
COPY nextjs/app ./app
COPY nextjs/lib ./lib
ENV NEXT_TELEMETRY_DISABLED=1 NODE_ENV=production
RUN npm run build

FROM ${NODE_IMAGE}
ENV NODE_ENV=production NEXT_TELEMETRY_DISABLED=1 HOSTNAME=0.0.0.0 PORT=8080
WORKDIR /srv/app
COPY --from=build /srv/build/.next/standalone ./
COPY --from=build /srv/build/.next/static ./.next/static
COPY nextjs/cluster.cjs ./cluster.cjs
USER node
ENTRYPOINT ["node", "cluster.cjs"]
