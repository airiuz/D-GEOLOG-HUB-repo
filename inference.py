import glob, json
from deploy import PDFparser

parser = PDFparser()
pdfs, pdf = None, "mcuz_6685389127332.pdf"

def inference(pdf):
    RESULT = parser.process_pdf(pdf)
    result = RESULT["result"]
    print(result)
    with open(f'media-files/JSON/{pdf[5:-4]}.json', 'w') as json_file:
        json.dump(result, json_file, indent=4, ensure_ascii=False)

if pdfs: 
    for file in sorted(glob.glob(pdfs)): 
        inference(file)

elif pdf: 
    inference(pdf)    

    