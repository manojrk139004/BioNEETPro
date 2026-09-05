// ═══════════════════════════════════════════════════════════
//  BIONEET PRO — Shared Utilities
// ═══════════════════════════════════════════════════════════

// ─── Toast Notifications ───────────────────────────────────
export function toast(msg, type = 'info') {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    document.body.appendChild(container);
  }
  const t = document.createElement('div');
  const cls = type === 's' || type === 'success' ? 'success' : type === 'e' || type === 'error' ? 'error' : 'info';
  t.className = `toast ${cls}`;
  const text = document.createElement('span');
  text.textContent = msg;
  t.appendChild(text);
  container.appendChild(t);
  setTimeout(() => {
    t.style.opacity = '0';
    t.style.transform = 'translateX(20px)';
    t.style.transition = 'all 0.3s ease';
    setTimeout(() => t.remove(), 300);
  }, 3500);
}

// ─── Modal Management ──────────────────────────────────────
export function openModal(id) {
  const el = document.getElementById(id);
  if (el) {
    el.classList.remove('hidden');
    document.body.style.overflow = 'hidden';
  }
}
export function closeModal(id) {
  const el = document.getElementById(id);
  if (el) {
    el.classList.add('hidden');
    document.body.style.overflow = '';
  }
}

// ─── Navigation (SPA page switching) ───────────────────────
let currentPage = 'home';
const pageCallbacks = {};

export function registerPageCallback(page, fn) {
  pageCallbacks[page] = fn;
}

export function go(page) {
  // Hide all pages
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  // Show target
  const target = document.getElementById('page-' + page);
  if (target) target.classList.add('active');
  currentPage = page;

  // Update nav active states
  document.querySelectorAll('.nav-links a').forEach(a => a.classList.remove('active'));
  document.querySelectorAll(`.nav-links a[data-page="${page}"]`).forEach(a => a.classList.add('active'));

  // Update sidebar active states
  document.querySelectorAll('.sidebar-item').forEach(s => s.classList.remove('active'));
  document.querySelectorAll(`.sidebar-item[data-page="${page}"]`).forEach(s => s.classList.add('active'));

  // Scroll to top
  window.scrollTo(0, 0);

  // Call page-specific renderer
  if (pageCallbacks[page]) pageCallbacks[page]();

  // Close mobile nav if open
  document.querySelectorAll('.nav-links').forEach(n => n.classList.remove('open'));
  document.querySelectorAll('.sidebar').forEach(s => s.classList.remove('open'));
  document.body.classList.remove('nav-open');
}

export function getCurrentPage() { return currentPage; }

// ─── Theme Toggle ──────────────────────────────────────────
export function initTheme() {
  const saved = localStorage.getItem('theme');
  const preferred = window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
  const theme = saved || preferred;
  document.documentElement.setAttribute('data-theme', theme);
  updateThemeIcon(theme);
}

export function toggleTheme() {
  const current = document.documentElement.getAttribute('data-theme') || 'dark';
  const next = current === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', next);
  localStorage.setItem('theme', next);
  updateThemeIcon(next);
}

function updateThemeIcon(theme) {
  const icons = document.querySelectorAll('.theme-toggle');
  icons.forEach(icon => {
    icon.textContent = theme === 'dark' ? '☀️' : '🌙';
  });
}

// ─── Date Formatting ───────────────────────────────────────
export function formatDate(d, opts) {
  if (!d) return '—';
  const date = new Date(d);
  if (isNaN(date.getTime())) return '—';
  return date.toLocaleDateString('en-IN', opts || { day: 'numeric', month: 'short', year: 'numeric' });
}

export function formatDateShort(d) {
  return formatDate(d, { day: 'numeric', month: 'short' });
}

export function timeAgo(d) {
  if (!d) return '';
  const now = Date.now();
  const diff = now - new Date(d).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'Just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  if (days < 7) return `${days}d ago`;
  return formatDateShort(d);
}

// ─── Tabs ──────────────────────────────────────────────────
export function switchTab(btn, tabId) {
  const tabsContainer = btn.closest('.tabs');
  if (tabsContainer) {
    tabsContainer.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  }
  btn.classList.add('active');
  const page = btn.closest('.page') || document;
  page.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
  const panel = document.getElementById(tabId);
  if (panel) panel.classList.add('active');
}

// ─── Chip activation ───────────────────────────────────────
export function chipActivate(chip) {
  const parent = chip.parentElement;
  if (parent) parent.querySelectorAll('.chip').forEach(c => c.classList.remove('active'));
  chip.classList.add('active');
}

// ─── Debounce ──────────────────────────────────────────────
export function debounce(fn, delay = 300) {
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), delay);
  };
}

// ─── Pad number ────────────────────────────────────────────
export function pad(n) { return n < 10 ? '0' + n : '' + n; }

// ─── Contrast color helper ─────────────────────────────────
export function getContrastColor(hex) {
  if (!hex) return '#fff';
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return (r * 299 + g * 587 + b * 114) / 1000 > 128 ? '#0D1117' : '#ffffff';
}

// ─── YouTube ID extractor ──────────────────────────────────
export function extractYtId(url) {
  if (!url) return '';
  const m = url.match(/(?:v=|youtu\.be\/)([a-zA-Z0-9_-]{11})/);
  return m ? m[1] : url;
}

// ─── Keyboard Shortcuts ────────────────────────────────────
const shortcuts = {};

export function registerShortcut(key, fn) {
  shortcuts[key.toLowerCase()] = fn;
}

export function initKeyboardShortcuts() {
  document.addEventListener('keydown', (e) => {
    // Don't trigger when typing in inputs
    if (['INPUT', 'TEXTAREA', 'SELECT'].includes(e.target.tagName)) return;

    const key = e.key.toLowerCase();
    if (shortcuts[key]) {
      e.preventDefault();
      shortcuts[key](e);
    }
  });
}

// ─── Navbar scroll effect ──────────────────────────────────
export function initNavScroll() {
  const nav = document.querySelector('.navbar');
  if (!nav) return;
  window.addEventListener('scroll', () => {
    nav.classList.toggle('scrolled', window.scrollY > 10);
  });
}

// ─── Animate counter ───────────────────────────────────────
export function animateCounter(el, target, duration = 1500) {
  if (!el) return;
  let start = 0;
  const step = target / (duration / 16);
  const timer = setInterval(() => {
    start += step;
    if (start >= target) {
      el.textContent = target + (el.dataset.suffix || '');
      clearInterval(timer);
    } else {
      el.textContent = Math.floor(start) + (el.dataset.suffix || '');
    }
  }, 16);
}

// ─── Mobile hamburger toggle ───────────────────────────────
export function initMobileNav() {
  const hamburger = document.querySelector('.nav-hamburger');
  const navLinks = document.getElementById('mainNavLinks') || document.getElementById('gNav') || document.getElementById('sNav') || document.getElementById('aNav');
  if (hamburger && navLinks) {
    hamburger.addEventListener('click', () => {
      navLinks.classList.toggle('open');
      document.body.classList.toggle('nav-open', navLinks.classList.contains('open'));
    });
  }
}

// ─── Streak System ─────────────────────────────────────────
export function getStreak() {
  const data = JSON.parse(localStorage.getItem('streak') || '{"count":0,"lastDate":""}');
  const today = new Date().toDateString();
  const yesterday = new Date(Date.now() - 86400000).toDateString();

  if (data.lastDate === today) return data.count;
  if (data.lastDate === yesterday) return data.count; // Will be incremented on activity
  return 0; // Streak broken
}

export function updateStreak() {
  const data = JSON.parse(localStorage.getItem('streak') || '{"count":0,"lastDate":""}');
  const today = new Date().toDateString();
  const yesterday = new Date(Date.now() - 86400000).toDateString();

  if (data.lastDate === today) return data.count; // Already counted today
  if (data.lastDate === yesterday) {
    data.count += 1;
  } else {
    data.count = 1; // Reset streak
  }
  data.lastDate = today;
  localStorage.setItem('streak', JSON.stringify(data));
  return data.count;
}

// ─── Bookmark system ───────────────────────────────────────
export function isBookmarked(qId) {
  const bookmarks = JSON.parse(localStorage.getItem('bookmarks') || '[]');
  return bookmarks.includes(qId);
}

export function toggleBookmark(qId) {
  let bookmarks = JSON.parse(localStorage.getItem('bookmarks') || '[]');
  if (bookmarks.includes(qId)) {
    bookmarks = bookmarks.filter(id => id !== qId);
    toast('Bookmark removed', 'info');
  } else {
    bookmarks.push(qId);
    toast('Question bookmarked! ⭐', 's');
  }
  localStorage.setItem('bookmarks', JSON.stringify(bookmarks));
  return bookmarks.includes(qId);
}
