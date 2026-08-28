#!/bin/bash
set -e

OUTPUT_DIR="output/survey_paper"
mkdir -p "$OUTPUT_DIR"

# Copy template files to output
if [ ! -f "$OUTPUT_DIR/main.tex" ]; then
    cp templates/survey/main.tex "$OUTPUT_DIR/"
fi

# Copy sections and bibliography
cp -r templates/survey/sections "$OUTPUT_DIR/" 2>/dev/null || true
cp templates/survey/figures "$OUTPUT_DIR/" 2>/dev/null || true

cd "$OUTPUT_DIR"

echo "First pdflatex run..."
pdflatex -interaction=nonstopmode main.tex || true

echo "Running bibtex..."
if [ -f bibliography.bib ]; then
    bibtex main || true
fi

echo "Second pdflatex run..."
pdflatex -interaction=nonstopmode main.tex || true

echo "Final pdflatex run..."
pdflatex -interaction=nonstopmode main.tex || true

echo "Compilation complete. PDF: $OUTPUT_DIR/main.pdf"
