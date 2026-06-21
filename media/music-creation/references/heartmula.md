# HeartMuLa — Open-Source Music Generation

Full setup, usage, and troubleshooting guide.

## Hardware Requirements

- **Minimum**: 8GB VRAM with `--lazy_load true`
- **Recommended**: 16GB+ VRAM
- **Multi-GPU**: `--mula_device cuda:0 --codec_device cuda:1`
- **CPU**: Possible but extremely slow (30-60+ min per song)

## Installation

```bash
cd ~/
git clone https://github.com/HeartMuLa/heartlib.git
cd heartlib

# Python 3.10 required
uv venv --python 3.10 .venv
. .venv/bin/activate
uv pip install -e .

# Fix compatibility issues
uv pip install --upgrade datasets transformers

# Download models
hf download --local-dir './ckpt' 'HeartMuLa/HeartMuLaGen'
hf download --local-dir './ckpt/HeartMuLa-oss-3B' 'HeartMuLa/HeartMuLa-oss-3B-happy-new-year'
hf download --local-dir './ckpt/HeartCodec-oss' 'HeartMuLa/HeartCodec-oss-20260123'
```

## Source Code Patches (Required)

**Patch 1 - RoPE cache fix** in `src/heartlib/heartmula/modeling_heartmula.py`:

Add after `reset_caches` try/except block:
```python
from torchtune.models.llama3_1._position_embeddings import Llama3ScaledRoPE
for module in self.modules():
    if isinstance(module, Llama3ScaledRoPE) and not module.is_cache_built:
        module.rope_init()
        module.to(device)
```

**Patch 2 - HeartCodec loading fix** in `src/heartlib/pipelines/music_generation.py`:

Add `ignore_mismatched_sizes=True` to all `HeartCodec.from_pretrained()` calls.

## Usage

```bash
cd heartlib && . .venv/bin/activate
python ./examples/run_music_generation.py \
  --model_path=./ckpt --version="3B" \
  --lyrics="./assets/lyrics.txt" --tags="./assets/tags.txt" \
  --save_path="./assets/output.mp3" --lazy_load true
```

**Tags format** (comma-separated, no spaces): `piano,happy,wedding,synthesizer,romantic`

**Lyrics format** (use bracketed structural tags): `[Verse]\nLyrics...\n\n[Chorus]\nChorus...`

## Key Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--max_audio_length_ms` | 240000 | Max length in ms (240s = 4 min) |
| `--topk` | 50 | Top-k sampling |
| `--temperature` | 1.0 | Sampling temperature |
| `--cfg_scale` | 1.5 | Classifier-free guidance scale |
| `--lazy_load` | false | Load/unload models on demand |
| `--mula_dtype` | bfloat16 | Dtype for HeartMuLa |
| `--codec_dtype` | float32 | Dtype for HeartCodec (fp32 for quality) |

## Pitfalls

1. Do NOT use bf16 for HeartCodec — degrades audio quality. Use fp32.
2. Tags may be ignored — lyrics tend to dominate
3. Triton not available on macOS — Linux/CUDA only for GPU accel
4. RTX 5080 incompatibility reported upstream
5. Dependency pin conflicts require manual upgrades and patches above

## Links

- Repo: https://github.com/HeartMuLa/heartlib
- Models: https://huggingface.co/HeartMuLa
- Paper: https://arxiv.org/abs/2601.10547
