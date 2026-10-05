#!/usr/bin/env python3
"""Builds index.html / upgrade.html / archive.html for The Signature OS Updater (site 33).
Shared fragments (style, welcome overlay, JAH nav, sign-in wiring) live here so the
three pages never drift. Run: python3 code/build_site.py
"""
import re

BASE = "https://justinahiggins614-cmyk.github.io"
REPO = BASE + "/signature-os-updater/"

# 31-site canonical nav, extracted from signature-earth/globe.html, + site 32.
import os
_NAV_PATHS = ["/tmp/nav31.html",
              os.path.expanduser("~/workspace/hidden_files/jahnet_nav.html")]
_NAV_SRC = next((p for p in _NAV_PATHS if os.path.exists(p)), None)
if _NAV_SRC is None:
    raise SystemExit("nav31.html not found in %r — cannot stamp nav" % (_NAV_PATHS,))
NAV31 = open(_NAV_SRC).read()
NAV33 = NAV31 + '<a href="' + BASE + '/signature-antivirus/">32 The Signature Antivirus</a>' \
    + '<br><span class="here">33 The Signature OS Updater \u2014 YOU ARE HERE</span>'

# NAV31 arrives with its own <div class="jahnet"> wrapper + THE JAH NETWORK title span;
# strip those so the FOOTER wrapper below renders exactly one bar (no nested dup).
NAV31 = re.sub(r'^\s*<div class="jahnet">\s*<span class="jahnet-t">THE JAH NETWORK</span>', "", NAV31)
NAV31 = re.sub(r'</div>\s*$', "", NAV31)


STYLE = """
:root{--grn:#35c26e;--grn2:#7fe6a4;--navy:#0a1428;--panel:#101d36;--line:#24406e;--txt:#eef4ff;--dim:#9db4d8}
*{box-sizing:border-box}
body{margin:0;font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;color:var(--txt);background:var(--navy);min-height:100vh}
.wrap{max-width:1060px;margin:0 auto;padding:14px 12px 40px}
.kicker{letter-spacing:.25em;font-size:.72rem;color:var(--grn);margin:10px 0 4px}
h1{font-size:1.7rem;margin:.1em 0}
h2{color:var(--grn2);font-size:1.25rem;margin:1.2em 0 .4em}
p{line-height:1.6}
.tabs{display:flex;gap:10px;flex-wrap:wrap;margin:12px 0}
.tabs a{flex:1 1 140px;text-align:center;text-decoration:none;color:var(--txt);background:var(--panel);border:2px solid var(--line);border-radius:999px;padding:11px 8px;font-weight:700}
.tabs a.active{background:var(--grn);color:#06130b;border-color:var(--grn)}
.card{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:16px;margin:12px 0}
.card h3{margin:.2em 0;color:var(--grn2)}
.btn{display:inline-block;background:var(--grn);color:#06130b;border:0;border-radius:999px;padding:13px 26px;font-weight:800;font-size:1rem;cursor:pointer;text-decoration:none;margin:6px 6px 6px 0}
.btn.ghost{background:transparent;color:var(--grn2);border:2px solid var(--grn)}
.btn.big{font-size:1.25rem;padding:16px 40px}
.btn:disabled{opacity:.45;cursor:default}
.hint{color:var(--dim);font-size:.85rem}
.mono{font-family:ui-monospace,Consolas,monospace;background:#060c1a;border:1px solid var(--line);border-radius:8px;padding:10px 12px;overflow-x:auto;font-size:.85rem}
.badge{display:inline-block;border-radius:999px;padding:3px 12px;font-size:.78rem;font-weight:700}
.badge.ok{background:#0e3a1f;color:var(--grn2)}
.badge.warn{background:#3a2f0e;color:#ffd97f}
.badge.no{background:#3a1414;color:#ff9d9d}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px}
.jahnet{margin:26px 0 10px;padding:14px;border:1px solid var(--line);border-radius:14px;background:#0c1830;font-size:.82rem;line-height:2.1}
.jahnet-t{color:var(--grn);font-weight:800;letter-spacing:.2em;margin-right:10px}
.jahnet a{color:#9db4d8;text-decoration:none;margin:0 8px 0 0;white-space:nowrap}
.jahnet .here{display:inline-block;background:#0e3a1f;color:var(--grn2);border:1px solid var(--grn);border-radius:999px;padding:2px 12px;font-weight:800;margin:4px 0}
footer{color:#7286b8;font-size:.78rem;text-align:center;margin:20px 0}
/* stepper */
.stepbar{display:flex;gap:6px;margin:14px 0;flex-wrap:wrap}
.step{flex:1 1 120px;text-align:center;padding:10px 6px;border-radius:10px;border:2px solid var(--line);color:var(--dim);font-weight:700;font-size:.85rem}
.step.on{border-color:var(--grn);color:var(--grn2)}
.step.done{border-color:var(--grn);background:#0e3a1f;color:var(--grn2)}
.stepsec{display:none}
.stepsec.on{display:block}
/* chat */
.chatlog{display:flex;flex-direction:column;gap:8px;max-height:380px;overflow:auto;padding:6px 2px}
.msg{max-width:88%;padding:10px 14px;border-radius:14px;font-size:.95rem;line-height:1.5}
.msg.ai{background:#16294d;align-self:flex-start;border-bottom-left-radius:4px}
.msg.me{background:var(--grn);color:#06130b;align-self:flex-end;border-bottom-right-radius:4px;font-weight:600}
.msg.sys{align-self:center;background:none;color:var(--dim);font-size:.82rem}
.chips{display:flex;flex-wrap:wrap;gap:8px;margin:10px 0}
.chip{background:#16294d;border:2px solid var(--line);color:var(--txt);border-radius:999px;padding:9px 16px;cursor:pointer;font-size:.9rem}
.chip:hover{border-color:var(--grn)}
.chatrow{display:flex;gap:8px;margin-top:8px}
.chatrow input{flex:1;padding:12px 14px;border-radius:999px;border:2px solid var(--line);background:#0a1428;color:var(--txt);font-size:.95rem}
/* plan */
.planitem{display:flex;gap:10px;align-items:flex-start;background:#0c1830;border:1px solid var(--line);border-radius:12px;padding:12px;margin:8px 0}
.planitem input{transform:scale(1.4);margin-top:4px}
.planitem .why{color:var(--dim);font-size:.88rem;margin-top:4px}
.planitem.off{opacity:.5}
/* archive */
.az{margin:8px 0}
.az summary{cursor:pointer;font-weight:800;color:var(--grn2);padding:10px;background:#0c1830;border:1px solid var(--line);border-radius:10px}
.az .row{padding:8px 4px;border-bottom:1px dashed #1d3358;font-size:.92rem}
.best{border:2px solid var(--grn);background:#0c2417}
input[type=text],textarea,select{background:#0a1428;color:var(--txt);border:2px solid var(--line);border-radius:10px;padding:11px 13px;font-size:.95rem;width:100%}
label.fl{display:block;margin:8px 0 4px;color:var(--grn2);font-weight:700}
"""

OVERLAY = """
<style>
#jahWelcome,#jahGuide,#jahGuideBtn{--amber:#35c26e;--amber2:#7fe6a4}
#jahGuideBtn{position:fixed;top:14px;right:14px;z-index:99900;min-width:48px;min-height:48px;border-radius:24px;border:1px solid var(--amber);background:#101d36;color:var(--amber2);font-weight:700;font-size:18px;padding:10px 16px;cursor:pointer}
#jahGuideBtn:hover{background:var(--amber);color:#06130b}
#jahWelcome{position:fixed;inset:0;z-index:100000;display:none;align-items:center;justify-content:center;padding:16px;background:rgba(0,0,0,.75)}
#jahWelcome.show{display:flex}
#jahWelcomeCard{background:#101d36;border:2px solid var(--amber);border-radius:14px;padding:22px 20px;max-width:540px;width:100%;max-height:88vh;overflow-y:auto;color:#eef4ff}
#jahWelcomeCard h2{margin:0 0 4px;color:var(--amber2);font-size:20px}
#jahWelcomeCard .wsub{margin:4px 0 0;color:#9db4d8;font-size:14px}
#jahWelcomeCard ol{margin:10px 0 0;padding-left:22px;font-size:14px;line-height:1.55}
#jahWelcomeCard ol li{margin:8px 0}
#jahWelcomeCard ol li b{color:var(--amber2)}
#jahWelcomeCard .wbtnrow{display:flex;gap:10px;margin-top:16px;flex-wrap:wrap}
#jahGuide .btn,#jahWelcome .btn{min-height:48px;min-width:48px;font-size:15px;padding:12px 22px;border-radius:10px;border:1px solid var(--amber);background:transparent;color:var(--amber2);cursor:pointer;font-family:inherit}
#jahWelcomeOk{font-weight:700;background:var(--amber)!important;color:#06130b!important;border:none!important}
#jahGuide{position:fixed;inset:0;z-index:99900;display:none;align-items:center;justify-content:center;padding:16px;background:rgba(0,0,0,.7)}
#jahGuide.show{display:flex}
#jahGuideCard{background:#101d36;border:1px solid var(--amber);border-radius:14px;max-width:680px;width:100%;max-height:86vh;overflow:auto;padding:20px 22px;color:#eef4ff}
#jahGuideCard h2{margin-top:0;color:var(--amber2)}
#jahGuideCard .gfeat{margin:0 0 14px;padding:10px 12px;background:#0a1428;border:1px solid #24406e;border-radius:10px}
#jahGuideCard .gfeat b{color:var(--amber2)}
#jahGuideCard .gfeat p{margin:4px 0 0;font-size:14px;line-height:1.5}
#jahGuideCloseRow{display:flex;gap:10px;margin-bottom:12px;flex-wrap:wrap;align-items:center;justify-content:space-between}
</style>
<button id="jahGuideBtn" aria-label="Open the site guide" title="How to use this site">?</button>
<div id="jahWelcome" aria-hidden="true">
  <div id="jahWelcomeCard" role="dialog" aria-modal="true" aria-label="Welcome to The Signature OS Updater">
    <h2>Welcome to The Signature OS Updater</h2>
    <p class="wsub">Save money. Save the planet. No PC left outdated.</p>
    <ol>
      <li><b>Check.</b> The Upgrade tab checks your machine &mdash; right in the browser, or deep with the free checker.</li>
      <li><b>Chat.</b> Patch, the upgrade AI, asks what you use your PC for and builds YOUR plan &mdash; not one-size-fits-all.</li>
      <li><b>Apply.</b> One yes downloads your customized upgrade pack. The overlay installs <b>on top</b> of your system &mdash; nothing removed, nothing lost.</li>
      <li><b>Good form.</b> A final health check verifies everything works before it calls the job done.</li>
    </ol>
    <div class="wbtnrow">
      <button class="btn" id="jahWelcomeOk" type="button">OK &mdash; Got it &#10003;</button>
      <button class="btn" id="jahWelcomeFull" type="button">Full how-to guide</button>
    </div>
  </div>
</div>
<div id="jahGuide" aria-hidden="true">
  <div id="jahGuideCard" role="dialog" aria-modal="true" aria-label="How to use this site">
    <div id="jahGuideCloseRow">
      <h2 style="margin:0">How to use this site</h2>
      <button class="btn" id="jahGuideClose" type="button">&#10005; Close</button>
    </div>
    <div class="gfeat"><b>&#128075; What this is</b><p>The Signature OS Updater brings old computers current <b>without removing anything</b>. The Signature overlay installs on top of your existing system &mdash; your files, your programs, your setup all stay exactly as they are. Free.</p></div>
    <div class="gfeat"><b>&#128176; Why: money and planet</b><p>A new PC costs hundreds. The overlay costs $0 &mdash; and every PC kept in use is one kept out of the landfill.</p></div>
    <div class="gfeat"><b>&#11006;&#65039; Upgrade tab</b><p>Four steps: <b>Check</b> your machine, <b>chat</b> with Patch about what you need, get your <b>plan</b>, then <b>apply</b> it with one download.</p></div>
    <div class="gfeat"><b>&#129302; Patch the AI</b><p>Patch interviews you about your work and your PC's problems, then tailors every upgrade to your answers.</p></div>
    <div class="gfeat"><b>&#128203; 1 Million Archive</b><p>Every upgrade pack ever made, A&ndash;Z &mdash; marching to a million. Ask the AI box finds the right pack for any machine.</p></div>
    <div class="gfeat"><b>&#128274; Safe by design</b><p>The toolkit only ever writes inside one <b>SignatureOS</b> folder. Delete that folder and the upgrade is fully undone. A post-upgrade health check verifies good form.</p></div>
    <div class="btnrow" style="display:flex;gap:10px;flex-wrap:wrap;margin-top:6px">
      <button class="btn" id="jahGuideTour" type="button">&#9654; Show the welcome guide</button>
      <button class="btn" id="jahGuideClose2" type="button">&#10005; Close guide</button>
    </div>
  </div>
</div>
<script>(function(){try{
var FLAG="jah-tour-seen-osupdater";
var JAHPS=(function(){try{return (typeof JAHProfile!=="undefined")&&JAHProfile.store?JAHProfile.store:localStorage;}catch(e){return localStorage;}})();
function ls(k,v){try{if(v===undefined)return JAHPS.get(k);JAHPS.set(k,v)}catch(e){return null}}
var w=document.getElementById("jahWelcome"),guide=document.getElementById("jahGuide"),
    guideCard=document.getElementById("jahGuideCard"),guideBtn=document.getElementById("jahGuideBtn");
function openWelcome(){if(!w)return;w.classList.add("show");w.setAttribute("aria-hidden","false");
  try{document.getElementById("jahWelcomeOk").focus({preventScroll:true})}catch(e){}}
function closeWelcome(){if(!w)return;w.classList.remove("show");w.setAttribute("aria-hidden","true");ls(FLAG,"1")}
document.getElementById("jahWelcomeOk").onclick=closeWelcome;
document.getElementById("jahWelcomeFull").onclick=function(){closeWelcome();openGuide()};
w.addEventListener("click",function(e){if(e.target===w)closeWelcome()});
document.addEventListener("keydown",function(e){if(w.classList.contains("show")&&e.key==="Escape"){closeWelcome();e.preventDefault()}});
function openGuide(){if(!guide)return;guide.classList.add("show");guide.setAttribute("aria-hidden","false");
  try{guideCard.scrollTop=0;document.getElementById("jahGuideClose").focus({preventScroll:true})}catch(e){}}
function closeGuide(){if(!guide)return;guide.classList.remove("show");guide.setAttribute("aria-hidden","true");
  try{guideBtn.focus({preventScroll:true})}catch(e){}}
guideBtn.onclick=openWelcome;
document.getElementById("jahGuideClose").onclick=closeGuide;
document.getElementById("jahGuideClose2").onclick=closeGuide;
document.getElementById("jahGuideTour").onclick=function(){closeGuide();openWelcome()};
guide.addEventListener("click",function(e){if(e.target===guide)closeGuide()});
if(!ls(FLAG)){setTimeout(openWelcome,900)}
}catch(e){}})();</script>
"""

SIGNIN_SCRIPTS = """
<script src="js/signin.js"></script>
<script src="js/godmode.js"></script>
<script>
(function () {
  var mount = document.querySelector('header .booksearch') ||
              document.querySelector('nav.jtabbar') ||
              document.querySelector('header nav') ||
              document.querySelector('header') ||
              document.body;
  if (window.JAHProfile && JAHProfile.ui) JAHProfile.ui.renderButton(mount);
})();
</script>
<script>
(function () {
  if (window.JAHProfile && JAHProfile.ui) {
    var mount = document.querySelector('header') || document.body;
    JAHProfile.ui.renderGreeting(mount);
  }
})();
</script>
"""

FOOTER = """
<div class="jahnet"><span class="jahnet-t">THE JAH NETWORK</span>""" + NAV33 + """</div>
<footer>The Signature OS Updater &middot; original Signature systems &middot; the overlay never modifies or removes your existing system &middot; delete the SignatureOS folder to undo</footer>
"""

def page(title, desc, active_tab, body_html, extra_head=""):
    tabs = [("index.html", "\U0001F3E0 Main"), ("upgrade.html", "\u2B06\uFE0F Upgrade"),
            ("archive.html", "\U0001F5C2\uFE0F 1 Million Archive")]
    tab_html = "".join(
        '<a href="%s"%s>%s</a>' % (href, ' class="active"' if href == active_tab else "", label)
        for href, label in tabs)
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
<title>%s \u2014 The Signature OS Updater</title>
<meta name="description" content="%s">
<style>%s</style>
%s
</head>
<body>
<div class="wrap">
<header>
<p class="kicker">SITE 33 OF 33 \u00B7 THE JAH NETWORK</p>
<h1>\U0001F504 The Signature OS Updater</h1>
<p class="hint">No PC left outdated. No new PC to buy.</p>
</header>
<nav class="tabs" aria-label="Site sections">%s</nav>
%s
%s
</div>
%s
%s
</body>
</html>""" % (title, desc, STYLE, extra_head, tab_html, body_html, FOOTER, OVERLAY, SIGNIN_SCRIPTS)

INDEX_BODY = """
<div class="card" style="border:2px solid var(--grn)">
<h3>\U0001F4B0 Save money. \U0001F331 Save the planet.</h3>
<p style="font-size:1.1rem"><b>Our mission:</b> no one should have to buy a new computer just because their old one feels old.
A new PC costs <b>$400&ndash;$700</b>. The Signature overlay costs <b>$0</b> &mdash; <b>free forever</b>.
No payments. No upsells. No trial traps. We're not in business and we're not selling anything &mdash;
this exists for you, period. And it goes <b>on top</b> of the system
you already have. Nothing removed. Nothing lost. Your files, your programs, your setup &mdash; all exactly as they are, only updated.</p>
<p>Every old machine brought current is one less machine in a landfill. A 1990s PC, a 2000s PC, a 2010s PC &mdash;
each one can have a full modern working life ahead of it. <b>Green by keeping, not by buying.</b></p>
<a class="btn big" href="upgrade.html">\u2B06\uFE0F Upgrade my PC &mdash; free</a>
<a class="btn ghost" href="archive.html">Browse the upgrade archive</a>
</div>

<div class="grid">
<div class="card"><h3>\U0001F50D 1. Check</h3><p>We check your machine &mdash; right in the browser, or deep with the free checker &mdash; and tell you plainly what it is and what it can take.</p></div>
<div class="card"><h3>\U0001F4AC 2. Chat</h3><p>Patch, the upgrade AI, asks what you use your PC for and what's wrong with it &mdash; then builds a plan customized for <b>your</b> job, not one-size-fits-all.</p></div>
<div class="card"><h3>\U0001F4CB 3. Plan</h3><p>Your tailored patch list: every compatible upgrade, explained per item. Toggle anything on or off in the advanced options.</p></div>
<div class="card"><h3>\u2705 4. Apply</h3><p>One yes downloads your customized pack. A final health check verifies your PC is in <b>good form</b> before the job is done.</p></div>
</div>

<div class="card">
<h3>\U0001F4E6 The Signature overlay &mdash; what it really is</h3>
<p>A real, free Python toolkit you download and run. It detects your machine (system, processor, memory, era),
then installs the Signature layer into <b>one folder</b> &mdash; the app collection, tools, lenses, PC-model data,
software set, your own online AI and offline AI, the AI Sweeper, and a full sweep. <b>It never touches anything
outside that folder.</b> Delete the folder and the upgrade is fully undone &mdash; a restore manifest is written with every install.</p>
<p class="hint">Honest limits: the overlay cannot fix broken hardware (a dead drive is a dead drive), cannot upgrade your
graphics card through software, and cannot install anything through the web browser &mdash; you download the toolkit
and run one command. Everything it claims to do, it really does.</p>
<a class="btn" href="tools/signature_os_overlay.py" download>\u2B07\uFE0F Download the toolkit (Python, free)</a>
<a class="btn ghost" href="tools/README.txt" download>Read what it does first</a>
<p class="hint"><b>Free forever.</b> No account, no payment, no catch &mdash; and if you ever want it gone, deleting one folder removes every trace.</p>
</div>

<div class="card">
<h3>\U0001F4CA By the numbers</h3>
<p><b id="packCount">__PACKS__</b> upgrade packs in the archive and counting &mdash; one for every kind of machine, marching to a million.</p>
<p class="hint">Counts stamped __STAMP__ &middot; the archive grows every 2 hours.</p>
</div>
"""

UPGRADE_BODY = """
<div class="stepbar" id="stepbar">
<div class="step on" data-s="1">1 \U0001F50D Check</div>
<div class="step" data-s="2">2 \U0001F4AC Q&amp;A</div>
<div class="step" data-s="3">3 \U0001F4CB Plan</div>
<div class="step" data-s="4">4 \u2705 Apply</div>
</div>

<section class="stepsec on" id="sec1">
<div class="card">
<h3>Step 1 &mdash; Check your machine</h3>
<p>First, a quick look right in your browser. <span class="hint">This is a rough estimate &mdash; your browser only shares a little. The deep check below reads the real numbers.</span></p>
<div id="browserEst"><p class="hint">Checking&hellip;</p></div>
<label class="fl" for="eraSel">Your PC's era (correct it if we guessed wrong)</label>
<select id="eraSel">
<option value="1990s">1990s machine</option>
<option value="2000s">2000s machine</option>
<option value="2010s" selected>2010s machine</option>
<option value="modern">Modern machine</option>
<option value="unknown">Not sure</option>
</select>
</div>

<div class="card">
<h3>\U0001F50E Deep check &mdash; the real numbers (recommended)</h3>
<p>Download the free checker, run one command on your PC, and paste the code it gives you back here. Then this page knows your <b>real</b> system, processor, memory and disk.</p>
<ol>
<li><a class="btn" href="tools/signature_os_overlay.py" download>\u2B07\uFE0F Download the checker</a></li>
<li><p>Run it: <span class="mono">python3 signature_os_overlay.py --code</span></p></li>
<li><label class="fl" for="codeBox">Paste your machine code here</label>
<textarea id="codeBox" rows="3" placeholder="Paste the single-line code here&hellip;"></textarea>
<button class="btn" id="readCode" type="button">Read my machine</button></li>
</ol>
<div id="machineCard"></div>
</div>

<div class="card">
<h3>\U0001F4B0 What you save</h3>
<p class="hint">Honest math: what a basic new PC costs vs. the overlay at $0.</p>
<div id="saver"></div>
<p class="hint">Estimates: typical basic new desktop/laptop prices; your mileage varies. The overlay can't fix dead hardware &mdash; if a part has failed, no software saves that.</p>
</div>

<div class="card"><button class="btn big" id="toStep2" type="button">My machine is checked &mdash; continue \u2192</button></div>
</section>

<section class="stepsec" id="sec2">
<div class="card">
<h3>Step 2 &mdash; Tell Patch what you need</h3>
<p>Patch is the upgrade AI. Answer a few questions &mdash; in your own words is fine &mdash; and your plan gets built around <b>your</b> job and <b>your</b> PC's problems.</p>
<div class="chatlog" id="chatlog" aria-live="polite"></div>
<div class="chips" id="chips"></div>
<div class="chatrow"><input id="chatIn" type="text" placeholder="Type your answer&hellip;" aria-label="Your answer"><button class="btn" id="chatSend" type="button">Send</button></div>
</div>
</section>

<section class="stepsec" id="sec3">
<div class="card">
<h3>Step 3 &mdash; Your customized plan</h3>
<p id="planIntro"></p>
<div id="planList"></div>
<p><button class="btn ghost" id="selectAll" type="button">Select all compatible</button>
<button class="btn big" id="toStep4" type="button">This is my plan &mdash; continue \u2192</button></p>
</div>
</section>

<section class="stepsec" id="sec4">
<div class="card">
<h3>Step 4 &mdash; Apply your upgrade</h3>
<div id="applySummary"></div>
<ol>
<li><p><b>Download the toolkit</b> (free, one file):<br><a class="btn" href="tools/signature_os_overlay.py" download>\u2B07\uFE0F Download signature_os_overlay.py</a></p></li>
<li><p><b>Download your personal upgrade profile</b> (remembers your plan):<br><button class="btn ghost" id="dlProfile" type="button">\u2B07\uFE0F Download my upgrade profile</button></p></li>
<li><p><b>Run it</b> &mdash; put both files in one folder and run:<br><span class="mono" id="runCmd">python3 signature_os_overlay.py --install --components ...</span></p></li>
<li><p><b>Good form check.</b> When the install finishes, the toolkit runs its post-upgrade health check automatically &mdash; key tools launch, disk healthy, startup clean. The upgrade isn't done until your PC is verified in good form.</p></li>
<li><p><b>Meet Patch, your on-machine AI buddy.</b> Every download includes its own AI &mdash; after installing, run <span class="mono">python3 ai_buddy.py</span> and talk to it. Patch knows your machine's upgrade state, answers questions about your PC in plain words, and runs the sweeper or health check for you (always with your say-so first).</p></li>
</ol>
<p class="hint">Nothing outside the <b>SignatureOS</b> folder is ever touched. Delete that folder and the upgrade is fully undone &mdash; zero residue, verified.</p>
<p class="hint"><b>Free forever.</b> No payments, no upsells, no business &mdash; this is for you.</p>
<p><button class="btn ghost" id="fullSweep" type="button">Or: apply the full standard sweep instead</button></p>
</div>
</section>
"""

ARCHIVE_BODY = """
<div class="card best">
<h3>\U0001F3C6 AI's Best of the Best</h3>
<div id="bestBox"><p class="hint">Loading&hellip;</p></div>
</div>
<div class="card">
<h3>\u2753 Ask the AI &mdash; find your pack</h3>
<p class="hint">Describe your machine ("2000s windows laptop for office work") and the AI finds the right upgrade pack.</p>
<div class="chatrow"><input id="askIn" type="text" placeholder="e.g. 2010s mac for school&hellip;" aria-label="Ask about upgrade packs"><button class="btn" id="askSend" type="button">Ask</button></div>
<div id="askOut" style="margin-top:10px"></div>
</div>
<div class="card">
<h3>\U0001F5C2\uFE0F All upgrade packs &mdash; <span id="arcCount">__PACKS__</span> and counting</h3>
<p class="hint">Every upgrade pack, A&ndash;Z by era. Marching to 1,000,000.</p>
<div id="az"></div>
</div>
"""

def main():
    import json, datetime
    man = {}
    try:
        man = json.load(open("data/manifest.json"))
    except Exception:
        pass
    packs = man.get("packs", 0)
    stamp = datetime.date.today().isoformat()
    idx = page("Bring any old PC current \u2014 free",
               "The Signature OS Updater: save money, save the planet. The Signature overlay updates old computers non-destructively \u2014 nothing removed, nothing lost.",
               "index.html", INDEX_BODY.replace("__PACKS__", "{:,}".format(packs)).replace("__STAMP__", stamp))
    upg = page("Upgrade your PC in 4 steps",
               "Check your machine, chat with Patch the upgrade AI, get your customized plan, apply it. Free, non-destructive.",
               "upgrade.html", UPGRADE_BODY, '<script src="js/upgrade.js" defer></script>')
    arc = page("1 Million Upgrade Archive",
               "Every Signature upgrade pack, A to Z \u2014 marching to one million.",
               "archive.html", ARCHIVE_BODY.replace("__PACKS__", "{:,}".format(packs)), '<script src="js/archive.js" defer></script>')
    open("index.html", "w").write(idx)
    open("upgrade.html", "w").write(upg)
    open("archive.html", "w").write(arc)
    print("built 3 pages, packs=%d" % packs)

if __name__ == "__main__":
    main()
