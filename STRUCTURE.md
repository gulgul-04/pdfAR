# pdfAR Architecture & File Structure

This document outlines the full-stack architecture of the pdfAR application, an enterprise-grade PDF annotation restoration tool. The system strictly separates a high-performance Python/FastAPI backend from a modern React/Vite frontend.

## Directory Tree

pdfAR/
├── .gitignore
├── README.md
├── STRUCTURE.md
│
├── backend/                       # Python Backend (Data Processing & API)
│   ├── requirements.txt
│   ├── venv/                      # Isolated Python environment
│   ├── main.py                    # FastAPI application and route definitions
│   ├── test_docs/                 # Local sandbox for PDF testing (Git Ignored)
│   │
│   └── engine/                    # Core PDF Processing Logic
│       ├── __init__.py
│       ├── config.py              # Centralized thresholds (Confidence scores, pixel tolerances)
│       ├── schema.py              # Pydantic models for FastAPI Request/Response validation
│       ├── file_handler.py        # Manages asynchronous OS-level file I/O
│       ├── geometry.py            # Spatial math: bounding boxes, rotation matrices, intersections
│       ├── extractor.py           # PyMuPDF: Extracts annotations, context, and metadata
│       ├── matcher.py             # RapidFuzz: Calculates string similarity and confidence
│       ├── injector.py            # PyMuPDF: Re-inserts and positions annotations
│       └── utils.py               # Text sanitization and general helper functions
│
└── frontend/                      # React/Vite Frontend (User Interface)
    ├── package.json
    ├── vite.config.js
    ├── tailwind.config.js
    ├── postcss.config.js
    ├── index.html
    │
    └── src/
        ├── main.jsx               # React entry point
        ├── index.css              # Tailwind directives
        ├── App.jsx                # Main application routing and state
        ├── components/            # Reusable UI widgets (Upload Area, Review Dashboard)
        └── assets/                # Static images and icons

## Module Responsibilities

### Backend Engine
* **`extractor.py`**: Reads the Original PDF. Identifies annotations, unwraps threaded replies, applies derotation matrices, and extracts semantic text anchors.
* **`matcher.py`**: Searches the Edited PDF. Utilizes fuzzy string matching (`RapidFuzz`) and context windows to locate moved text, scoring matches via the Confidence Engine.
* **`injector.py`**: Writes to the Edited PDF. Recalculates coordinates based on matched text or geometric offsets and embeds comments while preserving metadata.
* **`geometry.py`**: Offloads coordinate mathematics. Handles relative spatial anchoring, element proximity sorting, and table/image intersection logic.
* **`schema.py`**: Defines the strict API contracts for data entering and exiting the FastAPI layer.

### System Flow
1. **Upload:** Client uploads Original and Edited PDFs via the React UI.
2. **API Request:** Frontend posts files to the `/api/process` FastAPI endpoint.
3. **Extraction:** `extractor.py` parses the original document and builds the annotation dataset.
4. **Matching:** `matcher.py` analyzes the new document to find the new anchor locations.
5. **Validation:** FastAPI validates the output against `schema.py`.
6. **Review:** Low-confidence matches (< 80%) are returned to the React UI for manual user adjustment.
7. **Injection:** Confirmed matches are written into the final PDF via `injector.py`, and the file is returned for download.