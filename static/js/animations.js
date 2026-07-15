/**
 * ============================================================
 * GLOBAL ANIMATION SYSTEM - INTERSECTION OBSERVER
 * ============================================================
 * Auto-detects elements with animation classes throughout the site.
 * Works with dynamically rendered Django content.
 * Supports any template extending base.html.
 *
 * Features:
 * - Single Intersection Observer instance (performance optimized)
 * - Automatic reveal animations for .reveal, .reveal-left, etc.
 * - Stagger animations for card grids
 * - Back-to-top button auto-detection
 * - Prefers-reduced-motion support
 * - Memory leak free
 * ============================================================
 */

(function() {
  'use strict';

  // ===== CONFIGURATION =====
  const config = {
    revealSelector: '.reveal, .reveal-left, .reveal-right, .reveal-scale',
    staggerParentSelector: '.stagger-parent',
    staggerItemSelector: '.stagger-item',
    scrollTopButtonSelector: '#scrollTopBtn',
    scrollThreshold: 400,
    observerOptions: {
      threshold: 0.1,
      rootMargin: '0px 0px -50px 0px' // Trigger slightly before element is visible
    },
    respectReducedMotion: true
  };

  // ===== CHECK REDUCED MOTION PREFERENCE =====
  const prefersReducedMotion = () => {
    return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  };

  // ===== INTERSECTION OBSERVER FOR REVEAL ANIMATIONS =====
  class RevealAnimationController {
    constructor() {
      this.observedElements = new WeakSet();
      this.createObserver();
      this.init();
    }

    createObserver() {
      this.observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting && !this.observedElements.has(entry.target)) {
            this.revealElement(entry.target);
            this.observedElements.add(entry.target);
            // Unobserve after reveal to save performance
            this.observer.unobserve(entry.target);
          }
        });
      }, config.observerOptions);
    }

    revealElement(element) {
      if (prefersReducedMotion() && config.respectReducedMotion) {
        element.classList.add('active');
        return;
      }

      // Use requestAnimationFrame for smooth animation start
      requestAnimationFrame(() => {
        element.classList.add('active');
      });
    }

    observeElements(selector) {
      const elements = document.querySelectorAll(selector);
      elements.forEach(element => {
        if (!this.observedElements.has(element)) {
          this.observer.observe(element);
        }
      });
    }

    init() {
      // Observe all reveal elements
      this.observeElements(config.revealSelector);

      // Observe stagger items
      const staggerParents = document.querySelectorAll(config.staggerParentSelector);
      staggerParents.forEach(parent => {
        const items = parent.querySelectorAll(config.staggerItemSelector);
        items.forEach(item => {
          if (!this.observedElements.has(item)) {
            this.observer.observe(item);
          }
        });
      });
    }

    // Re-scan for dynamically added elements
    refresh() {
      this.init();
    }

    destroy() {
      this.observer.disconnect();
      this.observedElements = new WeakSet();
    }
  }

  // ===== SCROLL-TO-TOP BUTTON CONTROLLER =====
  class ScrollTopButtonController {
    constructor() {
      this.button = document.querySelector(config.scrollTopButtonSelector);
      this.isVisible = false;
      if (this.button) {
        this.init();
      }
    }

    init() {
      window.addEventListener('scroll', () => this.handleScroll(), { passive: true });
      if (this.button) {
        this.button.addEventListener('click', () => this.scrollToTop());
      }
    }

    handleScroll() {
      const isScrolled = window.scrollY > config.scrollThreshold;

      if (isScrolled && !this.isVisible) {
        this.show();
      } else if (!isScrolled && this.isVisible) {
        this.hide();
      }
    }

    show() {
      this.isVisible = true;
      if (this.button) {
        this.button.classList.remove('hidden');
        this.button.classList.add('visible');
        this.button.style.display = 'flex';
      }
    }

    hide() {
      this.isVisible = false;
      if (this.button) {
        this.button.classList.add('hidden');
        this.button.classList.remove('visible');
        // Delay hiding to show animation
        setTimeout(() => {
          if (!this.isVisible && this.button) {
            this.button.style.display = 'none';
          }
        }, 250);
      }
    }

    scrollToTop() {
      window.scrollTo({
        top: 0,
        behavior: 'smooth'
      });
    }
  }

  // ===== HERO SECTION ANIMATIONS =====
  class HeroAnimationController {
    constructor() {
      this.init();
    }

    init() {
      const heroHeading = document.querySelector('.hero-heading, .hero h1, .welcome-hero h1');
      const heroSubtitle = document.querySelector('.hero-subtitle, .hero p, .welcome-hero p');
      const heroButtons = document.querySelector('.hero-buttons, .hero-actions, .welcome-hero .hero-actions');
      const heroMedia = document.querySelector('.hero-media, .video-card');

      if (prefersReducedMotion() && config.respectReducedMotion) {
        [heroHeading, heroSubtitle, heroButtons, heroMedia].forEach(el => {
          if (el) el.style.opacity = '1';
        });
        return;
      }

      // Stagger animation for hero elements
      if (heroHeading) {
        this.animateWithDelay(heroHeading, 0);
      }
      if (heroSubtitle) {
        this.animateWithDelay(heroSubtitle, 100);
      }
      if (heroButtons) {
        this.animateWithDelay(heroButtons, 200);
      }
      if (heroMedia) {
        this.animateWithDelay(heroMedia, 300);
      }
    }

    animateWithDelay(element, delay) {
      setTimeout(() => {
        element.style.opacity = '1';
        element.classList.add('active');
      }, delay);
    }
  }

  // ===== DYNAMIC CONTENT OBSERVER =====
  class DynamicContentObserver {
    constructor(revealController) {
      this.revealController = revealController;
      this.setupMutationObserver();
    }

    setupMutationObserver() {
      const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
          if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
            // Check if any new nodes have animation classes
            mutation.addedNodes.forEach(node => {
              if (node.nodeType === Node.ELEMENT_NODE) {
                // Refresh reveal animations for new content
                if (node.matches?.(config.revealSelector) || node.querySelector?.(config.revealSelector)) {
                  this.revealController.refresh();
                }
              }
            });
          }
        });
      });

      observer.observe(document.body, {
        childList: true,
        subtree: true
      });
    }
  }

  // ===== MOBILE MENU ANIMATIONS =====
  class MobileMenuAnimationController {
    constructor() {
      this.init();
    }

    init() {
      const menuToggle = document.querySelector('[data-toggle="navbar-menu"], .menu-toggle, .hamburger');
      const navMenu = document.querySelector('.navbar-menu, [class*="nav-menu"], [class*="sidebar"]');

      if (!menuToggle || !navMenu) return;

      menuToggle.addEventListener('click', () => {
        navMenu.classList.toggle('active');
      });

      // Close menu on link click
      navMenu.querySelectorAll('a').forEach(link => {
        link.addEventListener('click', () => {
          navMenu.classList.remove('active');
        });
      });
    }
  }

  // ===== ANNOUNCEMENT TICKER ANIMATIONS =====
  class AnnouncementTickerController {
    constructor() {
      this.init();
    }

    init() {
      const ticker = document.querySelector('.announcement-ticker');
      if (!ticker) return;

      // Auto-hide after 5 seconds
      setTimeout(() => {
        if (ticker) {
          ticker.classList.add('hide');
        }
      }, 5000);
    }
  }

  // ===== INITIALIZATION & MAIN CONTROLLER =====
  class GlobalAnimationSystem {
    constructor() {
      this.revealController = null;
      this.scrollTopController = null;
      this.heroController = null;
      this.dynamicContentObserver = null;
      this.mobileMenuController = null;
      this.announcementController = null;

      this.init();
      this.setupDOMContentLoadedListener();
    }

    init() {
      // Initialize all controllers
      this.revealController = new RevealAnimationController();
      this.scrollTopController = new ScrollTopButtonController();
      this.mobileMenuController = new MobileMenuAnimationController();
      this.announcementController = new AnnouncementTickerController();

      // Initialize hero animations on page load
      if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
          this.heroController = new HeroAnimationController();
        });
      } else {
        this.heroController = new HeroAnimationController();
      }

      // Watch for dynamically added content
      this.dynamicContentObserver = new DynamicContentObserver(this.revealController);
    }

    setupDOMContentLoadedListener() {
      if (document.readyState !== 'loading') {
        this.onDOMReady();
      } else {
        document.addEventListener('DOMContentLoaded', () => this.onDOMReady());
      }
    }

    onDOMReady() {
      // Re-scan for any elements that might have been missed
      if (this.revealController) {
        this.revealController.refresh();
      }
    }

    // Public API for manual refresh (e.g., after AJAX content loads)
    refresh() {
      if (this.revealController) {
        this.revealController.refresh();
      }
    }

    // Public API for cleaning up
    destroy() {
      if (this.revealController) {
        this.revealController.destroy();
      }
    }
  }

  // ===== AUTO-INITIALIZE ON PAGE LOAD =====
  let globalAnimationSystem = null;

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      globalAnimationSystem = new GlobalAnimationSystem();
      // Expose to window for manual control if needed
      window.AnimationSystem = globalAnimationSystem;
    });
  } else {
    globalAnimationSystem = new GlobalAnimationSystem();
    window.AnimationSystem = globalAnimationSystem;
  }

  // ===== PUBLIC API =====
  window.AnimationAPI = {
    refresh: () => {
      if (globalAnimationSystem) {
        globalAnimationSystem.refresh();
      }
    },
    destroy: () => {
      if (globalAnimationSystem) {
        globalAnimationSystem.destroy();
      }
    },
    // Get current configuration
    getConfig: () => ({ ...config }),
    // Update configuration
    setConfig: (newConfig) => {
      Object.assign(config, newConfig);
    }
  };

  // ===== MUTATION OBSERVER FOR DYNAMICALLY ADDED ANIMATIONS =====
  // Watch for elements added via AJAX/Django template rendering
  const mutationObserver = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
      if (mutation.type === 'childList') {
        mutation.addedNodes.forEach((node) => {
          if (node.nodeType === Node.ELEMENT_NODE) {
            // Check if node or its children have animation classes
            if (
              node.classList?.contains('reveal') ||
              node.classList?.contains('card-hover') ||
              node.classList?.contains('stagger-parent') ||
              node.querySelector?.(config.revealSelector)
            ) {
              // Small delay to ensure DOM is fully updated
              requestAnimationFrame(() => {
                if (globalAnimationSystem) {
                  globalAnimationSystem.refresh();
                }
              });
            }
          }
        });
      }
    });
  });

  // Start observing the document for dynamic content
  mutationObserver.observe(document.body, {
    childList: true,
    subtree: true,
    attributes: false,
    characterData: false
  });

  // Clean up on page unload
  window.addEventListener('beforeunload', () => {
    mutationObserver.disconnect();
    if (globalAnimationSystem) {
      globalAnimationSystem.destroy();
    }
  });

})();
