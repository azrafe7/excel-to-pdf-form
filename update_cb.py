from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject, NumberObject, TextStringObject, DictionaryObject, StreamObject, ArrayObject
import fitz
from io import BytesIO
import pprint

# INPUT = r'c:\az_dev\UPWORK\excel-to-pdf-form.git\Blank K-1_flattened.pdf'
INPUT = r'c:\az_dev\UPWORK\excel-to-pdf-form.git\output2.pdf'
OUTPUT = "output.pdf"

class CustomPdfWriter(PdfWriter):

    def flatten_form_fields(self):
        """
        Flattens the form fields in the PDF, making them part of the content and non-editable.
        """
        for page in self.pages:
            if "/Annots" in page:
                annotations = page["/Annots"]
                new_annotations = ArrayObject()
                for annotation in annotations:
                    if annotation.get_object().get("/Subtype") == "/Widget":
                        field = annotation.get_object()
                        field_value = field.get("/V")
                        breakpoint()
                        if field_value:
                            self.add_field_value_to_content(page, field)
                    else:
                        new_annotations.append(annotation)
                page[NameObject("/Annots")] = new_annotations

    def add_field_value_to_content(self, page, field):
        """
        Adds the value of a form field to the page content.
        """
        field_value = field.get("/V")
        rect = field.get("/Rect")
        if field_value and rect:
            x0, y0, x1, y1 = rect

            # Handle different field types
            field_type = field.get("/FT")
            if field_type == "/Tx":  # Text field
                self.add_text_field_value(page, field, field_value, rect)
            else:
                print("Handle other elements here")

    def add_text_field_value(self, page, field, field_value, rect):
        """
        Adds the value of a text field to the page content.
        """
        x0, y0, x1, y1 = rect
        font_size = self.get_font_size(field)
        font_name = self.get_font_name(field)

        # Calculate the position to center the text within the box
        text_width = len(field_value) * font_size * 0.5  # Approximate text width
        text_height = font_size
        text_x = x0 + (x1 - x0 - text_width) / 2
        text_y = y0 + (y1 - y0 - text_height) / 2

        # Create a PDF content stream with the field value
        content = f"BT /{font_name} {font_size} Tf {text_x} {text_y} Td ({field_value}) Tj ET"

        # Create a StreamObject to hold the appearance stream
        appearance_stream = StreamObject()
        appearance_stream._data = content.encode("latin1")
        appearance_stream.update({
            NameObject("/Type"): NameObject("/XObject"),
            NameObject("/Subtype"): NameObject("/Form"),
            NameObject("/BBox"): rect,
            NameObject("/Resources"): DictionaryObject({
                NameObject("/Font"): DictionaryObject({
                    NameObject(f"/{font_name}"): DictionaryObject({
                        NameObject("/Type"): NameObject("/Font"),
                        NameObject("/Subtype"): NameObject("/Type1"),
                        NameObject("/BaseFont"): NameObject("/{font_name}")
                    })
                })
            })
        })

        # Add the appearance stream to the page content
        self.merge_stream_to_page(page, appearance_stream)

    def get_font_size(self, field):
        """
        Retrieves the font size from the field's appearance stream.
        """
        da = field.get("/DA")
        if da:
            da_parts = da.split()
            for i, part in enumerate(da_parts):
                if part == "Tf":
                    return float(da_parts[i - 1])
        return 12  # Default font size

    def get_font_name(self, field):
        """
        Retrieves the font name from the field's appearance stream.
        """
        da = field.get("/DA")
        if da:
            da_parts = da.split()
            for i, part in enumerate(da_parts):
                if part == "Tf":
                    return da_parts[i - 2][1:]  # Remove the leading slash
        return "F1"  # Default font name

    def merge_stream_to_page(self, page, stream):
        """
        Merges a StreamObject into the page's content.
        """
        page_content = page.get("/Contents")
        if isinstance(page_content, ArrayObject):
            page_content.append(stream)
        else:
            new_content = ArrayObject()
            if page_content:
                new_content.append(page_content)
            new_content.append(stream)
            page[NameObject("/Contents")] = new_content
            
            
if __name__ == '__main__':
    pdf_reader = PdfReader(INPUT)
    pdf_writer = PdfWriter()
    pdf_writer.clone_reader_document_root(pdf_reader)
    
    fields = pdf_reader.get_fields()
    # breakpoint()
    cb_fields = [field for field in fields if fields[field].get("/FT") == "/Btn"]
    # breakpoint()
    value = True
    for page in pdf_writer.pages:
        pdf_writer.set_need_appearances_writer(True)
        pdf_writer.update_page_form_field_values(page, {"partner_id": "1111 asd a", "info": "asafsd asdf sa"}, auto_regenerate=False)
        for cb in cb_fields:
            # breakpoint()
            cb_values = fields[cb].get("/_States_")
            cb_value_idx = 1 - int(value)
            pdf_writer.update_page_form_field_values(page, {cb: cb_values[cb_value_idx]}, auto_regenerate=False)

            # make read-only
            # annotations = [annotation for annotation in page.annotations if annotation == cb]
            #annotations = page.annotations
            #for annotation in annotations:
            #    # breakpoint()
            #    annotation.update({
            #        NameObject("/Ff"): NumberObject(1)
            #    })

    # Flatten form fields
    # pdf_writer.flatten_form_fields()

    # Flatten form fields using pymupdf
    bytes = BytesIO()
    pdf_writer.write(bytes)
    doc = fitz.open(stream=bytes)
    flattened_bytes = doc.convert_to_pdf()
    flattened_doc = fitz.open(stream=flattened_bytes)
    flattened_doc.save(OUTPUT)

    # pdf_writer.write(OUTPUT)
