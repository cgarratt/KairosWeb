(() => {
  'use strict';
  const panel = document.querySelector('[data-passkeys]');
  const status = panel.querySelector('[data-passkey-status]');
  const buttons = [...panel.querySelectorAll('[data-passkey-action]')];
  const password = panel.querySelector('[name=password]');

  async function exchange(body) {
    const response = await fetch(panel.dataset.endpoint, {
      method: 'POST',
      headers: {'Content-Type': 'application/json', 'X-Kairos-Csrf': panel.dataset.csrf},
      body: JSON.stringify(body),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.message || 'No se pudo completar la solicitud.');
    return data;
  }

  async function invoke(action) {
    const keyApi = window.PublicKeyCredential;
    if (action !== 'revoke' && !(window.isSecureContext && keyApi &&
        keyApi.parseCreationOptionsFromJSON && keyApi.parseRequestOptionsFromJSON)) {
      throw new Error('Este navegador no admite llaves de acceso para Kairos.');
    }
    if (password && !password.reportValidity()) return;
    const options = await exchange({action, step: 'options', password: password?.value});
    if (action === 'revoke') {
      status.textContent = 'Llave retirada de Kairos.';
      return;
    }
    const registering = action === 'register';
    const credential = registering
      ? await navigator.credentials.create({publicKey: keyApi.parseCreationOptionsFromJSON(options)})
      : await navigator.credentials.get({publicKey: keyApi.parseRequestOptionsFromJSON(options)});
    if (!credential) throw new Error('No se completó la verificación del dispositivo.');
    const remember = document.querySelector('[name=remember_me]')?.checked === true;
    const result = await exchange({action, step: 'verify', credential: credential.toJSON(), remember});
    if (result.redirect) {
      window.location.assign(result.redirect);
      return;
    }
    status.textContent = 'Llave activada. Puedes usarla la próxima vez que inicies sesión en la PWA.';
  }

  panel.addEventListener('submit', event => event.preventDefault());
  buttons.forEach(button => button.addEventListener('click', async () => {
    buttons.forEach(item => { item.disabled = true; });
    status.textContent = 'Verificando…';
    try {
      await invoke(button.dataset.passkeyAction);
    } catch (error) {
      status.textContent = error.name === 'NotAllowedError'
        ? 'La solicitud se canceló o el dispositivo no encontró una llave válida.'
        : error.message;
    } finally {
      if (password) password.value = '';
      buttons.forEach(item => { item.disabled = false; });
    }
  }));
})();
