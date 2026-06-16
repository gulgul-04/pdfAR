import fitz
import os

def create_test_pdf():
    print("Generating test PDFs...")
    os.makedirs("test_docs", exists_ok=True)

    # 1. Geneerate Original PDF
    doc_orig = fitz.open()
    page_orig = doc_orig.new_page()

    # Insert text
    text1 = "The supplier shall deliver within 30 days."
    text2 = "This paragraph is irrelevant and will be deleted by the editor."
    text3 = "Here is a sentence to test the margin sticky note logic."

    page_orig.insert_text((50, 100), text1, fontsize=12)
    page_orig.insert_text((50, 150), text2, fontsize=12)
    page_orig.insert_text((50, 200), text3, fontsize=12)

    # Add a Highlight Annotation (Type 8)
    rects = page_orig.search_for("30 days")
    if rects:
        annot_hl = page_orig.add_highlight_annot(rects[0])
        annot_hl.set_info({"content": "Should this be 45?", "title": "Reviewer"})
        annot_hl.update()

    # Add a Sticky Note Annotation (Type 0)
    annot_note = page_orig.add_text_annot(fitz.Point(30, 200), "Make sure this stays in the new version.")
    annot_note.set_info({"title": "Reviewer"})
    annot_note.update()

    doc_orig.save("test_docs/original.pdf")
    doc_orig.close()
    print("✅ Created test_docs/original.pdf")

    doc_edit = fitz.open()
    page_edit = doc_edit.new_page()

    # Insert some new text at the top to force layout shifting
    page_edit.insert_text((50, 50), "NEW HEADER: Vendor Agreement", fontsize=16)

    # Modify text1 (30 -> 45) to test Fuzzy Matching
    page_edit.insert_text((50, 150), "The supplier shall deliver within 45 days.", fontsize=12)
    
    # Delete text2 entirely to test Confidence Routing (Fail state)
    
    # Move text3 way down the page to test layout shifting
    page_edit.insert_text((50, 400), "Here is a sentence to test the margin sticky note logic.", fontsize=12)

    doc_edit.save("test_docs/edited.pdf")
    doc_edit.close()
    print("✅ Created test_docs/edited.pdf")

if __name__ == "__main__":
    create_test_pdf()