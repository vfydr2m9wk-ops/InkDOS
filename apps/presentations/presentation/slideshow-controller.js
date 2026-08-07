(function (global) {
  'use strict';

  class PresentationSlideshowController {
    constructor(options) {
      this.overlay = options.overlay;
      this.slideTarget = options.slideTarget;
      this.exitButton = options.exitButton;
      this.fullscreenButton = options.fullscreenButton;
      this.fullscreenLabel = options.fullscreenLabel;
      this.counter = options.counter;
      this.help = options.help;
      this.startButtons = options.startButtons || [];
      this.currentButtons = options.currentButtons || [];
      this.getPresentation = options.getPresentation;
      this.getCurrentSlide = options.getCurrentSlide;
      this.setCurrentSlide = options.setCurrentSlide;
      this.getSlideData = options.getSlideData;
      this.getTransitionType = options.getTransitionType;
      this.leaveTextEdit = options.leaveTextEdit;
      this.clearSelection = options.clearSelection;
      this.slideViewport = options.slideViewport;
      this.renderSlide = options.renderSlide;
      this.renderAll = options.renderAll;
      this.touchStart = null;
      this.helpTimer = null;
      this.resizeObserver = null;
      this.bind();
      this.updateFullscreenControl();
    }

    fullscreenElement() {
      return global.document.fullscreenElement ||
        global.document.webkitFullscreenElement || null;
    }

    updateFullscreenControl() {
      if (!this.overlay) {
        return;
      }
      const active = this.fullscreenElement() === this.overlay;
      this.overlay.classList.toggle('is-fullscreen', active);
      if (this.fullscreenLabel) {
        this.fullscreenLabel.textContent = active ? 'Exit full screen' : 'Full screen';
      }
      if (this.fullscreenButton) {
        this.fullscreenButton.setAttribute(
          'aria-label',
          active ? 'Exit full screen' : 'Enter full screen'
        );
      }
    }

    async toggleFullscreen() {
      if (!this.overlay) {
        return false;
      }
      try {
        if (this.fullscreenElement()) {
          if (global.document.exitFullscreen) {
            await global.document.exitFullscreen();
          } else if (global.document.webkitExitFullscreen) {
            global.document.webkitExitFullscreen();
          }
        } else if (this.overlay.requestFullscreen) {
          await this.overlay.requestFullscreen({navigationUI: 'hide'});
        } else if (this.overlay.webkitRequestFullscreen) {
          this.overlay.webkitRequestFullscreen();
        } else {
          this.markFullscreenUnavailable(
            'This browser or embedded web view does not expose the Fullscreen API. ' +
            'Presentation mode still fills the available window.'
          );
          return false;
        }
        this.updateFullscreenControl();
        global.requestAnimationFrame(() => this.fit());
        return true;
      } catch (error) {
        global.console.warn('Fullscreen request was blocked', error);
        this.markFullscreenUnavailable(
          'The browser blocked full screen. Presentation mode still fills the available window.'
        );
        return false;
      }
    }

    markFullscreenUnavailable(title) {
      if (this.fullscreenLabel) {
        this.fullscreenLabel.textContent = 'Full screen unavailable';
      }
      if (this.fullscreenButton) {
        this.fullscreenButton.title = title;
      }
    }

    showHelp() {
      if (!this.help) {
        return;
      }
      this.help.classList.remove('fade-out');
      global.clearTimeout(this.helpTimer);
      this.helpTimer = global.setTimeout(
        () => this.help.classList.add('fade-out'),
        3200
      );
    }

    enter(fromFirst = false) {
      const presentation = this.getPresentation();
      if (!presentation || !presentation.slides || !presentation.slides.length) {
        return;
      }
      this.leaveTextEdit();
      this.clearSelection();
      if (fromFirst) {
        this.setCurrentSlide(0);
      }
      global.document.body.classList.add('presentation-active');
      this.overlay.classList.remove('hidden');
      this.updateFullscreenControl();
      this.fit();
      this.showHelp();
      try {
        this.overlay.focus({preventScroll: true});
      } catch (error) {
        this.overlay.focus();
      }
      void this.toggleFullscreen();
    }

    animate() {
      const type = this.getTransitionType();
      this.slideTarget.classList.remove('fx-fade', 'fx-slide', 'fx-zoom');
      void this.slideTarget.offsetWidth;
      if (type !== 'none') {
        this.slideTarget.classList.add('fx-' + type);
      }
    }

    fit() {
      const presentation = this.getPresentation();
      if (!presentation || this.overlay.classList.contains('hidden')) {
        return;
      }
      const rect = this.overlay.getBoundingClientRect();
      const width = Math.max(1, rect.width || global.innerWidth);
      const height = Math.max(1, rect.height || global.innerHeight);
      const viewport = this.slideViewport();
      const scale = Math.max(
        0.05,
        Math.min((width - 2) / viewport.w, (height - 2) / viewport.h)
      );
      this.renderSlide(this.slideTarget, this.getSlideData(), true, scale);
      if (this.counter) {
        this.counter.textContent = (this.getCurrentSlide() + 1) + ' / ' +
          presentation.slides.length;
      }
      this.animate();
    }

    move(delta) {
      const presentation = this.getPresentation();
      if (!presentation || !presentation.slides.length) {
        return;
      }
      const current = this.getCurrentSlide();
      const next = Math.max(
        0,
        Math.min(presentation.slides.length - 1, current + delta)
      );
      if (next === current) {
        this.showHelp();
        return;
      }
      this.setCurrentSlide(next);
      this.fit();
    }

    async exit() {
      global.clearTimeout(this.helpTimer);
      if (this.fullscreenElement() === this.overlay) {
        try {
          if (global.document.exitFullscreen) {
            await global.document.exitFullscreen();
          } else if (global.document.webkitExitFullscreen) {
            global.document.webkitExitFullscreen();
          }
        } catch (error) {
          global.console.warn(error);
        }
      }
      this.overlay.classList.add('hidden');
      this.overlay.classList.remove('is-fullscreen');
      global.document.body.classList.remove('presentation-active');
      this.touchStart = null;
      this.renderAll();
    }

    handleKeydown(event) {
      const presentation = this.getPresentation();
      if (!presentation) {
        return;
      }
      if (event.key === 'Escape') {
        event.preventDefault();
        void this.exit();
      } else if (
        event.key === 'ArrowRight' || event.key === 'ArrowDown' ||
        event.key === 'PageDown' || event.key === ' ' || event.key === 'Enter'
      ) {
        event.preventDefault();
        this.move(1);
      } else if (
        event.key === 'ArrowLeft' || event.key === 'ArrowUp' ||
        event.key === 'PageUp' || event.key === 'Backspace'
      ) {
        event.preventDefault();
        this.move(-1);
      } else if (event.key === 'Home') {
        event.preventDefault();
        this.setCurrentSlide(0);
        this.fit();
      } else if (event.key === 'End') {
        event.preventDefault();
        this.setCurrentSlide(presentation.slides.length - 1);
        this.fit();
      }
      this.showHelp();
    }

    bind() {
      this.startButtons.forEach((button) => {
        if (button) {
          button.onclick = () => this.enter(true);
        }
      });
      this.currentButtons.forEach((button) => {
        if (button) {
          button.onclick = () => this.enter(false);
        }
      });
      if (this.exitButton) {
        this.exitButton.onclick = (event) => {
          event.stopPropagation();
          void this.exit();
        };
      }
      if (this.fullscreenButton) {
        this.fullscreenButton.onclick = (event) => {
          event.stopPropagation();
          void this.toggleFullscreen();
        };
      }
      this.overlay.addEventListener('keydown', (event) => this.handleKeydown(event));
      this.overlay.addEventListener('pointerdown', (event) => {
        if (event.target.closest('.present-controls')) {
          return;
        }
        this.touchStart = {x: event.clientX, y: event.clientY, id: event.pointerId};
      });
      this.overlay.addEventListener('pointerup', (event) => {
        if (
          !this.touchStart || this.touchStart.id !== event.pointerId ||
          event.target.closest('.present-controls')
        ) {
          return;
        }
        const dx = event.clientX - this.touchStart.x;
        const dy = event.clientY - this.touchStart.y;
        this.touchStart = null;
        if (Math.abs(dx) > 55 && Math.abs(dx) > Math.abs(dy)) {
          this.move(dx < 0 ? 1 : -1);
        } else {
          this.move(1);
        }
        this.showHelp();
      });
      this.overlay.addEventListener('pointercancel', () => {
        this.touchStart = null;
      });
      ['fullscreenchange', 'webkitfullscreenchange'].forEach((name) => {
        global.document.addEventListener(name, () => {
          this.updateFullscreenControl();
          global.requestAnimationFrame(() => this.fit());
        });
      });
      global.addEventListener('resize', () => {
        if (!this.overlay.classList.contains('hidden')) {
          global.requestAnimationFrame(() => this.fit());
        }
      });
      if (global.ResizeObserver) {
        this.resizeObserver = new global.ResizeObserver(() => {
          if (!this.overlay.classList.contains('hidden')) {
            global.requestAnimationFrame(() => this.fit());
          }
        });
        this.resizeObserver.observe(this.overlay);
      }
    }
  }

  global.InkDeskPresentationsSlideshow = Object.freeze({
    version: '0.20.2.9',
    create(options) {
      return new PresentationSlideshowController(options);
    },
  });
})(window);
