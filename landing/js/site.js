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

  function setDetail(key) {
    var detail = document.getElementById("phase-detail");
    if (!detail) return;
    var p = PHASES[key] || PHASES.INTAKE;
    detail.innerHTML =
      "<strong>" +
      p.title +
      "</strong><p>" +
      p.body +
      "</p>";
  }

  function bootPipeline() {
    var phases = document.querySelectorAll(".phase[data-phase]");
    if (!phases.length) return;

    phases.forEach(function (btn) {
      btn.addEventListener("click", function () {
        phases.forEach(function (b) {
          b.setAttribute("aria-pressed", "false");
        });
        btn.setAttribute("aria-pressed", "true");
        setDetail(btn.getAttribute("data-phase"));
      });
    });

    var first = phases[0];
    if (first) {
      first.setAttribute("aria-pressed", "true");
      setDetail(first.getAttribute("data-phase"));
    }
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
