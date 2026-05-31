# Homelab Architecture Diagram

The full architecture diagram for the Hermes + OpenCrawl homelab is at:

**`~/dev-site/opencrawl-architecture.html`**

Open it in any browser to see:

- External APIs (DeepSeek, OpenAI)
- Proxmox pve1 host boundary
- Hermes Main Agent (VM 105, 192.168.1.121) with LiteLLM proxy :4000
- OpenCrawl Worker (VM 104, 192.168.1.137) with Ollama :11434, Open WebUI :3000
- Auto-routing decision flow
- Health monitoring and sync arrows
- Info cards with specs

## Regenerating

When the architecture changes, regenerate the diagram using the `architecture-diagram` skill. Keep the same dark-themed SVG style (JetBrains Mono, slate-950 bg, cyan/emerald/amber semantic colors). Update the diagram file in place.
