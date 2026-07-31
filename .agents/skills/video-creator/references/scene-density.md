# Scene Density — Element Checklists

Every scene needs 8–10 visual elements. This prevents the "empty slide" look that telegraphs AI-generated video.

## Mandatory Layers (All Scenes)

### Background Layer (2–5 elements)
Pick 2–5 from this list per scene:

- [ ] **Radial glow** — `radial-gradient(circle, rgba(ACCENT, 0.15) 0%, rgba(ACCENT, 0) 70%)` at 400–600px, breathing animation
- [ ] **Grid lines** — horizontal and vertical, `rgba(ACCENT, 0.05)` opacity, 100–200px spacing
- [ ] **Ghost text** — large word(s) at 2–4% opacity, slow drift `sine.inOut 4s`
- [ ] **Scan line** — 2–4px height, sweeps top→bottom once or twice per scene
- [ ] **Canvas particles** — deterministic dots drifting, accent color at 15–25% opacity
- [ ] **Diagonal stripes** — skewX(-8deg) panels at 5–8% opacity
- [ ] **Noise/grain** — CSS noise overlay at 2–3% opacity

### Content Layer (3–5 elements)
The actual message:
- [ ] **Kicker/eyebrow** — Space Mono, 12–14px, uppercase, accent color, left-border accent rule
- [ ] **Headline** — Space Grotesk, 68–120px, weight 800, primary text color
- [ ] **Subheadline or body** — 18–28px, muted/secondary color
- [ ] **Primary UI element** — diagram, card, dashboard, chart, or code block
- [ ] **Secondary content** — supporting text, list items, or data

### Foreground Accents (3+ elements)
Details that make it look produced:
- [ ] **Corner marks** — 4 corners, 40–44px, accent at 20–25% opacity
- [ ] **Horizontal rule** — 60–160px wide, 3–5px tall, accent color or gradient, grows with `scaleX`
- [ ] **Label badges** — monospace, uppercase, bordered, accent background
- [ ] **Vertical divider** — between split-layout columns
- [ ] **Timestamp/metadata** — `LIVE — [LOCATION]` in small Space Mono, muted color

---

## Per-Scene Density Checklist

### Scene 1: Hook/Problem
```
BG:  ✓ Canvas particles  ✓ Grid lines  ✓ Ghost text
     ✓ Scanline sweep
MG:  ✓ Kicker label  ✓ Big headline  ✓ Subtext
     ✓ Terminal/chaos blocks (3–4)
FG:  ✓ Corner marks (4)  ✓ Vertical divider
Total: 11–14 elements ✅
```

### Scene 2: Platform Reveal
```
BG:  ✓ Radial glow (center)  ✓ Grid (subtle, fading)
MG:  ✓ Badge  ✓ Category tag  ✓ Big headline (2 lines)
     ✓ Scribble underline  ✓ Description text
FG:  ✓ Corner marks (4)  ✓ Accent rule
Total: 10–12 elements ✅
```

### Scene 3: Feature/Orchestration
```
BG:  ✓ Radial glow (subtle)  ✓ Grid continuation
MG:  ✓ Left column copy (kicker + headline + 3 list items)
     ✓ Right diagram (3–4 nodes + connectors + gate)
FG:  ✓ Corner marks (4)  ✓ Left border accent
Total: 12–16 elements ✅
```

### Scene 4: Proof Stats
```
BG:  ✓ Canvas or radial glow  ✓ Diagonal stripes (subtle)
MG:  ✓ 3 stat blocks × (accent bar + label + number + burst + description)
FG:  ✓ Corner marks (4)  ✓ Top border line
Total: 12–17 elements ✅
```

### Scene 5: Scale/Org Chart
```
BG:  ✓ Grid (very subtle)  ✓ Glow (bottom or corner)
MG:  ✓ Left: kicker + headline + body + tag row (5–6 tags)
     ✓ Right: org chart nodes + connectors
FG:  ✓ Corner marks (4)  ✓ Vertical border between columns
Total: 14–20 elements ✅
```

### Scene 6: CTA
```
BG:  ✓ Full accent-color bg  ✓ Diagonal stripes (darker shade, 3 panels)
MG:  ✓ Pre-tag  ✓ Per-word headline (3 words)  ✓ Circle ring
     ✓ Sub-description  ✓ URL box  ✓ CTA button
FG:  ✓ White corner marks (4)  ✓ By-line
Total: 12–15 elements ✅
```

---

## Anti-Patterns (Too Sparse)

❌ Solid black background with just a headline — add radial glow + grid + ghost text
❌ Three empty feature cards with no corner marks — add index numbers + icons + descriptions  
❌ Stats without accent bars or burst lines — add both
❌ CTA without stripes or ring animation — add both

## Ambient Motion Requirements

Every decorative element MUST have motion on the GSAP timeline (not standalone):

```js
// ✓ Correct — on tl, seekable
tl.to("#glow", { scale:1.08, yoyo:true, repeat:3, duration:2.5, ease:"sine.inOut" }, SCENE_START);
tl.to("#ghost", { y:-12, yoyo:true, repeat:2, duration:4, ease:"sine.inOut" }, SCENE_START);

// ✗ Wrong — standalone, invisible in render
gsap.to("#glow", { scale:1.08, yoyo:true, repeat:-1, duration:2.5, ease:"sine.inOut" });
```

**Calculate finite repeat count from scene duration:**
```js
var sceneDur = 6.5;       // scene lasts 6.5 seconds
var cycleDur = 2.5;        // one breath cycle = 2.5s
var repeats = Math.ceil(sceneDur / cycleDur); // → 3 repeats
tl.to("#glow", { scale:1.08, yoyo:true, repeat:repeats, duration:cycleDur, ease:"sine.inOut" }, T);
```
