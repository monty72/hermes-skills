# Model Cost Management

Strategy for keeping LLM spend minimal while maintaining capability fallbacks.

## Cheapest Available Model

### DeepSeek

| Model | Tier | Notes |
|-------|------|-------|
| `deepseek-v4-flash` | Cheapest | Fast, good for most tasks |
| `deepseek-chat` | Mid | Default, balanced |
| `deepseek-v4-pro` | Premium | Best quality, fallback only |

### OpenAI

| Model | Tier | Notes |
|-------|------|-------|
| `gpt-5.4-nano` | Cheapest OpenAI | Newest generation, very cheap |
| `gpt-4.1-nano` | Cheap | Older nano generation |
| `gpt-4.1-mini` | Mid | Smarter, still cheap |
| `gpt-4o-mini` | Legacy | Still cheap, older arch |
| `gpt-5.4-mini` | Mid | Newer smart option |

## Auto-Cheapest Cron Job

Run a daily check at 8am to ensure the model is always set to the cheapest available:

```bash
hermes cron create "0 8 * * *" \
  --name "cheapest-model-check" \
  --deliver local \
  --prompt "Check the current default model in Hermes config and if it's not the cheapest available option, switch to the cheapest. Use the OpenAI API to list available models and pick the cheapest nano/mini variant. Set model.default and model.provider accordingly. Report what was found and any changes made."
```

The job runs silently (no delivery unless something changed).

## Switching Models

```bash
# Change default model
hermes config set model.default gpt-5.4-nano

# Change provider (if switching between OpenAI, DeepSeek, Anthropic, etc.)
hermes config set model.provider openai

# Clear base_url if switching from a provider that had a custom endpoint
hermes config set model.base_url ""

# Set fallback (for reliability, not cost)
# fallback_providers is stored as a JSON string in config.yaml
```

## Provider Economics

| Provider | Cheapest Model | Why use |
|----------|---------------|---------|
| DeepSeek | `deepseek-v4-flash` | Generally cheapest per token overall |
| OpenAI | `gpt-5.4-nano` / `gpt-4.1-nano` | More expensive but key also enables image gen, STT, TTS |
| Anthropic | Claude Haiku | More expensive, best for coding |
| OpenRouter | Various | Can route to cheapest across many providers |

DeepSeek flash is cheaper than OpenAI nano on a per-token basis. Use DeepSeek for pure cost savings, OpenAI only when the same key is needed for image gen/STT/TTS.

## Verifying the Active Model

```bash
# Check config
grep -A5 '^model:' ~/.hermes/config.yaml

# Test the model directly
curl -s https://api.openai.com/v1/chat/completions \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"gpt-5.4-nano","messages":[{"role":"user","content":"hi"}],"max_completion_tokens":10}' \
  --max-time 30 | python3 -c "import sys,json; d=json.load(sys.stdin); print('OK' if 'choices' in d else d.get('error',{}).get('message','?'))"
```

Note: GPT-5.x models use `max_completion_tokens` not `max_tokens`.
