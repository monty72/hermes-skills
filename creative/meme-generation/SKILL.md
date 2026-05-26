---
name: meme-generation
description: "Generate real meme images by picking a template and overlaying text with Pillow."
version: 1.0.0
---

# Meme Generation

## Overview

Generate real meme images by picking a template and overlaying text with Pillow. Produces actual .png meme files.

## Requirements

```bash
pip install Pillow requests
```

## Available Templates

| Template | Key | Description |
|----------|-----|-------------|
| Drake | drake | Drake dislikes top, likes bottom |
| Distracted BF | distracted-bf | Guy checks out other girl |
| Two Buttons | two-buttons | Sweating guy choosing between two buttons |
| Change My Mind | change-my-mind | Steven Crowder at a table |
| Disaster Girl | disaster-girl | Girl smirking at camera, fire behind |
| Woman Yelling | woman-yelling | Woman yelling at cat |
| I Should Buy | i-should-buy | TV shopping channel guy |
| They're The Same | same-picture | They're the same picture meme |
| Boardroom Meeting | boardroom-meeting | Suggest idea, everyone disagrees |
| Bernie | bernie | Bernie Sanders mittens |

## Python API

```python
from PIL import Image, ImageDraw, ImageFont
import requests, io, textwrap

def create_meme(template_url, top_text="", bottom_text="", output="meme.png"):
    # Download template
    resp = requests.get(template_url)
    img = Image.open(io.BytesIO(resp.content))
    draw = ImageDraw.Draw(img)
    
    # Use default font
    font = ImageFont.load_default()
    
    w, h = img.size
    
    # Top text
    if top_text:
        lines = textwrap.wrap(top_text, width=40)
        y = 10
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            tw = bbox[2] - bbox[0]
            draw.text(((w - tw) / 2, y), line, font=font, fill="white")
            y += bbox[3] - bbox[1] + 5
    
    # Bottom text
    if bottom_text:
        lines = textwrap.wrap(bottom_text, width=40)
        y = h - 10 - (len(lines) * 20)
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            tw = bbox[2] - bbox[0]
            draw.text(((w - tw) / 2, y), line, font=font, fill="white")
            y += bbox[3] - bbox[1] + 5
    
    img.save(output)
    return output
```

## Generate from Template Key

```python
def get_template(key):
    templates = {
        "drake": "https://imgflip.com/s/meme/Drake-Hotline-Bling.png",
        "distracted-bf": "https://imgflip.com/s/meme/Distracted-Boyfriend.png",
        "two-buttons": "https://imgflip.com/s/meme/Two-Buttons.png",
        "change-my-mind": "https://imgflip.com/s/meme/Change-My-Mind.jpg",
        "disaster-girl": "https://imgflip.com/s/meme/Disaster-Girl.jpg",
        "woman-yelling": "https://imgflip.com/s/meme/Woman-Yelling-At-Cat.jpg",
        "i-should-buy": "https://imgflip.com/s/meme/I-Should-Buy-A-Boat.jpg",
        "same-picture": "https://imgflip.com/s/meme/Panik-Kalm-Panik.png",
        "boardroom-meeting": "https://imgflip.com/s/meme/Boardroom-Meeting-Suggestion.png",
        "bernie": "https://imgflip.com/s/meme/Bernie-I-Am-Once-Again-Asking-For-Your-Support.jpg",
    }
    return templates.get(key)

# Usage
template_url = get_template("drake")
create_meme(template_url, "Writing inline CSS", "Using Tailwind classes", "meme.png")
```

## CLI Script

```python
# meme.py — python meme.py drake "top text" "bottom text"
import sys

if __name__ == "__main__":
    key = sys.argv[1]
    top = sys.argv[2]
    bottom = sys.argv[3]
    url = get_template(key)
    if url:
        output = create_meme(url, top, bottom)
        print(f"Saved to {output}")
    else:
        print(f"Unknown template: {key}")
```
