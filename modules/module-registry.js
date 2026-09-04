(function(global){
'use strict';
const registry={
  "schemaVersion": 1,
  "registryVersion": "1.0.0-beta.2",
  "modules": [
    {
      "schemaVersion": 1,
      "id": "documents",
      "name": "Documents",
      "description": "Create, edit and save DOCX copies locally.",
      "version": "1.0.0-beta.1",
      "enabled": true,
      "optional": false,
      "order": 10,
      "entryPoint": "apps/documents/index.html",
      "icon": "assets/icons/documents.png",
      "badge": "D",
      "themeClass": "documents",
      "accent": "#2f6fed",
      "extensions": [
        "docx"
      ],
      "mimeTypes": [
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
      ],
      "capabilities": [
        "open",
        "new",
        "edit-basic",
        "copy-export",
        "section-aware-layout",
        "local-recovery-snapshots",
        "local-processing"
      ]
    },
    {
      "schemaVersion": 1,
      "id": "spreadsheets",
      "name": "Spreadsheets",
      "description": "Edit XLSX files locally and open legacy XLS workbooks.",
      "version": "1.0.0-beta.1",
      "enabled": true,
      "optional": false,
      "order": 20,
      "entryPoint": "apps/spreadsheets/index.html",
      "icon": "assets/icons/spreadsheets.png",
      "badge": "S",
      "themeClass": "spreadsheets",
      "accent": "#267a45",
      "extensions": [
        "xls",
        "xlsx"
      ],
      "mimeTypes": [
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
      ],
      "capabilities": [
        "open",
        "new",
        "edit-basic",
        "copy-export",
        "xls-import",
        "formula-preview",
        "local-recovery-snapshots",
        "local-processing"
      ]
    },
    {
      "schemaVersion": 1,
      "id": "presentations",
      "name": "Presentations",
      "description": "Create, edit and present PPT and PPTX files locally.",
      "version": "1.0.0-beta.1",
      "enabled": true,
      "optional": false,
      "order": 30,
      "entryPoint": "apps/presentations/index.html",
      "icon": "assets/icons/presentations.png",
      "badge": "P",
      "themeClass": "presentations",
      "accent": "#d64a24",
      "extensions": [
        "ppt",
        "pptx"
      ],
      "mimeTypes": [
        "application/vnd.ms-powerpoint",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation"
      ],
      "capabilities": [
        "open",
        "new",
        "edit-basic",
        "copy-export",
        "presentation-mode",
        "local-recovery-snapshots",
        "local-processing"
      ]
    },
    {
      "schemaVersion": 1,
      "id": "pdf",
      "name": "PDF Workspace",
      "description": "Read, navigate and review PDF files locally.",
      "version": "1.0.0-beta.1",
      "enabled": true,
      "optional": false,
      "order": 40,
      "entryPoint": "apps/pdf/index.html",
      "icon": "assets/icons/pdf.png",
      "badge": "PDF",
      "themeClass": "pdf",
      "accent": "#b42318",
      "extensions": [
        "pdf"
      ],
      "mimeTypes": [
        "application/pdf"
      ],
      "capabilities": [
        "open",
        "view",
        "forms",
        "navigation",
        "review-sidecar",
        "local-processing"
      ]
    },
    {
      "schemaVersion": 1,
      "id": "txt",
      "name": "Plain Text",
      "description": "Write and edit plain-text files locally.",
      "version": "1.0.0-beta.1",
      "enabled": true,
      "optional": true,
      "order": 50,
      "entryPoint": "apps/txt/index.html",
      "icon": "assets/icons/txt.png",
      "badge": "TXT",
      "themeClass": "txt",
      "accent": "#d9a514",
      "extensions": [
        "txt"
      ],
      "mimeTypes": [
        "text/plain"
      ],
      "capabilities": [
        "open",
        "new",
        "edit-basic",
        "copy-export",
        "find",
        "word-wrap",
        "font-size",
        "editable-file-title",
        "unsaved-change-navigation-warning",
        "local-processing"
      ]
    },
    {
      "schemaVersion": 1,
      "id": "epub",
      "name": "EPUB Reader",
      "description": "Read local EPUB books with pages, themes and contents.",
      "version": "1.0.0-beta.1",
      "enabled": true,
      "optional": true,
      "order": 60,
      "entryPoint": "apps/epub/index.html",
      "icon": "assets/icons/epub.png",
      "badge": "EPUB",
      "themeClass": "epub",
      "accent": "#7655c7",
      "extensions": [
        "epub"
      ],
      "mimeTypes": [
        "application/epub+zip"
      ],
      "capabilities": [
        "open",
        "read-only",
        "copy-export",
        "lateral-pagination",
        "font-size",
        "reading-themes",
        "table-of-contents",
        "simple-images",
        "editable-file-title",
        "unsaved-change-navigation-warning",
        "local-processing"
      ]
    }
  ],
  "missingModules": []
};
global.InkDeskModuleRegistry=Object.freeze(registry);
})(typeof window!=='undefined'?window:globalThis);
