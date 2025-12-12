FROM mcr.microsoft.com/devcontainers/base:ubuntu-24.04

# Install basic deps (mise requires curl, git, unzip)
RUN apt-get update && \
    apt-get install -y curl git unzip && \
    rm -rf /var/lib/apt/lists/*

# Install mise binary from official image
COPY --from=jdxcode/mise /usr/local/bin/mise /usr/local/bin/

# Ensure mise owns its dirs (needed inside containers)
RUN mkdir -p /home/vscode/.local/share && \
    chown -R vscode:vscode /home/vscode/.local

# Activate mise for bash and zsh
RUN echo 'eval "$(mise activate bash)"' >> /home/vscode/.bashrc && \
    echo 'eval "$(mise activate zsh)"' >> /home/vscode/.zshrc

# Set default user
USER vscode

