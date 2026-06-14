# Deployed Chatbot Comparison — Reference Data (Verified May 2026 via Brave Search API)

Pricing and feature data for the 6 major AI chatbots, verified via Brave Search API and Wikipedia, May 2026. Use as reference when building chatbot comparison pages.

> **Note:** This data was originally gathered from Wikipedia (which was slightly stale) and updated with live Brave Search API queries that returned pricing pages from fritz.ai, felloai.com, finout.io, mem0.ai, and official company pricing pages. Always verify before reusing in a later month.

## Pricing Reference

| Chatbot | Free Tier | Standard Paid | Mid/Power Tier | Top Tier | Notes |
|---------|-----------|---------------|----------------|----------|-------|
| **ChatGPT** (OpenAI) | ✅ GPT-5.3 Instant | Plus $20/mo (GPT-5.5) | **Pro $100/mo** (NEW Apr 9 2026 — 5x limits) | Pro $200/mo (unlimited) | Go $8/mo (with ads), Business $20-25/seat/mo. GPT-5.5 launched Apr 23 2026. |
| **Claude** (Anthropic) | ✅ Sonnet (limited) | Pro $20/mo ($17 annual) | Max **$100/mo** (5x usage, NEW) | Max $200/mo (20x usage) | Team $25/seat/mo. Long-context surcharges dropped Mar 13 2026. Latest: Sonnet 4.6, Opus 4.7. |
| **Gemini** (Google) | ✅ Gemini 3.5 Flash (generous) | AI Pro $20/mo | AI Ultra **$100/mo** (5x, NEW at I/O 2026) | AI Ultra $200/mo (was $250, dropped at I/O 2026) | AI Plus $8/mo. Gemini 3.1 Pro on Ultra. 1M context on all tiers. |
| **DeepSeek** | ✅ 100% free web chat 🏆 (no sub needed) | API only (cheapest) | V4 Pro: $0.435/M input (75% off until May 31) | R1: $0.55/M input | 5M free API tokens for new accounts. Cache hits fraction of miss cost. 95% cheaper than GPT-4. |
| **Grok** (xAI) | ✅ Limited access | SuperGrok Lite $10/mo (NEW) | SuperGrok $30/mo (standalone) | X Premium+ $40/mo | X Premium $8/mo. SuperGrok Heavy $300/mo. Grok 4.3, 1M context. Aurora image gen. |
| **Perplexity** | ✅ 5 Pro queries/4h | Pro $20/mo | Max $200/mo | Enterprise from $40/seat/mo | Education $10/mo. Comet browser now free (dropped paywall Mar 18 2026). Sonar API: $1-3/M tokens. |

## Feature Matrix

| Feature | ChatGPT | Claude | Gemini | DeepSeek | Grok | Perplexity |
|---------|---------|--------|--------|----------|------|------------|
| Latest model | GPT-5.5 / o3 | Sonnet 4.6 / Opus 4.7 | 3.5 Flash / 3.1 Pro | V4 Pro / R1 | Grok 4.3 | Sonar / multi-model |
| Context | 128K | 200K 🏆 | 1M 🏆 | 128K | 1M 🏆 | Variable |
| Voice | ✅🏆 Best | ⚠️ Beta | ✅ Good | ❌ | ✅ Good | ⚠️ Limited |
| Image gen | ✅ DALL·E | ❌ | ✅ Imagen | ❌ | ✅ Aurora | ❌ |
| Web search | ✅ Browse | ✅ Web | ✅🏆 Google | ✅ Search | ✅🏆 X Realtime | ✅🏆 Native |
| Code exec | ✅🏆 Ada | ⚠️ Basic | ✅ Colab | ✅ Basic | ⚠️ Basic | ❌ |
| File upload | ✅ Images, PDF, code | ✅ PDF, code, images | ✅ PDF, images, video | ✅ PDF, images | ✅ Images, PDF | ✅ PDF, images |
| Open source | ❌ | ❌ | ❌ | ✅🏆 Open-weight | ⚠️ Partially | ❌ |
| Mobile | ✅ Both | ✅ iOS | ✅ Both | ✅ Both | ✅ Both | ✅ Both |
| API cost (input) | $10-15/M (GPT-5.5) | $3-8/M (Sonnet) | $2-4/M (Pro) | $0.14-0.55/M 🏆 | $1.25/M | $1-3/M |

## Verdict Framework

When building a chatbot comparison page, always include a clear decision guide:
- **One tool for everything** → ChatGPT (most complete feature set, GPT-5.5, new $100 Pro mid-tier)
- **Writing/analysis/document work** → Claude (200K context, thoughtfulness, Opus 4.7)
- **Google power user** → Gemini (1M context, Drive/Gmail/YouTube integration, Ultra $100 new)
- **Budget-conscious** → DeepSeek (100% free web chat, cheapest API by 95%)
- **Real-time news/X analysis** → Grok (live X data, 1M context, unfiltered)
- **Research/fact-finding** → Perplexity (citations, web-grounded answers, Comet browser free)

## Scoring Guidelines

- **9.0+** = Excellent, best-in-class for something
- **8.0-8.9** = Very good, clear niche but compromises
- **7.0-7.9** = Good, but clear trade-offs
- **<7.0** = Niche or has significant drawbacks

Score structure: 30% core capability, 25% ecosystem/features, 20% value for money, 15% unique strengths, 10% polish/UX.

## Research Sources Used (May 2026)

| Source | URL | Data Used |
|--------|-----|-----------|
| fritz.ai ChatGPT pricing | https://fritz.ai/chatgpt-pricing/ | GPT-5.5 launch Apr 23, $100 Pro tier Apr 9, Go $8 pricing |
| felloai ChatGPT pricing | https://felloai.com/chatgpt-pricing-guide-free-go-plus-pro-alternatives-october-2025/ | All 6 pricing tiers confirmed |
| finout.io Claude pricing | https://www.finout.io/blog/claude-pricing-in-2026-for-individuals-organizations-and-developers | Max $100/$200 tiers, Team $25/seat |
| mem0.ai Claude pricing | https://mem0.ai/blog/anthropic-claude-pricing | Pro $20 ($17 annual), long-context surcharge dropped |
| Google AI subscriptions blog | https://blog.google/products-and-platforms/products/google-one/google-ai-subscriptions/ | Ultra $100 new, Ultra $200 (dropped from $250) |
| Mashable / Google I/O 2026 | https://mashable.com/article/google-io-2026-gemini-ultra-ai-subscription-tiers | Ultra $99.99 tier confirmed |
| PCMag Gemini | https://www.pcmag.com/how-to/i-paid-for-gemini-ai-plan-5-feature-justify-price-google-io | AI Plus $8, Pro $20, Ultra pricing |
| deepseek.ai pricing | https://deepseek.ai/pricing | V4 Pro $0.435/M, R1 $0.55/M, free web chat |
| nxcode.io DeepSeek | https://www.nxcode.io/resources/news/deepseek-api-pricing-complete-guide-2026 | 5M free tokens, cache hits 95% cheaper |
| felloai Grok pricing | https://felloai.com/grok-pricing/ | SuperGrok Lite $10, Heavy $300, all 6 tiers |
| mem0.ai Grok API | https://mem0.ai/blog/xai-grok-api-pricing | Grok 4.3 $1.25/$2.50/M, 1M context |
| felloai Perplexity pricing | https://felloai.com/perplexity-pricing/ | Max $200, Education $10, Sonar API, Comet free |
| Wikipedia (baseline) | https://en.wikipedia.org/wiki/Comparison_of_chatbots | Release dates, model lineage, feature baselines |
