/*
 * BANQED — site-wide JavaScript.
 *
 * Loaded on every page from base.html. Two things live here:
 *
 *   1. The front page newspaper: six spreads shown one at a time, turned by
 *      clicking the page, pressing the arrow keys, or using the controls.
 *   2. Small shared behaviours used across the site.
 *
 * The Wardrobe and Sales tables are a much larger job and have their own
 * file, banq_table.js, which only those two pages load.
 *
 * Everything here checks that the elements it needs are actually present
 * before running, so a page that has no newspaper on it simply skips it.
 */
 
(function () {
  "use strict";
 
  /* ----------------------------------------------------------------------
     The front page newspaper
     ---------------------------------------------------------------------- */
 
  function initPaper() {
    const paper = document.querySelector("[data-paper]");
    if (!paper) return;
 
    const spreads = Array.from(paper.querySelectorAll("[data-spread]"));
    if (spreads.length === 0) return;
 
    const prevButton = paper.querySelector("[data-paper-prev]");
    const nextButton = paper.querySelector("[data-paper-next]");
    const dotList = paper.querySelector("[data-paper-dots]");
    const hint = paper.querySelector("[data-paper-hint]");
 
    let current = 0;
    let hasTurned = false;
 
    // The front page opens full screen: the site banner stays hidden until
    // the reader first turns a page, then remains for the rest of the visit.
    document.body.classList.add("paper-fullscreen");
 
    // One dot per spread, each a real button so the paper stays navigable
    // by keyboard and readable to a screen reader.
    const dots = spreads.map(function (spread, index) {
      const item = document.createElement("li");
      const dot = document.createElement("button");
      dot.type = "button";
      dot.className = "paper__dot";
      dot.setAttribute("aria-label", `Go to page ${index + 1}`);
      dot.addEventListener("click", function (event) {
        event.stopPropagation();
        show(index);
      });
      item.appendChild(dot);
      dotList.appendChild(item);
      return dot;
    });
 
    function show(index) {
      current = Math.max(0, Math.min(index, spreads.length - 1));
 
      spreads.forEach(function (spread, i) {
        const isCurrent = i === current;
        spread.hidden = !isCurrent;
        spread.classList.toggle("is-current", isCurrent);
      });
 
      dots.forEach(function (dot, i) {
        dot.classList.toggle("is-current", i === current);
        dot.setAttribute("aria-current", i === current ? "true" : "false");
      });
 
      prevButton.disabled = current === 0;
      nextButton.disabled = current === spreads.length - 1;
 
      // The dark spread needs the page around it to go dark too, or the
      // white margins fight the design.
      paper.classList.toggle(
        "is-dark",
        spreads[current].classList.contains("spread--dark")
      );
 
      // Turning the page resets the reading position, since each spread is
      // its own page rather than a continuation of the last.
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
 
    function turn(step) {
      const target = current + step;
      if (target < 0 || target >= spreads.length) return;
      if (!hasTurned) {
        hasTurned = true;
        if (hint) hint.hidden = true;
        document.body.classList.remove("paper-fullscreen");
      }
      show(target);
    }
 
    nextButton.addEventListener("click", function (event) {
      event.stopPropagation();
      turn(1);
    });
 
    prevButton.addEventListener("click", function (event) {
      event.stopPropagation();
      turn(-1);
    });

    paper.querySelectorAll("[data-paper-turn]").forEach(function (button) {
      button.addEventListener("click", function (event) {
        event.stopPropagation();
        turn(1);
      });
    });
 
    // Clicking the page turns it, but not when the click was meant for
    // something else: a link, a button, or text the reader is selecting.
    paper.addEventListener("click", function (event) {
      if (event.target.closest("a, button")) return;
      if (window.getSelection && String(window.getSelection()).length > 0) return;
      turn(1);
    });
 
    document.addEventListener("keydown", function (event) {
      if (event.key === "ArrowRight" || event.key === "PageDown") {
        event.preventDefault();
        turn(1);
      } else if (event.key === "ArrowLeft" || event.key === "PageUp") {
        event.preventDefault();
        turn(-1);
      } else if (event.key === "Home") {
        event.preventDefault();
        show(0);
      } else if (event.key === "End") {
        event.preventDefault();
        show(spreads.length - 1);
      }
    });
 
    // Swiping through the paper on a phone should feel the same as clicking.
    let touchStartX = null;
    paper.addEventListener("touchstart", function (event) {
      touchStartX = event.changedTouches[0].clientX;
    }, { passive: true });
 
    paper.addEventListener("touchend", function (event) {
      if (touchStartX === null) return;
      const distance = event.changedTouches[0].clientX - touchStartX;
      if (Math.abs(distance) > 60) turn(distance < 0 ? 1 : -1);
      touchStartX = null;
    }, { passive: true });
 
    show(0);
  }
 
  /* ----------------------------------------------------------------------
     Shared site behaviour
     ---------------------------------------------------------------------- */
 
  // Mark the current page in the main navigation, so where you are is
  // legible without the nav having to be rebuilt per template.
  function markCurrentNavLink() {
    const path = window.location.pathname;
    document.querySelectorAll("nav a[href]").forEach(function (link) {
      const href = link.getAttribute("href");
      if (!href || href === "/") return;
      if (path === href || path.startsWith(href + "/")) {
        link.classList.add("is-current");
        link.setAttribute("aria-current", "page");
      }
    });
  }
 
  function init() {
    initPaper();
    markCurrentNavLink();
  }
 
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();