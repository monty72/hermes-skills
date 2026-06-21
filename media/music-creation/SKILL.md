---
name: music-creation
description: "Create, analyze, and prompt AI music generation. Covers HeartMuLa (open-source Suno-like generation), songsee (spectrogram/audio analysis), and Suno prompt engineering with songwriting craft."
tags: [music, audio, generation, songwriting, heartmula, suno, spectrogram, lyrics]
related_skills: [audiocraft-audio-generation]
---

# Music Creation & Analysis — AI Music Generation, Songwriting, Audio Analysis

Generate music via AI, analyze audio with spectrograms, and craft lyrics and styles that work with AI singers.

## When to Use

- User wants to generate music/songs from text descriptions
- User wants to analyze audio (spectrograms, features)
- User needs Suno prompt engineering help
- User is writing lyrics or adapting a song as a parody

## 1. AI Music Generation with HeartMuLa

See `references/heartmula.md` for full installation guide. Summary:

```bash
# Install
git clone https://github.com/HeartMuLa/heartlib.git
cd heartlib && uv venv --python 3.10 .venv && . .venv/bin/activate
uv pip install -e .

# Generate
python ./examples/run_music_generation.py \
  --model_path=./ckpt --version="3B" \
  --lyrics="./assets/lyrics.txt" --tags="./assets/tags.txt" \
  --save_path="./assets/output.mp3" --lazy_load true
```

**Minimum hardware:** 8GB VRAM with `--lazy_load true`. CPU mode possible but very slow.

## 2. Suno AI Prompt Engineering

See `references/songwriting-and-ai-music.md` for full guide. Key patterns:

**Style/Genre field formula:** Genre + Mood + Era + Instruments + Vocal Style + Production + Dynamics

```text
BAD: "sad rock song"
GOOD: "Cinematic orchestral spy thriller, 1960s Cold War era, smoky sultry female vocalist..."
```

**Dynamic arc description:** "Begins as a haunting whisper over sparse piano. Gradually layers in muted brass. Builds through the chorus with full orchestra. Outro strips back to a lone piano."

**Metatags** (in lyrics field): `[Verse] [Chorus] [Bridge] [Whispered] [Belted] [High Energy] [Orchestral swell]`

## 3. Audio Analysis with songsee

```bash
go install github.com/steipete/songsee/cmd/songsee@latest
songsee track.mp3 --viz spectrogram,mel,chroma,mfcc --style magma -o analysis.png
```

## 4. Songwriting Basics

- **Structure**: Verse/Chorus (ABABCB), AABA (jazz), AAA (strophic/folk)
- **Rhyme**: Mix perfect, family, assonance, and slant rhymes
- **Meter**: Match stressed syllables to beats; say lyrics aloud to check flow
- **Emotional arc**: Whisper → roar → whisper. Contrast drives impact
- **Show, don't tell**: "Your hoodie's still on the hook by the door" vs "I was sad"

## 5. Parody Adaptation

1. Map original structure (syllables per line, rhyme scheme, stressed syllables)
2. Match stressed syllables to original's beats
3. On held notes, match the VOWEL SOUND of the original
4. Keep some original lines for recognizability

## 6. Phonetic Tricks for AI Singers

- Spell words as they sound: "through" → "thru", "Nous" → "Noose"
- ALL CAPS = louder, more intense
- "lo-o-o-ove" = sustained/melisma
- Spell out numbers: "24/7" → "twenty four seven"
- Space acronyms: "AI" → "A I"

## References

- `references/heartmula.md` — Full HeartMuLa installation, patches, usage, and performance tuning
- `references/songwriting-and-ai-music.md` — Complete songwriting guide: structure, rhyme, meter, emotional arc, Suno prompts, parody adaptation
- `references/songsee.md` — songsee spectrogram and audio feature visualization reference
