#!/bin/bash
# Main-Agent Side: Health check wrapper for a remote Hermes worker
#
# Usage: Place this on the main Hermes host and create a no-agent cron job
#        that runs it. Silent on success (no delivery), outputs error on failure.
#
# Pattern: SSH to worker → run worker's health-report.sh → report errors
#
# PITFALL: If the worker's IP changes (e.g. after power cut / DHCP drift),
#          update WORKER_IP here AND in any other scripts referencing it.

WORKER_USER="matth"
WORKER_IP="192.168.1.XXX"          # <-- SET THIS to your worker's IP
WORKER_SCRIPT="~/scripts/health-report.sh"

result=$(ssh -o ConnectTimeout=5 -o BatchMode=yes "${WORKER_USER}@${WORKER_IP}" "${WORKER_SCRIPT}" 2>&1)
exit_code=$?

if [ $exit_code -ne 0 ]; then
    echo "❌ Worker health check FAILED (${WORKER_IP})"
    echo "$result"
    exit 1
fi

# Silent on success = no output = no delivery (no_agent pattern)
exit 0
