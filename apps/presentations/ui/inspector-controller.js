(function (global) {
  'use strict';

  const DEFAULT_COLORS = [
    '#d64a24',
    '#f07a4c',
    '#241f1c',
    '#ffffff',
    '#111827',
    '#2563eb',
    '#16a34a',
    '#7c3aed',
    '#db2777',
    '#f59e0b',
  ];

  class PresentationInspectorController {
    constructor(options) {
      this.workspace = options.workspace;
      this.button = options.button;
      this.canvas = options.canvas;
      this.getSelectedObject = options.getSelectedObject;
      this.markDirty = options.markDirty;
      this.renderSlide = options.renderSlide;
      this.relayout = options.relayout;
      this.cloneState = options.cloneState;
      this.pushHistory = options.pushHistory;
      this.emu = options.emu;
      this.open = false;
      this.rotationTimer = null;
      this.compactQuery = global.matchMedia
        ? global.matchMedia('(max-width:1000px)')
        : null;
      this.onKeyDown = this.handleKeyDown.bind(this);

      this.bindPropertyControls();
      this.bindPalette(options.colors || DEFAULT_COLORS);
      this.bindPanelToggle();
      global.addEventListener('keydown', this.onKeyDown);
      this.applyOpenState();
    }

    byId(id) {
      return global.document.getElementById(id);
    }

    isCompact() {
      return this.compactQuery
        ? this.compactQuery.matches
        : global.innerWidth <= 1000;
    }

    isOpen() {
      return this.open;
    }

    applyOpenState() {
      if (!this.button || !this.workspace) {
        return;
      }

      this.workspace.classList.toggle('inspector-open', this.open);
      this.workspace.classList.toggle('hide-inspector', !this.open);
      this.workspace.dataset.inspectorOpen = String(this.open);
      this.button.textContent = this.open
        ? 'Hide format panel'
        : 'Show format panel';
      this.button.setAttribute('aria-expanded', String(this.open));
      this.button.setAttribute('aria-controls', 'inspector');
    }

    setOpen(open, options = {}) {
      this.open = Boolean(open);
      this.applyOpenState();
      if (options.relayout !== false) {
        this.relayout();
      }
    }

    handleKeyDown(event) {
      if (event.key === 'Escape' && this.isCompact() && this.open) {
        this.setOpen(false);
      }
    }

    bindPanelToggle() {
      if (!this.button) {
        return;
      }
      this.button.onclick = () => this.setOpen(!this.open);
    }

    update() {
      const object = this.getSelectedObject();
      const coreIds = [
        'propX',
        'propY',
        'propW',
        'propH',
        'propOpacity',
        'propFill',
        'propRotation',
      ];

      coreIds.forEach((id) => {
        const control = this.byId(id);
        if (control) {
          control.disabled = !object;
        }
      });

      const imageTools = this.byId('imageTools');
      if (imageTools) {
        imageTools.classList.toggle(
          'hidden',
          !object || object.type !== 'image',
        );
      }
      if (!object) {
        return;
      }

      this.byId('propX').value = Math.round((object.x / this.emu) * 100) / 100;
      this.byId('propY').value = Math.round((object.y / this.emu) * 100) / 100;
      this.byId('propW').value = Math.round((object.w / this.emu) * 100) / 100;
      this.byId('propH').value = Math.round((object.h / this.emu) * 100) / 100;
      this.byId('propOpacity').value = object.opacity == null ? 1 : object.opacity;
      this.byId('propFill').value =
        object.fill && object.fill !== 'transparent' ? object.fill : '#ffffff';
      this.byId('propRotation').value = Math.round(object.rot || 0);

      if (object.type === 'image') {
        this.byId('cropZoom').value = object.cropZoom || 1;
        this.byId('cropX').value = object.cropX == null ? 50 : object.cropX;
        this.byId('cropY').value = object.cropY == null ? 50 : object.cropY;
      }
    }

    bindPropertyControls() {
      ['propX', 'propY', 'propW', 'propH'].forEach((id) => {
        this.byId(id).onchange = () => {
          const object = this.getSelectedObject();
          if (!object) {
            return;
          }
          const value = Number(this.byId(id).value) * this.emu;
          if (id === 'propX') {
            object.x = value;
          } else if (id === 'propY') {
            object.y = value;
          } else if (id === 'propW') {
            object.w = value;
          } else {
            object.h = value;
          }
          this.markDirty();
          this.renderSlide();
        };
      });

      this.byId('propOpacity').oninput = () => {
        const object = this.getSelectedObject();
        if (!object) {
          return;
        }
        object.opacity = Number(this.byId('propOpacity').value);
        this.markDirty();
        this.renderSlide();
      };

      this.byId('propFill').oninput = () => {
        const object = this.getSelectedObject();
        if (!object) {
          return;
        }
        object.fill = this.byId('propFill').value;
        this.markDirty();
        this.renderSlide();
      };

      const rotation = this.byId('propRotation');
      rotation.addEventListener('pointerdown', (event) => event.stopPropagation());
      rotation.addEventListener('keydown', (event) => event.stopPropagation());
      rotation.oninput = () => {
        const object = this.getSelectedObject();
        if (!object) {
          return;
        }
        const before = this.cloneState();
        object.rot = Number(rotation.value) || 0;
        this.markDirty();
        global.clearTimeout(this.rotationTimer);
        this.rotationTimer = global.setTimeout(
          () => this.pushHistory(before),
          350,
        );
        const element = this.canvas.querySelector(
          '[data-id="' + object.id + '"]',
        );
        if (element) {
          element.style.transform = 'rotate(' + object.rot + 'deg)';
        }
      };
      rotation.onchange = () => {
        const object = this.getSelectedObject();
        if (!object) {
          return;
        }
        object.rot = Number(rotation.value) || 0;
        this.markDirty();
        this.renderSlide();
      };

      ['cropZoom', 'cropX', 'cropY'].forEach((id) => {
        this.byId(id).oninput = () => {
          const object = this.getSelectedObject();
          if (!object || object.type !== 'image') {
            return;
          }
          object[id] = this.byId(id).valueAsNumber;
          this.markDirty();
          this.renderSlide();
        };
      });

      this.byId('resetCropBtn').onclick = () => {
        const object = this.getSelectedObject();
        if (!object || object.type !== 'image') {
          return;
        }
        object.cropZoom = 1;
        object.cropX = 50;
        object.cropY = 50;
        this.markDirty();
        this.renderSlide();
      };
    }

    bindPalette(colors) {
      const palette = this.byId('palette');
      colors.forEach((color) => {
        const button = global.document.createElement('button');
        button.className = 'swatch';
        button.style.background = color;
        button.title = color;
        button.onclick = () => {
          const object = this.getSelectedObject();
          if (!object) {
            return;
          }
          object.fill = color;
          this.markDirty();
          this.renderSlide();
        };
        palette.appendChild(button);
      });
    }

    destroy() {
      global.removeEventListener('keydown', this.onKeyDown);
      global.clearTimeout(this.rotationTimer);
    }
  }

  global.InkDeskPresentationsInspector = Object.freeze({
    version: '0.20.2.26',
    create(options) {
      return new PresentationInspectorController(options);
    },
  });
})(window);
