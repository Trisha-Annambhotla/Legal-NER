import fitz  # PyMuPDF
import os
import re

INPUT_FOLDER = "judgements"
OUTPUT_FOLDER = "extracted_text"

os.makedirs(OUTPUT_FOLDER, exist_ok=True)


def clean_text(text):
    text = re.sub(r'\n+', '\n', text)              # remove extra newlines
    text = re.sub(r'Page\s*\d+', '', text)         # remove page numbers
    text = re.sub(r'\s+', ' ', text)               # normalize spaces
    return text.strip()


def extract_text_from_pdf(pdf_path):
    try:
        doc = fitz.open(pdf_path)
        full_text = ""

        for page_num, page in enumerate(doc):
            blocks = page.get_text("blocks")
            
            # Sort blocks: top-to-bottom, left-to-right
            blocks.sort(key=lambda b: (b[1], b[0]))

            page_text = ""
            for block in blocks:
                page_text += block[4] + "\n"

            full_text += f"\n\n--- PAGE {page_num + 1} ---\n\n"
            full_text += page_text

        return clean_text(full_text)

    except Exception as e:
        print(f"❌ Error processing {pdf_path}: {e}")
        return None


def main():
    files = os.listdir(INPUT_FOLDER)

    pdf_files = [f for f in files if f.lower().endswith(".pdf")]

    if not pdf_files:
        print("⚠️ No PDF files found in 'judgements' folder.")
        return

    print(f"📄 Found {len(pdf_files)} PDF(s)\n")

    for file in pdf_files:
        pdf_path = os.path.join(INPUT_FOLDER, file)
        print(f"🔄 Processing: {file}")

        text = extract_text_from_pdf(pdf_path)

        if text:
            output_file = os.path.join(
                OUTPUT_FOLDER, file.replace(".pdf", ".txt")
            )

            with open(output_file, "w", encoding="utf-8") as f:
                f.write(text)

            print(f"✅ Saved: {output_file}\n")
        else:
            print(f"⚠️ Skipped: {file}\n")


if __name__ == "__main__":
    main()