import argparse
import os
import sys
import numpy as np

import cv2
import torch
from PIL import Image

sys.path.insert(0, os.path.join(os.getcwd(), ".."))
from unimernet.common.config import Config
import unimernet.tasks as tasks
from unimernet.processors import load_processor

class ImageProcessor:
    def __init__(self, cfg_path):
        self.cfg_path = cfg_path
        self.device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
        self.model, self.vis_processor = self.load_model_and_processor()

    def load_model_and_processor(self):
        args = argparse.Namespace(cfg_path=self.cfg_path, options=None)
        cfg = Config(args)
        task = tasks.setup_task(cfg)
        model = task.build_model(cfg).to(self.device)
        vis_processor = load_processor('formula_image_eval', cfg.config.datasets.formula_rec_eval.vis_processor.eval)

        return model, vis_processor

    def process_single_image(self, raw_image):
        open_cv_image = np.array(raw_image)
        if len(open_cv_image.shape) == 3:
            open_cv_image = open_cv_image[:, :, ::-1].copy()

        image = self.vis_processor(raw_image).unsqueeze(0).to(self.device)
        output = self.model.generate({"image": image})
        pred = output["pred_str"][0]
        return pred