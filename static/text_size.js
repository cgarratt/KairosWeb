(() => {
  'use strict';

  const storageKey = 'kairosweb-text-size';
  const scales = [90, 100, 110, 120, 130];
  let index = scales.indexOf(100);
  try {
    const saved = scales.indexOf(Number(localStorage.getItem(storageKey)));
    if (saved >= 0) index = saved;
  } catch {
    // The controls work for the current page when storage is unavailable.
  }

  const apply = () => {
    document.documentElement.style.setProperty('--kairos-text-scale', scales[index] / 100);
  };
  apply();

  document.addEventListener('DOMContentLoaded', () => {
    const controls = document.querySelector('.text-size-controls');
    if (!controls) return;

    const decrease = controls.querySelector('[data-text-step="-1"]');
    const increase = controls.querySelector('[data-text-step="1"]');
    const status = controls.querySelector('[role="status"]');

    function updateControls() {
      decrease.disabled = index === 0;
      increase.disabled = index === scales.length - 1;
    }

    function change(step) {
      const next = index + step;
      if (next < 0 || next >= scales.length) return;

      index = next;
      apply();
      updateControls();
      if (document.activeElement === decrease && decrease.disabled) increase.focus();
      if (document.activeElement === increase && increase.disabled) decrease.focus();
      status.textContent = 'Tamaño del texto: ' + scales[index] + ' %.';
      try {
        localStorage.setItem(storageKey, scales[index]);
      } catch {
        // Keep the active setting for this page.
      }
      window.dispatchEvent(new Event('kairos:text-size'));
    }

    decrease.addEventListener('click', () => change(-1));
    increase.addEventListener('click', () => change(1));
    updateControls();
    controls.hidden = false;
  });
})();
