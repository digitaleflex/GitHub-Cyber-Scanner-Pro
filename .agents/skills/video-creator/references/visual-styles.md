# Visual Styles — Design System Presets

8 named styles. Copy the YAML into `design.md` and add brand-specific color overrides.

---

## 1. Deconstructed (Neville Brody)
**Mood:** Industrial, raw, tech-aggressive
**Best for:** SaaS, security, developer tools, enterprise tech

```yaml
colors:
  bg: "#0A0A0A"
  bg-elevated: "#1A1A1A"
  accent: "#E63946"
  accent2: "#10b981"
  text: "#FFFFFF"
  muted: "#999999"
  border: "#141111"
typography:
  headline: { fontFamily: "Space Grotesk", fontWeight: 800, letterSpacing: "-0.03em" }
  label: { fontFamily: "Space Mono", fontWeight: 700, textTransform: uppercase, letterSpacing: "0.05em" }
elevation:
  border: "2px solid #141111"
  shadow: "4px 4px 0px #141111"
  shadow-hover: "6px 6px 0px #141111"
motion:
  energy: high
  entry: "back.out(2.5)"
  ambient: "sine.inOut"
  transition: glitch
```

Signature: Scan lines, brutal thick borders, offset shadows, zero border-radius.

---

## 2. Velvet Standard (Massimo Vignelli)
**Mood:** Premium, timeless, luxury enterprise
**Best for:** Luxury brands, enterprise software, investor decks, keynotes

```yaml
colors:
  bg: "#0a0a0a"
  accent: "#1a237e"
  text: "#FFFFFF"
  muted: "#888"
  border: "#333"
typography:
  headline: { fontFamily: "Helvetica Neue", fontWeight: 300, letterSpacing: "0.15em", textTransform: uppercase }
  body: { fontFamily: "Helvetica Neue", fontWeight: 300, lineHeight: 1.6 }
motion:
  energy: low
  entry: "sine.inOut"
  ambient: "sine.inOut"
  transition: blur-crossfade
```

Signature: Generous negative space, centered architecture, wide letter-spacing, slow reveals.

---

## 3. Maximalist Type (Paula Scher)
**Mood:** Loud, kinetic, announcements
**Best for:** Product launches, milestones, high-energy social

```yaml
colors:
  bg: "#0a0a0a"
  accent: "#E63946"
  accent2: "#FFD60A"
  text: "#FFFFFF"
typography:
  headline: { fontFamily: "Anton", fontWeight: 400, textTransform: uppercase, fontSize: "8rem" }
  subhead: { fontFamily: "Space Grotesk", fontWeight: 700 }
motion:
  energy: high
  entry: "expo.out"
  ambient: "power3.out"
  transition: ridged-burn
```

Signature: Type fills 60–80% of frame, overlapping layers, color slams, 2–3s rapid-fire scenes.

---

## 4. Data Drift (Refik Anadol)
**Mood:** Futuristic, AI, immersive
**Best for:** AI products, ML platforms, data companies

```yaml
colors:
  bg: "#0a0a0a"
  accent: "#7c3aed"
  accent2: "#06b6d4"
  text: "#e0e0e0"
  muted: "#666"
typography:
  headline: { fontFamily: "Inter", fontWeight: 200, letterSpacing: "0.05em" }
  body: { fontFamily: "Inter", fontWeight: 300 }
motion:
  energy: medium
  entry: "sine.inOut"
  ambient: "sine.inOut"
  transition: gravitational-lens
```

Signature: Particle fields, light traces, extreme scale shifts, organic morphing.

---

## 5. Shadow Cut (Hans Hillmann)
**Mood:** Dark, cinematic, dramatic
**Best for:** Security products, dramatic reveals, intense launches

```yaml
colors:
  bg: "#0a0a0a"
  surface: "#1a1a1a"
  accent: "#C1121F"
  text: "#f0f0f0"
  muted: "#666"
  border: "#333"
typography:
  headline: { fontFamily: "Oswald", fontWeight: 700, textTransform: uppercase }
  body: { fontFamily: "Inter", fontWeight: 400 }
motion:
  energy: medium
  entry: "power3.out"
  ambient: "sine.inOut"
  transition: domain-warp
```

Signature: Near-monochrome, elements emerge from darkness, heavy vignette, slow creep.

---

## 6. Soft Signal (Stefan Sagmeister)
**Mood:** Intimate, warm, human
**Best for:** Wellness, personal stories, human-centered apps

```yaml
colors:
  bg: "#FFF8EC"
  accent: "#F5A623"
  accent2: "#C4A3A3"
  text: "#2a2a2a"
  muted: "#888"
typography:
  headline: { fontFamily: "Playfair Display", fontWeight: 400, fontStyle: italic }
  body: { fontFamily: "Inter", fontWeight: 300, lineHeight: 1.7 }
motion:
  energy: low
  entry: "sine.inOut"
  ambient: "sine.inOut"
  transition: thermal-distortion
```

Signature: Light canvas, slow drifts, handwritten feel, never corporate.

---

## 7. Folk Frequency (Eduardo Terrazas)
**Mood:** Cultural, vivid, celebratory
**Best for:** Consumer apps, food, community, festive launches

```yaml
colors:
  bg: "#ffffff"
  accent: "#FF1493"
  accent2: "#0047AB"
  accent3: "#FFE000"
  text: "#1a1a1a"
typography:
  headline: { fontFamily: "Fredoka One", fontWeight: 400, fontSize: "4rem" }
  body: { fontFamily: "Nunito", fontWeight: 600 }
motion:
  energy: high
  entry: "back.out(1.6)"
  ambient: "sine.inOut"
  transition: swirl-vortex
```

Signature: Bold patterns, every element bounces/pops, celebratory energy.

---

## 8. Clean Corporate (Swiss Pulse)
**Mood:** Precise, data-driven, professional
**Best for:** B2B SaaS, metrics dashboards, analyst presentations

```yaml
colors:
  bg: "#1a1a1a"
  accent: "#0066FF"
  text: "#FFFFFF"
  muted: "#888"
  border: "#333"
typography:
  headline: { fontFamily: "Helvetica Neue", fontWeight: 700, fontSize: "5rem" }
  stat: { fontFamily: "Helvetica Neue", fontWeight: 700, fontSize: "7rem" }
  label: { fontFamily: "Inter", fontWeight: 400, fontSize: "0.875rem" }
motion:
  energy: high
  entry: "expo.out"
  ambient: none
  transition: cinematic-zoom
```

Signature: Grid-locked, numbers dominate at 80–120px, animated counters, hard cuts.

---

## Custom Design.md Template

```markdown
---
name: [Brand] Video Style
colors:
  bg: "#[hex]"           # Primary background
  bg-2: "#[hex]"         # Elevated surfaces
  accent: "#[hex]"       # Primary action color (CTAs, highlights)
  accent2: "#[hex]"      # Secondary accent (success, secondary actions)
  text: "#[hex]"         # Primary text
  muted: "#[hex]"        # Secondary text
  border: "#[hex]"       # Borders and dividers
typography:
  headline: { fontFamily: "[Font]", fontWeight: 800, letterSpacing: "-0.03em" }
  label: { fontFamily: "[Font]", fontWeight: 700, textTransform: uppercase }
elevation:
  border: "2px solid [border-color]"
  shadow: "4px 4px 0px [border-color]"
motion:
  energy: high | medium | low
  entry: "back.out(2.5)" | "expo.out" | "sine.inOut"
  transition: glitch | blur | push | cover
---

## Overview
[Brand voice in 2 sentences]

## Do's
- [Rule 1]
- [Rule 2]

## Don'ts
- [Anti-pattern 1]
- [Anti-pattern 2]
```
