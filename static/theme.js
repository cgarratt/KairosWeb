(() => {
  'use strict';
  const storageKey = 'kairosweb-theme';
  const themes = {light: 'Claro', dark: 'Azul marino oscuro', black: 'Negro'};
  const order = Object.keys(themes);
  const nextTheme = (current) => order[(order.indexOf(current) + 1) % order.length];

  function setTheme(value) {
    const theme = order.includes(value) ? value : 'light';
    document.documentElement.dataset.theme = theme;
    try { localStorage.setItem(storageKey, theme); } catch (_) {}
    document.querySelectorAll('[data-theme-toggle]').forEach(button => {
      const label = 'Activar tema ' + themes[nextTheme(theme)];
      button.setAttribute('aria-label', label);
      button.title = label;
    });
    document.querySelectorAll('input[name="theme-choice"]').forEach(input => {
      input.checked = input.value === theme;
    });
  }

  setTheme(document.documentElement.dataset.theme);
  document.addEventListener('click', event => {
    if (event.target.closest('[data-theme-toggle]')) {
      setTheme(nextTheme(document.documentElement.dataset.theme));
    }
  });
  document.addEventListener('change', event => {
    if (event.target.matches('input[name="theme-choice"]')) setTheme(event.target.value);
  });
})();
