# Voice Guide — TTS Setup and Selection

## Setup (One-Time)

```bash
# Install Python packages
pip install kokoro-onnx soundfile

# Download models (~340MB total, cached permanently)
mkdir -p models
curl -L -o models/kokoro-v1.0.onnx \
  https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx
curl -L -o models/voices-v1.0.bin \
  https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin
```

Models cache at `~/.cache/hyperframes/tts/` if using `npx hyperframes tts`. Otherwise store in project `models/` directory.

---

## Voice Reference (All 54 Available)

### Enterprise / Authority
| Voice | Gender | Accent | Best for |
|-------|--------|--------|----------|
| `bm_george` | Male | British | Enterprise pitch, keynote, B2B, boardroom |
| `bf_emma` | Female | British | Premium product, tutorial, documentation |
| `am_michael` | Male | American | SaaS marketing, confident promo |

### Developer / Technical
| Voice | Gender | Accent | Best for |
|-------|--------|--------|----------|
| `am_adam` | Male | American | Dev tools, CLI demos, explainers |
| `bf_emma` | Female | British | Technical documentation |

### Consumer / Warm
| Voice | Gender | Accent | Best for |
|-------|--------|--------|----------|
| `af_heart` | Female | American | Wellness, consumer, personal, warm |
| `af_sky` | Female | American | Energetic, social ads, lifestyle |
| `af_nova` | Female | American | Professional product demo |

### International
| Voice | Language | Use |
|-------|----------|-----|
| `ef_dora` | Spanish | Spanish-language content |
| `ff_siwis` | French | French content |
| `jf_alpha` | Japanese | Japanese content |

---

## Generation

### Via npx (preferred)
```bash
npx --yes hyperframes@0.6.51 tts script.txt --voice bm_george --output narration.wav --speed 0.92
```

### Via Python (when npx fails)
```python
from kokoro_onnx import Kokoro
import soundfile as sf

k = Kokoro("models/kokoro-v1.0.onnx", "models/voices-v1.0.bin")
text = open("script.txt").read().strip()
samples, rate = k.create(text, voice="bm_george", speed=0.92, lang="en-gb")
sf.write("narration.wav", samples, rate)
print(f"Generated: {len(samples)/rate:.1f}s")
```

---

## Speed Guide

| Speed | Character | Use |
|-------|-----------|-----|
| 0.80 | Very deliberate, heavy | Luxury, dramatic reveals |
| 0.88–0.92 | Measured, authoritative | Enterprise, boardroom |
| 0.95–1.00 | Natural pace | General product, tutorials |
| 1.05–1.10 | Upbeat, energetic | Social ads, launches |
| 1.15–1.20 | Fast, punchy | 15s social, highlights |

**Rule:** Enterprise videos use 0.88–0.92. Consumer/social use 1.0–1.15.

---

## Transcription

```bash
# English content (use small.en — never tiny.en, never just 'small' for English)
npx --yes hyperframes@0.6.51 transcribe narration.wav --model small.en

# Non-English (never .en suffix)
npx --yes hyperframes@0.6.51 transcribe narration.wav --model small --language es

# Output: transcript.json with word-level timestamps
```

### Transcript Quality Check
Always verify after transcription:
```python
import json
words = json.load(open("transcript.json"))
print(f"{len(words)} words, {words[-1]['end']:.1f}s total")
# Check for missing words or wrong timestamps
for w in words:
    print(f"{w['start']:.2f}–{w['end']:.2f}: {w['text']}")
```

**Common issues:**
- Brand names transcribed incorrectly → manually edit transcript.json
- Words merged together → check for 0.00 duration words
- Silence gaps → normal, just verify scene transitions land in gaps

---

## Script Formatting for TTS

```
❌ BAD  (TTS reads literally and sounds wrong)
"10x faster with 99.9% uptime and $2.3T market"

✅ GOOD (TTS reads naturally)
"ten times faster with ninety nine point nine percent uptime
 and nearly two point three trillion dollar market"
```

Other conversions:
- `API` → `A P I` (with spaces for letter-by-letter reading)
- `URL` → `U R L` or write out the actual URL
- `cyberagent.ng` → `cyberagent dot ng`
- `React.js` → `React dot js` or just `React`
- `npm install` → leave as-is (sounds fine)
- `$29/mo` → `twenty nine dollars per month`

---

## TTS → Transcribe → Caption Pipeline

```bash
# 1. Write script
cat > script.txt << 'EOF'
[Your voiceover script here]
EOF

# 2. Generate voiceover
python3 -c "
from kokoro_onnx import Kokoro; import soundfile as sf
k = Kokoro('models/kokoro-v1.0.onnx', 'models/voices-v1.0.bin')
s,r = k.create(open('script.txt').read().strip(), voice='bm_george', speed=0.92, lang='en-gb')
sf.write('narration.wav', s, r)
print(f'Duration: {len(s)/r:.1f}s')
"

# 3. Transcribe for timestamps
npx --yes hyperframes@0.6.51 transcribe narration.wav --model small.en

# 4. Verify
python3 -c "
import json; w=json.load(open('transcript.json'))
print(f'{len(w)} words, {w[-1][\"end\"]:.1f}s')
for x in w: print(f'{x[\"start\"]:.2f}: {x[\"text\"]}')
"
```

The transcript.json word timings then drive:
1. Scene transition timing (place cuts at sentence-end pauses)
2. Caption rendering (per-word pop animation)
3. Visual emphasis (burst lines, scribble, highlights synced to key nouns)
