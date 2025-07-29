# Infrastructure Dockerfile
FROM alpine:latest

# Install necessary tools
RUN apk add --no-cache \
    aws-cli \
    curl \
    jq \
    git \
    unzip

# Install Terraform
RUN curl -LO https://releases.hashicorp.com/terraform/1.7.0/terraform_1.7.0_linux_amd64.zip && \
    unzip terraform_1.7.0_linux_amd64.zip && \
    mv terraform /usr/local/bin/ && \
    rm terraform_1.7.0_linux_amd64.zip

WORKDIR /workspace

# Copy infrastructure scripts
COPY . .

# Make scripts executable (if they exist)
RUN find . -name "*.sh" -exec chmod +x {} \; 2>/dev/null || true

# Default command
CMD ["sh"] 