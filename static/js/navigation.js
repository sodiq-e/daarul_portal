(() => {
  const menuButton = document.getElementById('menuBtn');
  const menuButtonIcon = document.getElementById('menuBtnIcon');
  const sidebar = document.getElementById('sidebar');
  const overlay = document.getElementById('overlay');
  const offlineNotice = document.getElementById('offlineNotice');
  const offlineNoticeTitle = document.getElementById('offlineNoticeTitle');
  const offlineNoticeMessage = document.getElementById('offlineNoticeMessage');
  const offlineTip = document.getElementById('offlineTip');
  const offlineTipMessage = document.getElementById('offlineTipMessage');
  const offlineTipsData = document.getElementById('offlineTipMessages');
  const mobileBreakpoint = 1024;

  if (!menuButton || !menuButtonIcon || !sidebar || !overlay) return;

  let offlineTips = [];
  try {
    offlineTips = JSON.parse(offlineTipsData?.textContent || '[]');
  } catch (error) {
    console.warn('Unable to read offline tips:', error);
  }

  function showOfflineNotice(message = 'The request was stopped before it was sent. This page is still open.') {
    if (!offlineNotice) return;
    offlineNoticeTitle.textContent = 'You\'re offline';
    offlineNoticeMessage.textContent = message;
    if (offlineTips.length) {
      const tipIndex = Math.floor(Math.random() * offlineTips.length);
      offlineTipMessage.textContent = offlineTips[tipIndex];
      offlineTip.hidden = false;
    } else {
      offlineTip.hidden = true;
      offlineTipMessage.textContent = '';
    }
    offlineNotice.hidden = false;
  }

  window.showOfflineNotice = showOfflineNotice;

  document.getElementById('offlineNoticeDismiss')?.addEventListener('click', () => {
    offlineNotice.hidden = true;
  });

  window.addEventListener('offline', () => showOfflineNotice('Your connection was lost. This page is still open.'));
  window.addEventListener('online', () => {
    if (!offlineNotice || offlineNotice.hidden) return;
    offlineNoticeTitle.textContent = 'Connection restored';
    offlineNoticeMessage.textContent = 'Retry the action when you are ready.';
    offlineTip.hidden = true;
  });

  document.addEventListener('submit', (event) => {
    const form = event.target;
    if (!(form instanceof HTMLFormElement) || navigator.onLine !== false) return;
    const formUrl = new URL(form.action || window.location.href, window.location.href);
    if (formUrl.origin !== window.location.origin) return;
    event.preventDefault();
    showOfflineNotice();
  }, true);

  if (navigator.onLine === false) {
    showOfflineNotice('Your browser reports that this device is offline. This page is still open.');
  }

  function syncMenuButton() {
    const isOpen = window.innerWidth < mobileBreakpoint
      ? sidebar.classList.contains('active')
      : !sidebar.classList.contains('collapsed');
    menuButtonIcon.classList.toggle('fa-bars', !isOpen);
    menuButtonIcon.classList.toggle('fa-xmark', isOpen);
    menuButton.setAttribute('aria-expanded', String(isOpen));
    menuButton.setAttribute('aria-label', isOpen ? 'Close sidebar' : 'Open sidebar');
  }

  function getSidebarState() {
    return {
      desktopCollapsed: sidebar.classList.contains('collapsed'),
      mobileActive: sidebar.classList.contains('active'),
    };
  }

  function saveSidebarState() {
    try {
      localStorage.setItem('sidebarState', JSON.stringify(getSidebarState()));
    } catch (error) {
      console.warn('Unable to save sidebar state:', error);
    }
  }

  function normalizeMenuKey(text) {
    return text.trim().toLowerCase().replace(/\s+/g, '_').replace(/[^\w-]/g, '');
  }

  function saveSidebarMenuState() {
    try {
      const state = {};
      sidebar.querySelectorAll('.menu-header').forEach((header) => {
        const key = header.dataset.menuKey || normalizeMenuKey(header.textContent || '');
        const content = header.nextElementSibling;
        if (!content || !content.classList.contains('menu-content') || key === '') return;
        state[key] = content.classList.contains('collapsed');
      });
      localStorage.setItem('sidebarMenuState', JSON.stringify(state));
    } catch (error) {
      console.warn('Unable to save sidebar menu state:', error);
    }
  }

  function restoreSidebarState() {
    try {
      const savedState = localStorage.getItem('sidebarState');
      if (savedState) {
        const state = JSON.parse(savedState);
        const isDesktop = window.matchMedia('(min-width: 1024px)').matches;
        sidebar.classList.toggle('collapsed', Boolean(state.desktopCollapsed && isDesktop));

        if (state.mobileActive) {
          sidebar.classList.add('active');
          sidebar.classList.remove('collapsed');
          sidebar.querySelectorAll('.menu-content').forEach((content) => content.classList.remove('collapsed'));
          sidebar.querySelectorAll('.menu-header').forEach((header) => header.classList.add('active'));
          overlay.classList.add('show');
          document.body.classList.add('no-scroll');
        } else {
          sidebar.classList.remove('active');
          overlay.classList.remove('show');
          document.body.classList.remove('no-scroll');
        }
      }
    } catch (error) {
      console.warn('Unable to restore sidebar state:', error);
    }

    try {
      const savedMenuState = localStorage.getItem('sidebarMenuState');
      if (savedMenuState) {
        const state = JSON.parse(savedMenuState);
        sidebar.querySelectorAll('.menu-header').forEach((header) => {
          const key = header.dataset.menuKey || normalizeMenuKey(header.textContent || '');
          const content = header.nextElementSibling;
          if (!content || !content.classList.contains('menu-content') || key === '' || state[key] === undefined) return;
          content.classList.toggle('collapsed', Boolean(state[key]));
          header.classList.toggle('active', !state[key]);
        });
      }
    } catch (error) {
      console.warn('Unable to restore sidebar menu state:', error);
    }

    if (sidebar.classList.contains('collapsed')) {
      sidebar.querySelectorAll('.menu-content').forEach((content) => content.classList.remove('collapsed'));
    }
  }

  function closeSidebar() {
    sidebar.classList.remove('active');
    overlay.classList.remove('show');
    document.body.classList.remove('no-scroll');
    syncMenuButton();
    saveSidebarState();
  }

  function toggleMenu(header) {
    const content = header.nextElementSibling;
    if (!content || !content.classList.contains('menu-content')) return;

    if (sidebar.classList.contains('collapsed')) {
      header.classList.add('active');
      content.classList.remove('collapsed');
    } else {
      header.classList.toggle('active');
      content.classList.toggle('collapsed');
    }
    saveSidebarMenuState();
  }

  window.toggleMenu = toggleMenu;
  restoreSidebarState();
  syncMenuButton();

  const iconMap = new Map([
    ['logout', 'fas fa-sign-out-alt'],
    ['sign in', 'fas fa-sign-in-alt'],
    ['sign up', 'fas fa-user-plus'],
    ['profile', 'fas fa-user'],
    ['teacher', 'fas fa-chalkboard-teacher'],
    ['teachers', 'fas fa-users'],
    ['messages', 'fas fa-envelope'],
    ['message', 'fas fa-envelope'],
    ['search', 'fas fa-search'],
    ['settings', 'fas fa-cog'],
    ['result', 'fas fa-chart-bar'],
    ['results', 'fas fa-chart-bar'],
    ['announcement', 'fas fa-bullhorn'],
    ['gallery', 'fas fa-image'],
    ['classes', 'fas fa-chalkboard'],
    ['home', 'fas fa-home'],
    ['fees', 'fas fa-wallet'],
    ['attendance', 'fas fa-calendar-check'],
    ['cbt', 'fas fa-laptop-code'],
    ['portal', 'fas fa-comments'],
  ]);

  sidebar.querySelectorAll('a, form button').forEach((item) => {
    if (item.querySelector('i')) return;
    const text = (item.getAttribute('data-tooltip') || item.textContent || '').toLowerCase();
    const iconClass = [...iconMap].find(([label]) => text.includes(label))?.[1] || 'fas fa-link';
    const icon = document.createElement('i');
    icon.className = iconClass;
    item.insertBefore(icon, item.firstChild);
  });

  menuButton.addEventListener('click', (event) => {
    event.preventDefault();
    event.stopPropagation();

    if (window.innerWidth < mobileBreakpoint) {
      sidebar.classList.toggle('active');
      sidebar.classList.remove('collapsed');
      const isOpen = sidebar.classList.contains('active');
      overlay.classList.toggle('show', isOpen);
      document.body.classList.toggle('no-scroll', isOpen);
    } else {
      sidebar.classList.toggle('collapsed');
    }

    syncMenuButton();
    saveSidebarState();
  });

  overlay.addEventListener('click', closeSidebar);

  sidebar.querySelectorAll('a').forEach((link) => {
    link.addEventListener('click', () => {
      if (window.innerWidth < mobileBreakpoint) closeSidebar();
    });
  });

  const logoutButton = sidebar.querySelector('form button');
  if (logoutButton) {
    logoutButton.addEventListener('click', () => {
      if (window.innerWidth < mobileBreakpoint) closeSidebar();
    });
  }

  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && sidebar.classList.contains('active')) closeSidebar();
  });

  window.addEventListener('resize', syncMenuButton);

  function updateActiveNavItem() {
    const path = window.location.pathname;
    document.querySelectorAll('.nav-item').forEach((item) => {
      const href = item.getAttribute('href');
      item.classList.toggle('active', Boolean(href && href !== '#' && path.startsWith(href)));
    });
  }

  updateActiveNavItem();
  window.addEventListener('load', updateActiveNavItem);
  document.addEventListener('click', () => setTimeout(updateActiveNavItem, 100));

  document.addEventListener('DOMContentLoaded', () => {
    const activeLink = sidebar.querySelector('a.active');
    const parent = activeLink?.closest('.menu-content');
    if (!parent) return;
    parent.classList.remove('collapsed');
    const header = parent.previousElementSibling;
    if (header?.classList.contains('menu-header')) header.classList.add('active');
  });

  let touchStartX = 0;
  document.addEventListener('touchstart', (event) => {
    touchStartX = event.changedTouches[0].screenX;
  }, { passive: true });

  document.addEventListener('touchend', (event) => {
    const touchEndX = event.changedTouches[0].screenX;
    if (window.innerWidth < mobileBreakpoint && touchStartX - touchEndX > 50 && sidebar.classList.contains('active')) {
      closeSidebar();
    }
  }, { passive: true });
})();
