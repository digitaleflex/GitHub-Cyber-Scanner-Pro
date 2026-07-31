# Scene Templates — Complete HTML + CSS

Six reusable scene archetypes. Adapt colors, copy, and timing from your design.md.

---

## Template 1: Problem / Pain Scene (Split Layout)

```html
<!-- LEFT: pain statement | RIGHT: chaos illustration -->
<div id="s-pain" class="scene" style="display:flex">
  <!-- Canvas particle field -->
  <canvas id="pain-canvas" width="1920" height="1080" style="position:absolute;top:0;left:0;z-index:1;pointer-events:none"></canvas>

  <!-- Left 55%: copy -->
  <div style="width:1060px;height:1080px;display:flex;flex-direction:column;justify-content:center;
              padding:120px 80px 140px 100px;position:relative;z-index:5">
    <div id="pain-kicker" style="font-family:'Space Mono',monospace;font-size:12px;font-weight:700;
      text-transform:uppercase;letter-spacing:0.14em;color:#E63946;
      border-left:3px solid #E63946;padding-left:14px;margin-bottom:36px">
      The Challenge
    </div>
    <div id="pain-head" style="font-size:90px;font-weight:800;color:#FFFFFF;
      letter-spacing:-0.035em;line-height:0.92;margin-bottom:40px">
      [Pain state]<br/>is getting<br/><span style="color:#E63946">worse.</span>
    </div>
    <div id="pain-sub" style="font-size:20px;color:#888;line-height:1.7;max-width:520px">
      <strong style="color:#EBEBEB">[Audience descriptor]</strong> face [specific pain point] every [time frame].
    </div>
  </div>

  <!-- Vertical divider -->
  <div style="position:absolute;left:1060px;top:0;width:1px;height:100%;
    background:linear-gradient(to bottom,transparent,rgba(230,57,70,0.25) 30%,rgba(230,57,70,0.25) 70%,transparent);z-index:6"></div>

  <!-- Right 45%: chaos blocks -->
  <div style="flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;
              padding:60px;position:relative;z-index:5;overflow:hidden">
    <div id="tb1" style="width:100%;border:1px solid rgba(230,57,70,0.15);background:rgba(230,57,70,0.03);
      font-family:'Space Mono',monospace;font-size:13px;color:#555;padding:14px 18px;margin-bottom:10px;line-height:1.8">
      <span style="color:#E63946">ERROR</span> [agent error message]<br/>
      <span style="color:#555">status: unmonitored | owner: nobody</span>
    </div>
    <div id="tb2" style="width:100%;border:1px solid rgba(230,57,70,0.15);background:rgba(230,57,70,0.03);
      font-family:'Space Mono',monospace;font-size:13px;color:#555;padding:14px 18px;margin-bottom:10px;line-height:1.8">
      <span style="color:#E63946">WARN</span> [another problem]<br/>
      <span style="color:#555">audit_log: missing | reviewed_by: nobody</span>
    </div>
    <div id="tb3" style="width:100%;border:1px solid rgba(230,57,70,0.15);background:rgba(230,57,70,0.03);
      font-family:'Space Mono',monospace;font-size:13px;color:#555;padding:14px 18px;line-height:1.8">
      <span style="color:#555"># [Punchline about the chaos]</span><br/>
      <span style="color:#E63946">CRITICAL</span> [consequence]
    </div>
    <div style="font-family:'Space Mono',monospace;font-size:180px;font-weight:700;
      color:rgba(230,57,70,0.06);position:absolute;bottom:40px;right:40px;line-height:1">?</div>
  </div>

  <!-- Corner marks -->
  <div style="position:absolute;top:28px;left:28px;width:44px;height:44px;border:2px solid rgba(230,57,70,0.22);border-right:none;border-bottom:none;z-index:9"></div>
  <div style="position:absolute;top:28px;right:28px;width:44px;height:44px;border:2px solid rgba(230,57,70,0.22);border-left:none;border-bottom:none;z-index:9"></div>
  <div style="position:absolute;bottom:28px;left:28px;width:44px;height:44px;border:2px solid rgba(230,57,70,0.22);border-right:none;border-top:none;z-index:9"></div>
  <div style="position:absolute;bottom:28px;right:28px;width:44px;height:44px;border:2px solid rgba(230,57,70,0.22);border-left:none;border-top:none;z-index:9"></div>
</div>
```

GSAP for this scene:
```js
// Canvas particle field (attach to tl — not standalone)
var px={t:0};
tl.to(px,{t:SCENE_DURATION,duration:SCENE_DURATION,ease:"none",onUpdate:function(){
  /* draw particles + grid per frame — see techniques */
}},SCENE_START);

tl.fromTo("#pain-kicker",{opacity:0,x:-15},{opacity:1,x:0,duration:0.4,ease:"power3.out"},SCENE_START+0.3);
tl.fromTo("#pain-head",{opacity:0,y:50},{opacity:1,y:0,duration:0.65,ease:"back.out(1.6)"},SCENE_START+0.5);
tl.fromTo("#pain-sub",{opacity:0,y:20},{opacity:1,y:0,duration:0.45,ease:"power2.out"},SCENE_START+1.2);
tl.fromTo("#tb1",{opacity:0,x:30},{opacity:1,x:0,duration:0.35,ease:"power3.out"},SCENE_START+0.6);
tl.fromTo("#tb2",{opacity:0,x:30},{opacity:1,x:0,duration:0.35,ease:"power3.out"},SCENE_START+1.4);
tl.fromTo("#tb3",{opacity:0,x:30},{opacity:1,x:0,duration:0.35,ease:"power3.out"},SCENE_START+2.4);
```

---

## Template 2: Platform Reveal (Cinematic Centered)

```html
<div id="s-reveal" class="scene" style="display:flex;flex-direction:column;align-items:center;justify-content:center">
  <!-- Corner marks -->
  <div id="rev-cm1" style="position:absolute;top:28px;left:28px;width:44px;height:44px;border:2px solid rgba(230,57,70,0.22);border-right:none;border-bottom:none;z-index:9"></div>
  <div id="rev-cm2" style="position:absolute;top:28px;right:28px;width:44px;height:44px;border:2px solid rgba(230,57,70,0.22);border-left:none;border-bottom:none;z-index:9"></div>
  <div id="rev-cm3" style="position:absolute;bottom:28px;left:28px;width:44px;height:44px;border:2px solid rgba(230,57,70,0.22);border-right:none;border-top:none;z-index:9"></div>
  <div id="rev-cm4" style="position:absolute;bottom:28px;right:28px;width:44px;height:44px;border:2px solid rgba(230,57,70,0.22);border-left:none;border-top:none;z-index:9"></div>

  <div style="position:relative;z-index:5;display:flex;flex-direction:column;align-items:center;
              gap:24px;padding:100px 180px;text-align:center">
    <!-- Badge -->
    <div id="rev-badge" style="display:inline-flex;align-items:center;gap:12px;
      border:2px solid #141111;padding:8px 20px;font-family:'Space Mono',monospace;
      font-size:13px;font-weight:700;letter-spacing:0.07em;color:#FFFFFF;
      background:rgba(230,57,70,0.12)">
      <div style="width:10px;height:10px;background:#E63946;border:1px solid #FFFFFF"></div>
      [CATEGORY LABEL]
    </div>
    <!-- Tag -->
    <div id="rev-tag" style="font-family:'Space Mono',monospace;font-size:14px;font-weight:700;
      text-transform:uppercase;letter-spacing:0.14em;color:#10b981">
      Introducing [Product]
    </div>
    <!-- Headline with scribble underline -->
    <div id="rev-hl" style="font-size:100px;font-weight:800;color:#FFFFFF;
      letter-spacing:-0.04em;line-height:0.9;text-align:center">
      <span id="rev-w1" style="color:#E63946;font-style:italic;display:block">[Action verb].</span>
      <span id="rev-w2" style="display:block">
        <span style="position:relative;display:inline-block" id="rev-uw">[Key phrase].
          <svg style="position:absolute;left:0;bottom:-10px;width:100%;height:22px" viewBox="0 0 600 22" preserveAspectRatio="none">
            <path id="rev-sc" fill="none" stroke="#10b981" stroke-width="3" stroke-linecap="round"
              stroke-dasharray="900" stroke-dashoffset="900"
              d="M0,11 Q75,0 150,11 Q225,22 300,11 Q375,0 450,11 Q525,22 600,11"/>
          </svg>
        </span>
      </span>
    </div>
    <!-- Body -->
    <div id="rev-desc" style="font-size:24px;color:#888;line-height:1.6;text-align:center;max-width:780px">
      [Product] is the <strong style="color:#EBEBEB">[category]</strong> [audience] has been missing.
    </div>
  </div>
</div>
```

GSAP:
```js
tl.fromTo("#rev-badge",{opacity:0,y:-20},{opacity:1,y:0,duration:0.4,ease:"back.out(2)"},T);
tl.fromTo("#rev-tag",{opacity:0,letterSpacing:"0.28em"},{opacity:1,letterSpacing:"0.14em",duration:0.4,ease:"power3.out"},T+0.2);
tl.fromTo("#rev-w1",{opacity:0,y:60,rotation:3},{opacity:1,y:0,rotation:0,duration:0.5,ease:"back.out(2.5)"},T+0.5);
tl.fromTo("#rev-w2",{opacity:0,y:60},{opacity:1,y:0,duration:0.5,ease:"expo.out"},T+0.75);
var sc=document.getElementById("rev-sc"),l=sc.getTotalLength();
gsap.set(sc,{strokeDasharray:l,strokeDashoffset:l});
tl.to("#rev-sc",{strokeDashoffset:0,duration:0.6,ease:"power1.inOut"},T+1.1);
tl.fromTo("#rev-desc",{opacity:0,y:15},{opacity:1,y:0,duration:0.4,ease:"power2.out"},T+1.4);
```

---

## Template 3: Orchestration Flow Diagram

```html
<div id="s-orch" class="scene" style="display:flex;align-items:stretch">
  <!-- Left 38%: copy -->
  <div style="width:720px;border-right:2px solid #141111;display:flex;flex-direction:column;
              justify-content:center;padding:100px 70px;position:relative;z-index:5">
    <div id="orch-lbl" style="font-family:'Space Mono',monospace;font-size:12px;font-weight:700;
      text-transform:uppercase;letter-spacing:0.14em;color:#E63946;margin-bottom:24px">Human-Agent Orchestration</div>
    <div id="orch-h" style="font-size:68px;font-weight:800;color:#FFFFFF;letter-spacing:-0.03em;line-height:1;margin-bottom:36px">Assign.<br/>Gate.<br/>Track.</div>
    <div style="display:flex;flex-direction:column;gap:20px">
      <div id="orch-i1" style="display:flex;align-items:flex-start;gap:16px">
        <div style="width:8px;height:8px;background:#E63946;flex-shrink:0;margin-top:10px;border:1px solid rgba(230,57,70,0.3)"></div>
        <div style="font-size:17px;color:#EBEBEB;line-height:1.5"><strong style="color:#FFFFFF;font-weight:700;display:block;font-size:18px">Task Assignment</strong>Assign any task to any human or agent member</div>
      </div>
      <div id="orch-i2" style="display:flex;align-items:flex-start;gap:16px">
        <div style="width:8px;height:8px;background:#E63946;flex-shrink:0;margin-top:10px;border:1px solid rgba(230,57,70,0.3)"></div>
        <div style="font-size:17px;color:#EBEBEB;line-height:1.5"><strong style="color:#FFFFFF;font-weight:700;display:block;font-size:18px">Approval Gates</strong>Human checkpoints before agents proceed</div>
      </div>
      <div id="orch-i3" style="display:flex;align-items:flex-start;gap:16px">
        <div style="width:8px;height:8px;background:#E63946;flex-shrink:0;margin-top:10px;border:1px solid rgba(230,57,70,0.3)"></div>
        <div style="font-size:17px;color:#EBEBEB;line-height:1.5"><strong style="color:#FFFFFF;font-weight:700;display:block;font-size:18px">Full Audit Trail</strong>Every action logged with timestamp and owner</div>
      </div>
    </div>
  </div>

  <!-- Right 62%: flow diagram -->
  <div style="flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:60px 80px;position:relative;z-index:5">
    <div style="width:100%;max-width:900px;display:flex;flex-direction:column;gap:0">
      <!-- Node 1: Human -->
      <div id="fn1" style="display:flex;align-items:center;gap:18px;border:2px solid #141111;background:#1A1A1A;padding:18px 24px;box-shadow:4px 4px 0px #141111;opacity:0">
        <div style="width:52px;height:52px;border:2px solid #141111;background:#222;display:flex;align-items:center;justify-content:center;font-size:24px;flex-shrink:0;box-shadow:2px 2px 0px #141111">🧑‍💼</div>
        <div><div style="font-size:17px;font-weight:700;color:#FFFFFF">[Human role]</div><div style="font-family:'Space Mono',monospace;font-size:11px;color:#666;margin-top:2px;letter-spacing:0.04em">TASK OWNER · APPROVER</div></div>
        <div style="margin-left:auto;font-family:'Space Mono',monospace;font-size:10px;font-weight:700;padding:4px 10px;border:1px solid #10b981;color:#10b981;background:rgba(16,185,129,0.08);flex-shrink:0">HUMAN</div>
      </div>
      <!-- Connector 1 -->
      <div id="fc1" style="display:flex;align-items:center;gap:0;margin:4px 0;padding-left:26px;opacity:0">
        <div id="fc1l" style="flex:1;height:2px;background:rgba(230,57,70,0.3);transform:scaleX(0);transform-origin:left"></div>
        <div style="font-family:'Space Mono',monospace;font-size:11px;color:#666;background:#111;padding:2px 8px;border:1px solid #222;white-space:nowrap">assigns task</div>
        <div style="color:#E63946;font-size:14px;margin-left:4px">▼</div>
      </div>
      <!-- Node 2: Agent -->
      <div id="fn2" style="display:flex;align-items:center;gap:18px;border:2px solid #141111;background:#1A1A1A;padding:18px 24px;box-shadow:4px 4px 0px #141111;opacity:0">
        <div style="width:52px;height:52px;border:2px solid #141111;background:#222;display:flex;align-items:center;justify-content:center;font-size:24px;flex-shrink:0;box-shadow:2px 2px 0px #141111">🤖</div>
        <div><div style="font-size:17px;font-weight:700;color:#FFFFFF">[AI Agent]</div><div style="font-family:'Space Mono',monospace;font-size:11px;color:#666;margin-top:2px;letter-spacing:0.04em">EXECUTOR · IMPLEMENTER</div></div>
        <div style="margin-left:auto;font-family:'Space Mono',monospace;font-size:10px;font-weight:700;padding:4px 10px;border:1px solid #E63946;color:#E63946;background:rgba(230,57,70,0.08);flex-shrink:0">AI AGENT</div>
      </div>
      <!-- Connector 2 -->
      <div id="fc2" style="display:flex;align-items:center;gap:0;margin:4px 0;padding-left:26px;opacity:0">
        <div id="fc2l" style="flex:1;height:2px;background:rgba(230,57,70,0.3);transform:scaleX(0);transform-origin:left"></div>
        <div style="font-family:'Space Mono',monospace;font-size:11px;color:#666;background:#111;padding:2px 8px;border:1px solid #222;white-space:nowrap">requests approval</div>
        <div style="color:#E63946;font-size:14px;margin-left:4px">▼</div>
      </div>
      <!-- Approval Gate -->
      <div id="fgate" style="border:2px solid #FFD60A;background:rgba(255,214,10,0.06);padding:12px 20px;display:flex;align-items:center;gap:14px;opacity:0">
        <div style="font-size:22px">🔐</div>
        <div style="font-family:'Space Mono',monospace;font-size:12px;color:#FFD60A;font-weight:700;letter-spacing:0.05em">APPROVAL GATE — HUMAN SIGN-OFF REQUIRED</div>
      </div>
      <!-- Connector 3 -->
      <div id="fc3" style="display:flex;align-items:center;gap:0;margin:4px 0;padding-left:26px;opacity:0">
        <div id="fc3l" style="flex:1;height:2px;background:rgba(230,57,70,0.3);transform:scaleX(0);transform-origin:left"></div>
        <div style="font-family:'Space Mono',monospace;font-size:11px;color:#666;background:#111;padding:2px 8px;border:1px solid #222;white-space:nowrap">approved · proceeding</div>
        <div style="color:#E63946;font-size:14px;margin-left:4px">▼</div>
      </div>
      <!-- Node 4: Human returns -->
      <div id="fn4" style="display:flex;align-items:center;gap:18px;border:2px solid #141111;background:#1A1A1A;padding:18px 24px;box-shadow:4px 4px 0px #141111;opacity:0">
        <div style="width:52px;height:52px;border:2px solid #141111;background:#222;display:flex;align-items:center;justify-content:center;font-size:24px;flex-shrink:0;box-shadow:2px 2px 0px #141111">🧑‍💼</div>
        <div><div style="font-size:17px;font-weight:700;color:#FFFFFF">[Human role]</div><div style="font-family:'Space Mono',monospace;font-size:11px;color:#666;margin-top:2px;letter-spacing:0.04em">REVIEWER · SIGN-OFF</div></div>
        <div style="margin-left:auto;font-family:'Space Mono',monospace;font-size:10px;font-weight:700;padding:4px 10px;border:1px solid #10b981;color:#10b981;background:rgba(16,185,129,0.08);flex-shrink:0">HUMAN</div>
      </div>
    </div>
  </div>
</div>
```

GSAP:
```js
tl.fromTo("#orch-lbl",{opacity:0,x:-10},{opacity:1,x:0,duration:0.3,ease:"power3.out"},T);
tl.fromTo("#orch-h",{opacity:0,y:30},{opacity:1,y:0,duration:0.5,ease:"back.out(1.5)"},T+0.2);
["#orch-i1","#orch-i2","#orch-i3"].forEach(function(el,i){
  tl.fromTo(el,{opacity:0,x:-15},{opacity:1,x:0,duration:0.35,ease:"power2.out"},T+0.5+i*0.3);
});
// diagram builds sequentially
tl.fromTo("#fn1",{opacity:0,y:-20},{opacity:1,y:0,duration:0.35,ease:"back.out(2)"},T+0.2);
tl.fromTo("#fc1",{opacity:0},{opacity:1,duration:0.2},T+0.55);
tl.fromTo("#fc1l",{scaleX:0},{scaleX:1,duration:0.25,ease:"power2.out"},T+0.55);
tl.fromTo("#fn2",{opacity:0,y:-20},{opacity:1,y:0,duration:0.35,ease:"back.out(2)"},T+0.8);
tl.fromTo("#fc2",{opacity:0},{opacity:1,duration:0.2},T+1.2);
tl.fromTo("#fc2l",{scaleX:0},{scaleX:1,duration:0.25,ease:"power2.out"},T+1.2);
tl.fromTo("#fgate",{opacity:0,scale:0.9},{opacity:1,scale:1,duration:0.4,ease:"back.out(2)"},T+1.5);
tl.fromTo("#fc3",{opacity:0},{opacity:1,duration:0.2},T+2.8);
tl.fromTo("#fc3l",{scaleX:0},{scaleX:1,duration:0.25,ease:"power2.out"},T+2.8);
tl.fromTo("#fn4",{opacity:0,y:-20},{opacity:1,y:0,duration:0.35,ease:"back.out(2)"},T+3.0);
```

---

## Template 4: Proof Stats (3-Column)

```html
<div id="s-stats" class="scene" style="display:flex;align-items:center;justify-content:center">
  <div style="display:flex;gap:0;width:100%;max-width:1500px;align-items:stretch;padding:80px 120px">

    <!-- Stat 1 -->
    <div id="ss1" style="flex:1;border:2px solid #141111;background:#111;padding:60px 50px;border-right:none;opacity:0">
      <div id="sb1" style="width:40px;height:3px;background:#E63946;margin-bottom:24px;transform:scaleX(0);transform-origin:left"></div>
      <div style="font-family:'Space Mono',monospace;font-size:13px;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;color:#666;margin-bottom:8px">[Label 1]</div>
      <div style="font-family:'Space Mono',monospace;font-size:96px;font-weight:700;color:#FFFFFF;font-variant-numeric:tabular-nums;line-height:1;margin-bottom:12px">
        <span id="sv1">0</span><span style="color:#E63946;font-size:64px">[suffix]</span>
      </div>
      <div style="font-size:17px;color:#EBEBEB;line-height:1.5;max-width:260px">[Description]</div>
    </div>

    <!-- Stat 2 -->
    <div id="ss2" style="flex:1;border:2px solid #141111;background:#111;padding:60px 50px;border-right:none;border-left:2px solid #141111;opacity:0">
      <div id="sb2" style="width:40px;height:3px;background:#E63946;margin-bottom:24px;transform:scaleX(0);transform-origin:left"></div>
      <div style="font-family:'Space Mono',monospace;font-size:13px;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;color:#666;margin-bottom:8px">[Label 2]</div>
      <div style="font-family:'Space Mono',monospace;font-size:96px;font-weight:700;color:#FFFFFF;font-variant-numeric:tabular-nums;line-height:1;margin-bottom:12px">
        <span id="sv2">0</span><span style="color:#E63946;font-size:64px">[suffix]</span>
      </div>
      <div style="font-size:17px;color:#EBEBEB;line-height:1.5;max-width:260px">[Description]</div>
    </div>

    <!-- Stat 3 -->
    <div id="ss3" style="flex:1;border:2px solid #141111;background:#111;padding:60px 50px;border-left:2px solid #141111;opacity:0">
      <div id="sb3" style="width:40px;height:3px;background:#E63946;margin-bottom:24px;transform:scaleX(0);transform-origin:left"></div>
      <div style="font-family:'Space Mono',monospace;font-size:13px;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;color:#666;margin-bottom:8px">[Label 3]</div>
      <div style="font-family:'Space Mono',monospace;font-size:96px;font-weight:700;color:#FFFFFF;font-variant-numeric:tabular-nums;line-height:1;margin-bottom:12px">
        <span id="sv3">0</span><span style="color:#E63946;font-size:64px">[suffix]</span>
      </div>
      <div style="font-size:17px;color:#EBEBEB;line-height:1.5;max-width:260px">[Description]</div>
    </div>
  </div>
</div>
```

GSAP:
```js
tl.fromTo("#ss1",{opacity:0,y:30},{opacity:1,y:0,duration:0.45,ease:"back.out(2)"},T);
tl.fromTo("#ss2",{opacity:0,y:30},{opacity:1,y:0,duration:0.45,ease:"back.out(2)"},T+0.15);
tl.fromTo("#ss3",{opacity:0,y:30},{opacity:1,y:0,duration:0.45,ease:"back.out(2)"},T+0.30);
tl.fromTo("#sb1",{scaleX:0},{scaleX:1,duration:0.3,ease:"expo.out",transformOrigin:"left"},T+0.1);
tl.fromTo("#sb2",{scaleX:0},{scaleX:1,duration:0.3,ease:"expo.out",transformOrigin:"left"},T+0.25);
tl.fromTo("#sb3",{scaleX:0},{scaleX:1,duration:0.3,ease:"expo.out",transformOrigin:"left"},T+0.40);
tl.to("#sv1",{innerText:TARGET1,duration:0.7,ease:"power2.out",snap:{innerText:1}},T+0.2);
tl.to("#sv2",{innerText:TARGET2,duration:0.7,ease:"power2.out",snap:{innerText:1}},T+0.35);
tl.to("#sv3",{innerText:TARGET3,duration:0.7,ease:"power2.out",snap:{innerText:1}},T+0.50);
```

---

## Template 5: CTA Slam (Full Accent Color)

```html
<div id="s-cta" class="scene" style="background:#E63946;display:flex;align-items:center;justify-content:center;position:relative">
  <!-- Diagonal stripe accents -->
  <div id="cta-s1" style="position:absolute;width:280px;height:100%;background:#D62839;transform:skewX(-8deg);left:100px;opacity:0;pointer-events:none"></div>
  <div id="cta-s2" style="position:absolute;width:160px;height:100%;background:#D62839;transform:skewX(-8deg);left:440px;opacity:0;pointer-events:none"></div>
  <div id="cta-s3" style="position:absolute;width:200px;height:100%;background:#D62839;transform:skewX(-8deg);right:140px;opacity:0;pointer-events:none"></div>

  <!-- White corner marks -->
  <div style="position:absolute;top:28px;left:28px;width:44px;height:44px;border:2px solid rgba(255,255,255,0.2);border-right:none;border-bottom:none;z-index:9" id="cta-c1"></div>
  <div style="position:absolute;top:28px;right:28px;width:44px;height:44px;border:2px solid rgba(255,255,255,0.2);border-left:none;border-bottom:none;z-index:9" id="cta-c2"></div>
  <div style="position:absolute;bottom:28px;left:28px;width:44px;height:44px;border:2px solid rgba(255,255,255,0.2);border-right:none;border-top:none;z-index:9" id="cta-c3"></div>
  <div style="position:absolute;bottom:28px;right:28px;width:44px;height:44px;border:2px solid rgba(255,255,255,0.2);border-left:none;border-top:none;z-index:9" id="cta-c4"></div>

  <div style="position:relative;z-index:5;display:flex;flex-direction:column;align-items:center;
              gap:20px;padding:80px 200px;text-align:center">
    <div id="cta-pre" style="font-family:'Space Mono',monospace;font-size:13px;font-weight:700;
      text-transform:uppercase;letter-spacing:0.12em;color:rgba(255,255,255,0.5)">[Category]</div>

    <!-- Per-word headline -->
    <div id="cta-hl" style="font-size:108px;font-weight:800;color:#FFFFFF;letter-spacing:-0.04em;line-height:0.88;text-shadow:5px 5px 0px rgba(0,0,0,0.25)">
      <span id="cw0" style="display:inline-block;margin:0 0.03em;opacity:0">[Word 1]</span>
      <span id="cw1" style="display:inline-block;margin:0 0.03em;opacity:0">[Word 2].</span><br/>
      <!-- circle ring around brand name -->
      <span style="position:relative;display:inline-block">
        <span id="cw2" style="display:inline-block;margin:0 0.03em;opacity:0">[Brand].</span>
        <span id="cta-ring" style="position:absolute;top:50%;left:50%;width:112%;height:160%;
          transform:translate(-50%,-50%) rotate(-2deg) scale(0);
          border:4px solid #FFFFFF;border-radius:50%;pointer-events:none"></span>
      </span>
    </div>

    <div id="cta-sub" style="font-size:24px;color:rgba(255,255,255,0.75);max-width:700px;line-height:1.5">[Value proposition]</div>

    <div id="cta-urlrow" style="display:flex;gap:16px;align-items:center;margin-top:8px;opacity:0">
      <div style="font-family:'Space Mono',monospace;font-size:32px;font-weight:700;color:#FFFFFF;
        border:2px solid rgba(255,255,255,0.4);padding:12px 32px;
        background:rgba(0,0,0,0.18);box-shadow:4px 4px 0px rgba(0,0,0,0.25)">[URL]</div>
      <div style="font-size:20px;font-weight:700;color:#E63946;background:#FFFFFF;
        padding:12px 32px;border:2px solid rgba(0,0,0,0.1);box-shadow:4px 4px 0px rgba(0,0,0,0.2)">[CTA button] →</div>
    </div>
    <div id="cta-by" style="font-family:'Space Mono',monospace;font-size:13px;color:rgba(255,255,255,0.4)">[Tagline / by Company]</div>
  </div>
</div>
```

GSAP:
```js
tl.fromTo("#cta-s1",{opacity:0},{opacity:1,duration:0.18,ease:"power2.out"},T+0.1);
tl.fromTo("#cta-s2",{opacity:0},{opacity:1,duration:0.18,ease:"power2.out"},T+0.16);
tl.fromTo("#cta-s3",{opacity:0},{opacity:1,duration:0.18,ease:"power2.out"},T+0.22);
["#cta-c1","#cta-c2","#cta-c3","#cta-c4"].forEach(function(c,i){ tl.fromTo(c,{opacity:0},{opacity:1,duration:0.12},T+0.2+i*0.06); });
tl.fromTo("#cta-pre",{opacity:0,letterSpacing:"0.28em"},{opacity:1,letterSpacing:"0.12em",duration:0.4,ease:"power3.out"},T+0.3);
tl.fromTo("#cw0",{opacity:0,y:60,rotation:4},{opacity:1,y:0,rotation:0,duration:0.45,ease:"back.out(2.5)"},T+0.5);
tl.fromTo("#cw1",{opacity:0,y:80,scale:0.7},{opacity:1,y:0,scale:1,duration:0.45,ease:"expo.out"},T+0.7);
tl.fromTo("#cw2",{opacity:0,scale:0.5,rotation:-5},{opacity:1,scale:1,rotation:0,duration:0.55,ease:"back.out(3)"},T+0.95);
tl.fromTo("#cta-ring",{scale:0,rotation:-12,transformOrigin:"50% 50%"},{scale:1,rotation:-2,duration:0.55,ease:"back.out(1.7)"},T+1.5);
tl.fromTo("#cta-sub",{opacity:0,y:20},{opacity:1,y:0,duration:0.4,ease:"power2.out"},T+1.8);
tl.fromTo("#cta-urlrow",{opacity:0,scale:0.85},{opacity:1,scale:1,duration:0.45,ease:"back.out(1.5)"},T+2.2);
tl.fromTo("#cta-by",{opacity:0},{opacity:1,duration:0.3,ease:"power2.out"},T+2.7);
// Final fade to black (last scene only)
tl.to("#s-cta",{opacity:0,duration:0.9,ease:"power2.in"},END-0.9);
tl.set("#s-cta",{visibility:"hidden"},END);
```
