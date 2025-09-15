import torch
import torch.nn as nn
import torchvision.transforms as T
import numpy as np
from PIL import Image, ImageDraw
import os, glob
from DFINE.src.core import YAMLConfig
import time
import uuid
import cv2

class Detector:
    def __init__(self):
        self.classes = {0: "paragraph", 1: "title", 2: "central", 3: "hat", 4: "continued", 5: "footer", 6: "page", 7: "table", 8: "picture", 9: "formula", 10: "lined", 11: "caption", 12: "subtitle", 13: "right_block", 14: "left_block"}
        self.text = ["paragraph", "title", "central", "continued", "footer", "lined", "caption",  "subtitle"]
        self.picture = ["picture"]
        self.formula = ["formula"]
        self.table = ["table"]
        self.block = ["left_block", "right_block"]
        
        self.config = "/home/wsmsi4090/FOZILJON/UZGASHKLITI/DFINE/configs/dfine/custom/dfine_hgnetv2_x_custom.yml"
        self.checkpoint = "/home/wsmsi4090/FOZILJON/UZGASHKLITI/DFINE/output/dfine_hgnetv2_x_custom/last.pth"
        self.device = "cuda:0" if torch.cuda.is_available() else "cpu"
        self.size = 640
        
        cfg = YAMLConfig(self.config, resume=self.checkpoint)
        if 'HGNetv2' in cfg.yaml_cfg:
            cfg.yaml_cfg['HGNetv2']['pretrained'] = False
        
        if self.checkpoint:
            checkpoint = torch.load(self.checkpoint, map_location='cpu')
            if 'ema' in checkpoint:
                state = checkpoint['ema']['module']
            else:
                state = checkpoint['model']
        
        cfg.model.load_state_dict(state)
        class Model(nn.Module):
            def __init__(self):
                super().__init__()
                self.model = cfg.model.deploy()
                self.postprocessor = cfg.postprocessor.deploy()
    
            def forward(self, images, orig_target_sizes):
                outputs = self.model(images)
                outputs = self.postprocessor(outputs, orig_target_sizes)
                return outputs
        self.detection_model = Model().to(self.device)

    def set_type(self, dataset):
        label_map = {
            **{label: "text" for label in self.text},
            **{label: "image" for label in self.picture},
            **{label: "formula" for label in self.formula},
            **{label: "table" for label in self.table},
            **{label: "block" for label in self.block}
        }
    
        for item in dataset:
            item["type"] = label_map.get(item["label"], "trash")
        
        return dataset

    def intersection_percent(self, box1, box2):
        xmin1, ymin1, xmax1, ymax1 = box1["xmin"], box1["ymin"], box1["xmax"], box1["ymax"]
        xmin2, ymin2, xmax2, ymax2 = box2["xmin"], box2["ymin"], box2["xmax"], box2["ymax"]
        
        xmin_overlaped = max(xmin1,xmin2)
        ymin_overlaped = max(ymin1,ymin2)
        xmax_overlaped = min(xmax1,xmax2)
        ymax_overlaped = min(ymax1,ymax2)
        
        if xmin_overlaped>=xmax_overlaped or ymin_overlaped>=ymax_overlaped:
            return 0,0
            
        else:
            area = (xmax_overlaped-xmin_overlaped)*(ymax_overlaped-ymin_overlaped)
            area1 = (xmax1-xmin1)*(ymax1-ymin1)
            area2 = (xmax2-xmin2)*(ymax2-ymin2)
    
            if area/area1>=0.7 or area/area2>=0.7: return area/area1, area/area2
            else: return 0,0
    
    def remove_duplicates(self, dataset):
        for item in dataset:
            item['status'] = "active"
        
        for item1 in dataset:
            for item2 in dataset:
                if item1==item2:
                    continue
                
                if item1['status'] == "passive" or item2['status'] == "passive":
                    continue

                if item1["label"] in self.block and not (item2["label"] in self.block):
                    item1['status'] = "active"
                    continue

                if not(item1["label"] in self.block) and item2["label"] in self.block:
                    item1['status'] = "active"
                    continue

                item1_p, item2_p = self.intersection_percent(item1['box'], item2['box'])
                
                if item1_p==0 or item2_p==0:
                    continue
    
                if max(item1_p,item2_p)>0.7:
                    if item1['confidence']>=item2['confidence']:
                        item2['status'] = 'passive'
                    else:
                        item1['status'] = 'passive'
                    continue

                elif item1_p>=item2_p:
                    item1['status'] = "passive"
                    continue
                    
                elif item2_p>item1_p:
                    item2['status'] = "passive"
                    continue
                    
        dataset = [item for item in dataset if item["status"] != "passive"]
        return dataset

    def process_image(self, image, page):
        start = time.time()
        result = []
        
        img = image.convert('RGB')
        w, h = img.size
        orig_size = torch.tensor([[w, h]]).to(self.device)
    
        transforms = T.Compose([T.Resize((self.size, self.size)), T.ToTensor(),])
        im_data = transforms(img).unsqueeze(0).to(self.device)
        
        output = self.detection_model(im_data, orig_size)
        labels, boxes, scores = output
        
        boxes = boxes[0][scores[0]>0.3]
        labels = labels[0][scores[0]>0.3]
        scores = scores[0][scores[0]>0.3]

        for label, box, score in zip(labels, boxes, scores):
            label, score = int(label), float(score)
            if label in [3,6]: continue
            xmin,ymin,xmax,ymax = [int(x) for x in box.detach().cpu().numpy().astype(int)]
            result.append({
                "label": self.classes[label],
                "page": page,
                "box": {"xmin":xmin, "ymin":ymin, "xmax":xmax, "ymax":ymax},
                "confidence": round(score,3),
                "page_size": [w, h],
                "ID": str(uuid.uuid4()),
                "grID": str(uuid.uuid4())})

        result = sorted(result, key=lambda item: (item["page"], item["box"]["ymin"], item["box"]["xmin"]))
        result = self.remove_duplicates(result)
        result = self.set_type(result)
        return result, time.time()-start

    def predict(self, pages):
        torch.cuda.empty_cache()
        results = []
        total_time = 0
        for page, image in enumerate(pages, start=1):
            result, t = self.process_image(image, page)
            total_time += t
            results.extend(result)
        total_time = round(total_time, 3)
        torch.cuda.empty_cache()
        return results, total_time