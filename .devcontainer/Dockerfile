FROM python:3.13-bullseye@sha256:99979462fff2e165877ea3d7f341988d36bce0e9b3f21c00574141ca5b53fe14
RUN pip install --no-cache-dir --upgrade pip==24.3.1 setuptools==75.8.0 wheel==0.45.1 \
    && pip install --no-cache-dir uv

ENV PYTHONPATH=${PYTHONPATH}:/workspaces/expense-bot/src

RUN groupadd docker && \
    useradd -r -u 1001 -g docker vscode && \
    mkdir -p /home/vscode && \
    chown -R vscode:docker /home/vscode

RUN apt-get update \
    && apt-get -y install --no-install-recommends apt-utils dialog 2>&1 \
    #
    # Verify git, process tools, lsb-release (common in install instructions for CLIs) installed
    && apt-get -y install --no-install-recommends git iproute2 procps lsb-release less vim unzip zip \
    #
    # cleanup
    && apt-get autoremove -y \
    && apt-get clean -y \
    && rm -rf /var/lib/apt/lists/*

USER vscode
