// Progressive enhancement only. All sampling and inventory calculations run in Python.
const form = document.querySelector('#experiment-form');
form?.addEventListener('submit', () => {
  if (!form.checkValidity()) return;
  const button = form.querySelector('button[type="submit"]');
  button.disabled = true;
  button.querySelector('span').textContent = 'Running…';
  form.setAttribute('aria-busy', 'true');
});
window.addEventListener('pageshow', () => {
  const button = form?.querySelector('button[type="submit"]');
  if (button) { button.disabled = false; button.querySelector('span').textContent = 'Run simulation'; }
  form?.removeAttribute('aria-busy');
});

// The linked editor uses native form ownership and disclosure behavior.
const demandEditor = document.querySelector('#demand-settings');
document.querySelector('.demand-link')?.addEventListener('click', () => {
  demandEditor.open = true;
});

// Keep probability labels aligned while editing the possible quantities.
demandEditor?.addEventListener('input', (event) => {
  const index = event.target.dataset.demandIndex;
  if (index === undefined) return;
  demandEditor.querySelectorAll(`[data-demand-label="${index}"]`).forEach((label) => {
    label.textContent = event.target.value || '—';
  });
});
