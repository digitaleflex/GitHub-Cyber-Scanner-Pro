# Scene Timing Templates

## 15-Second Video (Social Ad)

```
Total: 15s | VO: ~37 words | Scenes: 3
─────────────────────────────────────
Scene 1: Hook          0.0 – 4.0s   (4s)
  Transition: push-left 0.4s
Scene 2: Benefit       4.4 – 10.5s  (6s)
  Transition: blur 0.5s
Scene 3: CTA          11.0 – 15.0s  (4s)
  Fade to black: 14.0–15.0s
─────────────────────────────────────
Rule: Hook must land the main message in 2s.
Every frame in scene 3 must be readable.
```

## 30-Second Video (Product Promo)

```
Total: 30–32s | VO: ~65–75 words | Scenes: 5–6
──────────────────────────────────────────────
Scene 1: Problem/Hook     0.0 – 7.0s   (7s)
  Transition: blur 0.5s
Scene 2: Platform intro   7.5 – 10.5s  (3s)
  Transition: vertical push 0.5s
Scene 3: Feature demo    11.0 – 17.0s  (6s)
  Transition: color dip 0.5s
Scene 4: Proof stats     17.5 – 20.5s  (3s)
  Transition: push-left 0.5s
Scene 5: Scale/story     21.0 – 28.0s  (7s)
  Transition: color blocks 0.6s
Scene 6: CTA             28.5 – 32.0s  (3.5s)
  Fade to black: 31.0–32.0s
──────────────────────────────────────────────
```

## 45-Second Video (Feature Explainer)

```
Total: 45s | VO: ~110 words | Scenes: 7–8
──────────────────────────────────────────────
Scene 1: Hook/Problem     0.0 – 6.0s   (6s)
Scene 2: Solution reveal  6.5 – 10.5s  (4s)
Scene 3: Feature 1       11.0 – 16.5s  (5.5s)
Scene 4: Feature 2       17.0 – 22.5s  (5.5s)
Scene 5: Feature 3       23.0 – 28.0s  (5s)
Scene 6: Proof/stats     28.5 – 33.5s  (5s)
Scene 7: Social proof    34.0 – 40.0s  (6s)
Scene 8: CTA             40.5 – 45.0s  (4.5s)
──────────────────────────────────────────────
```

## 60-Second Video (Enterprise Pitch)

```
Total: 60–62s | VO: ~145–155 words | Scenes: 8–10
──────────────────────────────────────────────────
Scene 1: Market problem    0.0 – 8.0s    (8s)
Scene 2: Platform reveal   8.5 – 13.0s   (4.5s)
Scene 3: Orchestration    13.5 – 22.0s   (8.5s)  ← longest: key demo
Scene 4: Features         22.5 – 29.0s   (6.5s)
Scene 5: Proof stats      29.5 – 34.0s   (4.5s)
Scene 6: Enterprise scale 34.5 – 42.0s   (7.5s)
Scene 7: Integrations     42.5 – 48.0s   (5.5s)
Scene 8: Trust/security   48.5 – 53.0s   (4.5s)
Scene 9: Pricing/CTA      53.5 – 60.0s   (6.5s)
Scene 10: Final hold      60.0 – 62.0s   (2s) fade
──────────────────────────────────────────────────
```

## Scene Duration Minimums

| Scene type | Min | Ideal | Max |
|-----------|-----|-------|-----|
| Hook/Slam | 3s | 4–5s | 6s |
| Platform reveal | 2.5s | 3–4s | 5s |
| Feature demo | 4s | 5–7s | 9s |
| Stats/proof | 3s | 4–5s | 6s |
| Scale/org | 4s | 6–8s | 10s |
| CTA | 3s | 4–5s | 6s |

## Aligning Scenes to Voiceover

```python
import json

words = json.load(open("transcript.json"))

# Find sentence boundaries
for i, w in enumerate(words):
    if w["text"].endswith((".", "?", "!")):
        gap = words[i+1]["start"] - w["end"] if i+1 < len(words) else 0
        print(f"Sentence ends at {w['end']:.2f}s  (gap: {gap:.2f}s before next)")
        print(f"  → Place transition at {w['end'] + 0.1:.2f}s")
        print()
```

Use these sentence-end times as your scene transition points. The gap between sentences is breathing room — place transitions there.

## Transition Budget

Each transition "costs" duration. Account for it:

| Transition | Cost |
|-----------|------|
| Blur crossfade | 0.5–0.65s |
| Push slide | 0.45–0.55s |
| Color blocks | 0.55–0.65s |
| Color dip | 0.5–0.6s |
| Glitch | 0.3–0.4s |
| Zoom through | 0.6–0.7s |

Total transition budget for a 30s video with 5 transitions: ~2.5–3s.
Your actual content runs: 30s - 3s transitions = 27s of scene content.
