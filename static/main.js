// Highlight today's row in the opening hours (1 = Montag … 7 = Sonntag)
const today = new Date().getDay() || 7;
document.querySelectorAll(`.hours tr[data-day="${today}"]`).forEach((row) => row.classList.add("today"));

// Gently fade sections in as they scroll into view
const revealEls = document.querySelectorAll(".reveal");
if ("IntersectionObserver" in window) {
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("visible");
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.15 }
  );
  revealEls.forEach((el) => observer.observe(el));
} else {
  revealEls.forEach((el) => el.classList.add("visible"));
}
