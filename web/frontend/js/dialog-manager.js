import { showUpdateDialog, closeUpdateDialog } from './update-dialog.js';

const DialogManager = {
  async showUpdatePrompt(titleOrOptions, maybeLines = []) {
    const options = typeof titleOrOptions === 'string'
      ? { title: titleOrOptions, lines: Array.isArray(maybeLines) ? maybeLines : [maybeLines].filter(Boolean) }
      : (titleOrOptions || {});

    const payload = {
      title: options.title ?? 'Update available',
      lines: Array.isArray(options.lines) ? options.lines : [options.lines].filter(Boolean),
    };

    try {
      return await showUpdateDialog(payload);
    } catch (error) {
      console.error('DialogManager.showUpdatePrompt fallback', error);
      const message = [payload.title, '', ...payload.lines].filter(Boolean).join('\n');
      return window.confirm(message);
    }
  },

  async showConfirm(message) {
    try {
      return window.confirm(message);
    } catch (error) {
      console.error('DialogManager.showConfirm fallback', error);
      return false;
    }
  },

  async showAlert(message) {
    try {
      window.alert(message);
    } catch (error) {
      console.error('DialogManager.showAlert fallback', error);
    }
  },

  closeAll() {
    closeUpdateDialog();
  },
};

function markReady() {
  globalThis.DialogManager = DialogManager;
  globalThis.DialogManagerReady = true;
}

globalThis.DialogManagerReady = false;

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', markReady);
} else {
  markReady();
}

export { DialogManager };
