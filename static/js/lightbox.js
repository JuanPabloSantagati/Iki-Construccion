// Lightbox de la galería de proyectos. Sin dependencias ni estilos inline (CSP estricta).
// Sin JS, cada miniatura es un link a la imagen grande: esto solo mejora la experiencia.
(() => {
  "use strict";

  const init = () => {
    const dialog = document.getElementById("lightbox");
    const links = Array.from(document.querySelectorAll("[data-gallery] [data-lightbox]"));
    if (!dialog || links.length === 0) return;

    const image = dialog.querySelector("[data-lightbox-image]");
    const counter = dialog.querySelector("[data-lightbox-counter]");
    const prev = dialog.querySelector("[data-lightbox-prev]");
    const next = dialog.querySelector("[data-lightbox-next]");
    let index = 0;
    let touchStartX = null;

    const show = (i) => {
      index = (i + links.length) % links.length;
      const link = links[index];
      image.src = link.href;
      image.alt = link.querySelector("img")?.alt ?? "";
      counter.textContent = `${index + 1} / ${links.length}`;
    };

    const open = (i) => {
      show(i);
      document.documentElement.classList.add("overflow-hidden");
      dialog.showModal();
    };

    // Una sola imagen: sin flechas.
    if (links.length === 1) {
      prev.classList.add("hidden");
      next.classList.add("hidden");
    }

    links.forEach((link, i) => {
      link.addEventListener("click", (event) => {
        event.preventDefault();
        open(i);
      });
    });

    prev.addEventListener("click", () => show(index - 1));
    next.addEventListener("click", () => show(index + 1));
    dialog.querySelector("[data-lightbox-close]").addEventListener("click", () => dialog.close());

    // Clic en el fondo (fuera de la imagen y los botones) cierra.
    dialog.addEventListener("click", (event) => {
      if (event.target === dialog || event.target === image.parentElement) dialog.close();
    });

    dialog.addEventListener("close", () => {
      document.documentElement.classList.remove("overflow-hidden");
      image.removeAttribute("src");
      links[index].focus();
    });

    dialog.addEventListener("keydown", (event) => {
      if (event.key === "ArrowLeft") show(index - 1);
      if (event.key === "ArrowRight") show(index + 1);
    });

    // Swipe en el celular.
    dialog.addEventListener(
      "touchstart",
      (event) => {
        touchStartX = event.changedTouches[0].clientX;
      },
      { passive: true },
    );
    dialog.addEventListener(
      "touchend",
      (event) => {
        if (touchStartX === null) return;
        const deltaX = event.changedTouches[0].clientX - touchStartX;
        touchStartX = null;
        if (Math.abs(deltaX) > 50) show(deltaX < 0 ? index + 1 : index - 1);
      },
      { passive: true },
    );
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
