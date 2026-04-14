#!/usr/bin/env python3
import sys
import json
from pathlib import Path

def extract_metadata(pdf_path):
    try:
        import PyPDF2
        
        with open(pdf_path, 'rb') as file:
            pdf = PyPDF2.PdfReader(file)
            info = pdf.metadata if pdf.metadata else {}
            
            metadata = {
                "filename": Path(pdf_path).name,
                "title": info.get("/Title", "") or Path(pdf_path).stem,
                "author": info.get("/Author", ""),
                "pages": len(pdf.pages)
            }
            
            return metadata
            
    except Exception as e:
        return {"error": str(e), "filename": Path(pdf_path).name}

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python extract_metadata.py <pdf_path>")
        sys.exit(1)
    
    metadata = extract_metadata(sys.argv[1])
    print(json.dumps(metadata, indent=2, ensure_ascii=False))
