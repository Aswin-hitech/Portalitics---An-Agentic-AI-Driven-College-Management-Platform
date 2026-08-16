// PORTALITICS — Premium University Digital Campus Script
// Enhanced with scroll-reveal, count-up, ripple effects, smooth interactions

document.addEventListener('DOMContentLoaded', () => {
  // Initialize Lucide icons
  if (window.lucide) {
    lucide.createIcons();
  }

  initPortaliticsLoader();
  initCommandPalette();
  initEvidenceDrawer();
  initNotificationDropdown();
  initSidebarCollapse();
  initSidebarTooltips();
  initScrollReveal();
  initCountUpNumbers();
  initButtonRipple();
  initProgressBarAnimation();
  initSmoothLinks();
});

// ========================================================================
// CORE UI
// ========================================================================

// Fade out initial Portalitics Loading Screen
function initPortaliticsLoader() {
  const loader = document.getElementById('portaliticsLoader');
  if (loader) {
    setTimeout(() => {
      loader.classList.add('hidden');
    }, 350);
  }
}

// Global Command Palette (Ctrl+K) Shortcut Listener
function initCommandPalette() {
  const cmdModal = document.getElementById('commandPaletteModal');
  const triggerBtn = document.getElementById('cmdSearchTriggerBtn');
  const cmdInput = document.getElementById('cmdPaletteInput');

  if (!cmdModal) return;

  function toggleCmd() {
    cmdModal.classList.toggle('active');
    if (cmdModal.classList.contains('active') && cmdInput) {
      cmdInput.focus();
    }
  }

  if (triggerBtn) {
    triggerBtn.addEventListener('click', toggleCmd);
  }

  document.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
      e.preventDefault();
      toggleCmd();
    }
    if (e.key === 'Escape' && cmdModal.classList.contains('active')) {
      cmdModal.classList.remove('active');
    }
  });

  cmdModal.addEventListener('click', (e) => {
    if (e.target === cmdModal) {
      cmdModal.classList.remove('active');
    }
  });
}

// Interactive [Why am I seeing this?] Evidence Drawer Toggle
function initEvidenceDrawer() {
  const drawerOverlay = document.getElementById('evidenceDrawer');
  const triggerBtns = document.querySelectorAll('.why-pill-btn, .trigger-drawer-btn');
  const closeBtn = document.getElementById('closeDrawerBtn');

  if (!drawerOverlay) return;

  triggerBtns.forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      drawerOverlay.classList.add('active');
    });
  });

  if (closeBtn) {
    closeBtn.addEventListener('click', () => {
      drawerOverlay.classList.remove('active');
    });
  }

  drawerOverlay.addEventListener('click', (e) => {
    if (e.target === drawerOverlay) {
      drawerOverlay.classList.remove('active');
    }
  });
}

// Notification Dropdown Toggle
function initNotificationDropdown() {
  const bellBtn = document.getElementById('notificationBellBtn');
  const dropdown = document.getElementById('notificationDropdown');

  if (!bellBtn || !dropdown) return;

  bellBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    const isOpen = dropdown.style.display === 'block';
    dropdown.style.display = isOpen ? 'none' : 'block';
  });

  document.addEventListener('click', () => {
    if (dropdown) dropdown.style.display = 'none';
  });
}

// ========================================================================
// SIDEBAR
// ========================================================================

// Sidebar Collapse / Expand Toggle
function initSidebarCollapse() {
  const sidebar = document.getElementById('sidebar');
  const collapseBtn = document.getElementById('sidebarCollapseBtn');

  if (!sidebar || !collapseBtn) return;

  // Restore saved state
  const savedState = localStorage.getItem('portalitics_sidebar_collapsed');
  if (savedState === 'true') {
    sidebar.classList.add('collapsed');
    document.body.classList.add('sidebar-collapsed');
  }

  collapseBtn.addEventListener('click', () => {
    const isCollapsed = sidebar.classList.toggle('collapsed');
    document.body.classList.toggle('sidebar-collapsed', isCollapsed);
    localStorage.setItem('portalitics_sidebar_collapsed', isCollapsed);

    // Rotate the collapse icon
    const icon = collapseBtn.querySelector('[data-lucide]');
    if (icon) {
      icon.style.transform = isCollapsed ? 'rotate(180deg)' : 'rotate(0deg)';
      icon.style.transition = 'transform 200ms ease';
    }
  });

  // Set initial icon rotation if collapsed
  if (savedState === 'true') {
    const icon = collapseBtn.querySelector('[data-lucide]');
    if (icon) {
      icon.style.transform = 'rotate(180deg)';
    }
  }
}

// Sidebar Tooltips (visible only in collapsed mode)
function initSidebarTooltips() {
  const sidebar = document.getElementById('sidebar');
  const tooltip = document.getElementById('sidebarTooltip');

  if (!sidebar || !tooltip) return;

  const navLinks = sidebar.querySelectorAll('.sidebar-link');

  navLinks.forEach(link => {
    link.addEventListener('mouseenter', (e) => {
      if (!sidebar.classList.contains('collapsed')) return;

      const textEl = link.querySelector('.nav-text');
      if (!textEl) return;

      tooltip.textContent = textEl.textContent.trim();

      const rect = link.getBoundingClientRect();
      tooltip.style.top = rect.top + (rect.height / 2) - 12 + 'px';
      tooltip.style.left = rect.right + 8 + 'px';
      tooltip.classList.add('visible');
    });

    link.addEventListener('mouseleave', () => {
      tooltip.classList.remove('visible');
    });
  });
}

// ========================================================================
// PREMIUM ANIMATIONS
// ========================================================================

// Intersection Observer based scroll-reveal
function initScrollReveal() {
  // Check for reduced motion preference
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  const revealElements = document.querySelectorAll('.reveal');
  if (revealElements.length === 0) return;

  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add('revealed');
        observer.unobserve(entry.target);
      }
    });
  }, {
    threshold: 0.1,
    rootMargin: '0px 0px -40px 0px'
  });

  revealElements.forEach(el => observer.observe(el));
}

// Count-up animation for KPI numbers
function initCountUpNumbers() {
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  const kpiNumbers = document.querySelectorAll('.kpi-number');
  if (kpiNumbers.length === 0) return;

  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        animateNumber(entry.target);
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.5 });

  kpiNumbers.forEach(el => observer.observe(el));
}

function animateNumber(element) {
  const text = element.textContent.trim();

  // Parse numeric values (supports: 8.4, 72%, 100, 42ms, 86.4%, etc.)
  const match = text.match(/^([\d.]+)(.*)$/);
  if (!match) return;

  const targetVal = parseFloat(match[1]);
  const suffix = match[2] || '';
  const isDecimal = match[1].includes('.');
  const decimalPlaces = isDecimal ? (match[1].split('.')[1] || '').length : 0;

  // Don't animate very small numbers or non-numeric
  if (isNaN(targetVal) || targetVal === 0) return;

  const duration = 800;
  const startTime = performance.now();
  const startVal = 0;

  element.classList.add('counting');

  function update(currentTime) {
    const elapsed = currentTime - startTime;
    const progress = Math.min(elapsed / duration, 1);

    // Ease out cubic
    const eased = 1 - Math.pow(1 - progress, 3);
    const currentVal = startVal + (targetVal - startVal) * eased;

    element.textContent = currentVal.toFixed(decimalPlaces) + suffix;

    if (progress < 1) {
      requestAnimationFrame(update);
    } else {
      element.textContent = match[1] + suffix;
      element.classList.remove('counting');
    }
  }

  requestAnimationFrame(update);
}

// Button ripple effect on click
function initButtonRipple() {
  const buttons = document.querySelectorAll('.btn-primary, .btn-outline');

  buttons.forEach(btn => {
    btn.addEventListener('click', function(e) {
      // Remove existing ripple
      this.classList.remove('ripple');

      // Position the ripple at click point
      const rect = this.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;

      this.style.setProperty('--ripple-x', x + 'px');
      this.style.setProperty('--ripple-y', y + 'px');

      // Force reflow to restart animation
      void this.offsetWidth;
      this.classList.add('ripple');

      // Clean up
      setTimeout(() => {
        this.classList.remove('ripple');
      }, 500);
    });
  });
}

// Animate progress bars when they enter viewport
function initProgressBarAnimation() {
  const progressFills = document.querySelectorAll('.academic-progress-fill');
  if (progressFills.length === 0) return;

  progressFills.forEach(fill => {
    const targetWidth = fill.style.width;
    fill.style.width = '0%';

    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          setTimeout(() => {
            fill.style.width = targetWidth;
          }, 200);
          observer.unobserve(fill);
        }
      });
    }, { threshold: 0.3 });

    observer.observe(fill);
  });
}

// Smooth anchor scrolling for in-page links
function initSmoothLinks() {
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
      const target = document.querySelector(this.getAttribute('href'));
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });
}
