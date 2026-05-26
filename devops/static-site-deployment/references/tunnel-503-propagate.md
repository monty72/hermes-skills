# localhost.run 503 Propagation

After the localhost.run tunnel establishes and prints the URL, the tunnel may return **HTTP 503** for 15-45 seconds while TLS termination and DNS propagate through their infrastructure.

## Symptoms

- Tunnel prints `https://<hash>.lhr.life tunneled with tls termination`
- `curl` returns `<h1>no tunnel here :(</h1>` or HTTP 503
- Local server at `localhost:PORT` responds fine (HTTP 200)
- No error in SSH output

## Cause

localhost.run's reverse proxy needs to:
1. Allocate a hostname on their authoritative DNS
2. Provision TLS cert via Let's Encrypt
3. Route the first connections through their load balancer

Until step 3 completes, the edge returns 503.

## Fix

Wait 10-15 seconds after the URL appears, then verify:

```bash
sleep 15 && curl -sI https://<hash>.lhr.life | head -1
# Expected: HTTP/2 200
```

If still 503 after 30 seconds, the tunnel may be on a stale connection. Kill all tunnels and retry:

```bash
kill $(pgrep -f 'ssh.*localhost.run') 2>/dev/null
sleep 2
ssh -R 80:localhost:8000 nokey@localhost.run
```

## Verification Pattern

```python
# From execute_code / terminal:
for i in range(10):
    r = terminal(f"curl -s -o /dev/null -w '%{{http_code}}' https://{url}")
    if r['output'].strip() == '200':
        print(f"Tunnel ready at attempt {i+1}")
        break
    sleep(3)
```
