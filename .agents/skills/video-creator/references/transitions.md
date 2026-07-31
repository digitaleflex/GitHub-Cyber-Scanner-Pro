# Transition Code Reference

All 8 transition types with copy-paste GSAP code. `T` = transition start time, `old` = outgoing scene ID, `new` = incoming scene ID.

**Non-negotiable rules:**
- NO exit animations before transition — scenes must be fully visible at T
- Hard-kill outgoing scene after swap: `tl.set(old, {opacity:0, visibility:"hidden"}, T+duration+0.1)`
- Scene 1 visible by default (no opacity:0). Scenes 2+ have opacity:0 in CSS.
- Add `overwrite:"auto"` to any tween that restates a property already set

---

## 1. Blur Crossfade (Chaos → Clarity)

**Use when:** Emotional shift, resolving tension, chaos becoming order.

```js
// Setup: place incoming scene behind outgoing at T
tl.to(old, { filter:"blur(14px)", scale:1.04, opacity:0, duration:0.5, ease:"power2.inOut" }, T);
tl.fromTo(new, { filter:"blur(14px)", scale:0.96, opacity:0 },
  { filter:"blur(0px)", scale:1, opacity:1, duration:0.5, ease:"power2.inOut" }, T+0.1);
tl.set(old, { opacity:0, visibility:"hidden" }, T+0.65);
// Total: ~0.65s
```

Adjust blur: 6px (snappy) → 14px (standard) → 25px (dreamy/luxury).

---

## 2. Vertical Push Up (Level Up, Progress)

**Use when:** Moving forward, ascending, upgrading.

```js
tl.to(old, { y:-1080, duration:0.45, ease:"power3.inOut" }, T);
tl.fromTo(new, { y:1080, opacity:1 }, { y:0, duration:0.45, ease:"power3.inOut" }, T);
tl.set(old, { opacity:0, visibility:"hidden" }, T+0.55);
// Total: ~0.55s
```

---

## 3. Push Slide Left (Sequential, Next Item)

**Use when:** Moving through a list, continuing a journey.

```js
tl.to(old, { x:-1920, duration:0.45, ease:"power3.inOut" }, T);
tl.fromTo(new, { x:1920, opacity:1 }, { x:0, duration:0.45, ease:"power3.inOut" }, T);
tl.set(old, { opacity:0, visibility:"hidden" }, T+0.55);
// Total: ~0.55s
```

Reverse for "back": flip x directions.

---

## 4. Staggered Color Blocks (High Impact Reveal)

**Use when:** Big moment, brand statement, CTA.
**Requires:** Two overlay divs `#ov-r` and `#ov-g` absolutely positioned above all scenes (z-index 80+).

```js
// CSS for overlays:
// #ov-r, #ov-g { position:absolute; top:0; left:0; width:1920px; height:1080px; z-index:80; opacity:0; pointer-events:none; }
// #ov-r { background:#E63946; }
// #ov-g { background:#10b981; }

tl.set("#ov-r", { x:-1920, opacity:1 }, T-0.01);
tl.set("#ov-g", { x:-1920, opacity:1 }, T-0.01);
tl.to("#ov-r", { x:0, duration:0.22, ease:"power3.inOut" }, T);
tl.to("#ov-g", { x:0, duration:0.22, ease:"power3.inOut", overwrite:"auto" }, T+0.07);
tl.set(old, { opacity:0, visibility:"hidden" }, T+0.2);
tl.set(new, { opacity:1 }, T+0.2);
tl.to("#ov-r", { x:1920, duration:0.22, ease:"power3.inOut" }, T+0.28);
tl.to("#ov-g", { x:1920, duration:0.22, ease:"power3.inOut", overwrite:"auto" }, T+0.35);
tl.set("#ov-r", { opacity:0 }, T+0.6);
tl.set("#ov-g", { opacity:0 }, T+0.6);
// Total: ~0.6s
```

---

## 5. Color Dip to Black (Dramatic Cut)

**Use when:** Topic change, scene reset, dramatic pause.
**Requires:** Overlay `#ov-k` with `background:#0A0A0A`.

```js
tl.to("#ov-k", { opacity:1, duration:0.25, ease:"power2.in" }, T);
tl.set(old, { opacity:0, visibility:"hidden" }, T+0.25);
tl.set(new, { opacity:1 }, T+0.25);
tl.to("#ov-k", { opacity:0, duration:0.25, ease:"power2.out" }, T+0.28);
tl.set("#ov-k", { opacity:0 }, T+0.6);
// Total: ~0.6s
```

---

## 6. Glitch (RGB Jitter — Industrial/Tech)

**Use when:** Tech reveals, agent/AI moments, industrial brand.
**Requires:** Three overlay divs `#glitch-r`, `#glitch-g`, `#glitch-b`.

```js
// CSS:
// #glitch-r { background:rgba(230,57,70,0.35); }
// #glitch-g { background:rgba(16,185,129,0.35); }
// #glitch-b { background:rgba(20,17,17,0.35); }

tl.set("#glitch-r", { opacity:1, x:40, y:-8 }, T);
tl.set("#glitch-g", { opacity:1, x:-30, y:12 }, T);
tl.set("#glitch-b", { opacity:1, x:15, y:-20 }, T);
tl.set(old, { x:-15 }, T);
tl.to("#glitch-r", { x:-45, y:20, duration:0.03, ease:"none", overwrite:"auto" }, T+0.03);
tl.to("#glitch-g", { x:55, y:-15, duration:0.03, ease:"none", overwrite:"auto" }, T+0.03);
tl.to(old,        { x:25, duration:0.03, ease:"none", overwrite:"auto" }, T+0.06);
tl.to("#glitch-r", { x:30, y:-30, duration:0.03, ease:"none", overwrite:"auto" }, T+0.06);
tl.to("#glitch-g", { x:-50, y:25, duration:0.03, ease:"none", overwrite:"auto" }, T+0.06);
tl.to(old,        { x:-20, duration:0.03, ease:"none", overwrite:"auto" }, T+0.09);
tl.to("#glitch-b", { x:-35, y:15, duration:0.03, ease:"none", overwrite:"auto" }, T+0.09);
tl.to(old,        { x:10, duration:0.03, ease:"none", overwrite:"auto" }, T+0.12);
tl.to("#glitch-r", { x:-60, y:10, duration:0.03, ease:"none", overwrite:"auto" }, T+0.12);
// Swap
tl.set(old, { opacity:0, x:0, visibility:"hidden" }, T+0.18);
tl.set(new, { opacity:1 }, T+0.18);
// Clear overlays
tl.set("#glitch-r", { opacity:0, x:0, y:0 }, T+0.35);
tl.set("#glitch-g", { opacity:0, x:0, y:0 }, T+0.35);
tl.set("#glitch-b", { opacity:0, x:0, y:0 }, T+0.35);
// Total: ~0.35s
```

---

## 7. Zoom Through (Scale Punch)

**Use when:** Pulling focus into the next scene, dramatic zoom.

```js
tl.to(old, { scale:1.2, filter:"blur(20px)", opacity:0, duration:0.3, ease:"power3.in" }, T);
tl.fromTo(new, { scale:0.75, filter:"blur(20px)", opacity:0 },
  { scale:1, filter:"blur(0px)", opacity:1, duration:0.5, ease:"expo.out" }, T+0.15);
tl.set(old, { opacity:0, visibility:"hidden" }, T+0.5);
// Total: ~0.65s
```

---

## 8. Vertical Push Down (Reveal from Above)

**Use when:** Unveiling, dropping into a new context.

```js
tl.to(old, { y:1080, duration:0.45, ease:"power3.inOut" }, T);
tl.fromTo(new, { y:-1080, opacity:1 }, { y:0, duration:0.45, ease:"power3.inOut" }, T);
tl.set(old, { opacity:0, visibility:"hidden" }, T+0.55);
// Total: ~0.55s
```

---

## Transition Selector Matrix

| Emotional shift | Best transition |
|-----------------|-----------------|
| Chaos → order | Blur crossfade |
| Low → high energy | Staggered color blocks |
| Sequential steps | Push slide left |
| Topic change | Color dip to black |
| Tech/industrial | Glitch |
| Scale reveal | Zoom through |
| Progress/level up | Vertical push up |
| Dramatic unveil | Vertical push down |

## Timing Cheatsheet

| Feel | Duration | Ease |
|------|----------|------|
| Snappy | 0.2–0.25s | power4.inOut |
| Standard | 0.4–0.5s | power3.inOut |
| Dramatic | 0.5–0.65s | power2.inOut |
| Luxe | 0.6–0.8s | sine.inOut |
