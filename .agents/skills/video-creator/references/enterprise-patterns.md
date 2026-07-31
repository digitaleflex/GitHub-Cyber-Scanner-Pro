# Enterprise Visual Patterns

Org charts, workflow diagrams, approval gates, RACI flows, dashboard mockups, and data visualizations for enterprise-targeted videos.

---

## Pattern 1: Org Chart (Top-Down Hierarchy)

```html
<div style="display:flex;flex-direction:column;align-items:center;width:100%">
  <!-- Level 0: Executive -->
  <div id="org-top" style="border:2px solid #E63946;background:rgba(230,57,70,0.08);
    padding:16px 24px;min-width:220px;text-align:center;box-shadow:3px 3px 0px #141111;opacity:0">
    <div style="font-size:24px;margin-bottom:6px">👤</div>
    <div style="font-size:15px;font-weight:700;color:#FFFFFF">CTO / VP Engineering</div>
    <div style="font-family:'Space Mono',monospace;font-size:10px;color:#666;margin-top:3px">HUMAN LEADER</div>
  </div>

  <!-- Vertical connector -->
  <div id="org-v0" style="width:2px;height:36px;background:rgba(230,57,70,0.3)"></div>

  <!-- Horizontal branch line -->
  <div id="org-branch" style="width:80%;height:2px;background:rgba(230,57,70,0.25)"></div>

  <!-- Level 1: Three columns -->
  <div style="width:80%;display:flex;justify-content:space-between;margin-top:0">
    <div id="org-n1" style="border:2px solid #141111;background:#1A1A1A;
      padding:14px 16px;min-width:160px;text-align:center;box-shadow:3px 3px 0px #141111;opacity:0">
      <div style="font-size:20px;margin-bottom:4px">🤖</div>
      <div style="font-size:13px;font-weight:700;color:#FFFFFF">Claude Squad</div>
      <div style="font-family:'Space Mono',monospace;font-size:10px;color:#666;margin-top:2px">3 AGENTS · BACKEND</div>
    </div>
    <div id="org-n2" style="border:2px solid #E63946;background:rgba(230,57,70,0.06);
      padding:14px 16px;min-width:180px;text-align:center;box-shadow:3px 3px 0px #141111;opacity:0">
      <div style="font-size:20px;margin-bottom:4px">🧑‍💻</div>
      <div style="font-size:13px;font-weight:700;color:#FFFFFF">Engineering Lead</div>
      <div style="font-family:'Space Mono',monospace;font-size:10px;color:#666;margin-top:2px">HUMAN · APPROVER</div>
    </div>
    <div id="org-n3" style="border:2px solid #141111;background:#1A1A1A;
      padding:14px 16px;min-width:160px;text-align:center;box-shadow:3px 3px 0px #141111;opacity:0">
      <div style="font-size:20px;margin-bottom:4px">⚡</div>
      <div style="font-size:13px;font-weight:700;color:#FFFFFF">Codex Squad</div>
      <div style="font-family:'Space Mono',monospace;font-size:10px;color:#666;margin-top:2px">4 AGENTS · DEPLOY</div>
    </div>
  </div>
</div>
```

GSAP:
```js
tl.fromTo("#org-top",{opacity:0,y:-20},{opacity:1,y:0,duration:0.35,ease:"back.out(2)"},T);
tl.fromTo("#org-v0",{scaleY:0},{scaleY:1,duration:0.2,ease:"power2.out",transformOrigin:"top"},T+0.35);
tl.fromTo("#org-branch",{scaleX:0},{scaleX:1,duration:0.3,ease:"power2.out",transformOrigin:"center"},T+0.55);
tl.fromTo("#org-n1",{opacity:0,y:-15},{opacity:1,y:0,duration:0.3,ease:"back.out(2)"},T+0.85);
tl.fromTo("#org-n2",{opacity:0,y:-15},{opacity:1,y:0,duration:0.3,ease:"back.out(2)"},T+1.0);
tl.fromTo("#org-n3",{opacity:0,y:-15},{opacity:1,y:0,duration:0.3,ease:"back.out(2)"},T+1.15);
```

---

## Pattern 2: RACI / Responsibility Matrix

```html
<div style="width:100%;border:2px solid #141111;background:#1A1A1A;box-shadow:4px 4px 0px #141111">
  <!-- Header row -->
  <div style="display:flex;border-bottom:2px solid #141111;background:#222">
    <div style="flex:2;padding:12px 20px;font-family:'Space Mono',monospace;font-size:12px;font-weight:700;color:#666;text-transform:uppercase;letter-spacing:0.06em">Task</div>
    <div style="flex:1;padding:12px 20px;border-left:2px solid #141111;font-family:'Space Mono',monospace;font-size:12px;font-weight:700;color:#10b981;text-transform:uppercase;text-align:center">Human</div>
    <div style="flex:1;padding:12px 20px;border-left:2px solid #141111;font-family:'Space Mono',monospace;font-size:12px;font-weight:700;color:#E63946;text-transform:uppercase;text-align:center">Agent</div>
    <div style="flex:1;padding:12px 20px;border-left:2px solid #141111;font-family:'Space Mono',monospace;font-size:12px;font-weight:700;color:#FFD60A;text-transform:uppercase;text-align:center">Gate</div>
  </div>
  <!-- Data rows — add id to each for stagger animation -->
  <div id="rr1" style="display:flex;border-bottom:1px solid #222;opacity:0">
    <div style="flex:2;padding:14px 20px;font-size:15px;font-weight:600;color:#FFFFFF">Write feature spec</div>
    <div style="flex:1;border-left:2px solid #141111;display:flex;align-items:center;justify-content:center">
      <div style="width:8px;height:8px;background:#10b981;border-radius:50%"></div>
    </div>
    <div style="flex:1;border-left:2px solid #141111"></div>
    <div style="flex:1;border-left:2px solid #141111"></div>
  </div>
  <div id="rr2" style="display:flex;border-bottom:1px solid #222;opacity:0">
    <div style="flex:2;padding:14px 20px;font-size:15px;font-weight:600;color:#FFFFFF">Implement code</div>
    <div style="flex:1;border-left:2px solid #141111"></div>
    <div style="flex:1;border-left:2px solid #141111;display:flex;align-items:center;justify-content:center">
      <div style="width:8px;height:8px;background:#E63946;border-radius:0"></div>
    </div>
    <div style="flex:1;border-left:2px solid #141111"></div>
  </div>
  <div id="rr3" style="display:flex;opacity:0">
    <div style="flex:2;padding:14px 20px;font-size:15px;font-weight:600;color:#FFFFFF">Approve & deploy</div>
    <div style="flex:1;border-left:2px solid #141111;display:flex;align-items:center;justify-content:center">
      <div style="width:8px;height:8px;background:#10b981;border-radius:50%"></div>
    </div>
    <div style="flex:1;border-left:2px solid #141111;display:flex;align-items:center;justify-content:center">
      <div style="width:8px;height:8px;background:#E63946;border-radius:0"></div>
    </div>
    <div style="flex:1;border-left:2px solid #141111;display:flex;align-items:center;justify-content:center">
      <div style="font-family:'Space Mono',monospace;font-size:10px;color:#FFD60A;font-weight:700">GATE</div>
    </div>
  </div>
</div>
```

---

## Pattern 3: Live Dashboard / Metrics Panel

```html
<div style="border:2px solid #141111;background:#1A1A1A;box-shadow:4px 4px 0px #141111;overflow:hidden;width:900px">
  <!-- Header bar (macOS-style) -->
  <div style="border-bottom:2px solid #141111;padding:12px 20px;background:#222;
    display:flex;align-items:center;gap:8px">
    <div style="width:10px;height:10px;border:1px solid #141111;background:#E63946"></div>
    <div style="width:10px;height:10px;border:1px solid #141111;background:#FFD60A"></div>
    <div style="width:10px;height:10px;border:1px solid #141111;background:#10b981"></div>
    <div style="font-family:'Space Mono',monospace;font-size:12px;color:#999;margin-left:10px;font-weight:700">
      [Product] Dashboard — Live
    </div>
    <div style="margin-left:auto;display:flex;align-items:center;gap:8px;
      font-family:'Space Mono',monospace;font-size:12px;color:#10b981;font-weight:700" id="dash-status">
      <div id="dash-dot" style="width:10px;height:10px;background:#10b981;border:1px solid #141111"></div>
      LIVE
    </div>
  </div>
  <!-- Metric cells -->
  <div style="display:flex">
    <div id="dc1" style="flex:1;padding:28px 24px;border-right:2px solid #141111;text-align:center">
      <div style="font-family:'Space Mono',monospace;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;color:#666;margin-bottom:8px">[Metric 1]</div>
      <div style="font-family:'Space Mono',monospace;font-size:52px;font-weight:700;color:#FFFFFF;font-variant-numeric:tabular-nums" id="dv1">0</div>
      <div style="font-family:'Space Mono',monospace;font-size:11px;color:#666;margin-top:4px">[context]</div>
    </div>
    <div id="dc2" style="flex:1;padding:28px 24px;border-right:2px solid #141111;text-align:center">
      <div style="font-family:'Space Mono',monospace;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;color:#666;margin-bottom:8px">[Metric 2]</div>
      <div style="font-family:'Space Mono',monospace;font-size:52px;font-weight:700;color:#FFFFFF;font-variant-numeric:tabular-nums" id="dv2">0</div>
      <div style="font-family:'Space Mono',monospace;font-size:11px;color:#666;margin-top:4px">[context]</div>
    </div>
    <div id="dc3" style="flex:1;padding:28px 24px;text-align:center">
      <div style="font-family:'Space Mono',monospace;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;color:#666;margin-bottom:8px">[Metric 3]</div>
      <div style="font-family:'Space Mono',monospace;font-size:52px;font-weight:700;color:#FFFFFF;font-variant-numeric:tabular-nums" id="dv3">0%</div>
      <div style="font-family:'Space Mono',monospace;font-size:11px;color:#666;margin-top:4px">[context]</div>
    </div>
  </div>
</div>
```

GSAP:
```js
tl.fromTo("#dash",{opacity:0,x:60},{opacity:1,x:0,duration:0.5,ease:"power3.out"},T);
tl.fromTo("#dash-dot",{scale:1},{scale:1.3,yoyo:true,repeat:4,duration:1.5,ease:"sine.inOut"},T+0.5);
tl.to("#dv1",{innerText:TARGET1,duration:0.6,ease:"power2.out",snap:{innerText:1}},T+0.5);
tl.to("#dv2",{innerText:TARGET2,duration:0.7,ease:"power2.out",snap:{innerText:1}},T+0.65);
// For percentage: use onUpdate
tl.to({},{duration:0.5,ease:"power2.out",onUpdate:function(){
  document.getElementById("dv3").textContent = (99 + this.progress() * 0.7).toFixed(1) + "%";
}},T+0.8);
```

---

## Pattern 4: Feature Card Grid (3-Column)

```html
<div style="display:flex;gap:24px;width:100%">
  <div id="fc1" style="flex:1;border:2px solid #141111;background:#1A1A1A;
    padding:36px 28px;box-shadow:4px 4px 0px #141111;position:relative;opacity:0">
    <div style="position:absolute;top:14px;right:18px;font-family:'Space Mono',monospace;
      font-size:12px;font-weight:700;color:#666">01</div>
    <div style="width:52px;height:52px;border:2px solid #141111;
      display:flex;align-items:center;justify-content:center;
      font-size:26px;margin-bottom:20px;box-shadow:2px 2px 0px #141111;
      background:rgba(230,57,70,0.12)">[icon]</div>
    <div style="font-size:20px;font-weight:700;color:#FFFFFF;margin-bottom:8px">[Title]</div>
    <div style="font-size:15px;color:#EBEBEB;line-height:1.6">[Description of the feature or benefit]</div>
  </div>
  <!-- Repeat for card 2 (id=fc2) and card 3 (id=fc3) -->
</div>
```

GSAP:
```js
tl.fromTo("#fc1",{opacity:0,y:-50},{opacity:1,y:0,duration:0.45,ease:"back.out(2.5)"},T);
tl.fromTo("#fc2",{opacity:0,y:-50},{opacity:1,y:0,duration:0.45,ease:"back.out(2.5)"},T+0.15);
tl.fromTo("#fc3",{opacity:0,y:-50},{opacity:1,y:0,duration:0.45,ease:"back.out(2.5)"},T+0.30);
```

---

## Pattern 5: Timeline / Process Steps

```html
<div style="display:flex;flex-direction:column;gap:0;width:600px">
  <div id="ps1" style="display:flex;align-items:flex-start;gap:0;opacity:0">
    <div style="display:flex;flex-direction:column;align-items:center">
      <div style="width:40px;height:40px;border:2px solid #141111;background:#E63946;
        display:flex;align-items:center;justify-content:center;
        font-family:'Space Mono',monospace;font-size:14px;font-weight:700;color:#FFFFFF">01</div>
      <div style="width:2px;height:60px;background:rgba(230,57,70,0.3)" id="pv1"></div>
    </div>
    <div style="padding:8px 0 0 20px">
      <div style="font-size:18px;font-weight:700;color:#FFFFFF;margin-bottom:4px">[Step title]</div>
      <div style="font-size:14px;color:#888;line-height:1.5">[Step description]</div>
    </div>
  </div>
  <!-- Repeat for steps 2, 3, 4 with ids ps2, ps3, ps4 -->
</div>
```

GSAP:
```js
["#ps1","#ps2","#ps3"].forEach(function(el,i){
  tl.fromTo(el,{opacity:0,x:-20},{opacity:1,x:0,duration:0.4,ease:"power2.out"},T+i*0.4);
  tl.fromTo(el.querySelector("div[id^='pv']")||"#pv"+(i+1),{scaleY:0},{scaleY:1,duration:0.3,ease:"power2.out",transformOrigin:"top"},T+i*0.4+0.4);
});
```
