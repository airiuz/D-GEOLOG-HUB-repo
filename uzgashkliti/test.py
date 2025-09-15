# from uzgashkliti.utils.converters.json2docx import Json2Docx
# import json

# path = "media-files/JSON/output.json"


# with open(path, 'r') as f:
#     data = json.load(f)

# json2docx = Json2Docx()

# docx_bytes = json2docx.generate_docx(data)

# with open("output.docx", "wb") as f:
#     f.write(docx_bytes) 




import os, sys


sys.path.insert(0, os.path.dirname(os.getcwd()))

from deploy import PDFparser

parser = PDFparser()
pdf_path = "/home/wsmsi4090/FOZILJON/UZGASHKLITI/media-files/private/files/2a5d068f-7e11-4e09-a982-07fd762a39c5.pdf"
result = parser.process_pdf(pdf_path)
print('result')

print(result)
