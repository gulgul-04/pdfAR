import fitz  # PyMuPDF
import os

def create_complex_test_suite():
    print("Generating Enterprise Stress-Test PDFs...")
    os.makedirs("test_docs", exist_ok=True)

    # =====================================================================
    # 1. GENERATE ORIGINAL PDF (3 Pages, 6 Annotation Types)
    # =====================================================================
    doc_orig = fitz.open()

    # --- PAGE 1: Highlights & Sticky Notes ---
    p1 = doc_orig.new_page()  # Create page right before using it
    p1.insert_text((50, 70), "SECTION 1: SYSTEM ARCHITECTURE", fontsize=16)
    
    text_hl = "The master architecture must be highly scalable and redundant."
    p1.insert_text((50, 100), text_hl, fontsize=12)
    rect_hl = p1.search_for("master architecture")[0]
    annot_hl = p1.add_highlight_annot(rect_hl)
    annot_hl.set_info({"title": "Lead Architect", "content": "Change this term to 'primary system'."})
    annot_hl.update()

    text_note = "All security protocols must be strictly enforced at the edge network."
    p1.insert_text((50, 150), text_note, fontsize=12)
    annot_note = p1.add_text_annot((30, 150), "Verify this against ISO 27001 guidelines.")
    annot_note.set_info({"title": "SecOps"})
    annot_note.update()

    # --- PAGE 2: Redactions & Square Shapes ---
    p2 = doc_orig.new_page()
    p2.insert_text((50, 70), "SECTION 2: CONFIDENTIAL DATA", fontsize=16)
    
    text_redact = "The acquisition target is Project Phoenix and will cost 40M."
    p2.insert_text((50, 100), text_redact, fontsize=12)
    rect_redact = p2.search_for("Project Phoenix")[0]
    annot_redact = p2.add_redact_annot(rect_redact)
    annot_redact.set_info({"title": "Legal Dept", "content": "Redact target name before external distribution."})
    annot_redact.update()

    text_sq = "TABLE 1: Q3 Financial Summary Review"
    p2.insert_text((50, 200), text_sq, fontsize=12)
    rect_sq = p2.search_for("TABLE 1: Q3 Financial Summary Review")[0]
    # Expand the bounding box slightly to act as a frame
    rect_sq_expanded = fitz.Rect(rect_sq.x0 - 10, rect_sq.y0 - 10, rect_sq.x1 + 10, rect_sq.y1 + 10)
    annot_sq = p2.add_rect_annot(rect_sq_expanded)
    annot_sq.set_info({"title": "Finance", "content": "Double check these Q3 figures."})
    annot_sq.update()

    # --- PAGE 3: FreeText & Caret Insertions ---
    p3 = doc_orig.new_page()
    p3.insert_text((50, 70), "SECTION 3: APPENDICES", fontsize=16)
    
    text_del = "This paragraph is deprecated and should be removed entirely in V2."
    p3.insert_text((50, 100), text_del, fontsize=12)
    rect_del = p3.search_for("deprecated")[0]
    annot_freetext = p3.add_freetext_annot(fitz.Rect(rect_del.x0, rect_del.y0 - 30, rect_del.x0 + 150, rect_del.y0 - 10), "Remove this paragraph!", fontsize=10)
    annot_freetext.set_info({"title": "Editor"})
    annot_freetext.update()

    text_caret = "Please insert the legal clause here for strict compliance."
    p3.insert_text((50, 200), text_caret, fontsize=12)
    rect_caret = p3.search_for("here")[0]
    annot_caret = p3.add_caret_annot(rect_caret.top_left)
    annot_caret.set_info({"title": "Legal Dept", "content": "Insert standard liability clause 4.2.1."})
    annot_caret.update()

    doc_orig.save("test_docs/original.pdf")
    doc_orig.close()
    print("✅ Created test_docs/original.pdf (3 Pages, 6 Annotations)")

    # =====================================================================
    # 2. GENERATE EDITED PDF (4 Pages, Massive Layout Shifts)
    # =====================================================================
    doc_edit = fitz.open()

    # --- EDITED PAGE 1: The Disrupter ---
    e1 = doc_edit.new_page()
    e1.insert_text((50, 70), "MASTER VENDOR AGREEMENT - REVISED 2026", fontsize=24)
    e1.insert_text((50, 150), "This massive new header page pushes all original content down to Page 2.", fontsize=12)

    # --- EDITED PAGE 2: Modified Text (Fuzzy Testing) ---
    e2 = doc_edit.new_page()
    e2.insert_text((50, 70), "SECTION 1: SYSTEM ARCHITECTURE", fontsize=16)
    # Changed "master architecture" to "primary system architecture"
    e2.insert_text((50, 100), "The primary system architecture must be highly scalable and redundant.", fontsize=12)
    # Moved way down the Y-axis
    e2.insert_text((50, 400), "All security protocols must be strictly enforced at the edge network.", fontsize=12)

    # --- EDITED PAGE 3: Context Shifts ---
    e3 = doc_edit.new_page()
    e3.insert_text((50, 70), "SECTION 2: CONFIDENTIAL DATA", fontsize=16)
    # Changed surrounding context, but "Project Phoenix" remains identical
    e3.insert_text((50, 100), "The upcoming acquisition target is Project Phoenix and will cost exactly 40M.", fontsize=12)
    # Shifted table down
    e3.insert_text((50, 300), "TABLE 1: Q3 Financial Summary Review", fontsize=12)

    # --- EDITED PAGE 4: Deletions & Insertions ---
    e4 = doc_edit.new_page()
    e4.insert_text((50, 70), "SECTION 3: APPENDICES", fontsize=16)
    
    # THE "DEPRECATED" PARAGRAPH IS COMPLETELY DELETED HERE.
    
    # Modified caret text slightly
    e4.insert_text((50, 150), "Please insert the updated legal clause here for strict operational compliance.", fontsize=12)

    doc_edit.save("test_docs/edited.pdf")
    doc_edit.close()
    print("✅ Created test_docs/edited.pdf (4 Pages, Shifted & Edited Layout)")

if __name__ == "__main__":
    create_complex_test_suite()