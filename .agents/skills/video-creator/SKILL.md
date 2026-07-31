---
name: video-creator
description: Full-stack cinematic video production skill. Creates professional, story-driven 1920x1080 MP4 videos for products, services, events, SaaS, enterprises, and brands using HyperFrames HTML compositions with GSAP animation, professional TTS voiceover (Kokoro bm_george/af_heart), Whisper transcription for synced captions, Canvas 2D particle effects, SVG animations, kinetic typography, scribble underlines, burst-line highlights, multi-scene transitions (glitch, push, blur, color blocks), and complete production pipeline (design.md → script → voiceover → transcript → composition → lint → validate → render). Use when asked to create any kind of video — product demo, service promo, event teaser, brand launch, enterprise pitch, social ad, explainer, or announcement.
---

# Video Creator

Professional cinematic video production for products, services, events, and brands. Every output is a 1920×1080 MP4 with voiceover, synced captions, rich animation, and multiple scene transitions.

## Quick Start (3 commands)

```bash
# 1. Scaffold project
npx --yes hyperframes@0.6.51 init my-video

# 2. Generate voiceover
python3 -c "from kokoro_onnx import Kokoro; import soundfile as sf; k=Kokoro('models/kokoro-v1.0.onnx','models/voices-v1.0.bin'); s,r=k.create(open('script.txt').read(),voice='bm_george',speed=0.92,lang='en-gb'); sf.write('narration.wav',s,r)"

# 3. Transcribe for captions
npx --yes hyperframes@0.6.51 transcribe narration.wav --model small.en

# 4. Render
npx --yes hyperframes@0.6.51 render
```

## Production Pipeline

Always follow this sequence — never skip steps:

```
1. BRIEF       → audience, platform, duration, tone
2. SCRIPT      → write narration (~2.5 wps), hook first
3. design.md   → brand colors, fonts, motion energy
4. VOICEOVER   → npx hyperframes tts OR python kokoro_onnx directly
5. TRANSCRIPT  → npx hyperframes transcribe → transcript.json
6. PLAN        → scene rhythm declaration before any HTML
7. BUILD       → layout-first → then GSAP animation
8. LINT        → npx hyperframes lint (0 errors required)
9. VALIDATE    → npx hyperframes validate --no-contrast
10. RENDER     → npx hyperframes render
```

## Step 1 — Brief the Production

Ask (or infer from context):
- **Subject**: product / service / event / brand?
- **Audience**: enterprise, developer, consumer, investor?
- **Platform**: social (15s), website hero (30s), product demo (60s), presentation?
- **Tone**: authoritative, energetic, warm, dramatic, technical?
- **Assets**: brand colors, logo, screenshots, existing copy?

Read [references/brief-templates.md](references/brief-templates.md) for audience-specific starting points.

## Step 2 — Script Writing

**Pacing formula:** 2.5 words per second at natural speed
- 15s → ~37 words
- 30s → ~75 words  
- 60s → ~150 words

**Structure:** Hook → Problem/Story → Proof → CTA

**Hook patterns (never use generic openings):**
- Bold claim: *"The financial infrastructure that powers modern engineering."*
- Contrast: *"Your agents are deployed. Nobody's watching them."*
- Question: *"What if your entire team — human and AI — moved as one?"*
- Number shock: *"Forty percent of enterprise AI projects fail at governance."*

**Voice register by audience:**
- Enterprise → declarative, measured, `bm_george` voice
- Developer → direct, technical, `am_adam` voice
- Consumer → warm, story-driven, `af_heart` voice
- Startup/energy → punchy, fast, `af_sky` voice

Write numbers as words in the script (TTS reads literally): `10x` → `ten times`, `$2.3T` → `nearly two point three trillion dollars`.

Read [references/script-patterns.md](references/script-patterns.md) for full script examples per video type.

## Step 3 — Design System (design.md)

Always create `design.md` before writing any HTML. It defines the brand contract.

**Required fields:**
```yaml
colors:
  bg: "#0A0A0A"           # primary background (dark or light)
  accent: "#E63946"       # main action color
  accent2: "#10b981"      # secondary accent
  text: "#FFFFFF"
  muted: "#999999"
  border: "#141111"
typography:
  headline: { fontFamily: "Space Grotesk", fontWeight: 800 }
  label:    { fontFamily: "Space Mono", fontWeight: 700 }
motion:
  energy: high | medium | low
  transition: glitch | blur | push | cover
```

**Visual style picker** (read [references/visual-styles.md](references/visual-styles.md) for full YAML tokens):
| Style | Best for | Signature |
|-------|----------|-----------|
| Deconstructed | Tech, SaaS, security | Scan lines, brutal borders, Space Grotesk/Mono |
| Maximalist | Launches, announcements | Giant type fills frame, color slams |
| Velvet Standard | Enterprise, luxury | Wide letter-spacing, generous space |
| Data Drift | AI, ML, fintech | Particle fields, thin futuristic sans |
| Shadow Cut | Dramatic reveals, security | Near-monochrome + blood accent |
| Folk Frequency | Consumer, community | Bold color, bounce, pattern |

## Step 4 — Voiceover Generation

### Via npx (preferred when available)
```bash
npx --yes hyperframes@0.6.51 tts script.txt --voice bm_george --output narration.wav --speed 0.92
```

### Via Python direct (fallback if npx fails)
```bash
# First-run: download models (~340MB total, cached)
curl -L -o models/kokoro-v1.0.onnx \
  https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx
curl -L -o models/voices-v1.0.bin \
  https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin

# Generate
python3 << 'EOF'
from kokoro_onnx import Kokoro
import soundfile as sf
k = Kokoro("models/kokoro-v1.0.onnx", "models/voices-v1.0.bin")
text = open("script.txt").read().strip()
samples, rate = k.create(text, voice="bm_george", speed=0.92, lang="en-gb")
sf.write("narration.wav", samples, rate)
print(f"Generated: {len(samples)/rate:.1f}s")
EOF
```

**Voice guide:**
| Voice | Character | Use for |
|-------|-----------|---------|
| `bm_george` | Authoritative British male | Enterprise, B2B, keynote |
| `bf_emma` | Clear British female | Tutorial, documentation, premium |
| `am_michael` | Confident American male | Marketing, promo, SaaS |
| `am_adam` | Neutral American male | Developer tools, explainers |
| `af_heart` | Warm American female | Consumer, wellness, personal |
| `af_sky` | Energetic American female | Social ads, launches, lifestyle |

**Install dependencies** (one time):
```bash
pip install kokoro-onnx soundfile
```

## Step 5 — Transcription (Word-Level Captions)

```bash
npx --yes hyperframes@0.6.51 transcribe narration.wav --model small.en
# → produces transcript.json with word-level timestamps
```

Output format:
```json
[
  { "text": "Enterprise", "start": 0.03, "end": 0.82 },
  { "text": "teams", "start": 0.82, "end": 1.18 }
]
```

Use timestamps to:
1. Anchor scene transitions to spoken sentence boundaries
2. Drive per-word caption animations (pop in per word)
3. Sync visual emphasis (burst lines, highlights) to key nouns

## Step 6 — Scene Rhythm Planning

**Declare the rhythm before writing any HTML.** Name the pattern:

```
SLAM → breathe → CASCADE → PUNCH → CTA           (product launch)
PAIN → GLIMPSE → PROOF → CONVICTION              (problem/solution)
HOOK → STORY → PROOF → SCALE → CTA              (enterprise pitch)
TEASE → REVEAL → DETAIL → DETAIL → CTA          (feature showcase)
```

**Scene timing template (30s enterprise):**
```
Scene 1: Problem/Hook      0–7s    (sentence 1-2 of VO)
Scene 2: Platform intro    7–10s   (sentence 3)
Scene 3: Feature demo     10–17s   (sentence 4-5)
Scene 4: Proof/stats      17–21s   (sentence 6)
Scene 5: Scale            21–28s   (sentence 7-8)
Scene 6: CTA              28–32s   (sentence 9)
```

Read [references/scene-timing.md](references/scene-timing.md) for timing templates per duration.

## Step 7 — Build the Composition

### HTML Structure (mandatory)
```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>
body { margin:0; width:1920px; height:1080px; overflow:hidden; background:#0A0A0A; }
.scene { position:absolute; top:0; left:0; width:1920px; height:1080px; overflow:hidden; }
#s1 { z-index:1; background:#0A0A0A; }        /* scene 1 — visible by default */
#s2 { z-index:2; background:#0A0A0A; opacity:0; }  /* all others hidden */
</style>
</head>
<body>
<div id="root" data-composition-id="main" data-width="1920" data-height="1080"
     data-start="0" data-duration="32">

  <!-- Audio (separate from video, always) -->
  <audio id="vo" data-start="0" data-duration="31.1" data-track-index="10"
         data-volume="1" src="narration.wav"></audio>

  <!-- Transition overlays (always above all scenes) -->
  <div id="ov-r" style="position:absolute;top:0;left:0;width:1920px;height:1080px;z-index:80;background:#E63946;opacity:0;pointer-events:none"></div>

  <!-- Scenes -->
  <div id="s1" class="scene"><!-- content --></div>
  <div id="s2" class="scene"><!-- content --></div>
</div>

<script>
window.__timelines = window.__timelines || {};
var tl = gsap.timeline({ paused: true });
// ... animations ...
window.__timelines["main"] = tl;
</script>
</body>
</html>
```

### Layout Before Animation (non-negotiable)
1. Build the **end-state** of each scene in pure CSS first
2. Content containers: `display:flex; flex-direction:column; padding:120px 160px; width:100%; height:100%;`
3. Never use `position:absolute; top:Npx` on content — only on decoratives
4. Add `gsap.fromTo()` after layout is confirmed
5. Run `npx hyperframes inspect` to verify no overflow

### GSAP Rules
```js
// ALWAYS use fromTo (not from) inside scenes for deterministic seeking
tl.fromTo("#el", { opacity:0, y:40 }, { opacity:1, y:0, duration:0.5, ease:"back.out(2)" }, 1.2);

// NEVER bare gsap.to() for ambient motion — must be on tl
tl.to("#glow", { scale:1.08, yoyo:true, repeat:4, duration:2, ease:"sine.inOut" }, 0);

// NEVER repeat:-1 (breaks capture engine) — calculate finite repeats
// For a 4s beat: Math.ceil(4 / 2) = 2 cycles
tl.to("#pulse", { scale:1.1, yoyo:true, repeat:3, duration:2, ease:"sine.inOut" }, 0);

// Hard-kill scene exits
tl.set("#s1", { opacity:0, visibility:"hidden" }, exitTime);

// Always register
window.__timelines["main"] = tl;
```

## Scene Density Requirements

Every scene MUST have:
- **Background layer**: radial glow + grid/pattern + ghost text + scanline (2–5 elements)
- **Content layer**: headline + subtitle + supporting element (3–5 elements)
- **Foreground accents**: corner marks + divider line + label/badge (3+ elements)
- **Total**: 8–10 visual elements minimum

Read [references/scene-density.md](references/scene-density.md) for per-scene element checklists.

## Transition Library

Read [references/transitions.md](references/transitions.md) for full code. Quick picks:

| Energy | Transition | Code pattern |
|--------|-----------|--------------|
| Chaos → Clarity | **Blur crossfade** | `tl.to(old, {filter:"blur(14px)",scale:1.04,opacity:0,duration:0.5})` |
| Level up | **Vertical push** | `tl.to(old,{y:-1080,duration:0.45,ease:"power3.inOut"}, T)` |
| Next item | **Push slide left** | `tl.to(old,{x:-1920,duration:0.45,ease:"power3.inOut"}, T)` |
| Hard cut | **Color dip to black** | `tl.to("#ov-k",{opacity:1,duration:0.25})` then `tl.set(new,{opacity:1})` |
| Big moment | **Staggered color blocks** | Red then green block slides across, swaps scene underneath |
| Industrial | **Glitch** | RGB overlay jitter, 6 frames at ±40px, 0.35s |

**No exit animations** before transitions except the final scene's fade to black.

## Animation Techniques Library

### 1. Canvas 2D Particle Field (background ambience)
```html
<canvas id="bg-canvas" width="1920" height="1080" style="position:absolute;top:0;left:0;z-index:1"></canvas>
<script>
var c=document.getElementById("bg-canvas"),ctx=c.getContext("2d");
function h(x,y){var n=x*374761393+y*668265263;n=(n^(n>>13))*1274126177;return((n^(n>>16))&0x7fffffff)/0x7fffffff}
var N=120, pts=[];
for(var i=0;i<N;i++) pts.push({bx:h(i,0)*1920,by:h(i,1)*1080,vx:(h(i,3)-0.5)*0.3,vy:(h(i,4)-0.5)*0.2,r:1+h(i,2)*2.5});
var px={t:0};
tl.to(px,{t:DURATION,duration:DURATION,ease:"none",onUpdate:function(){
  var ti=px.t;
  ctx.clearRect(0,0,1920,1080);
  // grid
  ctx.strokeStyle="rgba(230,57,70,0.04)"; ctx.lineWidth=1;
  for(var gx=0;gx<1920;gx+=160){ctx.beginPath();ctx.moveTo(gx,0);ctx.lineTo(gx,1080);ctx.stroke()}
  for(var gy=0;gy<1080;gy+=120){ctx.beginPath();ctx.moveTo(0,gy);ctx.lineTo(1920,gy);ctx.stroke()}
  // particles
  for(var i=0;i<N;i++){
    var p=pts[i],x=(p.bx+p.vx*ti*60)%1920,y=(p.by+p.vy*ti*60)%1080;
    if(x<0)x+=1920;if(y<0)y+=1080;
    ctx.fillStyle="rgba(230,57,70,"+(0.15+0.1*h(i,Math.floor(ti*6)))+")";
    ctx.fillRect(x-p.r/2,y-p.r/2,p.r,p.r);
  }
}},0);
</script>
```

### 2. SVG Scribble Underline
```html
<span style="position:relative;display:inline-block">
  key phrase
  <svg style="position:absolute;left:0;bottom:-8px;width:100%;height:20px" viewBox="0 0 500 20" preserveAspectRatio="none">
    <path id="scr" fill="none" stroke="#E63946" stroke-width="3" stroke-linecap="round"
      stroke-dasharray="800" stroke-dashoffset="800"
      d="M0,10 Q62,0 125,10 Q187,20 250,10 Q312,0 375,10 Q437,20 500,10"/>
  </svg>
</span>
<script>
// after path element exists in DOM:
var p=document.getElementById("scr"), l=p.getTotalLength();
gsap.set(p,{strokeDasharray:l,strokeDashoffset:l});
tl.to("#scr",{strokeDashoffset:0,duration:0.7,ease:"power1.inOut"}, START);
</script>
```

### 3. Per-Word Kinetic Headline (voice-synced)
```html
<div id="headline">
  <span class="w" id="w0">Ship</span>
  <span class="w" id="w1">faster.</span>
  <span class="w" id="w2">CyberAgent.</span>
</div>
<script>
// timings from transcript.json word start times
var times = [0.0, 0.3, 0.7];
var eases = ["back.out(2.5)", "expo.out", "back.out(3)"];
var dirs  = [{y:60,rotation:4}, {y:80,scale:0.7}, {scale:0.5,rotation:-5}];
times.forEach(function(t,i){
  tl.fromTo("#w"+i,
    Object.assign({opacity:0},dirs[i]),
    Object.assign({opacity:1,y:0,scale:1,rotation:0,duration:0.45,ease:eases[i]},{}),
    t);
});
</script>
```

### 4. Burst Lines (stat reveal)
```html
<div style="position:relative;display:inline-block">
  <div id="stat-num">10×</div>
  <div style="position:absolute;top:50%;left:50%;width:0;height:0" id="burst">
    <span style="position:absolute;display:block;width:3px;height:52px;background:#E63946;left:-1.5px;top:-52px;transform:rotate(0deg);transform-origin:bottom center;opacity:0"></span>
    <span style="position:absolute;display:block;width:3px;height:38px;background:#E63946;left:-1.5px;top:-38px;transform:rotate(36deg);transform-origin:bottom center;opacity:0"></span>
    <!-- repeat for 8-12 lines at 30-45deg increments, vary lengths 36-60px -->
  </div>
</div>
<script>
tl.fromTo("#burst span",{scaleY:0,opacity:0},{scaleY:1,opacity:1,duration:0.35,ease:"power2.out",stagger:0.025},STAT_TIME);
</script>
```

### 5. Character-by-Character Terminal Typing
```html
<div style="font-family:'Space Mono',monospace">
  <span style="color:#E63946">❯ </span>
  <span id="cmd"></span>
  <span id="cur" style="display:inline-block;width:10px;height:18px;background:#E63946;vertical-align:text-bottom"></span>
</div>
<script>
var CMD="your-cli-command --flag value";
var el=document.getElementById("cmd");
tl.fromTo("#cur",{opacity:1},{opacity:0,duration:0.12,yoyo:true,repeat:12,ease:"steps(1)"},START);
for(var i=0;i<CMD.length;i++){
  (function(idx){
    tl.call(function(){ el.textContent=CMD.substring(0,idx+1); },[],START+(idx/CMD.length)*0.9);
  })(i);
}
</script>
```

### 6. Circle Highlight Around Key Word
```html
<span style="position:relative;display:inline-block">
  CyberAgent
  <span id="ring" style="position:absolute;top:50%;left:50%;width:115%;height:155%;
    transform:translate(-50%,-50%) rotate(-2deg) scale(0);
    border:4px solid #E63946;border-radius:50%;pointer-events:none"></span>
</span>
<script>
tl.fromTo("#ring",
  {scale:0,rotation:-15,transformOrigin:"50% 50%"},
  {scale:1,rotation:-2,duration:0.55,ease:"back.out(1.7)"},
  RING_TIME);
</script>
```

### 7. Synced Caption System
```js
// Read transcript.json → group into 3-4 word chunks → render per word
var WORDS = [ /* from transcript.json */ ];
var groups = [];
for(var i=0;i<WORDS.length;){
  var g=[]; while(i<WORDS.length && g.length<4){ g.push(WORDS[i]); i++; if(g[g.length-1].t.match(/[.,!?]$/) && g.length>=2) break; }
  groups.push(g);
}
var cap=document.getElementById("captions"); // position:absolute;bottom:52px;width:1920px;text-align:center;z-index:99
groups.forEach(function(grp,gi){
  var div=document.createElement("div");
  div.style.cssText="position:absolute;bottom:0;left:50%;transform:translateX(-50%);display:flex;gap:8px;opacity:0";
  div.id="cg"+gi;
  grp.forEach(function(w,wi){
    var sp=document.createElement("span");
    sp.id="cw"+gi+"_"+wi;
    sp.textContent=w.text;
    sp.style.cssText="font-size:52px;font-weight:700;color:#fff;opacity:0;display:inline-block;text-shadow:0 2px 24px rgba(0,0,0,0.9)";
    // Brand names in accent color
    if(w.text.match(/CyberAgent|YourBrand/)) sp.style.color="#E63946";
    div.appendChild(sp);
  });
  cap.appendChild(div);
  var gs=grp[0].start, ge=grp[grp.length-1].end+0.1;
  tl.fromTo("#cg"+gi,{opacity:0},{opacity:1,duration:0.08},gs);
  tl.to("#cg"+gi,{opacity:0,duration:0.12},ge);
  tl.set("#cg"+gi,{opacity:0},ge+0.12);
  grp.forEach(function(w,wi){
    tl.fromTo("#cw"+gi+"_"+wi,{opacity:0,y:8,scale:0.88},{opacity:1,y:0,scale:1,duration:0.12,ease:"back.out(2)"},w.start);
  });
});
```

## Scene Templates by Type

Read [references/scene-templates.md](references/scene-templates.md) for complete HTML+CSS for:
- Problem/pain scene (split layout: copy left, terminal chaos right)
- Platform reveal (centered cinematic, scribble underline)
- Feature diagram (orchestration flow, approval gates, connectors)
- Proof stats (3-column stat blocks with burst lines)
- Org chart / scale diagram (hierarchy animation)
- CTA slam (full accent-color, diagonal stripes, circle ring)

## Output Quality Checklist

Before render:
- [ ] `npx hyperframes lint` → 0 errors
- [ ] `npx hyperframes validate --no-contrast` → no console errors
- [ ] `npx hyperframes inspect` → no unintentional overflow
- [ ] All `gsap.fromTo()` (not `from()`) for clip elements
- [ ] All ambient loops on `tl` (not bare `gsap.to()`)
- [ ] All scene exits have `tl.set(el, {visibility:"hidden"}, exitTime)`
- [ ] No `repeat:-1` anywhere
- [ ] No exit animations before transitions (except final scene)
- [ ] Audio in `<audio>` element with `data-track-index`, not `<video>`
- [ ] `window.__timelines["main"] = tl` registered

## References

- [references/brief-templates.md](references/brief-templates.md) — Starting briefs for 8 video types
- [references/script-patterns.md](references/script-patterns.md) — Full script examples with word counts
- [references/visual-styles.md](references/visual-styles.md) — 8 named visual styles with YAML tokens
- [references/scene-timing.md](references/scene-timing.md) — Timing templates for 15s/30s/60s
- [references/scene-density.md](references/scene-density.md) — Element checklists per scene type
- [references/scene-templates.md](references/scene-templates.md) — Complete HTML for 6 scene archetypes
- [references/transitions.md](references/transitions.md) — Full transition code for all 8 types
- [references/enterprise-patterns.md](references/enterprise-patterns.md) — Org charts, approval gates, RACI flows
- [references/caption-system.md](references/caption-system.md) — Full caption renderer with styling guide
- [references/voice-guide.md](references/voice-guide.md) — Voice selection, speed, language, model setup
