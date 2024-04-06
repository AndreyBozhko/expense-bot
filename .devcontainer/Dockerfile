FROM python:3.9-buster@sha256:a21bc1f5190fa4f5d13dbdec6adc8d65ae2d3025411ecab367f616831dd570cb
RUN pip install --no-cache-dir --upgrade pip==22.3.1 setuptools==65.6.3 wheel==0.43.0 \
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
