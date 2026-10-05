/* The Signature OS Updater - guided 4-step upgrade flow. ES5, no deps.
   Steps: 1 CHECK -> 2 Q&A (Patch) -> 3 PLAN -> 4 APPLY. Honest throughout:
   the browser can only estimate; real numbers come from the checker code. */
(function () {
  "use strict";
  function $(id) { return document.getElementById(id); }
  function esc(s) { return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) {
    return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }

  var S = { step: 1, era: "2010s", machine: null,
            answers: { job: null, jobNote: "", issues: [], net: null, priority: null },
            plan: [] };

  var COMPONENTS = {
    apps:       { name: "App collection",   desc: "The Signature app archive index, on your machine." },
    tools:      { name: "Technician tools", desc: "Sweep, update-check and helper scripts." },
    lenses:     { name: "Lens views",       desc: "Overview, spec, code, demo and help lenses for everything." },
    pc_models:  { name: "PC model data",    desc: "The PC Depository model index for your era." },
    software:   { name: "Software set",     desc: "Modern software manifest matched to your machine." },
    ai_sweeper: { name: "AI Sweeper",       desc: "Finds what's wrong, fixes the safe stuff, asks before the risky stuff." },
    sweep:      { name: "Full sweep",       desc: "Deep health and cleanup pass over the whole machine." },
    ai_offline: { name: "Offline AI",       desc: "Signature Llama on your PC \u2014 no internet needed." },
    ai_online:  { name: "Online AI",        desc: "Your AI over the internet, with your own key." }
  };
  var ORDER = ["ai_sweeper", "sweep", "apps", "software", "tools", "lenses", "pc_models", "ai_offline", "ai_online"];

  function eraNow() {
    if (S.machine && S.machine.era_class) {
      var e = String(S.machine.era_class).replace("-class", "");
      if (e === "modern") return "modern";
      if (e === "1990s" || e === "2000s" || e === "2010s") return e;
    }
    return S.era;
  }

  /* compatibility of each component with the machine: yes / limited / no + honest reason */
  function compat(c) {
    var era = eraNow(), net = S.answers.net;
    if (c === "ai_offline" && era === "1990s")
      return { level: "no", note: "Needs more memory than 90s-era machines have. Online AI is the honest pick here." };
    if (c === "ai_offline" && era === "2000s")
      return { level: "limited", note: "Can work, but slow on 2 GB or less \u2014 your call." };
    if (c === "ai_online" && net === "Mostly offline")
      return { level: "limited", note: "You're mostly offline, so this only helps when you're connected." };
    if (c === "ai_online" && era === "1990s")
      return { level: "limited", note: "Works, but needs a connection \u2014 fine on dial-up-era patience." };
    if (era === "unknown")
      return { level: "limited", note: "Probably fine \u2014 the deep check will confirm." };
    return { level: "yes", note: "" };
  }

  function goStep(n) {
    S.step = n;
    var bars = document.querySelectorAll("#stepbar .step"), i;
    for (i = 0; i < bars.length; i++) {
      var s = parseInt(bars[i].getAttribute("data-s"), 10);
      bars[i].className = "step" + (s === n ? " on" : s < n ? " done" : "");
    }
    for (i = 1; i <= 4; i++) $("sec" + i).className = "stepsec" + (i === n ? " on" : "");
    window.scrollTo(0, 0);
    if (n === 2 && !S.qaStarted) { S.qaStarted = true; startQA(); }
    if (n === 3) renderPlan();
    if (n === 4) renderApply();
  }

  /* ---------- STEP 1: CHECK ---------- */
  function browserOS() {
    try {
      if (navigator.userAgentData && navigator.userAgentData.platform) return navigator.userAgentData.platform;
    } catch (e) {}
    var p = navigator.platform || "", ua = navigator.userAgent || "";
    if (/Win/i.test(p) || /Windows/i.test(ua)) return "Windows (browser estimate)";
    if (/Mac/i.test(p) || /Macintosh/.test(ua)) return "macOS (browser estimate)";
    if (/Linux/i.test(p) || /Android/.test(ua)) return /Android/.test(ua) ? "Android (browser estimate)" : "Linux (browser estimate)";
    return "Unknown";
  }
  function renderBrowserEst() {
    var mem = (navigator.deviceMemory) ? "about " + navigator.deviceMemory + " GB (coarse browser figure)" : "not visible to the browser";
    $("browserEst").innerHTML =
      "<p><b>System:</b> " + esc(browserOS()) + "<br>" +
      "<b>Memory:</b> " + esc(mem) + "<br>" +
      "<b>Era:</b> your browser can't tell \u2014 pick it above, or run the deep check.</p>";
  }
  function fmtVal(v) {
    if (v == null || v === "unknown") return "unknown";
    if (typeof v === "number" && v > 0) return v.toLocaleString();
    return String(v);
  }
  function renderMachine() {
    var m = S.machine, box = $("machineCard");
    if (!m) { box.innerHTML = ""; return; }
    var era = eraNow();
    var h = "<div class=\"card\" style=\"border-color:var(--grn)\"><h3>\u2705 Machine read \u2014 here's what you've got</h3><p>" +
      "<b>System:</b> " + esc(fmtVal(m.os)) + " " + esc(fmtVal(m.os_version)) +
      " &middot; <b>Processor:</b> " + esc(fmtVal(m.arch)) + (m.cpu_count ? " (" + m.cpu_count + " cores)" : "") +
      " &middot; <b>Memory:</b> " + esc(m.ram_gb === "unknown" ? "unknown" : m.ram_gb + " GB") +
      " &middot; <b>Era class:</b> " + esc(era) + " (estimate from hardware)</p>";
    h += "<p><b>What this machine can take:</b></p><p>";
    ORDER.forEach(function (c) {
      var cp = compat(c);
      h += '<span class="badge ' + (cp.level === "yes" ? "ok" : cp.level === "limited" ? "warn" : "no") + '">' +
        esc(COMPONENTS[c].name) + "</span> ";
    });
    h += "</p><p class=\"hint\">Green = fits. Amber = fits with a caveat. Red = honestly not for this machine.</p>";
    var notes = [];
    ORDER.forEach(function (c) { var cp = compat(c); if (cp.level !== "yes") notes.push("<b>" + esc(COMPONENTS[c].name) + ":</b> " + esc(cp.note)); });
    if (notes.length) h += "<p>" + notes.join("<br>") + "</p>";
    h += "</div>";
    box.innerHTML = h;
    renderSaver();
  }
  function readCode() {
    var raw = $("codeBox").value.trim().replace(/\s+/g, "");
    if (!raw) return;
    try {
      var json = decodeURIComponent(escape(window.atob(raw)));
      var m = JSON.parse(json);
      if (!m || !m.os) throw new Error("bad");
      S.machine = m;
      renderMachine();
      say2sys("Machine code accepted \u2014 real numbers loaded.");
    } catch (e) {
      $("machineCard").innerHTML = "<p class=\"hint\">That code didn't read \u2014 make sure you copied the whole single line from <span class=\"mono\">--code</span>. You can also continue with the browser estimate.</p>";
    }
  }
  function say2sys(t) {
    var d = document.createElement("div"); d.className = "msg sys"; d.textContent = t;
    var log = $("sec1"); log.appendChild(d);
    setTimeout(function () { if (d.parentNode) d.parentNode.removeChild(d); }, 4000);
  }

  var NEW_COST = { "1990s": 400, "2000s": 450, "2010s": 550, "modern": 700, "unknown": 550 };
  function renderSaver() {
    var era = eraNow(), cost = NEW_COST[era] || 550;
    $("saver").innerHTML =
      "<div class=\"grid\">" +
      "<div class=\"card\"><h3>\U0001F6D2\uFE0F Buy new</h3><p style=\"font-size:1.6rem\"><b>$" + cost + "</b></p><p class=\"hint\">Typical basic new desktop/laptop. Plus setup time, plus your old files to move.</p></div>" +
      "<div class=\"card\" style=\"border-color:var(--grn)\"><h3>\U0001F504 Update with Signature</h3><p style=\"font-size:1.6rem\"><b>$0</b></p><p class=\"hint\">The overlay is free. Your files stay put. Nothing to move.</p></div>" +
      "<div class=\"card\"><h3>\U0001F4B0 You keep</h3><p style=\"font-size:1.6rem\"><b>~$" + cost + "</b></p><p class=\"hint\">In your pocket \u2014 and about 20 lbs of electronics keeps working instead of getting scrapped (estimate).</p></div>" +
      "</div>";
  }

  document.addEventListener("DOMContentLoaded", function () {
    renderBrowserEst();
    renderSaver();
    $("eraSel").addEventListener("change", function () { S.era = this.value; renderSaver(); });
    $("readCode").addEventListener("click", readCode);
    $("toStep2").addEventListener("click", function () { goStep(2); });
  });

  /* ---------- STEP 2: PATCH Q&A ---------- */
  var chatStarted = false;
  function chatSay(who, text, done) {
    var log = document.getElementById("chatlog");
    var d = document.createElement("div");
    d.className = "msg " + who; log.appendChild(d);
    log.scrollTop = log.scrollHeight;
    if (who === "ai") {
      d.textContent = "\u2026";
      var i = 0;
      var timer = setInterval(function () {
        i++;
        if (i >= 2) { clearInterval(timer); d.textContent = text; log.scrollTop = log.scrollHeight; if (done) done(); }
      }, 350);
    } else { d.textContent = text; log.scrollTop = log.scrollHeight; if (done) done(); }
  }
  function showChips(list, multi, cb) {
    var box = document.getElementById("chips"); box.innerHTML = "";
    var picked = [];
    list.forEach(function (label) {
      var b = document.createElement("button");
      b.type = "button"; b.className = "chip"; b.textContent = label;
      b.onclick = function () {
        if (multi) {
          var ix = picked.indexOf(label);
          if (ix >= 0) { picked.splice(ix, 1); b.style.borderColor = ""; }
          else { picked.push(label); b.style.borderColor = "var(--grn)"; }
        } else { box.innerHTML = ""; cb(label); }
      };
      box.appendChild(b);
    });
    if (multi) {
      var done = document.createElement("button");
      done.type = "button"; done.className = "chip"; done.style.borderColor = "var(--grn)";
      done.textContent = "That's everything \u2192";
      done.onclick = function () { box.innerHTML = ""; cb(picked); };
      box.appendChild(done);
    }
  }
  function freeText(cb) {
    var inp = document.getElementById("chatIn");
    var btn = document.getElementById("chatSend");
    btn.onclick = function () {
      var v = inp.value.trim(); if (!v) return;
      inp.value = ""; document.getElementById("chips").innerHTML = "";
      chatSay("me", v, function () { cb(v); });
    };
    inp.onkeydown = function (e) { if (e.key === "Enter") btn.onclick(); };
    setTimeout(function () { try { inp.focus(); } catch (e) {} }, 100);
  }
  function chipOrText(list, multi, cb) {
    /* chips for speed, free text always welcome */
    showChips(list, multi, function (picked) {
      if (typeof picked === "string") { chatSay("me", picked, function () { cb(picked); }); }
      else { if (picked.length) chatSay("me", picked.join("; "), function () { cb(picked); }); else cb(picked); }
    });
    freeText(function (v) { cb(v); });
  }

  var JOBS = ["Work / office", "Creative work", "Coding / building", "School / study", "Web & email", "Games", "A bit of everything"];
  var FOLLOW = {
    "Work / office": { q: "Office life \u2014 got it. Is it mostly documents and email, video calls, or the whole circus?", chips: ["Documents & email", "Video calls", "The whole circus"] },
    "Creative work": { q: "A creative machine. What do you make \u2014 art and design, music, video, or a mix of it all?", chips: ["Art & design", "Music", "Video", "A mix"] },
    "Coding / building": { q: "A builder. What are you building \u2014 websites, apps, or scripts and tools?", chips: ["Websites", "Apps", "Scripts & tools"] },
    "School / study": { q: "Study machine. Is it for your own schoolwork and research, or teaching?", chips: ["My schoolwork", "Research", "Teaching"] },
    "Web & email": { q: "Mostly the web. Email and browsing, or do you live inside web apps?", chips: ["Email & browsing", "Web apps", "Both"] },
    "Games": { q: "Games \u2014 and I'll be straight with you: no software can upgrade a graphics card. I'll tune what your hardware can honestly do. Older classics or newer stuff?", chips: ["Older classics", "Newer games", "Both"] },
    "A bit of everything": { q: "The classic do-everything PC. What's the ONE thing it must do well?", chips: ["Work", "School", "Fun", "All of it"] }
  };
  var ISSUES = ["Slow to start", "Slow in general", "Out of space", "Crashes / freezes", "Can't run new software", "Feels unsafe online"];
  var NETS = ["Fast", "Slow", "Mostly offline"];
  var PRIOS = ["Speed", "New apps", "AI help", "Keeping files safe", "Everything"];

  function kw(t, words) { t = t.toLowerCase(); for (var i = 0; i < words.length; i++) if (t.indexOf(words[i]) >= 0) return true; return false; }
  function guessJob(text) {
    if (kw(text, ["office", "work", "job", "email", "document", "excel", "spreadsheet"])) return "Work / office";
    if (kw(text, ["art", "music", "video", "photo", "design", "draw", "edit"])) return "Creative work";
    if (kw(text, ["code", "program", "develop", "website", "app build", "script"])) return "Coding / building";
    if (kw(text, ["school", "study", "homework", "class", "student", "teach"])) return "School / study";
    if (kw(text, ["game", "play", "gaming"])) return "Games";
    if (kw(text, ["brows", "web", "internet", "youtube"])) return "Web & email";
    return "A bit of everything";
  }
  function guessIssues(text) {
    var out = [];
    if (kw(text, ["slow to start", "boot", "startup", "takes forever to start"])) out.push("Slow to start");
    if (kw(text, ["slow"])) out.push("Slow in general");
    if (kw(text, ["space", "full", "storage", "disk"])) out.push("Out of space");
    if (kw(text, ["crash", "freeze", "froze", "blue screen", "restart"])) out.push("Crashes / freezes");
    if (kw(text, ["can't run", "cant run", "won't run", "too old", "new software", "update"])) out.push("Can't run new software");
    if (kw(text, ["virus", "unsafe", "hack", "scam", "worried", "security"])) out.push("Feels unsafe online");
    return out;
  }

  function eraWord() {
    var e = eraNow();
    return e === "unknown" ? "machine" : "your " + e + " machine";
  }

  function startQA() {
    chatSay("ai", "Hey, I'm Patch \u2014 your upgrade AI. I'll build a plan around YOU: your work, your PC, your problems. First \u2014 what do you mainly use this PC for?", function () {
      chipOrText(JOBS, false, function (ans) {
        var job = JOBS.indexOf(ans) >= 0 ? ans : guessJob(ans);
        S.answers.job = job;
        var f = FOLLOW[job];
        chatSay("ai", (JOBS.indexOf(ans) < 0 ? "Got it \u2014 sounds like " + job.toLowerCase() + ". " : "") + f.q, function () {
          chipOrText(f.chips, false, function (ans2) {
            S.answers.jobNote = ans2;
            chatSay("ai", "Noted. Now the honest part \u2014 what's the most annoying thing about " + eraWord() + " right now? Pick everything that fits, or just tell me in your own words.", function () {
              chipOrText(ISSUES, true, function (ans3) {
                var iss = (typeof ans3 === "string") ? guessIssues(ans3) : ans3;
                if (typeof ans3 === "string" && !iss.length) iss = ["Slow in general"];
                S.answers.issues = iss;
                var reflect = iss.length ? "Oof \u2014 " + iss.join(", ").toLowerCase() + ". I've seen it a hundred times on machines this age." : "Okay \u2014 no big complaints, you just want it current.";
                chatSay("ai", reflect + " How's the internet on it?", function () {
                  chipOrText(NETS, false, function (ans4) {
                    var net = NETS.indexOf(ans4) >= 0 ? ans4 : (/offline/i.test(ans4) ? "Mostly offline" : /slow/i.test(ans4) ? "Slow" : "Fast");
                    S.answers.net = net;
                    var p2 = net === "Mostly offline"
                      ? "Good to know \u2014 I'll lean on the offline AI and skip anything that needs the cloud."
                      : net === "Slow" ? "Slow internet \u2014 noted, I'll keep downloads light and favor on-machine tools."
                      : "Fast internet \u2014 that opens up the online AI and the full software set.";
                    chatSay("ai", p2 + " Last one \u2014 what matters most to you?", function () {
                      chipOrText(PRIOS, false, function (ans5) {
                        var pr = PRIOS.indexOf(ans5) >= 0 ? ans5 : "Everything";
                        S.answers.priority = pr;
                        var a = S.answers;
                        chatSay("ai", "Perfect. So: " + a.job.toLowerCase() + " (" + a.jobNote.toLowerCase() + "), " +
                          (a.issues.length ? "bothered by " + a.issues.join(", ").toLowerCase() : "no big complaints") +
                          ", " + a.net.toLowerCase() + " internet, and " + a.priority.toLowerCase() + " matters most \u2014 on " + eraWord() + ". " +
                          "Let me build your plan\u2026", function () {
                          setTimeout(function () { goStep(3); }, 1200);
                        });
                      });
                    });
                  });
                });
              });
            });
          });
        });
      });
    });
  }

  /* ---------- STEP 3: PLAN ---------- */
  function planItem(comp, why, boost) {
    var cp = compat(comp);
    S.plan.push({ comp: comp, why: why, level: cp.level, note: cp.note,
                  checked: cp.level !== "no", boost: boost || 0 });
  }
  function buildPlan() {
    S.plan = [];
    var a = S.answers, era = eraNow();
    var job = a.job, issues = a.issues, net = a.net, prio = a.priority;

    /* issues drive the fixer items first */
    if (issues.indexOf("Slow to start") >= 0 || issues.indexOf("Slow in general") >= 0)
      planItem("ai_sweeper", "You said it's slow \u2014 the Sweeper finds startup bloat and junk and clears what's safe.", 3);
    if (issues.indexOf("Out of space") >= 0)
      planItem("sweep", "Disk's full \u2014 the full sweep hunts space hogs and reclaims gigabytes.", 3);
    if (issues.indexOf("Crashes / freezes") >= 0)
      planItem("ai_sweeper", "Crashes and freezes \u2014 the Sweeper checks startup and system health, and tells you straight if it looks like failing hardware (software can't fix that).", 3);
    if (issues.indexOf("Can't run new software") >= 0)
      planItem("software", "Can't run new stuff \u2014 the software set brings modern programs matched to what " + eraWord() + " can actually handle.", 3);
    if (issues.indexOf("Feels unsafe online") >= 0)
      planItem("software", "Safety worries \u2014 the software set includes a modern browser, and our sister site the Signature Antivirus covers the rest.", 3);
    if (!issues.length) planItem("sweep", "No complaints \u2014 a full sweep keeps it that way and verifies good form.", 2);

    /* job drives the content items */
    var jobWhy = { "Work / office": "for your office work (" + a.jobNote.toLowerCase() + ")",
      "Creative work": "for your creative work (" + a.jobNote.toLowerCase() + ")",
      "Coding / building": "for building " + a.jobNote.toLowerCase(),
      "School / study": "for " + a.jobNote.toLowerCase(),
      "Web & email": "for " + a.jobNote.toLowerCase(),
      "Games": "for play \u2014 tuned to what your hardware can honestly run (no software upgrades a graphics card; this plan focuses on what your machine CAN do)",
      "A bit of everything": "so it does a bit of everything well" }[job] || "for your everyday use";
    planItem("apps", "The app collection, picked " + jobWhy + ".", 2);
    if (job === "Coding / building") planItem("tools", "Technician tools \u2014 a builder needs a real toolbox.", 2);
    if (job === "Creative work") planItem("lenses", "Lens views \u2014 see every project five ways.", 2);
    if (job === "School / study") planItem("lenses", "Lens views \u2014 study every topic five ways.", 1);
    planItem("pc_models", "PC model data \u2014 know exactly what " + eraWord() + " is.", 0);

    /* AI per connectivity + era, honestly gated */
    if (prio === "AI help" || prio === "Everything" || job !== "Games") {
      if (compat("ai_offline").level !== "no")
        planItem("ai_offline", (net === "Mostly offline" ? "You're mostly offline \u2014 this AI lives on the PC, no internet needed." : "Your own AI on the machine, no internet needed.") +
          (compat("ai_offline").level === "limited" ? " (May be slow on this much memory \u2014 your call.)" : ""), prio === "AI help" ? 3 : 1);
      if (compat("ai_online").level !== "no" && net !== "Mostly offline")
        planItem("ai_online", "Online AI with your own key for the heavy questions.", prio === "AI help" ? 2 : 0);
    }
    /* priority boosts */
    if (prio === "Speed") { planItem("ai_sweeper", "Speed is your priority \u2014 the Sweeper is the fastest win there is.", 3); }
    if (prio === "New apps") { planItem("apps", "New apps are your priority \u2014 the collection is the point.", 3); }
    if (prio === "Keeping files safe") {
      planItem("tools", "Keeping files safe \u2014 straight talk: back up first (the toolkit writes a restore manifest, but a backup is still king). The tools include the sweep that verifies your disk.", 2);
    }
    /* dedupe, keep first (highest intent), sort by boost */
    var seen = {}, out = [];
    S.plan.forEach(function (it) { if (!seen[it.comp]) { seen[it.comp] = 1; out.push(it); } });
    out.sort(function (x, y) { return y.boost - x.boost; });
    S.plan = out;
  }

  function renderPlan() {
    buildPlan();
    var a = S.answers;
    $("planIntro").innerHTML = "Built for <b>" + esc(a.job || "you") + "</b>" +
      (a.jobNote ? " (" + esc(a.jobNote) + ")" : "") + " on <b>" + esc(eraWord()) + "</b>. " +
      "Toggle anything \u2014 these are the advanced options, all yours.";
    var h = "";
    S.plan.forEach(function (it, i) {
      var c = COMPONENTS[it.comp];
      var badge = it.level === "yes" ? '<span class="badge ok">fits</span>'
        : it.level === "limited" ? '<span class="badge warn">with caveat</span>' : '<span class="badge no">skip</span>';
      h += '<label class="planitem' + (it.checked ? "" : " off") + '">' +
        '<input type="checkbox" data-i="' + i + '"' + (it.checked ? " checked" : "") + (it.level === "no" ? " disabled" : "") + ">" +
        "<div><b>" + esc(c.name) + "</b> " + badge + "<div class=\"why\">" + esc(it.why) +
        (it.note ? " <i>" + esc(it.note) + "</i>" : "") + "<br><span class=\"hint\">" + esc(c.desc) + "</span></div></div></label>";
    });
    $("planList").innerHTML = h || "<p class=\"hint\">Nothing fit \u2014 try the full standard sweep below.</p>";
    var boxes = $("planList").querySelectorAll("input[type=checkbox]");
    for (var i = 0; i < boxes.length; i++) {
      boxes[i].addEventListener("change", function () {
        var it = S.plan[parseInt(this.getAttribute("data-i"), 10)];
        it.checked = this.checked;
        this.parentNode.className = "planitem" + (it.checked ? "" : " off");
      });
    }
    $("selectAll").onclick = function () {
      S.plan.forEach(function (it) { if (it.level !== "no") it.checked = true; });
      renderPlan();
    };
    $("toStep4").onclick = function () { goStep(4); };
  }

  /* ---------- STEP 4: APPLY ---------- */
  function selected() { return S.plan.filter(function (it) { return it.checked && it.level !== "no"; }); }
  function renderApply() {
    var sel = selected();
    var comps = sel.map(function (it) { return it.comp; });
    var h = "<p><b>Your upgrade:</b> " + (comps.length ? comps.map(function (c) { return esc(COMPONENTS[c].name); }).join(" \u00B7 ") : "full standard sweep") + "</p>";
    h += "<p class=\"hint\">" + sel.length + " of " + S.plan.length + " planned items selected.</p>";
    $("applySummary").innerHTML = h;
    $("runCmd").textContent = "python3 signature_os_overlay.py --install --components " + (comps.length ? comps.join(",") : "all");
    $("dlProfile").onclick = function () {
      var profile = { tool: "signature-os-updater", version: 1,
        created: new Date().toISOString(),
        machine: S.machine || { estimate: true, era: S.era },
        answers: S.answers,
        components: comps.length ? comps : ORDER.slice(),
        note: "Place next to signature_os_overlay.py and run the command above." };
      var blob = new Blob([JSON.stringify(profile, null, 2)], { type: "application/json" });
      var a = document.createElement("a");
      a.href = URL.createObjectURL(blob); a.download = "my-signature-upgrade.json";
      document.body.appendChild(a); a.click();
      setTimeout(function () { document.body.removeChild(a); }, 500);
    };
    $("fullSweep").onclick = function () {
      S.plan.forEach(function (it) { if (it.level !== "no") it.checked = true; });
      renderApply();
      $("runCmd").textContent = "python3 signature_os_overlay.py --install --components all";
    };
  }
})();
