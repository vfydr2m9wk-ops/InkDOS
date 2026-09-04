(function (global) {
  'use strict';

  const PPTX_MIME = 'application/vnd.openxmlformats-officedocument.presentationml.presentation';

  class PresentationRecoveryController {
    constructor(options) {
      this.getPresentation = options.getPresentation;
      this.setPresentation = options.setPresentation;
      this.getCurrentSlide = options.getCurrentSlide;
      this.setCurrentSlide = options.setCurrentSlide;
      this.getSelectedId = options.getSelectedId;
      this.resetSelection = options.resetSelection;
      this.getZoom = options.getZoom;
      this.setZoom = options.setZoom;
      this.setActiveTheme = options.setActiveTheme;
      this.resetHistory = options.resetHistory;
      this.showApp = options.showApp;
      this.renderAll = options.renderAll;
      this.markDirtyState = options.markDirtyState;
      this.setReady = options.setReady;
      this.loadFile = options.loadFile;
      this.setSourceBuffer = options.setSourceBuffer;
      this.clearSource = options.clearSource;
      this.restoring = false;
      this.manager = this.createManager(options.appVersion);
      this.installDebugHandle();
    }

    createManager(appVersion) {
      if (!global.InkDOSLocalRecovery) {
        return null;
      }
      return global.InkDOSLocalRecovery.create({
        module: 'presentations',
        appVersion,
        defaultFileName: 'Untitled presentation.pptx',
        serialize: () => this.capture(),
        restore: (context) => this.restore(context),
        status: (message) => {
          if (message && /failed/i.test(message)) {
            this.setReady(message);
          }
        },
      });
    }

    installDebugHandle() {
      if (!this.manager) {
        return;
      }
      global.__InkDOSPresentationsRecovery = {
        manager: this.manager,
        capture: () => this.capture(),
        restore: (context) => this.restore(context),
      };
    }

    isRestoring() {
      return this.restoring;
    }

    documentKey(file) {
      return 'file:' + [file.name, file.size, file.lastModified || 0].join(':');
    }

    async capture() {
      const presentation = this.getPresentation();
      if (!presentation) {
        return null;
      }
      return {
        kind: 'presentations',
        schemaVersion: 1,
        fileName: (presentation.name || 'Untitled presentation') + '.pptx',
        pres: JSON.parse(JSON.stringify(presentation)),
        currentSlide: this.getCurrentSlide(),
        selectedId: this.getSelectedId(),
        zoom: this.getZoom(),
      };
    }

    async restore(context) {
      const payload = context && context.snapshot && context.snapshot.payload;
      if (!payload || payload.kind !== 'presentations' || !payload.pres) {
        throw new Error('Unsupported presentation recovery snapshot.');
      }

      if (context.source && context.source.data) {
        this.restoring = true;
        try {
          const sourceName = String(payload.fileName || 'Recovered.pptx')
            .replace(/\.pptx$/i, '') + '.pptx';
          await this.loadFile(new global.File(
            [context.source.data],
            sourceName,
            {type: PPTX_MIME}
          ));
          this.setSourceBuffer(context.source.data);
        } finally {
          this.restoring = false;
        }
      } else {
        this.clearSource();
      }

      const presentation = JSON.parse(JSON.stringify(payload.pres));
      this.setPresentation(presentation);
      this.setActiveTheme(presentation.theme || null);
      this.setCurrentSlide(Math.max(
        0,
        Math.min(Number(payload.currentSlide) || 0, presentation.slides.length - 1)
      ));
      this.resetSelection(payload.selectedId || null);
      this.setZoom(Math.max(.35, Math.min(2, Number(payload.zoom) || .9)));
      this.resetHistory();
      this.showApp();
      this.renderAll();
      this.markDirtyState();
      this.setReady('Unsaved recovery restored');
    }

    markDirty() {
      if (this.manager) {
        this.manager.markDirty();
      }
    }

    markClean() {
      if (this.manager) {
        this.manager.markClean();
      }
    }

    flush() {
      return this.manager ? this.manager.flush() : Promise.resolve();
    }


    cancelPrompt() {
      if (this.manager) {
        this.manager.cancelPrompt();
      }
    }

    async startNewDocument() {
      if (!this.manager) {
        return;
      }
      this.manager.cancelPrompt();
      await this.manager.discardCurrent();
      return this.manager.startDocument({
        fileName: 'Untitled presentation.pptx',
        resetSnapshots: true,
      });
    }

    async startOpenedFile(file, buffer) {
      if (!this.manager) {
        return;
      }
      this.manager.cancelPrompt();
      await this.manager.discardCurrent();
      return this.manager.startDocument({
        documentKey: this.documentKey(file),
        fileName: file.name,
        sourceData: buffer,
        sourceMeta: {kind: 'pptx'},
        resetSnapshots: true,
      });
    }

    promptLatest() {
      if (this.manager) {
        return this.manager.promptLatest();
      }
      return Promise.resolve();
    }
  }

  global.InkDOSPresentationsRecovery = {
    create(options) {
      return new PresentationRecoveryController(options);
    },
  };
})(window);
