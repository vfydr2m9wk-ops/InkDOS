(function (global) {
  'use strict';

  const PPTX_MIME = 'application/vnd.openxmlformats-officedocument.presentationml.presentation';

  class PresentationFileController {
    constructor(options) {
      this.ns = options.ns;
      this.getPresentation = options.getPresentation;
      this.setPresentation = options.setPresentation;
      this.getActiveTheme = options.getActiveTheme;
      this.setActiveTheme = options.setActiveTheme;
      this.getTextDefaults = options.getTextDefaults;
      this.setTextDefaults = options.setTextDefaults;
      this.getIdSequence = options.getIdSequence;
      this.setIdSequence = options.setIdSequence;
      this.setCurrentSlide = options.setCurrentSlide;
      this.resetSelection = options.resetSelection;
      this.resetHistory = options.resetHistory;
      this.showApp = options.showApp;
      this.renderAll = options.renderAll;
      this.markSaved = options.markSaved;
      this.setReady = options.setReady;
      this.parseXml = options.parseXml;
      this.relMap = options.relMap;
      this.normalizePath = options.normalizePath;
      this.first = options.first;
      this.all = options.all;
      this.attr = options.attr;
      this.loadTheme = options.loadTheme;
      this.parseDefaultTextStyle = options.parseDefaultTextStyle;
      this.parseSlide = options.parseSlide;
      this.orderMatchesSource = options.orderMatchesSource;
      this.patchImportedSlide = options.patchImportedSlide;
      this.shapeObjectXml = options.shapeObjectXml;
      this.pictureObjectXml = options.pictureObjectXml;
      this.importLegacyPpt = options.importLegacyPpt;
      this.onOpenedSource = options.onOpenedSource;
      this.isRecoveryRestore = options.isRecoveryRestore;
      this.markRecoveryClean = options.markRecoveryClean;
      this.flushRecovery = options.flushRecovery || (() => Promise.resolve());
      this.sourceBuffer = null;
    }

    clearSource() {
      this.sourceBuffer = null;
    }

    getSourceBuffer() {
      return this.sourceBuffer;
    }

    setSourceBuffer(buffer) {
      this.sourceBuffer = buffer ? buffer.slice(0) : null;
    }

    async load(file) {
      this.setReady('Opening…');
      const isLegacyPpt = /\.ppt$/i.test(file.name || '');
      if (!isLegacyPpt && !/\.pptx$/i.test(file.name || '')) {
        throw new Error('Please choose a PPT or PPTX presentation file.');
      }

      const previous = {
        activeTheme: this.getActiveTheme(),
        textDefaults: this.getTextDefaults(),
        idSequence: this.getIdSequence(),
      };

      try {
        if (global.InkDeskRuntime) {
          global.InkDeskRuntime.validateInputSize(file.size, file.name);
        }
        const buffer = await file.arrayBuffer();
        if (isLegacyPpt) {
          const importer = this.importLegacyPpt || global.InkDeskPresentationsPptImport;
          if (!importer || typeof importer.importLegacyPpt !== 'function') {
            throw new Error('Legacy PPT import is unavailable.');
          }
          const imported = importer.importLegacyPpt(buffer, file.name);
          this.sourceBuffer = null;
          this.setPresentation(imported);
          this.setActiveTheme(imported.theme || null);
          this.setCurrentSlide(0);
          this.resetSelection();
          this.resetHistory();
          this.showApp();
          this.renderAll();
          this.markSaved();
          if (!this.isRecoveryRestore() && this.onOpenedSource) await this.onOpenedSource(file, buffer);
          this.setReady('Opened legacy PPT');
          this.installDebugHandle(imported.slides.length);
          return imported;
        }
        if (global.InkDeskRuntime) {
          global.InkDeskRuntime.validateZipPackage(buffer, file.name);
        }
        const zip = await global.JSZip.loadAsync(buffer);
        const presentationFile = zip.file('ppt/presentation.xml');
        const presentationRelsFile = zip.file('ppt/_rels/presentation.xml.rels');
        if (!presentationFile || !presentationRelsFile) {
          throw new Error('Invalid PPTX package');
        }

        const pxml = this.parseXml(
          await presentationFile.async('text'),
          'ppt/presentation.xml'
        );
        const rels = this.parseXml(
          await presentationRelsFile.async('text'),
          'ppt/_rels/presentation.xml.rels'
        );
        const relsMap = this.relMap(rels);
        const sldSz = this.first(pxml, 'sldSz');
        const activeTheme = await this.loadTheme(zip);
        this.setActiveTheme(activeTheme);
        this.setTextDefaults(this.parseDefaultTextStyle(pxml));

        const output = {
          name: file.name.replace(/\.pptx$/i, ''),
          width: +this.attr(sldSz, 'cx', '12192000'),
          height: +this.attr(sldSz, 'cy', '6858000'),
          source: 'pptx',
          theme: activeTheme,
          compatibility: {
            engine: '0.19.0-beta-pptx-preservation',
            themeResolved: true,
            masterArtwork: true,
            richTextInheritance: true,
            presenterNotesEditor: true,
            presenterNotesExport: true,
            chartsPreview: true,
            transitionsPreview: true,
          },
          originalSlideRids: [],
          slides: [],
        };

        const ids = this.all(this.first(pxml, 'sldIdLst') || pxml, 'sldId');
        for (let index = 0; index < ids.length; index += 1) {
          const item = ids[index];
          const rid = item.getAttributeNS(this.ns.r, 'id') ||
            this.attr(item, 'r:id') || this.attr(item, 'id');
          const target = relsMap[rid];
          if (!target) {
            continue;
          }
          const slidePath = this.normalizePath('ppt', target);
          if (!zip.file(slidePath)) {
            continue;
          }
          const parsed = await this.parseSlide(zip, slidePath, index);
          output.originalSlideRids.push(rid);
          parsed.sourcePresentationRid = rid;
          parsed.sourceSlideId = this.attr(item, 'id', String(256 + index));
          output.slides.push(parsed);
        }

        if (!output.slides.length) {
          throw new Error('No slides found');
        }

        this.sourceBuffer = buffer.slice(0);
        this.setPresentation(output);
        this.setActiveTheme(output.theme || null);
        this.setCurrentSlide(0);
        this.resetSelection();
        this.resetHistory();
        this.showApp();
        this.renderAll();
        this.markSaved();
        if (!this.isRecoveryRestore() && this.onOpenedSource) {
          await this.onOpenedSource(file, buffer);
        }
        this.setReady('Opened');
        this.installDebugHandle(output.slides.length);
        return output;
      } catch (error) {
        this.setActiveTheme(previous.activeTheme);
        this.setTextDefaults(previous.textDefaults);
        this.setIdSequence(previous.idSequence);
        this.setReady(
          this.getPresentation()
            ? 'Open failed; previous presentation preserved'
            : 'Open error'
        );
        throw error;
      }
    }

    installDebugHandle(slideCount) {
      global.__LocalPresentationsDebug = {
        version: '0.19.0-beta-pptx-preservation',
        slideCount,
        getPresentation: () => this.getPresentation(),
        getSourceBuffer: () => this.sourceBuffer,
      };
    }

    async save() {
      const presentation = this.getPresentation();
      if (!presentation) {
        return;
      }
      try {
        if (this.sourceBuffer && presentation.source === 'pptx') {
          return await this.saveImportedPptx();
        }
        return await this.saveNewPptx();
      } catch (error) {
        global.console.error(error);
        global.alert('Save failed: ' + error.message);
        this.setReady('Save error');
      }
    }

    async saveImportedPptx() {
      const presentation = this.getPresentation();
      if (!this.orderMatchesSource()) {
        throw new Error(
          'Slide insertion, deletion, or duplication in imported presentations is not yet ' +
          'available in preservation mode. Save the original slide set or create a new presentation.'
        );
      }
      this.setReady('Preparing copy…');
      const previousPresentation = JSON.stringify(presentation);
      const previousSource = this.sourceBuffer.slice(0);
      try {
        const zip = await global.JSZip.loadAsync(previousSource);
        for (const slide of presentation.slides) {
          if (slide.sourcePath) {
            await this.patchImportedSlide(zip, slide);
          }
        }
        const bytes = await zip.generateAsync({
          type: 'uint8array',
          compression: 'DEFLATE',
          compressionOptions: {level: 6},
        });
        const nextSource = bytes.buffer.slice(
          bytes.byteOffset,
          bytes.byteOffset + bytes.byteLength
        );
        const blob = new Blob([bytes], {type: PPTX_MIME});
        await this.flushRecovery();
        this.downloadBlob(
          blob,
          (presentation.name || 'InkDesk Presentation') + '_copy.pptx'
        );
        this.sourceBuffer = nextSource;
        this.setReady('Download requested');
      } catch (error) {
        const restored = JSON.parse(previousPresentation);
        this.setPresentation(restored);
        this.setActiveTheme(restored.theme || null);
        this.sourceBuffer = previousSource;
        this.renderAll();
        throw error;
      }
    }

    async saveNewPptx() {
      const presentation = this.getPresentation();
      if (!presentation) {
        return;
      }
      const hasNotes = presentation.slides.some(
        (slide) => String(slide.notes || '').trim()
      );
      if (
        hasNotes &&
        !global.confirm(
          'Presenter notes are not exported in the current stabilization release. ' +
          'Continue and save the slides without notes?'
        )
      ) {
        return;
      }

      this.setReady('Saving…');
      try {
        const zip = new global.JSZip();
        zip.file(
          '_rels/.rels',
          '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' +
          '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">' +
          '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/' +
          'relationships/officeDocument" Target="ppt/presentation.xml"/></Relationships>'
        );
        zip.file(
          'ppt/_rels/presentation.xml.rels',
          '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' +
          '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">' +
          presentation.slides.map((slide, index) =>
            '<Relationship Id="rId' + (index + 1) + '" Type="http://schemas.openxmlformats.org/' +
            'officeDocument/2006/relationships/slide" Target="slides/slide' + (index + 1) + '.xml"/>'
          ).join('') + '</Relationships>'
        );
        const slideType = presentation.width / presentation.height < 1.5
          ? 'screen4x3'
          : 'screen16x9';
        zip.file(
          'ppt/presentation.xml',
          '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' +
          '<p:presentation xmlns:a="' + this.ns.a + '" xmlns:r="' + this.ns.r + '" xmlns:p="' +
          this.ns.p + '"><p:sldMasterIdLst/><p:sldIdLst>' +
          presentation.slides.map((slide, index) =>
            '<p:sldId id="' + (256 + index) + '" r:id="rId' + (index + 1) + '"/>'
          ).join('') + '</p:sldIdLst><p:sldSz cx="' + presentation.width + '" cy="' +
          presentation.height + '" type="' + slideType + '"/><p:notesSz cx="6858000" ' +
          'cy="9144000"/></p:presentation>'
        );

        let mediaIndex = 1;
        const contentTypes = [
          '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>',
          '<Default Extension="xml" ContentType="application/xml"/>',
          '<Default Extension="png" ContentType="image/png"/>',
          '<Default Extension="jpg" ContentType="image/jpeg"/>',
          '<Default Extension="jpeg" ContentType="image/jpeg"/>',
          '<Default Extension="gif" ContentType="image/gif"/>',
          '<Override PartName="/ppt/presentation.xml" ' +
          'ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>',
        ];

        for (let index = 0; index < presentation.slides.length; index += 1) {
          const slideData = presentation.slides[index];
          const relationships = [];
          let pictureXml = '';
          let shapeXml = '';
          for (const object of slideData.objects) {
            if (object.type === 'image') {
              const extension = (object.ext || 'png').replace('jpeg', 'jpg');
              const name = 'image' + mediaIndex + '.' + extension;
              const base64 = object.src.split(',')[1] || '';
              zip.file('ppt/media/' + name, base64, {base64: true});
              const relationshipId = 'rId' + (relationships.length + 1);
              relationships.push(
                '<Relationship Id="' + relationshipId + '" Type="http://schemas.openxmlformats.org/' +
                'officeDocument/2006/relationships/image" Target="../media/' + name + '"/>'
              );
              pictureXml += this.pictureObjectXml(object, relationshipId, mediaIndex);
              mediaIndex += 1;
            } else {
              shapeXml += this.shapeObjectXml(object);
            }
          }
          zip.file(
            'ppt/slides/slide' + (index + 1) + '.xml',
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' +
            '<p:sld xmlns:a="' + this.ns.a + '" xmlns:r="' + this.ns.r + '" xmlns:p="' +
            this.ns.p + '"><p:cSld><p:bg><p:bgPr><a:solidFill><a:srgbClr val="' +
            (slideData.background || '#ffffff').replace('#', '') +
            '"/></a:solidFill></p:bgPr></p:bg><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/>' +
            '<p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/>' +
            '<a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm>' +
            '</p:grpSpPr>' + shapeXml + pictureXml + '</p:spTree></p:cSld><p:clrMapOvr>' +
            '<a:masterClrMapping/></p:clrMapOvr></p:sld>'
          );
          zip.file(
            'ppt/slides/_rels/slide' + (index + 1) + '.xml.rels',
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' +
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">' +
            relationships.join('') + '</Relationships>'
          );
          contentTypes.push(
            '<Override PartName="/ppt/slides/slide' + (index + 1) + '.xml" ' +
            'ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>'
          );
        }

        zip.file(
          '[Content_Types].xml',
          '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' +
          '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">' +
          contentTypes.join('') + '</Types>'
        );
        const blob = await zip.generateAsync({
          type: 'blob',
          mimeType: PPTX_MIME,
          compression: 'DEFLATE',
          compressionOptions: {level: 6},
        });
        await this.flushRecovery();
        this.downloadBlob(
          blob,
          (presentation.name || 'InkDesk Presentation') + '_copy.pptx'
        );
        this.setReady('Download requested');
      } catch (error) {
        global.console.error('New presentation export failed.', error);
        throw error;
      }
    }

    downloadBlob(blob, name) {
      if (global.InkDeskRuntime) {
        return global.InkDeskRuntime.requestDownload(blob, name);
      }
      if (!(blob instanceof Blob) || !blob.size) {
        throw new Error('The generated presentation copy is empty.');
      }
      const link = global.document.createElement('a');
      const url = global.URL.createObjectURL(blob);
      link.href = url;
      link.download = name;
      link.rel = 'noopener';
      link.hidden = true;
      global.document.body.appendChild(link);
      try {
        link.click();
      } finally {
        link.remove();
        global.setTimeout(() => global.URL.revokeObjectURL(url), 15000);
      }
    }
  }

  global.InkDeskPresentationsFileIO = {
    create(options) {
      return new PresentationFileController(options);
    },
  };
})(window);
