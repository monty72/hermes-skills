# Model Cost Management

Strategy for keeping LLM spend minimal while maintaining capability fallbacks.

## Cheapest Available Model

### Via Direct API

| Model | Provider | Input Cost /M | Provider Config | Notes |
|-------|---------|---------------|-----------------|-------|
| `gpt-4o-mini` | LiteLLM / `custom` | ~$0.15 | `provider: custom`, `base_url: <proxy>/v1` | Fast, good quality, cheaper than DeepSeek |
| `deepseek-v4-flash` | DeepSeek | ~$0.50 | `provider: deepseek` | Previous default, more expensive than gpt-4o-mini |
| `deepseek-chat` | DeepSeek | Mid | `provider: deepseek` | Default, balanced |
| `deepseek-v4-pro` | DeepSeek | Premium | `provider: deepseek` | Best quality, fallback only |

### Via OpenRouter (router to cheapest)

| Model | Route | Input Cost /M | Notes |
|-------|-------|---------------|-------|
| Gemini 2.0 Flash | `google/gemini-2.0-flash-001` | ~$0.10 | Very good quality for price |
| Llama 3.1 8B | `meta-llama/llama-3.1-8b-instruct` | ~$0.06 | Fast, open-weight |
| GPT-4o-mini | `openai/gpt-4o-mini` | ~$0.15 | Via OpenRouter routing |

### Free Tier

| Provider | Model | Limit | Config |
|----------|-------|-------|--------|
| Groq | Llama 3.1 8B, Mixtral | Rate-limited (30 req/min) | `GROQ_API_KEY` + `provider: custom`, `base_url: https://api.groq.com/openai/v1` |
| Ollama (local) | hermes3:8b, qwen2.5, llama3.2 | Free, no rate limit | `provider: custom`, `base_url: http://localhost:11434/v1` |

## Using the `custom` Provider

Hermes has a `custom` provider plugin (`plugins/model-providers/custom/`) that works with **any OpenAI-compatible endpoint** — including LiteLLM proxies, Ollama, vLLM, Groq, and local inference servers.

### Configuration

```yaml
model:
  provider: custom
  base_url: <openai-compatible-base-url/v1>
  default: <model-name>
  api_key: ""    # optional — omit if the endpoint doesn't need auth
```

### Use Cases

| Endpoint | base_url | Example model | Auth |
|----------|----------|---------------|------|
| LiteLLM proxy | `http://proxy-host:4000/v1` | `gpt-4o-mini` | Proxy handles its own key |
| Ollama (local) | `http://localhost:11434/v1` | `hermes3:8b` | None |
| Groq | `https://api.groq.com/openai/v1` | `llama-3.1-8b-instant` | `GROQ_API_KEY` |
| Custom vLLM | `http://your-server:8000/v1` | Any served model | Varies |

### ⚠️ Local Ollama Requires a GPU

Local models are **not viable on CPU-only machines** — even a 3B model loads 9GB+ with a 64K context window (Hermes default) and can time out at 30+ seconds per generation. Only attempt local inference on a machine with:
- A GPU (NVIDIA with 8GB+ VRAM, or Apple Silicon with unified memory)
- Or accept very slow CPU inference for tiny models (<3B) with reduced context

### Verifying a Custom Provider Works

```bash
# Quick test — the endpoint should speak OpenAI-compatible API
curl -s --max-time 10 <base_url>/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"<model>","messages":[{"role":"user","content":"hi"}],"max_tokens":10}'
```

## Switching Models

```bash
# For a direct provider (DeepSeek, Gemini, etc.)
hermes config set model.provider deepseek
hermes config set model.default deepseek-v4-flash
hermes config set model.base_url "https://api.deepseek.com/v1"

# For an OpenAI-compatible endpoint via custom provider (LiteLLM, Ollama, Groq, etc.)
hermes config set model.provider custom
hermes config set model.base_url http://localhost:11434/v1
hermes config set model.default hermes3:8b

# Set fallback (for reliability when primary is down)
# fallback_providers is stored as a JSON string in config.yaml
hermes config set fallback_providers '[{"provider":"custom","model":"gpt-4o-mini","base_url":"http://192.168.1.121:4000/v1"}]'
```
