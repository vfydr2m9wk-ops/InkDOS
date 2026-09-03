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
  const CURRENT_USER = 'Current User';
  const PERSIST_DIRECTORY = 'PersistDirectoryAtom';

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
      const options = u16(bytes, offset);
      const length = u32(bytes, offset + 4);
      if (length > bytes.length - offset - 8) break;
      records.push({ type: u16(bytes, offset + 2), options, data: bytes.subarray(offset + 8, offset + 8 + length) });
      offset += 8 + length;
    }
    return records;
  }
  function childrenOf(record) {
    const children = [];
    if (!record || !record.data) return children;
    for (let offset = 0; offset + 8 <= record.data.length;) {
      const length = u32(record.data, offset + 4);
      if (length > record.data.length - offset - 8) break;
      children.push({ type: u16(record.data, offset + 2), options: u16(record.data, offset), data: record.data.subarray(offset + 8, offset + 8 + length) });
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
  function recordsOf(record, type, output = []) {
    childrenOf(record).forEach((child) => {
      if (child.type === type) output.push(child);
      recordsOf(child, type, output);
    });
    return output;
  }
  function color(value, fallback) {
    const rgb = Number(value) & 0xFFFFFF;
    if (!rgb) return fallback;
    return '#' + [rgb & 255, (rgb >>> 8) & 255, (rgb >>> 16) & 255]
      .map((part) => part.toString(16).padStart(2, '0')).join('');
  }
  function officeArtProperties(record) {
    const properties = {};
    const count = Math.min(record.options >>> 4, Math.floor(record.data.length / 6));
    for (let index = 0; index < count; index += 1) {
      const offset = index * 6;
      const property = u16(record.data, offset);
      properties[property & 0x3FFF] = { value: u32(record.data, offset + 2), complex: !!(property & 0x8000) };
    }
    return properties;
  }
  function anchorOf(record) {
    if (!record || record.data.length < 8) return null;
    const values = Array.from({ length: 4 }, (_, index) => view(record.data).getInt16(index * 2, true));
    const scale = 914400 / 576;
    return { x: Math.round(values[0] * scale), y: Math.round(values[1] * scale), w: Math.round(values[2] * scale), h: Math.round(values[3] * scale) };
  }
  function textOf(record) {
    const parts = [];
    collectText(record, parts);
    return parts.map(cleanText).filter(Boolean).join('\n').slice(0, MAX_TEXT_LENGTH);
  }
  function shapeName(type) {
    return type === 1 || type === 20 ? 'line' : type === 32 ? 'roundRect' : 'rect';
  }
  function picturePayloads(bytes) {
    if (!bytes) return [];
    return parseRecords(bytes).map((record) => {
      const payload = record.data.subarray(17);
      if (payload[0] === 0x89 && payload[1] === 0x50 && payload[2] === 0x4E && payload[3] === 0x47) return { bytes: payload, mime: 'image/png', ext: 'png' };
      if (payload[0] === 0xFF && payload[1] === 0xD8) return { bytes: payload, mime: 'image/jpeg', ext: 'jpg' };
      if (payload[0] === 0x42 && payload[1] === 0x4D) return { bytes: payload, mime: 'image/bmp', ext: 'bmp' };
      if (payload[0] === 0xD7 && payload[1] === 0xCD) return { bytes: payload, mime: 'image/wmf', ext: 'wmf' };
      if (payload[0] === 0x01 && payload[1] === 0x00 && payload[2] === 0x00 && payload[3] === 0x00) return { bytes: payload, mime: 'image/emf', ext: 'emf' };
      return null;
    }).filter(Boolean);
  }
  function fontEntities(record) {
    return recordsOf(record, 0x0FBA).map((font) => utf16(font.data).replace(/\u0000/g, '').trim())
      .filter((name) => name && !name.startsWith('___PPT'));
  }
  function persistInfo(records) {
    const directory = records.find((record) => record.type === 6002);
    const userEdit = records.slice().reverse().find((record) => record.type === 4085);
    if (!directory) return { directoryEntries: 0, userEdit: false };
    const entries = [];
    for (let offset = 0; offset + 4 <= directory.data.length;) {
      const packed = u32(directory.data, offset);
      const count = packed >>> 20;
      if (!count || count > 4096 || offset + 4 + count * 4 > directory.data.length) break;
      for (let index = 0; index < count; index += 1) entries.push(u32(directory.data, offset + 4 + index * 4));
      offset += 4 + count * 4;
    }
    return { directoryEntries: entries.length, userEdit: !!userEdit };
  }
  function currentUserInfo(bytes) {
    return { present: !!bytes, declaredLength: bytes && bytes.length >= 4 ? u32(bytes, 0) : 0 };
  }
  function dataUrl(payload) {
    if (!payload || typeof global.btoa !== 'function') return '';
    let binary = '';
    for (let offset = 0; offset < payload.bytes.length; offset += 0x8000) {
      binary += String.fromCharCode(...payload.bytes.subarray(offset, offset + 0x8000));
    }
    return 'data:' + payload.mime + ';base64,' + global.btoa(binary);
  }
  function artObjects(record, pictures, fonts, slideIndex) {
    const objects = [];
    const containers = recordsOf(record, 0xF004);
    containers.forEach((container, index) => {
      const children = childrenOf(container);
      const shape = children.find((child) => child.type === 0xF00A);
      const anchor = anchorOf(children.find((child) => child.type === 0xF010));
      if (!shape || !anchor || anchor.w <= 0 || anchor.h <= 0) return;
      const shapeType = shape.options >>> 4;
      const properties = officeArtProperties(children.find((child) => child.type === 0xF00B) || { options: 0, data: new Uint8Array() });
      const text = textOf(children.find((child) => child.type === 0xF00D));
      const base = { id: 'legacy-object-' + (slideIndex + 1) + '-' + (index + 1), x: Math.max(0, anchor.x), y: Math.max(0, anchor.y), w: anchor.w, h: anchor.h, z: index + 1, legacyShapeType: shapeType };
      const imageIndex = properties[0x0104] && properties[0x0104].value;
      if (shapeType === 75 && imageIndex && pictures[imageIndex - 1]) {
        const image = pictures[imageIndex - 1];
        objects.push({ ...base, type: 'image', src: dataUrl(image), ext: image.ext, cropZoom: 1, cropX: 50, cropY: 50, legacyImageIndex: imageIndex });
      } else if (text) {
        const fill = properties[0x0181] && color(properties[0x0181].value, 'transparent');
        const line = properties[0x01BF] && color(properties[0x01BF].value, '#70757d');
        objects.push({ ...base, type: 'text', text, font: fonts[0] || 'Arial', size: 24,
          color: '#20242a', align: 'left', fill: fill || 'transparent',
          line: line || 'transparent', lineWidth: 1, shape: shapeName(shapeType),
          legacyTextStyle: { font: fonts[0] || 'Arial', size: 24, align: 'left',
            bullets: text.split('\n').map(() => false) } });
      } else {
        const fill = properties[0x0181] && color(properties[0x0181].value, '#ffffff');
        const line = properties[0x01BF] && color(properties[0x01BF].value, '#70757d');
        objects.push({ ...base, type: 'shape', shape: shapeName(shapeType), fill: fill || '#ffffff', line: line || '#70757d', lineWidth: 1 });
      }
    });
    return objects;
  }
  function parseSlide(record, index, pictures, fonts) {
    const objects = artObjects(record, pictures, fonts, index);
    const title = objects.find((object) => object.type === 'text' && object.text.trim());
    return { id: 'legacy-slide-' + (index + 1),
      title: title ? title.text.split('\n')[0] : 'Slide ' + (index + 1),
      background: '#ffffff', objects, notes: '',
      compatibilityWarnings: ['Legacy drawing fidelity is partial; unsupported records were skipped.'] };
  }
  function importLegacyPpt(buffer, fileName) {
    if (global.InkDeskRuntime) global.InkDeskRuntime.validateInputSize(buffer.byteLength, fileName);
    const documentStream = new CompoundFileReader(buffer).stream(PPT_DOCUMENT);
    if (!documentStream) throw new Error('The legacy PowerPoint document stream is missing.');
    const records = parseRecords(documentStream);
    const slideRecords = [];
    records.forEach((record) => collectSlides(record, slideRecords));
    const pictures = picturePayloads(new CompoundFileReader(buffer).stream('Pictures'));
    const fonts = [...new Set(fontEntities({ data: documentStream }))];
    const persistence = persistInfo(records);
    const currentUser = currentUserInfo(new CompoundFileReader(buffer).stream(CURRENT_USER));
    const slides = slideRecords.map((record, index) => parseSlide(record, index, pictures, fonts));
    if (!slides.length) throw new Error('No legacy PowerPoint slides could be decoded.');
    return {
      name: String(fileName || 'Presentation.ppt').replace(/\.ppt$/i, ''),
      width: 9144000,
      height: 6858000,
      source: 'ppt',
      theme: { fonts: { majorLatin: 'Arial', minorLatin: 'Arial' }, colors: { accent1: '#d64a24', dk1: '#000000', lt1: '#ffffff' } },
      compatibility: { engine: '0.21.0-legacy-ppt-fidelity', legacyPptImport: true,
        textEditable: true, saveAsPptx: true, legacyDrawingFidelity: 'partial',
        persistedVersionSelection: false,
        masterCount: records.filter((record) => record.type === 0x03F0).length },
      legacyDiagnostics: { slideContainers: slideRecords.length,
        shapeCount: slides.reduce((total, slide) => total + slide.objects.filter((object) => object.type === 'shape').length, 0),
        textObjectCount: slides.reduce((total, slide) => total + slide.objects.filter((object) => object.type === 'text').length, 0),
        imageCount: slides.reduce((total, slide) => total + slide.objects.filter((object) => object.type === 'image').length, 0),
        pictureCount: pictures.length, notesCount: 0, officeArt: true, fonts,
        masterCount: records.filter((record) => record.type === 0x03F0).length,
        currentUser, persistedDirectoryAtom: PERSIST_DIRECTORY,
        persistedDirectoryEntries: persistence.directoryEntries, userEditAtom: persistence.userEdit },
      originalSlideRids: [],
      slides,
    };
  }

  global.InkDeskPresentationsPptImport = { importLegacyPpt };
})(window);
