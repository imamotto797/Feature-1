"""
PDF text extraction utilities.

Uses PyMuPDF (fitz) for fast, reliable text extraction from born-digital
PDFs. PyMuPDF outperforms most pure-Python alternatives in both speed and
accuracy for standard CV documents.
"""

import fitz  # PyMuPDF
from fastapi import HTTPException, UploadFile


async def extract_text_from_pdf(file: UploadFile) -> str:
    """
    Read an uploaded PDF file and return all extractable text.

    Parameters
    ----------
    file : UploadFile
        The PDF file uploaded via multipart/form-data.

    Returns
    -------
    str
        Concatenated plain text from every page.

    Raises
    ------
    HTTPException
        400 – if the file is not a valid PDF or contains no extractable text.
    """
    # --- 1. Validate content type -----------------------------------------
    if file.content_type not in ("application/pdf", "application/x-pdf"):
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is not a PDF. "
            "Please provide a file with content-type application/pdf.",
        )

    # --- 2. Read the raw bytes --------------------------------------------
    try:
        pdf_bytes: bytes = await file.read()
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Could not read uploaded file: {exc}",
        ) from exc

    # --- 3. Open the PDF with PyMuPDF -------------------------------------
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail="The uploaded file could not be parsed as a PDF. "
            "It may be corrupted or password-protected.",
        ) from exc

    # --- 4. Extract text page by page -------------------------------------
    try:
        full_text: str = ""
        for page in doc:  # iterate over every page
            full_text += page.get_text()  # plain-text extraction
        doc.close()
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while extracting text: {exc}",
        ) from exc

    # --- 5. Guard against empty / image-only PDFs -------------------------
    if not full_text.strip():
        raise HTTPException(
            status_code=400,
            detail="No extractable text found in the PDF. "
            "The document may consist only of images (scanned CV).",
        )

    return full_text