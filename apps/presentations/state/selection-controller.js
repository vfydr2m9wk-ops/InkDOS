(function (global) {
  'use strict';

  class PresentationSelectionController {
    constructor(options) {
      this.canvas = options.canvas;
      this.getPresentation = options.getPresentation;
      this.getCurrentSlideData = options.getCurrentSlideData;
      this.getEditingId = options.getEditingId;
      this.getZoom = options.getZoom;
      this.scaleX = options.scaleX;
      this.scaleY = options.scaleY;
      this.toPixelX = options.toPixelX;
      this.toPixelY = options.toPixelY;
      this.markDirty = options.markDirty;
      this.renderSlide = options.renderSlide;
      this.selectedId = null;
      this.drag = null;

      this.startDrag = this.startDrag.bind(this);
      this.startResize = this.startResize.bind(this);
      this.startRotate = this.startRotate.bind(this);
      this.onPointerMove = this.onPointerMove.bind(this);
      this.onPointerUp = this.onPointerUp.bind(this);

      if (this.canvas) {
        this.canvas.onclick = () => this.clear();
      }
      global.addEventListener('pointermove', this.onPointerMove);
      global.addEventListener('pointerup', this.onPointerUp);
    }

    getId() {
      return this.selectedId;
    }

    setId(id, options = {}) {
      this.selectedId = id || null;
      if (options.render !== false) {
        this.renderSlide();
      }
      return this.selectedId;
    }

    clear(options = {}) {
      return this.setId(null, options);
    }

    reset(id = null, options = {}) {
      return this.setId(id, options);
    }

    getSelectedObject() {
      const slide = this.getCurrentSlideData();
      if (!slide || !this.selectedId) {
        return null;
      }
      return slide.objects.find((object) => object.id === this.selectedId) || null;
    }

    canvasPoint(event) {
      const rect = this.canvas.getBoundingClientRect();
      return {
        x: (event.clientX - rect.left) / this.getZoom() / this.scaleX(),
        y: (event.clientY - rect.top) / this.getZoom() / this.scaleY(),
      };
    }

    startDrag(event) {
      if (event.target.classList.contains('handle') || this.getEditingId()) {
        return;
      }
      const id = event.currentTarget.dataset.id;
      this.setId(id);
      const object = this.getSelectedObject();
      const point = this.canvasPoint(event);
      this.drag = {
        mode: 'move',
        id,
        startX: point.x,
        startY: point.y,
        ox: object.x,
        oy: object.y,
      };
      event.currentTarget.setPointerCapture(event.pointerId);
      event.preventDefault();
    }

    startResize(event) {
      event.stopPropagation();
      const object = this.getSelectedObject();
      const point = this.canvasPoint(event);
      const handle = event.currentTarget.dataset.handle;
      this.drag = {
        mode: 'resize',
        handle,
        id: object.id,
        startX: point.x,
        startY: point.y,
        ox: object.x,
        oy: object.y,
        ow: object.w,
        oh: object.h,
      };
      event.currentTarget.setPointerCapture(event.pointerId);
      event.preventDefault();
    }

    startRotate(event) {
      event.stopPropagation();
      const object = this.getSelectedObject();
      const center = {
        x: object.x + object.w / 2,
        y: object.y + object.h / 2,
      };
      const point = this.canvasPoint(event);
      this.drag = {
        mode: 'rotate',
        id: object.id,
        cx: center.x,
        cy: center.y,
        startAngle: Math.atan2(point.y - center.y, point.x - center.x) * 180 / Math.PI,
        startRot: object.rot || 0,
      };
      event.currentTarget.setPointerCapture(event.pointerId);
      event.preventDefault();
    }

    onPointerMove(event) {
      if (!this.drag) {
        return;
      }
      const slide = this.getCurrentSlideData();
      const object = slide && slide.objects.find((item) => item.id === this.drag.id);
      if (!object) {
        return;
      }
      const point = this.canvasPoint(event);
      if (this.drag.mode === 'move') {
        object.x = this.drag.ox + (point.x - this.drag.startX);
        object.y = this.drag.oy + (point.y - this.drag.startY);
        this.showGuides(object);
      } else if (this.drag.mode === 'rotate') {
        object.rot = this.drag.startRot + (
          Math.atan2(point.y - this.drag.cy, point.x - this.drag.cx) * 180 / Math.PI -
          this.drag.startAngle
        );
      } else {
        this.resizeObject(object, point);
      }
      this.renderSlide();
      this.markDirty();
    }

    resizeObject(object, point) {
      const dx = point.x - this.drag.startX;
      const dy = point.y - this.drag.startY;
      const handle = this.drag.handle;
      let x = this.drag.ox;
      let y = this.drag.oy;
      let width = this.drag.ow;
      let height = this.drag.oh;

      if (handle.includes('r')) {
        width = this.drag.ow + dx;
      }
      if (handle.includes('l')) {
        x = this.drag.ox + dx;
        width = this.drag.ow - dx;
      }
      if (handle.includes('b')) {
        height = this.drag.oh + dy;
      }
      if (handle.includes('t')) {
        y = this.drag.oy + dy;
        height = this.drag.oh - dy;
      }

      object.x = x;
      object.y = y;
      object.w = Math.max(120000, width);
      object.h = Math.max(80000, height);
    }

    onPointerUp() {
      this.drag = null;
      this.clearGuides();
    }

    clearGuides() {
      global.document.querySelectorAll('.guide').forEach((guide) => guide.remove());
    }

    showGuides(object) {
      this.clearGuides();
      const presentation = this.getPresentation();
      if (!presentation) {
        return;
      }
      const centerX = object.x + object.w / 2;
      const centerY = object.y + object.h / 2;
      if (Math.abs(centerX - presentation.width / 2) < 130000) {
        const guide = global.document.createElement('div');
        guide.className = 'guide v';
        guide.style.left = this.toPixelX(presentation.width / 2) + 'px';
        this.canvas.appendChild(guide);
      }
      if (Math.abs(centerY - presentation.height / 2) < 130000) {
        const guide = global.document.createElement('div');
        guide.className = 'guide h';
        guide.style.top = this.toPixelY(presentation.height / 2) + 'px';
        this.canvas.appendChild(guide);
      }
    }

    addHandles(element) {
      ['tl', 'tc', 'tr', 'ml', 'mr', 'bl', 'bc', 'br'].forEach((position) => {
        const handle = global.document.createElement('div');
        handle.className = 'handle ' + position;
        handle.dataset.handle = position;
        handle.onpointerdown = this.startResize;
        element.appendChild(handle);
      });
      const stem = global.document.createElement('div');
      stem.className = 'rotate-stem';
      element.appendChild(stem);
      const rotate = global.document.createElement('div');
      rotate.className = 'handle rotate';
      rotate.dataset.handle = 'rotate';
      rotate.onpointerdown = this.startRotate;
      element.appendChild(rotate);
    }

    destroy() {
      global.removeEventListener('pointermove', this.onPointerMove);
      global.removeEventListener('pointerup', this.onPointerUp);
      this.clearGuides();
    }
  }

  global.InkDeskPresentationsSelection = Object.freeze({
    version: '0.20.2.28',
    create(options) {
      return new PresentationSelectionController(options);
    },
  });
})(window);
