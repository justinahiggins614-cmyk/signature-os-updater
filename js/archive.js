/* Archive page: Best of the Best, Ask-the-AI keyword find, A-Z by era. ES5, no deps. */
(function () {
  "use strict";
  function $(id) { return document.getElementById(id); }
  function esc(s) { return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) {
    return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }

  fetch("data/upgrades.json").then(function (r) { return r.json(); }).then(function (packs) {
    $("arcCount").textContent = packs.length.toLocaleString();
    var best = null, i;
    for (i = 0; i < packs.length; i++) if (packs[i].best) best = packs[i];
    if (best) {
      $("bestBox").innerHTML =
        "<p><b>" + esc(best.id) + " \u2014 " + esc(best.title) + "</b></p>" +
        "<p>" + esc(best.blurb) + "</p>" +
        "<p class=\"hint\">Includes: " + esc(best.components.join(", ")) + "</p>" +
        "<a class=\"btn\" href=\"upgrade.html\">Start with this pack \u2192</a>";
    }
    /* A-Z by era */
    var groups = {};
    packs.forEach(function (p) { (groups[p.era] = groups[p.era] || []).push(p); });
    var order = ["1990s", "2000s", "2010s", "modern"];
    var html = "";
    order.forEach(function (era) {
      var g = groups[era] || [];
      html += '<details class="az"><summary>' + esc(era) + ' machines \u2014 ' + g.length + ' packs</summary>';
      g.slice(0, 60).forEach(function (p) {
        html += '<div class="row"><b>' + esc(p.id) + '</b> \u2014 ' + esc(p.title) +
          '<br><span class="hint">' + esc(p.blurb) + '</span></div>';
      });
      if (g.length > 60) html += '<div class="row hint">\u2026and ' + (g.length - 60) + ' more in this era.</div>';
      html += "</details>";
    });
    $("az").innerHTML = html;

    /* Ask the AI: honest keyword find over the pack data */
    function score(p, words) {
      var t = (p.title + " " + p.blurb + " " + p.era + " " + p.os + " " + p.focus_label).toLowerCase();
      var s = 0, w;
      for (var k = 0; k < words.length; k++) { w = words[k]; if (w && t.indexOf(w) >= 0) s++; }
      return s;
    }
    function ask() {
      var q = $("askIn").value.toLowerCase();
      var words = q.replace(/[^a-z0-9 ]/g, " ").split(/\s+/).filter(function (w) { return w.length > 2; });
      var ranked = packs.map(function (p) { return { p: p, s: score(p, words) }; })
        .filter(function (r) { return r.s > 0; })
        .sort(function (a, b) { return b.s - a.s; }).slice(0, 3);
      if (!ranked.length) {
        $("askOut").innerHTML = "<p>I couldn't match that to a pack \u2014 try words like an era (1990s, 2010s), a system (windows, mac), or a use (office, school, games). " +
          "Or take the 4-step upgrade walkthrough and Patch will build your plan personally: <a href=\"upgrade.html\">start here \u2192</a></p>";
        return;
      }
      var h = "<p><b>Here's what fits:</b></p>";
      ranked.forEach(function (r) {
        h += "<div class=\"planitem\"><div><b>" + esc(r.p.id) + " \u2014 " + esc(r.p.title) + "</b>" +
          "<div class=\"why\">" + esc(r.p.blurb) + "</div></div></div>";
      });
      h += "<p><a class=\"btn\" href=\"upgrade.html\">Apply one with the guided upgrade \u2192</a></p>";
      $("askOut").innerHTML = h;
    }
    $("askSend").onclick = ask;
    $("askIn").addEventListener("keydown", function (e) { if (e.key === "Enter") ask(); });
  }).catch(function () {
    $("bestBox").innerHTML = "<p class=\"hint\">Pack data is loading \u2014 check back in a moment.</p>";
    /* Offline: the Ask box must still answer honestly instead of silently doing nothing. */
    $("askSend").onclick = function () {
      $("askOut").innerHTML = "<p class=\"hint\">The pack catalog could not be loaded (you may be offline) \u2014 " +
        "check your connection and try again, or take the 4-step upgrade walkthrough: " +
        "<a href=\"upgrade.html\">start here \u2192</a></p>";
    };
  });
})();
