(function (global) {
  'use strict';

  function createSaveController({
    state,
    elements,
    pdfjs,
    cleanName,
    status,
    toast,
    saveReview
  }) {
    if (
      !state ||
      !elements ||
      !pdfjs ||
      typeof cleanName !== 'function' ||
      typeof status !== 'function' ||
      typeof toast !== 'function' ||
      typeof saveReview !== 'function'
    ) {
      throw new Error(
        'InkDesk PDF save controller requires state, elements, pdfjs, cleanName, status, toast and saveReview.'
      );
    }

    const E = elements;

    function download(bytes, name, type) {
      const blob = bytes instanceof Blob
        ? bytes
        : new Blob([bytes], { type });
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement('a');
      anchor.href = url;
      anchor.download = name;
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      setTimeout(() => URL.revokeObjectURL(url), 30000);
    }

    function setAvailable(available) {
      E.saveModifiedPdfBtn.disabled = !available;
      if (!available) {
        E.saveModifiedPdfBtn.classList.remove('is-saving');
        E.saveModifiedPdfBtn.removeAttribute('aria-busy');
      }
    }

    function beginSaving() {
      E.saveModifiedPdfBtn.disabled = true;
      E.saveModifiedPdfBtn.classList.add('is-saving');
      E.saveModifiedPdfBtn.setAttribute('aria-busy', 'true');
    }

    function finishSaving() {
      E.saveModifiedPdfBtn.classList.remove('is-saving');
      E.saveModifiedPdfBtn.removeAttribute('aria-busy');
      E.saveModifiedPdfBtn.disabled = !state.doc;
    }

    function markSaved() {
      state.dirty = false;
      E.dirtyMark.hidden = true;
    }

    function modifiedFileName() {
      return cleanName(state.file?.name)
        .replace(/\.pdf$/i, '') + '-modified.pdf';
    }

    async function saveUnannotatedPdf() {
      status('Saving PDF…');
      const bytes = await state.doc.saveDocument();
      download(bytes, modifiedFileName(), 'application/pdf');
      markSaved();
      toast('PDF saved');
      return Object.freeze({ mode: 'pdfjs', annotated: false });
    }

    async function saveAnnotatedPdf() {
      const exporter = global.InkDeskPdfFlattenExport;
      if (!exporter || typeof exporter.exportDocument !== 'function') {
        throw new Error('The local annotated-PDF exporter is unavailable.');
      }

      const result = await exporter.exportDocument({
        pdfDocument: state.doc,
        pdfjsLib: pdfjs,
        documentObject: document,
        annotations: state.annotations,
        fileName: cleanName(state.file.name),
        dpi: 144,
        jpegQuality: 0.91,
        maxPagePixels: 8000000,
        onProgress(progress) {
          const phase = progress.phase === 'encode'
            ? 'Encoding'
            : 'Rendering';
          status(
            `${phase} annotated PDF · page ` +
            `${progress.page} of ${progress.total}`
          );
        }
      });

      download(result.bytes, result.fileName, 'application/pdf');
      markSaved();
      saveReview();
      toast(`Annotated PDF saved · ${result.pageCount} pages`);
      return Object.freeze({ mode: 'flattened', annotated: true });
    }

    async function saveModifiedPdf() {
      if (!state.doc || !state.file || E.saveModifiedPdfBtn.disabled) {
        return null;
      }

      beginSaving();

      try {
        return state.annotations.length > 0
          ? await saveAnnotatedPdf()
          : await saveUnannotatedPdf();
      } catch (error) {
        global.alert(
          'InkDesk could not create the PDF copy. ' +
          'The original file and the local review were not changed.'
        );
        console.error(error);
        status('PDF save failed.');
        return null;
      } finally {
        finishSaving();
      }
    }

    E.saveModifiedPdfBtn.onclick = saveModifiedPdf;

    return Object.freeze({
      saveModifiedPdf,
      setAvailable
    });
  }

  global.InkDeskPdfSaveController = Object.freeze({
    version: '0.20.2.14',
    createSaveController
  });
})(globalThis);
