(() => {
  const toggle = document.getElementById("menuToggle");
  const overlay = document.getElementById("navOverlay");
  if (!toggle) return;

  const closeNav = () => document.body.classList.remove("nav-open");
  const openNav = () => document.body.classList.add("nav-open");

  toggle.addEventListener("click", () => {
    if (document.body.classList.contains("nav-open")) {
      closeNav();
    } else {
      openNav();
    }
  });

  overlay?.addEventListener("click", closeNav);
})();
