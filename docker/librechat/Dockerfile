# =============================================================================
# Algomotive-branded LibreChat frontend
#
# Preserves the tested upstream API, entrypoint, runtime user, data paths, and
# authentication behavior while rebuilding only the customer-facing frontend.
# =============================================================================
ARG LIBRECHAT_IMAGE=ghcr.io/danny-avila/librechat:latest

FROM ${LIBRECHAT_IMAGE}

USER root

# Controlled Algomotive authentication source overrides.
COPY --chown=node:node algomotive/src/components/Auth/AuthLayout.tsx \
  /app/client/src/components/Auth/AuthLayout.tsx
COPY --chown=node:node algomotive/src/components/Auth/algomotive-auth.css \
  /app/client/src/components/Auth/algomotive-auth.css
COPY --chown=node:node algomotive/src/routes/Layouts/Startup.tsx \
  /app/client/src/routes/Layouts/Startup.tsx
COPY --chown=node:node algomotive/src/components/Chat/Footer.tsx \
  /app/client/src/components/Chat/Footer.tsx
COPY --chown=node:node algomotive/src/locales/en/translation.json \
  /app/client/src/locales/en/translation.json

# Browser and progressive web application identity.
COPY --chown=node:node algomotive/index.html \
  /app/client/index.html
COPY --chown=node:node algomotive/public/manifest.webmanifest \
  /app/client/public/manifest.webmanifest
COPY --chown=node:node algomotive/public/assets/ \
  /app/client/public/assets/

# The upstream runtime image omits frontend development tools such as Vite.
# Restore the lockfile-defined development dependencies only during image build.
# The final runtime still starts with the upstream entrypoint as USER node.
RUN npm ci --include=dev \
  && cd /app/client \
  && npm run build \
  && cp /app/client/public/manifest.webmanifest /app/client/dist/manifest.webmanifest \
  && test -s /app/client/dist/index.html \
  && test -s /app/client/dist/manifest.webmanifest \
  && grep -q "Algomotive AI Operations Platform" /app/client/dist/index.html \
  && grep -q "Algomotive AI Operations Platform" /app/client/dist/manifest.webmanifest

USER node
