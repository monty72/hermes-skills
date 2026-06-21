# songsee — Audio Spectrogram & Feature Visualization CLI

Generate spectrograms and multi-panel audio feature visualizations.

## Prerequisites

```bash
go install github.com/steipete/songsee/cmd/songsee@latest
```

Optional: `ffmpeg` for formats beyond WAV/MP3.

## Quick Start

```bash
songsee track.mp3 -o spectrogram.png
songsee track.mp3 --viz spectrogram,mel,chroma,hpss,selfsim,loudness,tempogram,mfcc,flux
songsee track.mp3 --start 12.5 --duration 8 -o slice.jpg
cat track.mp3 | songsee - --format png -o out.png
```

## Visualization Types

| Type | Description |
|------|-------------|
| `spectrogram` | Standard frequency spectrogram |
| `mel` | Mel-scaled spectrogram |
| `chroma` | Pitch class distribution |
| `hpss` | Harmonic/percussive separation |
| `selfsim` | Self-similarity matrix |
| `loudness` | Loudness over time |
| `tempogram` | Tempo estimation |
| `mfcc` | Mel-frequency cepstral coefficients |
| `flux` | Spectral flux (onset detection) |

## Flags

| Flag | Description |
|------|-------------|
| `--viz` | Types (comma-separated) |
| `--style` | Palette: `classic`, `magma`, `inferno`, `viridis`, `gray` |
| `--width` / `--height` | Image dimensions |
| `--window` / `--hop` | FFT window and hop size |
| `--min-freq` / `--max-freq` | Frequency range |
| `--start` / `--duration` | Time slice |
| `--format` | `jpg` or `png` |
