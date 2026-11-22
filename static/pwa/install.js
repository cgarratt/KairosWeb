if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/pwa/sw.js', {scope: '/pwa/'}).catch(() => {
    // Online access remains available if the device cannot register the worker.
  });
}
