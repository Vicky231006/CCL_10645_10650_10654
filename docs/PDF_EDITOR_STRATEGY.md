# Resumo — PDF Editing Strategy

The prompt asks for two related capabilities:
1. After AI suggests changes, export a **new PDF** directly (e.g. "use this JD keyword / reworded bullet").
2. A **PDF editor interface** where the user edits the resume *in the browser* and it exports properly.

## The core problem
Arbitrary PDFs are a fixed-layout print format. They do **not** contain editable semantics. Attempting
free-text editing of raw PDF bytes (à la a generic PDF editor) reliably produces:
- broken text reflow and overlapping glyphs,
- destroyed text-selection / copy-paste,
- unparseable output for ATS systems (the exact audience Resumo serves).

Editing the PDF *binary* is therefore the wrong layer. The correct layer is the **structured resume model**.

## Chosen strategy: structured edit → deterministic re-render
```
upload (any format) ─► parse ─► editable structured model ─► live preview
                                        │                        │
                                        │                  (looks like a PDF)
                                        ▼
                             one-click re-export  ─►  PDF / DOCX / LaTeX / TXT
```

- The resume is stored as structured JSON (`ResumeContent`) + typed `ResumeSection` rows.
- The **in-browser editor** edits those fields directly (contenteditable-like inline editing over a
  page-accurate preview). What the user sees is a faithful A4/US-Letter rendering of the Jake's-template
  layout; what they edit is real data.
- Export renders the *current* model with `reportlab` (PDF), `python-docx` (DOCX), a Jinja/format string
  (LaTeX, matching jakegut/resume structure), and plain text (ATS-safe).
- Because export is deterministic and always from the model, **AI-approved changes flow straight into a
  new PDF** through the same pipeline — satisfying requirement (1) with zero extra machinery.

### Why this is better than pixel editing
- Preserves selectable text, hyperlinks, consistent spacing and ATS readability by construction.
- Undo/redo, autosave, version history, and section reordering all operate on data, not pixels.
- The same source produces PDF, DOCX, LaTeX and TXT in perfect agreement.

## "Free edit" mode (approved posture)
For users who genuinely need freeform placement, the editor supports:
- per-section reordering and hide/restore,
- bullet add/edit/remove/reorder,
- font-scale, page-size (A4 default, US Letter), and margin controls,
- a "notes to self" pane stored separately from exported content.

These controls are mapped to model fields, so they remain exportable and ATS-safe. They are deliberately
**bounded** — Resumo is not a desktop publishing tool, and unbounded formatting is what breaks ATS parsing.

## Limits (documented honestly)
- Scanned/image PDFs are OCR'd (when `pytesseract`/Tesseract is installed) and the *extracted text* is
  editable; the original scan image itself is not pixel-editable.
- If the Tesseract binary is not installed, Resumo reports that OCR is unavailable rather than pretending.
- Legacy `.doc` conversion requires LibreOffice/`antiword`; when absent, Resumo reports the limitation and
  still accepts `.docx`.
