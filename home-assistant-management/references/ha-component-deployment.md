# HA Custom Component Deployment — Full Reference

*Absorbed from the consolidated `ha-component-deployment` skill.*

## Prerequisites
- SSH access to HA machine (typically `root@<ha-ip>`)
- HA long-lived access token for REST API (`HASS_TOKEN`)
- HA URL — typically `http://<ha-ip>:8123`

## Install via SSH

```bash
ssh root@<ha-ip> "
  cd /config
  wget -q -O component.zip 'https://github.com/{owner}/{repo}/archive/refs/tags/v{version}.zip'
  unzip -q component.zip
  ls {repo}-*/custom_components/  # Verify domain folder exists
  cp -r {repo}-*/custom_components/{domain} custom_components/
  ls custom_components/{domain}/manifest.json  # Verify
  rm -rf component.zip {repo}-*/
"
```

For releases with pre-built assets:
```bash
wget -q -O octopus_energy.zip 'https://github.com/{owner}/{repo}/releases/download/v{version}/octopus_energy.zip'
```

## Restart HA

```bash
# Via SSH
ssh root@<ha-ip> "ha core restart"

# Via REST API
POST /api/services/homeassistant/restart
```

Poll for recovery:
```bash
for i in $(seq 1 30); do
  result=$(curl -s -o /dev/null -w "%{http_code}" http://<ha-ip>:8123/api/ 2>/dev/null)
  if [ "$result" = "200" ] || [ "$result" = "401" ]; then echo "HA is back!"; break; fi
  sleep 2
done
```

## Config Flow via REST API

**Step 1 — Start the flow:**
```python
POST /api/config/config_entries/flow
{"handler": "{domain}", "show_advanced_options": false}
```

**Step 2 — Submit form:**
```python
POST /api/config/config_entries/flow/{flow_id}
{
  "api_key": "sk_live_...",
  "favour_direct_debit_rates": True,
  "expandable_section": {           # REQUIRED even if empty
    "sub_field": "value"
  }
}
```

**Step types in response:**
- `"type": "form"` — another step needed, check `step_id`
- `"type": "create_entry"` — done!

## Key Pitfalls

1. **Expandable sections are API-required** — even when visually collapsed in UI, the API rejects missing sections with `"required key not provided"`
2. **Config flow IDs are single-use** — cannot retry a failed step; start fresh
3. **GitHub releases may lack assets** — use source archive URL pattern, not release asset URLs
4. **HA restart via API may return 500** — fall back to SSH `ha core restart`
5. **`unavailable` with `restored: true`** — integration never connected (expired token). Re-authenticate via HA UI
