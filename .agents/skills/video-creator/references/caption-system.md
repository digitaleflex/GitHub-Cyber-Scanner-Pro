# Caption System — Synced Word-Level Captions

Full implementation from transcript.json to rendered captions.

## HTML Structure

Add this div inside `#root`, above all scenes (z-index: 99):

```html
<div id="captions" style="position:absolute;bottom:52px;left:0;width:1920px;
  display:flex;justify-content:center;z-index:99;pointer-events:none"></div>
```

## Complete Caption Renderer

Drop this into your `<script>` block, before the timeline:

```js
/* ── CAPTION SYSTEM ──────────────────────────────── */
var TRANSCRIPT = [
  // Paste your transcript.json content here as a JS array
  {text:"Enterprise",start:0.03,end:0.82},
  {text:"teams",start:0.82,end:1.18},
  // ...
];

// Word class overrides — add brand names, keywords, stats
var WORD_CLASSES = {
  "CyberAgent": "brand",    // accent color (red)
  "YourBrand":  "brand",
  "orchestration": "kw",    // keyword highlight
  "approval": "kw",
  "accountability": "kw",
  // numbers get "stat" class automatically if they match /^\d/
};

// Group words into 3-4 word caption chunks, breaking on punctuation
function groupWords(words, maxPerGroup) {
  var groups = [], i = 0;
  while (i < words.length) {
    var g = [];
    while (i < words.length && g.length < (maxPerGroup || 4)) {
      g.push(words[i]); i++;
      var t = g[g.length-1].text;
      if (t.match(/[.,!?]$/) && g.length >= 2) break;
    }
    if (g.length) groups.push(g);
  }
  return groups;
}

// Render captions and add to timeline
function buildCaptions(tl, transcript) {
  var groups = groupWords(transcript, 4);
  var cap = document.getElementById("captions");

  groups.forEach(function(grp, gi) {
    var div = document.createElement("div");
    div.id = "cg" + gi;
    div.style.cssText = [
      "position:absolute;bottom:0;left:50%;",
      "transform:translateX(-50%);",
      "display:flex;gap:10px;flex-wrap:wrap;",
      "justify-content:center;max-width:1400px;opacity:0"
    ].join("");

    grp.forEach(function(w, wi) {
      var sp = document.createElement("span");
      sp.id = "cw" + gi + "_" + wi;
      sp.textContent = w.text;

      // Determine class
      var cls = WORD_CLASSES[w.text.replace(/[.,!?]$/,"")] || "";
      if (!cls && w.text.match(/^\d/)) cls = "stat";

      // Style by class
      var color = cls === "brand" ? "#E63946" :
                  cls === "kw"    ? "#10b981" :
                  cls === "stat"  ? "#E63946" :
                                    "#FFFFFF";
      var weight = (cls === "brand" || cls === "stat") ? "800" : "700";

      sp.style.cssText = [
        "font-family:'Space Grotesk',sans-serif;",
        "font-size:52px;",
        "font-weight:" + weight + ";",
        "color:" + color + ";",
        "opacity:0;",
        "display:inline-block;",
        "text-shadow:0 2px 24px rgba(0,0,0,0.9),0 0 2px rgba(0,0,0,1);",
        "letter-spacing:-0.01em;"
      ].join("");

      if (cls === "brand") sp.style.fontStyle = "italic";

      div.appendChild(sp);
    });

    cap.appendChild(div);

    // Group show/hide
    var gStart = grp[0].start;
    var gEnd   = grp[grp.length-1].end + 0.12;

    tl.fromTo("#cg"+gi, {opacity:0}, {opacity:1, duration:0.08}, gStart);
    tl.to("#cg"+gi, {opacity:0, duration:0.12}, gEnd);
    tl.set("#cg"+gi, {opacity:0}, gEnd + 0.12);

    // Per-word pop
    grp.forEach(function(w, wi) {
      tl.fromTo(
        "#cw"+gi+"_"+wi,
        {opacity:0, y:8, scale:0.88},
        {opacity:1, y:0, scale:1, duration:0.12, ease:"back.out(2)"},
        w.start
      );
    });
  });
}

// Call it:
buildCaptions(tl, TRANSCRIPT);
/* ─────────────────────────────────────────────────── */
```

## Caption Sizing Guide

| Screen size | Font size | Max width | Gap |
|-------------|-----------|-----------|-----|
| 1920×1080   | 52px      | 1400px    | 10px |
| 1080×1920 (portrait) | 60px | 900px | 8px |

## Position Rules

- Landscape: `bottom: 52px` — below lower third but above letterbox
- Portrait: adjust to `bottom: 120px` to clear mobile UI chrome
- Never cover the focal point of any scene
- Use `z-index: 99` to ensure always on top of all scene content

## Styling Variations

### Boxed / Pill style (higher readability)
```css
.cap-word {
  background: rgba(0,0,0,0.75);
  padding: 4px 10px;
  border-radius: 4px;
}
```

### High contrast (accessibility)
```css
.cap-word {
  color: #FFFF00;
  text-shadow: 2px 2px 0px #000, -2px -2px 0px #000;
}
```

### Minimal (luxury brands)
```css
/* Reduce font-size to 36px, lighter weight 400, wider letter-spacing */
.cap-word {
  font-size: 36px;
  font-weight: 400;
  letter-spacing: 0.04em;
}
```

## Syncing Captions to Scenes

Use transcript timestamps to determine scene transition points:

```python
import json
words = json.load(open("transcript.json"))

# Find natural sentence breaks (words with . ! ? at end)
breaks = [w for w in words if w["text"].endswith((".", "!", "?"))]
for b in breaks:
    print(f"Sentence ends at {b['end']:.2f}s — place transition here")
```

Place scene transitions at sentence-end times, with a 0.3–0.5s buffer before the next sentence starts.

## Word Emphasis Techniques

Beyond color — combine with CSS patterns for key words:

```js
// Scribble underline on a specific caption word
// (only for single important words, not every word)
function addScribbleToWord(wordEl, tl, startTime) {
  var svg = document.createElementNS("http://www.w3.org/2000/svg","svg");
  svg.style.cssText = "position:absolute;left:0;bottom:-6px;width:100%;height:18px;pointer-events:none";
  svg.setAttribute("viewBox","0 0 300 18");
  svg.setAttribute("preserveAspectRatio","none");
  var path = document.createElementNS("http://www.w3.org/2000/svg","path");
  path.setAttribute("d","M0,9 Q37,0 75,9 Q112,18 150,9 Q187,0 225,9 Q262,18 300,9");
  path.setAttribute("fill","none");
  path.setAttribute("stroke","#E63946");
  path.setAttribute("stroke-width","2.5");
  path.setAttribute("stroke-linecap","round");
  var L = path.getTotalLength ? 400 : 400;
  path.style.strokeDasharray = L;
  path.style.strokeDashoffset = L;
  svg.appendChild(path);
  wordEl.style.position = "relative";
  wordEl.appendChild(svg);
  tl.to(path, {strokeDashoffset:0, duration:0.4, ease:"power1.inOut"}, startTime);
}
```
