(function (global) {
  'use strict';

  const FREE = 0xFFFFFFFF;
  const END = 0xFFFFFFFE;
  const MAX_STREAM_BYTES = 64 * 1024 * 1024;
  const MAX_RECORDS = 200000;
  const MAX_TEXT_LENGTH = 200000;
  const PPT_DOCUMENT = 'PowerPoint Document';
  const SLIDE_CONTAINER = 0x03EE;
  const TEXT_CHARS = 0x0FA0;
  const TEXT_BYTES = 0x0FA8;

  function view(bytes) {
    return new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
  }
  function u16(bytes, offset) { return view(bytes).getUint16(offset, true); }
  function u32(bytes, offset) { return view(bytes).getUint32(offset, true); }
  function concat(parts) {
    const result = new Uint8Array(parts.reduce((total, part) => total + part.length, 0));
    let offset = 0;
    parts.forEach((part) => { result.set(part, offset); offset += part.length; });
    return result;
  }
  function utf16(bytes) {
    let result = '';
    for (let offset = 0; offset + 1 < bytes.length; offset += 2) {
      result += String.fromCharCode(u16(bytes, offset));
    }
    return result;
  }
  function codePage(bytes) {
    try { return new TextDecoder('windows-1252').decode(bytes); } catch (_) {
      return Array.from(bytes, (value) => String.fromCharCode(value)).join('');
    }
  }
  function cleanText(value) {
    return String(value || '').replace(/\u0000/g, '').replace(/\r\n?/g, '\n').replace(/\u000b/g, '\n').trim();
  }

  class CompoundFileReader {
    constructor(buffer) {
      this.bytes = new Uint8Array(buffer);
      if (this.bytes.length < 512 || Array.from(this.bytes.subarray(0, 8)).join(',') !== '208,207,17,224,161,177,26,225') {
        throw new Error('The selected file is not a valid legacy PowerPoint document.');
      }
      const header = view(this.bytes);
      const sectorShift = u16(this.bytes, 30);
      if (![9, 12].includes(sectorShift) || u16(this.bytes, 32) !== 6) {
        throw new Error('This legacy PowerPoint container uses an unsupported layout.');
      }
      this.sectorSize = 2 ** sectorShift;
      this.miniSectorSize = 64;
      this.maxSectors = Math.ceil((this.bytes.length - 512) / this.sectorSize);
      this.firstDirectory = u32(this.bytes, 48);
      this.miniCutoff = u32(this.bytes, 56);
      this.firstMiniFat = u32(this.bytes, 60);
      this.miniFatCount = u32(this.bytes, 64);
      this.firstDifat = u32(this.bytes, 68);
      this.difatCount = u32(this.bytes, 72);
      const fatCount = u32(this.bytes, 44);
      if (fatCount > this.maxSectors || this.difatCount > this.maxSectors) {
        throw new Error('The legacy PowerPoint allocation tables are malformed.');
      }
      const difat = [];
      for (let offset = 76; offset < 512; offset += 4) {
        const sector = u32(this.bytes, offset);
        if (sector !== FREE && sector !== END) difat.push(sector);
      }
      let next = this.firstDifat;
      const seen = new Set();
      for (let count = 0; count < this.difatCount && next !== END && next !== FREE && !seen.has(next); count += 1) {
        if (next >= this.maxSectors) throw new Error('The legacy PowerPoint DIFAT chain is malformed.');
        seen.add(next);
        const sector = this.sector(next);
        for (let offset = 0; offset + 4 < sector.length; offset += 4) difat.push(u32(sector, offset));
        next = u32(sector, sector.length - 4);
      }
      this.fat = [];
      difat.slice(0, fatCount).forEach((sectorId) => {
        const sector = this.sector(sectorId);
        for (let offset = 0; offset + 4 <= sector.length; offset += 4) this.fat.push(u32(sector, offset));
      });
      const directory = this.readChain(this.firstDirectory);
      this.entries = [];
      for (let offset = 0; offset + 128 <= directory.length; offset += 128) {
        const entry = directory.subarray(offset, offset + 128);
        const nameLength = u16(entry, 64);
        const name = nameLength >= 2 ? utf16(entry.subarray(0, Math.min(64, nameLength - 2))) : '';
        this.entries.push({ name, type: entry[66], start: u32(entry, 116), size: u32(entry, 120) });
      }
      this.miniFat = [];
      if (this.miniFatCount && this.firstMiniFat !== END && this.firstMiniFat !== FREE) {
        const miniFat = this.readChain(this.firstMiniFat);
        for (let offset = 0; offset + 4 <= miniFat.length; offset += 4) this.miniFat.push(u32(miniFat, offset));
      }
      const root = this.entries.find((entry) => entry.type === 5);
      this.miniStream = root ? this.readChain(root.start).subarray(0, root.size) : new Uint8Array();
      void header;
    }
    sector(id) {
      const offset = (id + 1) * this.sectorSize;
      if (id >= this.maxSectors || offset < 0 || offset >= this.bytes.length) return new Uint8Array();
      return this.bytes.subarray(offset, Math.min(offset + this.sectorSize, this.bytes.length));
    }
    readChain(start) {
      const parts = [], seen = new Set();
      let sector = start;
      while (sector !== FREE && sector !== END && sector < this.fat.length && !seen.has(sector) && parts.length < this.maxSectors) {
        seen.add(sector); parts.push(this.sector(sector)); sector = this.fat[sector];
      }
      return concat(parts);
    }
    readMiniChain(start, size) {
      const parts = [], seen = new Set();
      let sector = start, total = 0;
      while (sector !== FREE && sector !== END && sector < this.miniFat.length && !seen.has(sector) && total < size) {
        seen.add(sector);
        parts.push(this.miniStream.subarray(sector * this.miniSectorSize, (sector + 1) * this.miniSectorSize));
        total += this.miniSectorSize; sector = this.miniFat[sector];
      }
      return concat(parts).subarray(0, size);
    }
    stream(name) {
      const entry = this.entries.find((item) => item.type === 2 && item.name.toLowerCase() === name.toLowerCase());
      if (!entry || entry.size > MAX_STREAM_BYTES) return null;
      return entry.size < this.miniCutoff ? this.readMiniChain(entry.start, entry.size) : this.readChain(entry.start).subarray(0, entry.size);
    }
  }

  function parseRecords(bytes) {
    const records = [];
    for (let offset = 0; offset + 8 <= bytes.length && records.length < MAX_RECORDS;) {
      const length = u32(bytes, offset + 4);
      if (length > bytes.length - offset - 8) break;
      records.push({ type: u16(bytes, offset + 2), data: bytes.subarray(offset + 8, offset + 8 + length) });
      offset += 8 + length;
    }
    return records;
  }
  function childrenOf(record) {
    const children = [];
    for (let offset = 0; offset + 8 <= record.data.length;) {
      const length = u32(record.data, offset + 4);
      if (length > record.data.length - offset - 8) break;
      children.push({ type: u16(record.data, offset + 2), data: record.data.subarray(offset + 8, offset + 8 + length) });
      offset += 8 + length;
    }
    return children;
  }
  function collectText(record, output) {
    const nested = childrenOf(record);
    if (!nested.length) return;
    nested.forEach((child) => {
      if (child.type === TEXT_CHARS) output.push(utf16(child.data));
      else if (child.type === TEXT_BYTES) output.push(codePage(child.data));
      else collectText(child, output);
    });
  }
  function collectSlides(record, output) {
    if (record.type === SLIDE_CONTAINER) {
      output.push(record);
      return;
    }
    childrenOf(record).forEach((child) => collectSlides(child, output));
  }
  function parseSlide(record, index) {
    const text = [];
    collectText(record, text);
    const values = text.map(cleanText).filter(Boolean).join('\n').slice(0, MAX_TEXT_LENGTH);
    const slide = { id: 'legacy-slide-' + (index + 1), title: values.split('\n')[0] || 'Slide ' + (index + 1), background: '#ffffff', objects: [], notes: '', compatibilityWarnings: ['Legacy drawing fidelity is not preserved.'] };
    if (values) slide.objects.push({ id: 'legacy-text-' + (index + 1), type: 'text', x: 900000, y: 700000, w: 10200000, h: 5200000, text: values, font: 'Arial', size: 24, color: '#20242a', align: 'left', z: 1 });
    return slide;
  }
  function importLegacyPpt(buffer, fileName) {
    if (global.InkDeskRuntime) global.InkDeskRuntime.validateInputSize(buffer.byteLength, fileName);
    const documentStream = new CompoundFileReader(buffer).stream(PPT_DOCUMENT);
    if (!documentStream) throw new Error('The legacy PowerPoint document stream is missing.');
    const records = parseRecords(documentStream);
    const slideRecords = [];
    records.forEach((record) => collectSlides(record, slideRecords));
    const slides = slideRecords.map((record, index) => parseSlide(record, index));
    if (!slides.length) throw new Error('No legacy PowerPoint slides could be decoded.');
    return {
      name: String(fileName || 'Presentation.ppt').replace(/\.ppt$/i, ''),
      width: 9144000,
      height: 6858000,
      source: 'ppt',
      theme: { fonts: { majorLatin: 'Arial', minorLatin: 'Arial' }, colors: { accent1: '#d64a24', dk1: '#000000', lt1: '#ffffff' } },
      compatibility: { engine: '0.20.3-legacy-ppt-text-import', legacyPptImport: true, textEditable: true, saveAsPptx: true, legacyDrawingFidelity: false, persistedVersionSelection: false },
      originalSlideRids: [],
      slides,
    };
  }

  global.InkDeskPresentationsPptImport = { importLegacyPpt };
})(window);
