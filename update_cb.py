from pypdf import PdfReader, PdfWriter
from io import BytesIO

# INPUT = r'c:\az_dev\UPWORK\excel-to-pdf-form.git\Blank K-1_flattened.pdf'
INPUT = r'c:\az_dev\UPWORK\excel-to-pdf-form.git\output2.pdf'
OUTPUT = "output.pdf"

if __name__ == '__main__':
    pdf_reader = PdfReader(INPUT)
    pdf_writer = PdfWriter()
    pdf_writer.clone_reader_document_root(pdf_reader)
    
    fields = pdf_reader.get_fields()
    breakpoint()
    cb_fields = [field for field in fields if fields[field].get("/FT") == "/Btn"]
    breakpoint()
    value = False
    for page in pdf_writer.pages:
        for cb in cb_fields:
            breakpoint()
            cb_values = fields[cb].get("/_States_")
            cb_value_idx = 1 - int(value)
            pdf_writer.update_page_form_field_values(page, {cb: cb_values[cb_value_idx]}, auto_regenerate=False)
    
    pdf_writer.write(OUTPUT)    
    