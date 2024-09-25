from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
import pandas as pd
from pypdf import PdfReader, PdfWriter
import fitz
from io import BytesIO
import zipfile
from typing import Dict, List, Optional

import logging
log = logging.getLogger("uvicorn")
log.setLevel(logging.DEBUG)
 
app = FastAPI()

class ProcessRequest(BaseModel):
    excel_file: UploadFile
    pdf_file: UploadFile

@app.get("/")
async def root():
    return {"message": "Server running"}

@app.get("/test")
async def test_page():
    return FileResponse('index.html')

class FieldMapping:
    def __init__(self):
        self.mapping: Dict[str, List[str]] = {}

    def add_field(self, pdf_field: str, excel_columns: List[str]):
        self.mapping[pdf_field] = excel_columns

    def get_mapping(self) -> Dict[str, List[str]]:
        return self.mapping

@app.post("/process")
async def process_files(excel_file: UploadFile = File(...), pdf_file: UploadFile = File(...)):
    try:
        # Read Excel file
        excel_content = await excel_file.read()
        df = pd.read_excel(BytesIO(excel_content), engine="openpyxl")
        
        # Read PDF form
        pdf_content = await pdf_file.read()
        pdf_reader = PdfReader(BytesIO(pdf_content))
        
        # Get the default field mapping
        field_mapping = FieldMapping()
        for col in df.columns:
            field_mapping.add_field(col, [col])
            
        # Add custom fields mapping
        field_mapping.add_field("info", ["name", "address", "city", "state", "zip_code"])
        
        mapping = field_mapping.get_mapping()
        
        # Process each row in the Excel file
        output_pdfs = []
        for index, row in df.iterrows():
            pdf_writer = PdfWriter()
            pdf_writer.clone_reader_document_root(pdf_reader)
            
            # Fill form fields
            # breakpoint()
            fields = pdf_writer.get_fields()
            for pdf_field, excel_columns in mapping.items():
                for page in pdf_writer.pages:
                    if pdf_field in fields:
                        is_checkbox = fields[pdf_field].get("/Type") == "/Btn" or fields[pdf_field].get("/FT") == "/Btn"
                        if is_checkbox:
                            # Handle checkbox fields
                            field_value = any(row[col] == 1 or str(row[col]).lower() == "true" or str(row[col]).lower() == "yes" for col in excel_columns)
                            cb_values = fields[pdf_field].get("/_States_")
                            cb_value_idx = 1 - int(field_value)
                            if field_value:
                                pdf_writer.update_page_form_field_values(page, {pdf_field: cb_values[cb_value_idx]})
                            else:
                                pdf_writer.update_page_form_field_values(page, {pdf_field: cb_values[-1]})
                        else:
                            # Handle other fields
                            field_value = ", ".join(str(row[col]) for col in excel_columns)
                            pdf_writer.update_page_form_field_values(
                                page, {pdf_field: field_value}
                            )
                    else:
                        print(f"Field '{pdf_field}' not found in the PDF form.")
            
            # Save filled and flattened PDF to BytesIO object
            output_pdf = BytesIO()
            pdf_writer.write(output_pdf)
            doc = fitz.open(stream=output_pdf)
            flattened_bytes = BytesIO(doc.convert_to_pdf())
            flattened_bytes.seek(0)
            output_pdfs.append(flattened_bytes)
        
        # Create a zip file containing all filled PDFs
        zip_filename = "filled_forms.zip"
        with zipfile.ZipFile(zip_filename, "w") as zip_file:
            for i, pdf_bytes in enumerate(output_pdfs):
                zip_file.writestr(f"filled_form_{i+1}.pdf", pdf_bytes.getvalue())
        
        print(f"Files processed. Downloading {zip_filename}...")
        return FileResponse(zip_filename, media_type="application/zip", filename=zip_filename)
    
    except Exception as e:
        error_detail = str(e)
        log.error(e)
        raise HTTPException(status_code=500, detail=f"An error occurred: {error_detail}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)