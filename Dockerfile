# OdorSig reproducible environment.
#
# Pins the same external tool versions recorded in environment_lock.txt
# (AutoDock Vina, Open Babel, PyMOL) plus the Python dependencies in
# requirements.txt, so the pipeline and test suite run the same way
# regardless of host machine.
#
# Build:
#   docker build -t odorsig .
# Run the test suite:
#   docker run --rm odorsig pytest -v
# Run the Streamlit app (exposes port 8501):
#   docker run --rm -p 8501:8501 -e ODORSIG_ENTREZ_EMAIL=you@example.com odorsig \
#       streamlit run code/app.py
#
# Note: Step_01/Step_02 (NCBI Entrez, SWISS-MODEL via Selenium) still need a
# real Entrez contact email (ODORSIG_ENTREZ_EMAIL) and outbound network
# access at *runtime* — this image does not bundle a Chrome/Chromedriver
# pair, since Selenium Manager resolves one automatically on first use.

FROM python:3.11-slim

# --- Pinned external tools (see environment_lock.txt) ----------------------
# NOTE (unverified): this image has not been build-tested in this
# environment (no Docker available here). AutoDock Vina below is pinned to
# an exact release binary and follows the same download pattern already
# exercised successfully in .github/workflows/ci.yml. Open Babel and PyMOL,
# however, are installed from Debian's apt repository, whose package
# versions do not track upstream releases 1:1 -- `apt-get install
# openbabel=3.1.1*`/`pymol=3.1.0*` may simply not resolve on this base
# image's Debian release. Before relying on this image, build it and run
# `obabel -V` / `pymol -cq -d "print(cmd.get_version())"` inside a container
# to confirm the installed versions actually match environment_lock.txt
# (openbabel 3.1.1 / pymol-open-source 3.1.0); pin via a different apt
# source, conda-forge, or building from source if they don't.
ARG VINA_VERSION=1.2.7

RUN apt-get update && apt-get install -y --no-install-recommends \
        wget \
        ca-certificates \
        openbabel \
        pymol \
    && rm -rf /var/lib/apt/lists/*

# AutoDock Vina is distributed as a standalone binary, not an apt/pip package.
RUN wget -q \
        "https://github.com/ccsb-scripps/AutoDock-Vina/releases/download/v${VINA_VERSION}/vina_${VINA_VERSION}_linux_x86_64" \
        -O /usr/local/bin/vina \
    && chmod +x /usr/local/bin/vina \
    && vina --version

WORKDIR /app

# --- Python dependencies ----------------------------------------------------
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir pytest

COPY . .

# Runtime directories (see code/Automation_code/config.py) default under
# /app; override ODORSIG_BASE_DIR to use a mounted volume instead.
ENV ODORSIG_BASE_DIR=/app/runs

CMD ["pytest", "-v"]
