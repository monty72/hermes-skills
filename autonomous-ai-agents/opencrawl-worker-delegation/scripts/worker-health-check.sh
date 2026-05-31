#!/bin/bash
# Silent health check for OpenCrawl worker
# Silent on success, outputs errors on failure
result=$(ssh -o ConnectTimeout=5 -o BatchMode=yes matth@192.168.1.137 "~/scripts/health-report.sh" 2>&1)
exit_code=$?
if [ $exit_code -ne 0 ]; then
    echo "❌ OpenCrawl health check FAILED"
    echo "$result"
    exit 1
fi
# Silent on success - no output = no delivery (no_agent pattern)
exit 0
