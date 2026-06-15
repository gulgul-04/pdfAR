# Intelligent PDF Annotation Restorer (pdfAR)

An enterprise-grade, full-stack application designed to solve the notorious problem of lost PDF comments during document revisions. 

When a heavily annotated PDF is converted to Word, edited, and exported back to PDF, all XFDF coordinate-based annotations are permanently lost or misplaced due to text reflow. **pdfAR** shifts the paradigm from coordinate-based tracking to semantic content anchoring, ensuring comments are preserved and intelligently relocated regardless of layout shifts, paragraph reflows, or pagination changes.

##  Core Features

* **Semantic Anchor Engine:** Extracts not just the annotation, but the surrounding contextual text, creating a unique "fingerprint" for every comment.
* **Fuzzy Logic Matching:** Utilizes Levenshtein distance string matching to locate where the referenced text moved in the newly edited document.
* **Confidence Scoring Engine:** Assigns a reliability score (0-100%) to every relocated comment. High-confidence matches are automatically injected; low-confidence matches are flagged to prevent data corruption.
* **Zero-Data-Retention Architecture:** Designed for sensitive legal and corporate documents. Processing happens entirely in ephemeral memory, ensuring total data privacy.

##  Technology Stack

* **Backend:** Python, FastAPI, PyMuPDF (`fitz`), RapidFuzz
* **Frontend:** React, Vite, Tailwind CSS
* **Deployment:** Local-first architecture for maximum privacy

##  Architecture Overview

The application strictly decouples the heavy PDF parsing engine from the user interface:
1.  `backend/`: A standalone FastAPI service containing the extraction, string-matching, and injection pipelines. 
2.  `frontend/`: A modern, responsive React dashboard where users upload documents and review the "Needs Review" dashboard for low-confidence annotations.