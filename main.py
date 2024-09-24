from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel
import pandas as pd
from pypdf import PdfReader, PdfWriter
from io import BytesIO
import tempfile
import os

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

@app.post("/process")
async def process_files(excel_file: UploadFile = File(...), pdf_file: UploadFile = File(...)):
    try:
        # Read Excel file
        excel_content = await excel_file.read()
        df = pd.read_excel(BytesIO(excel_content), engine="openpyxl")
        
        # Read PDF form
        pdf_content = await pdf_file.read()
        pdf_reader = PdfReader(BytesIO(pdf_content))
        
        # Process only the first row of the Excel file
        if len(df) > 0:
            row = df.iloc[0]
            
            pdf_writer = PdfWriter()
            
            # Clone the document root from the original PDF
            pdf_writer.clone_reader_document_root(pdf_reader)
            
            # Fill form fields
            breakpoint()
            for field_name, field_value in row.items():
                if field_name in pdf_reader.get_fields():
                    pdf_writer.update_page_form_field_values(
                        pdf_writer.pages[0], {field_name: str(field_value)}
                    )
            
            # Save filled PDF to BytesIO object
            output_pdf = BytesIO()
            pdf_writer.write(output_pdf)
            output_pdf.seek(0)
            
            # Return the filled PDF as a downloadable file
            return StreamingResponse(
                output_pdf,
                media_type="application/pdf",
                headers={"Content-Disposition": f"attachment; filename=filled_form.pdf"}
            )
        else:
            raise HTTPException(status_code=400, detail="Excel file is empty")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)