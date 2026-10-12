document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.flash').forEach((el) => {
    window.setTimeout(() => { if (el.isConnected) el.remove(); }, 6500);
  });

  const root = document.documentElement;
  const toggle = document.getElementById('themeToggle');
  const applyTheme = (theme) => {
    root.dataset.theme = theme;
    if (toggle) {
      toggle.textContent = theme === 'dark' ? '☀ Light mode' : '◐ Dark mode';
      toggle.setAttribute('aria-pressed', String(theme === 'dark'));
    }
  };
  let savedTheme = 'light';
  try { savedTheme = localStorage.getItem('jobtrack-theme') || 'light'; } catch (e) { /* storage can be disabled */ }
  applyTheme(savedTheme === 'dark' ? 'dark' : 'light');
  if (toggle) {
    toggle.addEventListener('click', () => {
      const nextTheme = root.dataset.theme === 'dark' ? 'light' : 'dark';
      applyTheme(nextTheme);
      try { localStorage.setItem('jobtrack-theme', nextTheme); } catch (e) { /* theme still works for this page */ }
    });
  }
});
