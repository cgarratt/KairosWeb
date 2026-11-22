(() => {
  'use strict';
  const notices = document.querySelectorAll('[data-report-notice]');
  if (!notices.length) return;

  const stack = document.createElement('aside');
  stack.className = 'report-notices';
  stack.setAttribute('aria-label', 'Avisos del reporte');

  for (const notice of notices) {
    const popup = document.createElement('div');
    popup.className = 'report-notice';
    const close = document.createElement('button');
    close.className = 'report-notice-close tool-icon';
    close.type = 'button';
    close.setAttribute('aria-label', 'Cerrar aviso');
    close.textContent = '×';
    close.addEventListener('click', () => {
      popup.remove();
      const next = stack.querySelector('.report-notice-close') ||
        document.querySelector('#spot-refresh, .global-nav-link');
      next?.focus({preventScroll: true});
      if (!stack.childElementCount) stack.remove();
    });
    popup.append(close, notice);
    stack.append(popup);
  }

  document.body.append(stack);
})();
