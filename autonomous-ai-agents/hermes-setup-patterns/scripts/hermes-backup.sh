#!/bin/bash
# Hermes full backup - run weekly
# This is a no-agent cron script (~/.hermes/scripts/hermes-backup.sh)
# It runs without the LLM — just shell commands.
set -e

BACKUP_DIR="/home/matth/hermes-backups"
mkdir -p "$BACKUP_DIR"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
BACKUP_FILE="$BACKUP_DIR/hermes-full-$TIMESTAMP.tar.gz"
SKILLS_REPO="/home/matth/.hermes/skills"

echo "=== Hermes Backup $TIMESTAMP ==="

# 1. Push skills to GitHub
echo ">>> Pushing skills to GitHub..."
cd "$SKILLS_REPO"
git add -A
git commit --allow-empty -m "Auto-backup $TIMESTAMP" 2>/dev/null || true
git push origin master 2>&1 || echo "Git push failed (continuing)"

# 2. Create full tarball
echo ">>> Creating tarball..."
tar czf "$BACKUP_FILE" \
  --exclude=".hermes/hermes-agent" \
  --exclude=".hermes/node_modules" \
  --exclude=".hermes/skills/.git" \
  --exclude=".hermes/lsp" \
  --exclude=".hermes/logs" \
  --exclude=".hermes/sessions" \
  --exclude=".hermes/cache" \
  -C /home/matth .hermes/ .hermes-vault/ .local/bin/hermes-vault

# 3. Prune old backups (keep last 8)
echo ">>> Pruning old backups..."
ls -t "$BACKUP_DIR"/hermes-full-*.tar.gz 2>/dev/null | tail -n +9 | xargs -r rm

echo "=== Backup complete ==="
echo "File: $BACKUP_FILE ($(du -h "$BACKUP_FILE" | cut -f1))"
