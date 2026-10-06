// Draws each career timeline's bars once, from the left, when it scrolls into view.
// The bars are visible without this script; it only adds the motion.
(() => {
  const timelines = document.querySelectorAll("[data-timeline]");
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (!timelines.length || reduceMotion || !("IntersectionObserver" in window)) {
    return;
  }

  const observer = new IntersectionObserver(
    (entries) => {
      for (const entry of entries) {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-drawn");
          observer.unobserve(entry.target);
        }
      }
    },
    { threshold: 0.25 },
  );

  for (const timeline of timelines) {
    timeline.querySelectorAll(".timeline-row").forEach((row, index) => {
      row.style.setProperty("--row", index);
    });
    timeline.classList.add("is-ready");
    observer.observe(timeline);
  }
})();
