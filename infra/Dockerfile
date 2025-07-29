# Infrastructure Dockerfile
FROM alpine:latest

# Install necessary tools
RUN apk add --no-cache \
    terraform \
    aws-cli \
    curl \
    jq \
    git

WORKDIR /workspace

# Copy infrastructure scripts
COPY . .

# Make scripts executable
RUN chmod +x *.sh

# Default command
CMD ["sh"] 