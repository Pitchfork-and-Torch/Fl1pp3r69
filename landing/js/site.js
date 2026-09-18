/**
 * Fl1pp3r69 landing - ARGUS VEIL interactions
 * Pipeline phase detail + smooth-scroll helpers. No network calls.
 */
(function () {
  "use strict";

  var PHASES = {
    INTAKE: {
      title: "INTAKE",
      body: "Name the op, pick type / PATHNUM, optional template. Nothing free-floats outside a CASEFILE.",
    },
    OP_PREP: {
      title: "OP_PREP",
      body: "Mint opId, write OPERATION + ACTIVE_OP + CHECKPOINT. OPSEC defaults engage before probe.",
    },
    PROBE: {
      title: "PROBE",
      body: "Launch domain tools (DEWDROP, DAMP_CROWD, EMBER_TRACE, LODGE, BITKEY, HAZE, GPIO LAB, INKWELL) under the hub.",
    },
    CAPTURE: {
      title: "CAPTURE",
      body: "Raw artifacts land in the op tree with meta sidecars. Stock app files can enter via CLAIM.",
    },
    VERIFY: {
      title: "VERIFY",
      body: "SHA-256 every sealed item into CASEFILE-MANIFEST. Fail closed on mismatch. Desktop can Merkle-seal large vaults.",
    },
    EXFIL: {
      title: "EXFIL",
      body: "Deliberate only: SD export or USB serial. Nothing auto-uploads. Air-gap remains first-class.",
    },
    CLOSE: {
      title: "CLOSE",
      body: "Seal the op, clear ACTIVE_OP when matching, update index + timeline. Chain-of-custody ready for report.",
    },
  };

  function setDetail(btn) {
    var detail = document.getElementById("phase-detail");
    if (!detail || !btn) return;
    var key = btn.getAttribute("data-phase");
    var p = PHASES[key] || PHASES.INTAKE;
    detail.innerHTML =
      "<strong>" +
      p.title +
      "</strong><p>" +
      p.body +
      "</p>";
    if (btn.id) detail.setAttribute("aria-labelledby", btn.id);
  }

  function activatePhase(tabs, btn, moveFocus) {
    tabs.forEach(function (b) {
      var on = b === btn;
      b.setAttribute("aria-selected", on ? "true" : "false");
      b.tabIndex = on ? 0 : -1;
    });
    setDetail(btn);
    if (moveFocus) btn.focus();
  }

  function bootPipeline() {
    var tabs = Array.prototype.slice.call(
      document.querySelectorAll('.phase[role="tab"][data-phase]')
    );
    if (!tabs.length) return;

    tabs.forEach(function (btn, i) {
      btn.addEventListener("click", function () {
        activatePhase(tabs, btn, false);
      });
      btn.addEventListener("keydown", function (e) {
        var next = null;
        if (e.key === "ArrowRight" || e.key === "ArrowDown") {
          next = tabs[(i + 1) % tabs.length];
        } else if (e.key === "ArrowLeft" || e.key === "ArrowUp") {
          next = tabs[(i - 1 + tabs.length) % tabs.length];
        } else if (e.key === "Home") {
          next = tabs[0];
        } else if (e.key === "End") {
          next = tabs[tabs.length - 1];
        }
        if (!next) return;
        e.preventDefault();
        activatePhase(tabs, next, true);
      });
    });

    var selected =
      document.querySelector('.phase[role="tab"][aria-selected="true"]') ||
      tabs[0];
    activatePhase(tabs, selected, false);
  }

  function bootYear() {
    var el = document.getElementById("year");
    if (el) el.textContent = String(new Date().getFullYear());
  }

  function boot() {
    bootPipeline();
    bootYear();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
