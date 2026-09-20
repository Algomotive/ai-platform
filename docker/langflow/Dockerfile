# =============================================================================
# LangFlow — production image.
# Wraps the upstream LangFlow image with a dispatching entrypoint that runs
# either the gunicorn web tier ("web") or a Celery worker ("worker").
# =============================================================================
ARG LANGFLOW_IMAGE=langflowai/langflow:1.10.1

FROM ${LANGFLOW_IMAGE}

USER root

# Create the persistent config/state dir owned by the image's runtime user
# (uid 1000, group root). A freshly-created named volume mounted here inherits
# this ownership, so LangFlow can write its secret_key / DB without running as
# root.
RUN mkdir -p /var/lib/langflow \
    && chown -R 1000:0 /var/lib/langflow \
    && chmod -R g+rwX /var/lib/langflow

# Bring in our entrypoints (world-readable/executable so the image's existing
# non-root user can run them). The web tier is launched via `langflow run`,
# which serves the UI + API and manages gunicorn/uvicorn workers itself.
COPY --chmod=0755 entrypoint.sh /opt/aiplatform/entrypoint.sh
COPY --chmod=0755 worker-entrypoint.sh /opt/aiplatform/worker-entrypoint.sh

# File-parsing deps for the Cosmic AR File Intake Flow (ADR-0004): openpyxl reads
# Excel (.xlsx/.xlsm/.xls), pdfplumber reads PDF. CSV uses stdlib and needs no dep.
# Installed as root before dropping to USER 1000. A `langflow`/`langflow-worker`
# image rebuild is required to exercise Excel/PDF reading at runtime
# (`docker compose build langflow langflow-worker`); compose config is unaffected.
# Pins are minor-bounded to stay compatible with the image's Python.
RUN pip install --no-cache-dir \
      "openpyxl>=3.1,<4" \
      "pdfplumber>=0.11,<0.12"

ENV LANGFLOW_CONFIG_DIR=/var/lib/langflow \
    PYTHONUNBUFFERED=1

EXPOSE 7860 9090

# Algomotive Workflow Studio identity overlay.
# Keep this layer limited to stable frontend entry assets. Hashed application
# bundles remain owned by the pinned upstream Langflow image.
COPY --chmod=0644 algomotive/favicon.ico \
    /app/.venv/lib/python3.14/site-packages/langflow/frontend/favicon.ico
COPY --chmod=0644 algomotive/algomotive-favicon-v1.png \
    /app/.venv/lib/python3.14/site-packages/langflow/frontend/algomotive-favicon-v1.png
COPY --chmod=0644 algomotive/manifest.json \
    /app/.venv/lib/python3.14/site-packages/langflow/frontend/manifest.json
COPY --chmod=0644 algomotive/algomotive-mark.svg \
    /app/.venv/lib/python3.14/site-packages/langflow/frontend/assets/algomotive-mark.svg
COPY --chmod=0644 algomotive/algomotive-wordmark-dark.svg \
    /app/.venv/lib/python3.14/site-packages/langflow/frontend/assets/algomotive-wordmark-dark.svg
COPY --chmod=0644 algomotive/patch_frontend.py \
    /opt/aiplatform/patch-langflow-frontend.py
COPY --chmod=0644 algomotive/workspace_controls.js \
    /app/.venv/lib/python3.14/site-packages/langflow/frontend/assets/algomotive-workspace-shell-v12.js

RUN python /opt/aiplatform/patch-langflow-frontend.py

RUN python - <<'PY'
from pathlib import Path

index = Path(
    "/app/.venv/lib/python3.14/site-packages/langflow/frontend/index.html"
)
text = index.read_text(encoding="utf-8")

old = "<title>Langflow</title>"
new = "<title>Algomotive Workflow Studio</title>"

if old not in text:
    raise RuntimeError("Expected Langflow browser title was not found")

index.write_text(text.replace(old, new, 1), encoding="utf-8")

if new not in index.read_text(encoding="utf-8"):
    raise RuntimeError("Algomotive browser title overlay was not applied")
PY

# Drop back to the non-root runtime user.
USER 1000

ENTRYPOINT ["/opt/aiplatform/entrypoint.sh"]
CMD ["web"]
