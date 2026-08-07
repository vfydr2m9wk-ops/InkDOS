(function (global) {
  'use strict';

  class PresentationThumbnailsController {
    constructor(options) {
      this.list = options.list;
      this.workspace = options.workspace;
      this.button = options.button;
      this.getPresentation = options.getPresentation;
      this.getCurrentSlide = options.getCurrentSlide;
      this.goToSlide = options.goToSlide;
      this.safeFont = options.safeFont;
      this.relayout = options.relayout;
      this.bindToggle();
      this.updateToggleLabel();
    }

    bindToggle() {
      if (!this.button || !this.workspace) {
        return;
      }
      this.button.onclick = () => {
        this.workspace.classList.toggle('hide-slides');
        this.updateToggleLabel();
        this.relayout();
      };
    }

    updateToggleLabel() {
      if (!this.button || !this.workspace) {
        return;
      }
      this.button.textContent = this.workspace.classList.contains('hide-slides')
        ? 'Show thumbnails'
        : 'Hide thumbnails';
    }

    render() {
      const presentation = this.getPresentation();
      if (!this.list || !presentation) {
        return;
      }

      this.list.innerHTML = '';
      presentation.slides.forEach((slide, index) => {
        const thumbnail = global.document.createElement('div');
        thumbnail.className = 'thumb ' + (
          index === this.getCurrentSlide() ? 'active' : ''
        );
        thumbnail.tabIndex = -1;
        thumbnail.dataset.slideIndex = index;
        thumbnail.setAttribute('role', 'button');
        thumbnail.setAttribute('aria-label', 'Slide ' + (index + 1));
        thumbnail.innerHTML = [
          '<div class="thumb-num">' + (index + 1) + '</div>',
          '<div class="thumb-box"><div class="thumb-title"></div></div>',
        ].join('');
        thumbnail.querySelector('.thumb-title').textContent =
          slide.title || ('Slide ' + (index + 1));
        thumbnail.onclick = () => this.goToSlide(index, true);
        this.list.appendChild(thumbnail);
        this.renderMini(slide, thumbnail.querySelector('.thumb-box'));
      });
    }

    renderMini(slide, box) {
      const presentation = this.getPresentation();
      if (!presentation || !box) {
        return;
      }

      const mini = global.document.createElement('div');
      mini.className = 'thumb-mini';
      mini.style.width = '160px';
      mini.style.height = '90px';
      mini.style.transform = 'scale(' + ((box.clientWidth || 120) / 160) + ')';
      box.appendChild(mini);

      const ratio = (presentation.width || 12192000) /
        (presentation.height || 6858000);
      let viewportWidth = 160;
      let viewportHeight = viewportWidth / ratio;
      if (viewportHeight > 90) {
        viewportHeight = 90;
        viewportWidth = viewportHeight * ratio;
      }

      const area = global.document.createElement('div');
      area.style.position = 'absolute';
      area.style.left = ((160 - viewportWidth) / 2) + 'px';
      area.style.top = ((90 - viewportHeight) / 2) + 'px';
      area.style.width = viewportWidth + 'px';
      area.style.height = viewportHeight + 'px';
      area.style.overflow = 'hidden';
      area.style.backgroundColor = slide.background || '#fff';
      area.style.backgroundImage = slide.backgroundImage || 'none';
      area.style.backgroundRepeat = slide.backgroundRepeat || 'no-repeat';
      area.style.backgroundSize = slide.backgroundSize || 'auto';
      mini.appendChild(area);

      const scaleX = viewportWidth / presentation.width;
      const scaleY = viewportHeight / presentation.height;
      slide.objects.slice(0, 80).forEach((object) => {
        this.renderObjectPreview(area, object, slide, scaleX, scaleY, viewportHeight);
      });
    }

    renderObjectPreview(area, object, slide, scaleX, scaleY, viewportHeight) {
      const element = global.document.createElement('div');
      element.style.position = 'absolute';
      element.style.left = (object.x * scaleX) + 'px';
      element.style.top = (object.y * scaleY) + 'px';
      element.style.width = Math.max(1, object.w * scaleX) + 'px';
      element.style.height = Math.max(1, object.h * scaleY) + 'px';
      element.style.zIndex = String(Math.max(1, Number(object.z) || 1));
      element.style.overflow = 'hidden';
      element.style.boxSizing = 'border-box';

      if (object.type === 'text') {
        this.renderTextPreview(element, object, viewportHeight);
      } else if (object.type === 'image') {
        element.style.backgroundImage = 'url(' + object.src + ')';
        element.style.backgroundSize = object.fitMode === 'fill'
          ? '100% 100%'
          : (object.fitMode === 'contain' ? 'contain' : 'cover');
        element.style.backgroundRepeat = 'no-repeat';
        element.style.backgroundPosition = 'center';
      } else if (object.type === 'table') {
        element.style.border = '1px solid #555';
        element.textContent = object.cells.map((row) => row.join(' ')).join(' ');
        element.style.fontSize = '3px';
      } else if (object.type === 'chart') {
        element.style.border = '1px solid rgba(80,80,80,.4)';
        element.style.fontSize = '3px';
        element.textContent = (object.title || 'Chart') + ' ' +
          (object.categories || []).join(' ');
      } else if (object.useBackgroundFill) {
        element.style.backgroundColor = slide.background || '#fff';
        element.style.backgroundImage = slide.backgroundImage || 'none';
        element.style.backgroundRepeat = slide.backgroundRepeat || 'no-repeat';
        element.style.backgroundSize = slide.backgroundSize || 'auto';
      } else {
        element.style.background = object.fill || 'transparent';
        element.style.border = object.lineWidth && object.lineWidth > 0
          ? '1px solid ' + (object.line || '#333')
          : 'none';
        if (object.shape === 'roundRect') {
          element.style.borderRadius = '3px';
        }
      }
      area.appendChild(element);
    }

    renderTextPreview(element, object, viewportHeight) {
      element.style.fontFamily = this.safeFont(object.font);
      element.style.fontSize = Math.max(2, (object.size || 14) * (viewportHeight / 540)) + 'px';
      element.style.color = object.color || '#222';
      element.style.textAlign = object.align || 'left';

      if (!object.paragraphs || !object.paragraphs.length) {
        element.textContent = object.placeholderPrompt || object.text || '';
        return;
      }

      object.paragraphs.forEach((paragraph) => {
        const paragraphElement = global.document.createElement('div');
        paragraphElement.style.whiteSpace = 'nowrap';
        if (paragraph.bullet) {
          const bullet = global.document.createElement('span');
          bullet.textContent = (paragraph.bullet.char || '•') + ' ';
          bullet.style.color = paragraph.bullet.color || object.color || '#222';
          paragraphElement.appendChild(bullet);
        }
        paragraph.runs.forEach((run) => {
          const span = global.document.createElement('span');
          span.textContent = run.text;
          span.style.color = run.color || object.color || '#222';
          span.style.fontWeight = run.bold ? '700' : '400';
          paragraphElement.appendChild(span);
        });
        element.appendChild(paragraphElement);
      });
    }
  }

  global.InkDeskPresentationsThumbnails = Object.freeze({
    version: '0.20.2.14',
    create(options) {
      return new PresentationThumbnailsController(options);
    },
  });
})(window);
