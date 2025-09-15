import pytesseract
import numpy as np
import time, cv2, fitz
from PIL import Image

def rotation(image):
    try:
        osd = pytesseract.image_to_osd(image, output_type=pytesseract.Output.DICT)
        rotation = osd["rotate"]
    except:
        rotation = 0
    
    if rotation != 0:
        rotated_image = image.rotate(-rotation, resample=Image.BICUBIC, expand=True)
        return rotated_image
    return image

class Preprocessing:
    def __init__(self):
        pass
        
    def PDF2IMAGE(self, pdf):
        images = []
        doc = fitz.open(pdf)
        pixel = 2000

        for page_number in range(doc.page_count):
            page = doc.load_page(page_number)
            width, height = page.rect.width, page.rect.height
            zoom = pixel / max(width, height)
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)
            img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)

            if pix.n == 3: img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
            elif pix.n == 4: img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
                
            images.append(img)
        return images

    def run(self, pdf):       
        PAGES = []
        start = time.time()
        images = self.PDF2IMAGE(pdf)
        
        batch_size = 1
        batches = [images[i:i + batch_size] for i in range(0, len(images), batch_size)]
        
        for batch in batches:
            for img in batch:
                rotated_image = rotation(Image.fromarray(img))
                prep_image = cv2.cvtColor(np.array(rotated_image), cv2.COLOR_BGR2RGB)
                PAGES.append(Image.fromarray(prep_image))
                
        total_time = round(time.time() - start, 3)
        return PAGES, total_time