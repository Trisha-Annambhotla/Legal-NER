import json
import os
import spacy
from spacy.tokens import DocBin

nlp = spacy.blank("en")
TEXT_FOLDER = "extracted_text"


def load_text(file_id):
    file_number = file_id.split("_")[-1]

    for file in os.listdir(TEXT_FOLDER):
        if file.startswith(file_number + "."):
            print(f"Matched: {file}")
            with open(os.path.join(TEXT_FOLDER, file), "r", encoding="utf-8") as f:
                return f.read()

    print(f"No file for {file_id}")
    return ""


def find_spans(text, entity_text):
    spans = []
    start = 0

    while True:
        start = text.find(entity_text, start)
        if start == -1:
            break
        end = start + len(entity_text)
        spans.append((start, end))
        start = end

    return spans


def process_file(input_file):
    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    doc_bin = DocBin()
    rag_data = []

    for file_id, doc in data.items():
        print(f"\nProcessing {file_id}")

        full_text = load_text(file_id)
        print("Text length:", len(full_text))

        if not full_text:
            continue

        spacy_doc = nlp.make_doc(full_text)
        ents = []

        for ent in doc.get("entities", []):
            spans = find_spans(full_text, ent["text"])

            for start, end in spans:
                span = spacy_doc.char_span(start, end, label=ent["label"])
                if span:
                    ents.append(span)

        spacy_doc.ents = ents
        doc_bin.add(spacy_doc)

        rag_data.append({
            "file_no": file_id,
            "case_name": doc.get("case_title"),
            "structured": doc.get("structured", {})
        })

    print("\nTotal docs:", len(list(doc_bin.get_docs(nlp.vocab))))
    return doc_bin, rag_data


# -------- RUN -------- #
doc_bin, rag_output = process_file("master_annotations.json")

print("Saving files...")
doc_bin.to_disk("train.spacy")

with open("rag_data.json", "w", encoding="utf-8") as f:
    json.dump(rag_output, f, indent=2, ensure_ascii=False)

print("✅ Files created!")