---
name: docker-management
description: "Manage Docker containers, images, volumes, networks, and Compose stacks — lifecycle ops, debugging, cleanup, and Dockerfile optimization."
version: 1.0.0
---

# Docker Management

## Overview

Manage Docker containers, images, volumes, networks, and Docker Compose stacks.

## Container Lifecycle

```bash
# List containers
docker ps                    # running
docker ps -a                 # all
docker ps --format '{{.Names}}\t{{.Status}}\t{{.Ports}}'

# Start/stop/restart
docker start <container>
docker stop <container>
docker restart <container>

# Remove
docker rm <container>
docker rm -f <container>     # force running

# Execute command in running container
docker exec -it <container> <cmd>
docker exec <container> <cmd>  # non-interactive

# View logs
docker logs <container>
docker logs -f <container>   # follow
docker logs --tail 100 <container>

# Inspect
docker inspect <container>
docker stats
```

## Images

```bash
# List
docker images

# Build
docker build -t <name>:<tag> .

# Pull/push
docker pull <image>
docker push <image>

# Remove
docker rmi <image>
docker rmi $(docker images -q) --force  # remove all

# Prune unused
docker image prune
docker image prune -a  # all unused
```

## Volumes

```bash
# List
docker volume ls

# Create
docker volume create <name>

# Inspect
docker volume inspect <name>

# Remove
docker volume rm <name>
docker volume prune  # remove unused
```

## Networks

```bash
# List
docker network ls

# Create
docker network create <name>

# Connect/disconnect container
docker network connect <network> <container>
docker network disconnect <network> <container>

# Inspect
docker network inspect <name>

# Remove
docker network rm <name>
```

## Docker Compose

```bash
# Start services
docker compose up
docker compose up -d        # detached
docker compose up --build   # rebuild images

# Stop
docker compose down
docker compose down -v      # remove volumes too

# View logs
docker compose logs -f

# Exec into service
docker compose exec <service> <cmd>

# List services
docker compose ps

# Rebuild single service
docker compose build <service>
docker compose up -d --no-deps <service>
```

## Cleanup

```bash
# Prune everything unused
docker system prune
docker system prune -a --volumes  # aggressive

# Disk usage
docker system df
docker system df -v  # verbose
```

## Debugging

```bash
# Check resource usage
docker stats --no-stream

# View events
docker events --since 5m

# Copy files
docker cp <container>:/path /local/path
docker cp /local/path <container>:/path

# Check port mapping
docker port <container>
