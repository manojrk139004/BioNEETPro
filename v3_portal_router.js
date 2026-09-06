/**
 * BioNEETPro V3 — Multi-Portal Product Architecture Router
 * Coordinates:
 * 1. Dedicated URL & Subdomain detection (/student, /teacher, /admin, /)
 * 2. Strict client-side and server-backed role enforcement
 * 3. Cross-portal access notifications and redirection guardrails
 * 4. Contextual AI Assistant persona alignment (Dr. Priya / Prof. Sharma / BioNEETPro Ops)
 * 5. Clean browser history and navigation synchronization
 */

(function() {
  'use strict';

  window.V3 = window.V3 || {};

  var PORTALS = {
    LANDING: 'LANDING',
    STUDENT: 'STUDENT',
    TEACHER: 'TEACHER',
    ADMIN: 'ADMIN'
  };
  V3.PORTALS = PORTALS;

  var activePortal = PORTALS.LANDING;
  V3.activePortal = activePortal;

  /**
   * Detect current portal from hostname (production subdomains) or pathname.
   */
  function detectPortal() {
    var host = (window.location.hostname || '').toLowerCase();
    var path = (window.location.pathname || '').toLowerCase();

    // 1. Subdomain-based detection
    if (host.startsWith('students.') || host === 'students.bioneetpro.com') {
      return PORTALS.STUDENT;
    }
    if (host.startsWith('teachers.') || host === 'teachers.bioneetpro.com') {
      return PORTALS.TEACHER;
    }
    if (host.startsWith('admin.') || host === 'admin.bioneetpro.com') {
      return PORTALS.ADMIN;
    }

    // 2. Path-based detection (fallback & local dev)
    if (path.startsWith('/student')) {
      return PORTALS.STUDENT;
    }
    if (path.startsWith('/teacher')) {
      return PORTALS.TEACHER;
    }
    if (path.startsWith('/admin')) {
      return PORTALS.ADMIN;
    }

    // Check hash fallback
    var hash = (window.location.hash || '').toLowerCase();
    if (hash.startsWith('#/student') || hash === '#student') return PORTALS.STUDENT;
    if (hash.startsWith('#/teacher') || hash === '#teacher') return PORTALS.TEACHER;
    if (hash.startsWith('#/admin') || hash === '#admin') return PORTALS.ADMIN;

    return PORTALS.LANDING;
  }
  V3.detectPortal = detectPortal;

  /**
   * Get user role from memory or localStorage.
   */
  function getCurrentRole() {
    if (window.DB && window.DB.userRole) return window.DB.userRole.toUpperCase();
    if (window.DB && window.DB.isAdmin) return 'SUPER_ADMIN';
    if (window.DB && window.DB.isTeacher) return 'TEACHER';
    try {
      var stored = localStorage.getItem('userRole');
      if (stored) return stored.toUpperCase();
    } catch (e) {}
    return 'STUDENT';
  }
  V3.getCurrentRole = getCurrentRole;

  /**
   * Render top portal indicator bar
   */
  function renderPortalIndicator() {
    var existing = document.getElementById('v3PortalIndicator');
    if (existing) existing.remove();

    var portal = V3.activePortal;
    if (portal === PORTALS.LANDING) return;

    var bar = document.createElement('div');
    bar.id = 'v3PortalIndicator';
    bar.className = 'portal-indicator-bar ' + portal.toLowerCase() + '-theme';

    var role = getCurrentRole();
    var isElevated = (role === 'SUPER_ADMIN' || role === 'TEACHER');

    var tagText = '';
    var switcherHtml = '';

    if (portal === PORTALS.STUDENT) {
      tagText = '🎓 Student Portal &bull; NEET Biology Learning';
      if (isElevated) {
        switcherHtml = '<button class="portal-switcher-btn" onclick="V3.navigateToPortal(\'TEACHER\')">Return to Teacher Studio →</button>';
      }
    } else if (portal === PORTALS.TEACHER) {
      tagText = '👨‍🏫 Teacher Portal &bull; Assessment & Analytics Studio';
      if (role === 'SUPER_ADMIN') {
        switcherHtml = '<button class="portal-switcher-btn" onclick="V3.navigateToPortal(\'ADMIN\')">Switch to Super Admin Console →</button>';
      } else {
        switcherHtml = '<button class="portal-switcher-btn" onclick="V3.navigateToPortal(\'STUDENT\')">Student View →</button>';
      }
    } else if (portal === PORTALS.ADMIN) {
      tagText = '👑 Super Admin Portal &bull; Institutional Governance Console';
      switcherHtml = '<button class="portal-switcher-btn" onclick="V3.navigateToPortal(\'TEACHER\')">Teacher Studio</button> <button class="portal-switcher-btn" onclick="V3.navigateToPortal(\'STUDENT\')">Student Portal</button>';
    }

    bar.innerHTML = '<div class="portal-indicator-tag">' + tagText + '</div>' +
                    '<div style="display:flex;gap:8px;align-items:center">' +
                      switcherHtml +
                      '<button class="portal-switcher-btn" onclick="V3.navigateToPortal(\'LANDING\')">Ecosystem Home</button>' +
                    '</div>';

    var main = document.getElementById('main') || document.body;
    main.parentNode.insertBefore(bar, main);
  }
  V3.renderPortalIndicator = renderPortalIndicator;

  /**
   * Display cross-portal redirection banner
   */
  function showPortalAlert(targetElId, title, message, redirectPortal, redirectUrl) {
    var targetEl = document.getElementById(targetElId);
    if (!targetEl) return;

    var existing = targetEl.querySelector('.portal-redirect-banner');
    if (existing) existing.remove();

    var banner = document.createElement('div');
    banner.className = 'portal-redirect-banner';
    banner.innerHTML = '<div class="alert-icon">⚠️</div>' +
      '<div style="flex:1">' +
        '<h4>' + title + '</h4>' +
        '<p>' + message + '</p>' +
        '<div style="display:flex;gap:10px">' +
          '<button type="button" id="btnPortalRedirectNow">Go to ' + redirectPortal + ' Portal Immediately</button>' +
        '</div>' +
      '</div>';

    targetEl.insertBefore(banner, targetEl.firstChild);

    var btn = banner.querySelector('#btnPortalRedirectNow');
    if (btn) {
      btn.onclick = function() {
        V3.navigateToPortal(redirectPortal, redirectUrl);
      };
    }
  }

  /**
   * Synchronize active portal with auth state and route.
   */
  function syncPortalAuth() {
    var portal = V3.activePortal;
    var user = window.DB && window.DB.currentUser;
    var role = getCurrentRole();

    // In Landing mode, no role gating needed
    if (portal === PORTALS.LANDING) {
      renderPortalIndicator();
      return;
    }

    // Gating for logged-in users
    if (user && user.id) {
      if (portal === PORTALS.TEACHER && role === 'STUDENT') {
        // A student is inside Teacher Portal
        showPortalAlert(
          'page-teacher',
          'Student Account Detected',
          'This account is registered as a Student. Faculty access requires teacher credentials. Redirecting to your Student Portal...',
          PORTALS.STUDENT,
          '/student'
        );
        setTimeout(function() {
          if (V3.activePortal === PORTALS.TEACHER && getCurrentRole() === 'STUDENT') {
            V3.navigateToPortal(PORTALS.STUDENT);
          }
        }, 2500);
        return;
      }

      if (portal === PORTALS.ADMIN && role !== 'SUPER_ADMIN') {
        // Non-admin inside Admin Portal
        showPortalAlert(
          'page-admin',
          'Access Denied: Institutional Admin Required',
          'Super Admin credentials are required to access institutional governance. Redirecting to your assigned portal...',
          role === 'TEACHER' ? PORTALS.TEACHER : PORTALS.STUDENT,
          role === 'TEACHER' ? '/teacher' : '/student'
        );
        setTimeout(function() {
          if (V3.activePortal === PORTALS.ADMIN && getCurrentRole() !== 'SUPER_ADMIN') {
            V3.navigateToPortal(role === 'TEACHER' ? PORTALS.TEACHER : PORTALS.STUDENT);
          }
        }, 2500);
        return;
      }
    }

    renderPortalIndicator();
    alignAIAssistantPersona();
  }
  V3.syncPortalAuth = syncPortalAuth;

  /**
   * Align the floating AI Assistant persona to current portal context.
   */
  function alignAIAssistantPersona() {
    var portal = V3.activePortal;
    var role = 'STUDENT';
    var name = 'Dr. Priya';
    var title = 'NEET Biology AI Mentor';
    var avatar = '👩‍🏫';

    if (portal === PORTALS.TEACHER) {
      role = 'TEACHER';
      name = 'Prof. Sharma';
      title = 'Assessment & Curriculum Specialist';
      avatar = '👨‍🏫';
    } else if (portal === PORTALS.ADMIN) {
      role = 'SUPER_ADMIN';
      name = 'BioNEET Operations';
      title = 'Institutional Systems Advisor';
      avatar = '⚙️';
    }

    // Update global state for assistant
    window.__currentAssistantRole = role;
    if (typeof window.switchAssistantPersona === 'function') {
      window.switchAssistantPersona(role);
    }

    // Update assistant UI headers if rendered
    var nameEl = document.getElementById('assistantHeaderName');
    var titleEl = document.getElementById('assistantHeaderTitle');
    var avEl = document.getElementById('assistantHeaderAvatar');

    if (nameEl) nameEl.textContent = name;
    if (titleEl) titleEl.textContent = title;
    if (avEl) avEl.textContent = avatar;
  }
  V3.alignAIAssistantPersona = alignAIAssistantPersona;

  /**
   * Primary portal navigation router
   */
  function navigateToPortal(portal, subroute, options) {
    options = options || {};
    portal = (portal || PORTALS.LANDING).toUpperCase();
    V3.activePortal = portal;

    var path = window.location.pathname || '';
    var newPath = '/';

    if (portal === PORTALS.STUDENT) {
      newPath = '/student';
      if (subroute && subroute.startsWith('/')) newPath += subroute;
    } else if (portal === PORTALS.TEACHER) {
      newPath = '/teacher';
      if (subroute && subroute.startsWith('/')) newPath += subroute;
    } else if (portal === PORTALS.ADMIN) {
      newPath = '/admin';
      if (subroute && subroute.startsWith('/')) newPath += subroute;
    }

    // Update history without reloading
    if (!options.silent && window.history && window.history.pushState && path !== newPath) {
      try {
        window.history.pushState({ portal: portal, subroute: subroute }, '', newPath);
      } catch (e) {}
    }

    // Activate the appropriate views
    var user = window.DB && window.DB.currentUser;

    if (portal === PORTALS.LANDING) {
      if (typeof window.go === 'function') window.go('home');
      renderPortalIndicator();
      return;
    }

    if (portal === PORTALS.STUDENT) {
      if (!user) {
        if (subroute === '/login' || subroute === 'login') {
          if (typeof window.go === 'function') window.go('login');
        } else {
          // If unauthenticated on /student, go to login or home
          if (typeof window.go === 'function') window.go('login');
        }
      } else {
        // Resolve student subroutes
        if (subroute === '/mcq' || subroute === 'mcq') {
          if (typeof window.go === 'function') window.go('mcq');
        } else if (subroute === '/tutor' || subroute === 'ai-tutor') {
          if (typeof window.go === 'function') window.go('ai-tutor');
        } else if (subroute === '/flashcards' || subroute === 'flashcards') {
          if (typeof window.go === 'function') window.go('flashcards');
        } else {
          if (typeof window.go === 'function') window.go('dashboard');
        }
      }
    } else if (portal === PORTALS.TEACHER) {
      if (!user) {
        var teacherLogin = document.getElementById('page-teacher-login');
        if (teacherLogin && typeof window.go === 'function') {
          window.go('teacher-login');
        } else if (typeof window.go === 'function') {
          window.go('login');
        }
      } else {
        if (typeof window.go === 'function') window.go('teacher');
        if (subroute === '/builder' || subroute === 'builder') {
          if (typeof window.switchTeacherTab === 'function') window.switchTeacherTab('builder');
        } else if (subroute === '/analytics' || subroute === 'analytics') {
          if (typeof window.switchTeacherTab === 'function') window.switchTeacherTab('analytics');
        } else {
          if (typeof window.switchTeacherTab === 'function') window.switchTeacherTab('assessments');
        }
      }
    } else if (portal === PORTALS.ADMIN) {
      if (!user) {
        if (typeof window.go === 'function') window.go('admin-login');
      } else {
        if (subroute === '/teachers' || subroute === 'admin-teachers') {
          if (typeof window.go === 'function') window.go('admin-teachers');
        } else if (subroute === '/students' || subroute === 'admin-students') {
          if (typeof window.go === 'function') window.go('admin-students');
        } else {
          if (typeof window.go === 'function') window.go('admin');
        }
      }
    }

    syncPortalAuth();
  }
  V3.navigateToPortal = navigateToPortal;

  // Initialize router on DOMContentLoaded
  function initRouter() {
    var detected = detectPortal();
    V3.activePortal = detected;

    var path = (window.location.pathname || '').toLowerCase();
    var subroute = '';
    if (path.startsWith('/student/')) subroute = path.replace('/student', '');
    else if (path.startsWith('/teacher/')) subroute = path.replace('/teacher', '');
    else if (path.startsWith('/admin/')) subroute = path.replace('/admin', '');

    navigateToPortal(detected, subroute, { silent: true });

    // Handle browser back/forward buttons
    window.addEventListener('popstate', function(event) {
      var p = detectPortal();
      navigateToPortal(p, '', { silent: true });
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initRouter);
  } else {
    initRouter();
  }

})();
