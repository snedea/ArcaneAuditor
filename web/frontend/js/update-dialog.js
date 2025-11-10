const doc = globalThis.document;

let activeCleanup = null;

function removeExisting() {
  const existing = doc.getElementById('aa-update-preference-dialog');
  if (existing) {
    existing.remove();
  }
}

function buildButton({ text, styles, onClick }) {
  const button = doc.createElement('button');
  button.textContent = text;
  button.style.cssText = styles.join(';');
  button.addEventListener('click', onClick, { once: true });
  return button;
}

function createDialog({ title, lines }) {
  removeExisting();

  const overlay = doc.createElement('div');
  overlay.id = 'aa-update-preference-dialog';
  overlay.style.cssText = [
    'position: fixed',
    'inset: 0',
    'background: rgba(15, 23, 42, 0.65)',
    'backdrop-filter: blur(4px)',
    'display: flex',
    'align-items: center',
    'justify-content: center',
    'z-index: 2147483647',
  ].join(';');

  const modal = doc.createElement('div');
  modal.style.cssText = [
    'background: #0f172a',
    'color: #f8fafc',
    'min-width: 360px',
    'max-width: 480px',
    'padding: 28px 32px',
    'border-radius: 18px',
    'box-shadow: 0 32px 60px rgba(15, 23, 42, 0.55)',
    'border: 1px solid rgba(148, 163, 184, 0.35)',
    'font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
  ].join(';');
  modal.setAttribute('role', 'dialog');
  modal.setAttribute('aria-modal', 'true');

  const heading = doc.createElement('h2');
  heading.textContent = title;
  heading.style.cssText = 'margin: 0 0 12px 0; font-size: 1.2rem; font-weight: 700;';
  heading.id = 'aa-update-dialog-title';
  modal.setAttribute('aria-labelledby', heading.id);
  modal.appendChild(heading);

  lines.forEach((text) => {
    const paragraph = doc.createElement('p');
    paragraph.textContent = text;
    paragraph.style.cssText = 'margin: 12px 0; line-height: 1.5; color: #cbd5f5;';
    modal.appendChild(paragraph);
  });

  const hint = doc.createElement('p');
  hint.style.cssText = 'margin: 12px 0 20px; font-size: 0.9rem; color: #94a3b8;';
  modal.appendChild(hint);

  const buttonRow = doc.createElement('div');
  buttonRow.style.cssText = 'display: flex; gap: 12px; justify-content: flex-end;';

  return { overlay, modal, buttonRow };
}

export function showUpdateDialog({ title, lines = [] }) {
  if (!Array.isArray(lines)) {
    lines = [String(lines)].filter(Boolean);
  }

  return new Promise((resolve) => {
    try {
      const { overlay, modal, buttonRow } = createDialog({ title, lines });

      let resolved = false;
      let escHandler;
      const cleanup = (value) => {
        if (resolved) return;
        resolved = true;
        removeExisting();
        if (escHandler) {
          doc.removeEventListener('keydown', escHandler);
        }
        activeCleanup = null;
        resolve(value);
      };

      activeCleanup = () => cleanup(false);

      const disableBtn = buildButton({
        text: 'Disable',
        styles: [
          'padding: 10px 18px',
          'border-radius: 9999px',
          'border: 1px solid rgba(148, 163, 184, 0.6)',
          'background: rgba(15, 23, 42, 0.8)',
          'color: #e2e8f0',
          'font-weight: 600',
          'cursor: pointer',
        ],
        onClick: () => cleanup(false),
      });

      const enableBtn = buildButton({
        text: 'Enable',
        styles: [
          'padding: 10px 20px',
          'border-radius: 9999px',
          'border: none',
          'background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%)',
          'color: #f8fafc',
          'font-weight: 700',
          'cursor: pointer',
          'box-shadow: 0 10px 25px rgba(99, 102, 241, 0.35)',
        ],
        onClick: () => cleanup(true),
      });

      escHandler = (event) => {
        if (event.key === 'Escape') {
          cleanup(false);
        }
      };

      overlay.addEventListener('click', (event) => {
        if (event.target === overlay) {
          cleanup(false);
        }
      });

      doc.addEventListener('keydown', escHandler);

      buttonRow.append(disableBtn, enableBtn);
      modal.appendChild(buttonRow);
      overlay.appendChild(modal);
      doc.body.appendChild(overlay);
      enableBtn.focus();
    } catch (err) {
      console.error('Failed to render update preference dialog', err);
      activeCleanup = null;
      resolve(false);
    }
  });
}

export function closeUpdateDialog() {
  if (typeof activeCleanup === 'function') {
    const cleanup = activeCleanup;
    activeCleanup = null;
    cleanup(false);
    return;
  }
  removeExisting();
}
