import uuid, os, cv2, re, time, io, pytesseract, torch
import sys
import argparse

from img2table.ocr import TesseractOCR
from img2table.document import Image
from collections import defaultdict
from PIL import Image as PImage
import numpy as np
import torch
#from UniMERNet.demo import ImageProcessor
from unimernet.common.config import Config
import unimernet.tasks as tasks
from unimernet.processors import load_processor

class FormulaLatexPredictor:
    def __init__(self):
        FORMULA_CFG_PATH = os.path.join(os.getcwd(), "unimernet", "formula.yaml")
        cfg = Config(argparse.Namespace(cfg_path=FORMULA_CFG_PATH, options=None))
        task = tasks.setup_task(cfg)
        
        self.model = task.build_model(cfg).to("cuda:0" if torch.cuda.is_available() else "cpu")
        self.processor =  load_processor('formula_image_eval', cfg.config.datasets.formula_rec_eval.vis_processor.eval)

    def predict(self, raw_image):
        open_cv_image = np.array(raw_image)
        if len(open_cv_image.shape) == 3:
            open_cv_image = open_cv_image[:, :, ::-1].copy()

        image = self.processor(raw_image).unsqueeze(0).to("cuda:0" if torch.cuda.is_available() else "cpu")
        output = self.model.generate({"image": image})
        return output["pred_str"][0]

class Postprocessing:
    def __init__(self):
        self.docx_h = 1056
        self.docx_w = 816
        self.table_ocr = TesseractOCR(n_threads=2, lang="uzb_cyrl+rus+eng")
        self.formula2latex = FormulaLatexPredictor()

    def position(self, width, xmin, xmax):
        left, right = 3*width/25, 23*width/25
        if abs(left-xmin)<=abs(right-xmax): return "left"
        return "right"

    def collinear_by_Y(self, blok1, blok2):
        ymin1,ymax1 = blok1["box"]["ymin"],blok1["box"]["ymax"]
        ymin2,ymax2 = blok2["box"]["ymin"],blok2["box"]["ymax"]
        return ymin1<=(ymin2+ymax2)/2<=ymax1 or ymin2<=(ymin1+ymax1)/2<=ymax2

    def remove_blocks(self, dataset, blocks, footer):
        DATASET = []
        next_prior = False
        for i in range(len(dataset) - 1):
            if next_prior:
                next_prior=False
                continue
            item = dataset[i]
            next_item = dataset[i+1]
            if item["label"]=="left_block" and next_item["label"]=="right_block" and self.collinear_by_Y(item, next_item):
                ldata = blocks[item["ID"]]
                rdata = blocks[next_item["ID"]]
                if ldata[-1]["label"]=="paragraph" and rdata[-1]["label"]=="continued":
                    if ldata[-1]["src"].endswith("-"): ldata[-1]["src"] = ldata[-1]["src"][:-1]+rdata[0]["src"]
                    else: ldata[-1]["src"] = ldata[-1]["src"]+ " " +rdata[0]["src"]
                    rdata = rdata[1:]
                for data in ldata: DATASET.append(data)
                for data in rdata: DATASET.append(data)
                next_prior = True
            else:
                DATASET.append(item)
                next_prior = False
        if not next_prior:
            DATASET.append(dataset[-1])
        
        dataset = []
        for i in range(len(DATASET)):
            item = DATASET[i]
            if item["label"]=="left_block":
                ldata = blocks[item["ID"]]
                for data in ldata: dataset.append(data)
            
            elif item["label"]=="right_block":
                rdata = blocks[item["ID"]]
                for data in rdata:
                    data["position"] = "right"
                    dataset.append(data)
            else: dataset.append(item)

        dataset.extend(footer)
        return dataset
    
    def merger(self, data):
        filtered_items = []
        for i in range(len(data) - 1):
            item = data[i]
            if "enable" in item:
                if item["enable"] == False: continue
            else: item["enable"] = True
            next_item = data[i + 1]
            next_item["enable"] = True
            if item["label"] == "paragraph" and next_item["label"] == "continued":
                if item["src"].endswith("-"):
                    item["src"] = item["src"][:-1]+next_item["src"]
                else:
                    item["src"] = item["src"]+ " " +next_item["src"]
                    next_item["enable"] = False
            filtered_items.append(item)
        if data[-1]["enable"]==True:
            filtered_items.append(data[-1])
        dataset = [item for item in data if item["enable"]]
        dataset = [{k: v for k, v in item.items() if k != "enable"} for item in dataset]
        return dataset

    def extract_text(self, cropped_label, tess_config):
        ocr_data = pytesseract.image_to_data(cropped_label, config=tess_config, lang="uzb_cyrl+rus+eng", output_type=pytesseract.Output.DATAFRAME)
        filtered_data = ocr_data[(ocr_data['conf'] > 30) & (ocr_data['text'].notna())]
        lines = list(filtered_data.groupby('line_num')['text'].apply(lambda x: ' '.join(map(str, x))))
        return ' '.join(lines).replace('- ', '-')
        
    def text(self, layout):
        page = np.array(self.images[layout["page"]-1])
        cropped_label = page[layout["box"]["ymin"]:layout["box"]["ymax"], layout["box"]["xmin"]:layout["box"]["xmax"]]
        position, alignment, weight, style, size, tab_size = None, None, None, None, None, None
        if layout["label"] in ["title", "central", "caption"]:
            src = self.extract_text(cropped_label, f"--psm 6 --oem 3")
            if layout["label"]=="title": position, alignment, weight, style, size, tab_size, src = None, "center", "bold", "normal", 13, None, src.replace("(15С)", "(ISC)").replace("(MIC)", "(МГС)")
            elif layout["label"]=="central": position, alignment, weight, style, size, tab_size = None, "center", "normal", "normal", 13, None
            elif layout["label"]=="caption": position, alignment, weight, style, size, tab_size = self.position(page.shape[1], layout["box"]["xmin"], layout["box"]["xmax"]), "center", "normal", "normal", 13, None
        else:
            src = self.extract_text(cropped_label, f"--psm 3 --oem 3")
            if layout["label"]=="paragraph": position, alignment, weight, style, size, tab_size = None, "justify", "normal", "normal", 13, 1
            elif layout["label"]=="subtitle": position, alignment, weight, style, size, tab_size = None, "justify", "bold", "normal", 13, 1
            elif layout["label"]=="continued": position, alignment, weight, style, size, tab_size = self.position(page.shape[1], layout["box"]["xmin"], layout["box"]["xmax"]), "justify", "normal", "normal", 13, 0
            elif layout["label"]=="lined": position, alignment, weight, style, size, tab_size = None, "justify", "normal", "normal", 13, 1
            elif layout["label"]=="footer": position, alignment, weight, style, size, tab_size = None, "justify", "normal", "normal", 13, 0
        dictionary = {"label":layout["label"], "confidence":layout["confidence"], "page":layout["page"], "tab_size":tab_size, "src":src, "ID":layout["ID"], "grID":layout["grID"], "box":{"xmin":layout["box"]["xmin"], "ymin":layout["box"]["ymin"], "xmax":layout["box"]["xmax"], "ymax":layout["box"]["ymax"]}, "type":layout["type"], "position":position, "alignment":alignment, "font":{"weight":weight, "style":style, "size":size},"page_size":{"width":page.shape[1], "height":page.shape[0]}}
        return dictionary
        
    def table(self, layout):
        page = np.array(self.images[layout["page"]-1])
        page = cv2.cvtColor(page, cv2.COLOR_BGR2RGB)
        xmin = max(layout["box"]["xmin"]-10, 0)
        ymin = max(layout["box"]["ymin"]-10, 0)
        xmax = min(layout["box"]["xmax"]+10, page.shape[1])
        ymax = min(layout["box"]["ymax"]+10, page.shape[0])     
        cropped_label = page[ymin:ymax,xmin:xmax]
        weight, style, size = "normal", "normal", 10
        table_name = str(uuid.uuid4())+".jpg"
        absolute_path = "/home/wsmsi4090/FOZILJON/UZGASHKLITI/media-files/table/"+table_name
        global_path = "http://10.10.0.108:8005/table/"+table_name
        coefficient_w, coefficient_h = abs(layout["box"]["xmax"]-layout["box"]["xmin"])/page.shape[1], abs(layout["box"]["ymax"]-layout["box"]["ymin"])/page.shape[0]
        h_ratio, w_ratio = 0,0
        if page.shape[1]<page.shape[0]: h_ratio, w_ratio = self.docx_h * coefficient_h, self.docx_w * coefficient_w
        else: h_ratio, w_ratio = self.docx_w * coefficient_h, self.docx_h * coefficient_w
        rgb_image = cv2.cvtColor(cropped_label, cv2.COLOR_BGR2RGB)
        pil_image = PImage.fromarray(rgb_image)
        byte_stream = io.BytesIO()
        pil_image.save(byte_stream, format="PNG")
        byte_stream.seek(0)
        image = Image(byte_stream, detect_rotation=True)
        try: extracted_tables = image.extract_tables(ocr=self.table_ocr, implicit_rows=False, implicit_columns=False, borderless_tables=False, min_confidence=30)
        except Exception as e1:
            try: extracted_tables = image.extract_tables(ocr=self.table_ocr, implicit_rows=False, implicit_columns=False, borderless_tables=True, min_confidence=30)
            except Exception as e2: extracted_tables = []
        if len(extracted_tables)==0: 
            cropped_label = page[ymin+10:ymax-10,xmin+10:xmax-10]
            src, layout["label"], layout["type"], weight, style, size = absolute_path, "table", "image", None, None, None
        else: src = extracted_tables[0].html.replace("\n", "")
        dictionary = {"label":layout["label"], "confidence":layout["confidence"], "page":layout["page"], "tab_size":None, "src":src, "ID":layout["ID"], "grID":layout["grID"], "box":{"xmin":layout["box"]["xmin"], "ymin":layout["box"]["ymin"], "xmax":layout["box"]["xmax"], "ymax":layout["box"]["ymax"]}, "type":layout["type"], "position":None, "alignment":"center", "font":{"weight": weight, "style": style, "size": size }, "ratio":{"width": h_ratio, "height": w_ratio}, "page_size":{"width": page.shape[1], "height": page.shape[0]}}
        cv2.imwrite(absolute_path, cropped_label)
        return dictionary

    def formula(self, layout):
        page = np.array(self.images[layout["page"]-1])
        xmin = max(layout["box"]["xmin"]-10, 0)
        ymin = max(layout["box"]["ymin"]-10, 0)
        xmax = min(layout["box"]["xmax"]+10, page.shape[1])
        ymax = min(layout["box"]["ymax"]+10, page.shape[0])
        cropped_label = page[ymin:ymax,xmin:xmax]
        weight, style, size = "normal", "normal", 11
        formula_name = str(uuid.uuid4())+".jpg"
        absolute_path = "/home/wsmsi4090/FOZILJON/UZGASHKLITI/media-files/formula/"+formula_name
        global_path = "http://10.10.0.108:8005/formula/"+formula_name
        coefficient_w, coefficient_h = abs(layout["box"]["xmax"]-layout["box"]["xmin"])/page.shape[1], abs(layout["box"]["ymax"]-layout["box"]["ymin"])/page.shape[0]
        h_ratio, w_ratio = 0,0
        if page.shape[1]<page.shape[0]: h_ratio, w_ratio = self.docx_h * coefficient_h, self.docx_w * coefficient_w
        else: h_ratio, w_ratio = self.docx_w * coefficient_h, self.docx_h * coefficient_w
        pil_image = PImage.fromarray(cropped_label)
        try:
            src = self.formula2latex.predict(pil_image)
            src = {"latex":src, "image":absolute_path}
            print(src)
        except: 
            src, layout["label"], layout["type"], weight, style, size = absolute_path, "formula", "image", None, None, None
        cropped_label = page[ymin+10:ymax-10,xmin+10:xmax-10]

        dictionary = { "label":layout["label"], "confidence":layout["confidence"], "page":layout["page"], "tab_size":None, "src":src, "ID":layout["ID"], "grID":layout["grID"], "box":{"xmin":layout["box"]["xmin"], "ymin":layout["box"]["ymin"], "xmax":layout["box"]["xmax"], "ymax":layout["box"]["ymax"]}, "type":layout["type"], "position":None, "alignment":"center", "font":{"weight":weight,"style":style,"size":size}, "ratio":{"width":h_ratio, "height":w_ratio}, "page_size":{"width": page.shape[1], "height": page.shape[0]}}
        cv2.imwrite(absolute_path, cropped_label)
        return dictionary
    
    def image(self, layout):
        page = np.array(self.images[layout["page"]-1])
        page = cv2.cvtColor(page, cv2.COLOR_BGR2RGB)
        xmin = max(layout["box"]["xmin"]-10, 0)
        ymin = max(layout["box"]["ymin"]-10, 0)
        xmax = min(layout["box"]["xmax"]+10, page.shape[1])
        ymax = min(layout["box"]["ymax"]+10, page.shape[0])
        cropped_label = page[ymin:ymax,xmin:xmax]
        image_name = str(uuid.uuid4())+".jpg"
        absolute_path = "/home/wsmsi4090/FOZILJON/UZGASHKLITI/media-files/image/"+image_name
        global_path = "http://10.10.0.108:8005/image/"+image_name
        src = absolute_path
        coefficient_w, coefficient_h = abs(layout["box"]["xmax"]-layout["box"]["xmin"])/page.shape[1], abs(layout["box"]["ymax"]-layout["box"]["ymin"])/page.shape[0]
        h_ratio, w_ratio = 0,0
        if page.shape[1]<page.shape[0]: h_ratio, w_ratio = self.docx_h * coefficient_h, self.docx_w * coefficient_w
        else: h_ratio, w_ratio = self.docx_w * coefficient_h, self.docx_h * coefficient_w
        dictionary = {"label":layout["label"], "confidence":layout["confidence"], "page":layout["page"], "tab_size":None, "src":src, "ID":layout["ID"], "grID":layout["grID"], "box":{"xmin":layout["box"]["xmin"], "ymin":layout["box"]["ymin"], "xmax":layout["box"]["xmax"], "ymax":layout["box"]["ymax"]}, "type":layout["type"], "position":None, "alignment":"center", "font":{"weight":None, "style":None, "size":None}, "ratio":{"width":h_ratio, "height":w_ratio}, "page_size":{"width":page.shape[1], "height":page.shape[0]}}
        cv2.imwrite(absolute_path, cropped_label)
        return dictionary
        
    def process(self, images, DATASET, BLOCKS):
        torch.cuda.empty_cache()
        start = time.time()
        self.images, self.pages = images, DATASET[-1]["page"]
        RESULTS, FOOTER = [], []
        
        for layout in DATASET:
            if layout["type"] == "text":
                json = self.text(layout)
                if layout["label"] == "footer":
                    FOOTER.append(json)
                    continue
            elif layout["type"] == "table": json = self.table(layout)
            elif layout["type"] == "formula": json = self.formula(layout)
            elif layout["type"] == "image": json = self.image(layout)
            else: json = layout
            RESULTS.append(json)

        BLOCK = defaultdict(list)
        for block, data in BLOCKS.items():
            JSON = []
            for layout in data:
                if layout["type"] == "text": 
                    json = self.text(layout)
                    if layout["label"] == "footer":
                        FOOTER.append(json)
                        continue
                elif layout["type"] == "table": json = self.table(layout)
                elif layout["type"] == "formula": json = self.formula(layout)
                elif layout["type"] == "image": json = self.image(layout)
                JSON.append(json)
            BLOCK[block] = JSON  
        result = self.remove_blocks(RESULTS, BLOCK, FOOTER)
        RESULTS = self.merger(result)
        torch.cuda.empty_cache()
        total_time = round(time.time() - start, 3)
        return RESULTS, total_time