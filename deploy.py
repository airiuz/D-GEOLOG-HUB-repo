import os, time, csv
import importlib.util
import sys, json
module_path = "/home/wsmsi4090/FOZILJON/UZGASHKLITI"
# sys.path.append(module_path) 
# sys.path.append("/home/wsmsi4090/FOZILJON/UZGASHKLITI")
# sys.path.append("/home/wsmsi4090/FOZILJON/UZGASHKLITI/UniMERNet")
# import preprocessing
# import algorithm
# import postprocessing
# from DFINE.detector import Detector
def load_module(module_name, path):
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

preprocessing = load_module("preprocessing", f"""{module_path}/preprocessing.py""")
algorithm = load_module("algorithm", f"""{module_path}/algorithm.py""")
detector = load_module("detector", f"""{module_path}/DFINE/detector.py""")
postprocessing = load_module("postprocessing", f"""{module_path}/postprocessing.py""")

class PDFparser:
    def __init__(self):
        self._images = []
        self._preprocessor = preprocessing.Preprocessing()
        self._detector = detector.Detector()
        self._algorithm = algorithm.Algorithm()
        self._postprocessor = postprocessing.Postprocessing()  
    def write_results(self):
        with open('statistics.csv', mode='a', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=self.statistics.keys())
            file.seek(0, 2)
            if file.tell() == 0:
                writer.writeheader()
            writer.writerow(self.statistics)
    
    def process_pdf(self, pdf_path):
        self.statistics = {
            "pdf_name": os.path.splitext(os.path.basename(pdf_path))[0],
            "page_count": 0,
            "preprocessing_status": "failed",
            "detection_status": "failed",
            "algorithm_status": "failed",
            "postprocessing_status": "failed",
            "total_time": 0,
            "per_page_time": 0}
        
        try:
            self._images, total_time_prep = self._preprocessor.run(pdf_path)
            self.statistics["preprocessing_status"] = f"{total_time_prep}"
            self.statistics["page_count"] = len(self._images)
            print("preprocessing done")
        except Exception as e:
            print(e)
            self.write_results()
            return {"total_time": 0, "result": f"Preprocessing Error: {e}"}
    
        try:
            layout_data, total_time_lay = self._detector.predict(self._images)
            self.statistics["detection_status"] = f"{total_time_lay}"
            print("Detection done")
        except Exception as e:
            self.write_results()
            return {"total_time": 0, "result": f"Layout Detection Error: {e}"}

        try:
            clean_layouts, clean_blocks, total_time_alg = self._algorithm.use(layout_data)
            self.statistics["algorithm_status"] = f"{total_time_alg}"
            print("algorithm done")
        except Exception as e:
            self.write_results()
            return {"total_time": 0, "result": f"Algorithm Error: {e}"}

        results, total_time_post = self._postprocessor.process(self._images, clean_layouts, clean_blocks)
        with open("/home/wsmsi4090/FOZILJON/UZGASHKLITI/media-files/JSON/output.json", 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=4, ensure_ascii=False)
        self.statistics["postprocessing_status"] = f"{total_time_post}"
        print("postprocessing done")
        
        # except Exception as e:
        #     self.write_results()
        #     return {"total_time": 0, "result": f"Postprocessing Error: {e}"}
        print("all processes done")
        
        total = total_time_prep + total_time_lay + total_time_alg + total_time_post
        self.statistics["total_time"] = round(total,3)
        self.statistics["per_page_time"] = round(total/len(self._images),3)
        self.write_results()
        return {"total_time": total, "result": results}

if "__main__" == __name__:
    deployer = PDFparser()
    deployer.process_pdf("/home/wsmsi4090/FOZILJON/UZGASHKLITI/eskd.pdf")