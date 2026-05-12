FROM jenkins/jenkins:lts

USER root

# Install Python + venv
RUN apt update && \
    apt install -y python3 python3-pip python3-venv && \
    apt clean

# Create virtual environment
RUN python3 -m venv /opt/venv

# Fix permissions (VERY IMPORTANT)
RUN chown -R jenkins:jenkins /opt/venv

# Install dependencies inside venv
RUN /opt/venv/bin/pip install --upgrade pip
RUN /opt/venv/bin/pip install requests yfinance

# Install Jenkins plugins required for pipeline jobs
# Using jenkins-plugin-cli (bundled in official Jenkins images)
RUN jenkins-plugin-cli --plugins \
    workflow-job \
    workflow-cps \
    workflow-aggregator \
    pipeline-model-definition \
    git

# Set venv as default
ENV PATH="/opt/venv/bin:$PATH"

# Create init scripts directory
RUN mkdir -p /usr/share/jenkins/ref/init.groovy.d

# Copy ONLY security init script (no job creation)
COPY scripts/init_jenkins.groovy /usr/share/jenkins/ref/init.groovy.d/001-init-security.groovy

USER jenkins