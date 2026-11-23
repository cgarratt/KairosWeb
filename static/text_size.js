(() => {
  'use strict';

  const storageKey = 'kairosweb-text-size';
  const scales = [90, 100, 110, 120, 130];
  let index = scales.indexOf(100);
  try {
    const saved = scales.indexOf(Number(localStorage.getItem(storageKey)));
    if (saved >= 0) index = saved;
  } catch {
    // The button works for the current page when storage is unavailable.
  }

  function applyScale() {
    document.documentElement.style.setProperty('--kairos-text-scale', scales[index] / 100);
  }
  applyScale();

  document.addEventListener('DOMContentLoaded', () => {
    const controls = document.querySelector('.text-size-controls');
    if (!controls) return;

    const button = controls.querySelector('[data-text-cycle]');
    const status = controls.querySelector('[role="status"]');
    const nextIndex = () => (index + 1) % scales.length;

    function updateLabel() {
      const label = 'Ajustar tamaño del texto. Actual: ' + scales[index]
        + ' %. Siguiente: ' + scales[nextIndex()] + ' %.';
      button.setAttribute('aria-label', label);
      button.title = label;
    }

    button.addEventListener('click', () => {
      index = nextIndex();
      applyScale();
      updateLabel();
      status.textContent = 'Tamaño del texto: ' + scales[index] + ' %.';
      try {
        localStorage.setItem(storageKey, scales[index]);
      } catch {
        // Keep the active setting for this page.
      }
      window.dispatchEvent(new Event('kairos:text-size'));
    });

    updateLabel();
    controls.hidden = false;
  });
})();
