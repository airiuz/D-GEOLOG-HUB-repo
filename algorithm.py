import time
import uuid
from collections import defaultdict
import numpy as np

class Algorithm:
    def __init__(self):
        pass

    def collinear_by_X(self, blok1, blok2):
        xmin1,xmax1 = blok1["box"]["xmin"],blok1["box"]["xmax"]
        xmin2,xmax2 = blok2["box"]["xmin"],blok2["box"]["xmax"]
        return xmax1-25 <= xmin2+25 or xmax2-25 <= xmin1+25
        
    def collinear_by_Y(self, blok1, blok2):
        ymin1,ymax1 = blok1["box"]["ymin"],blok1["box"]["ymax"]
        ymin2,ymax2 = blok2["box"]["ymin"],blok2["box"]["ymax"]
        return ymin1<=(ymin2+ymax2)/2<=ymax1 or ymin2<=(ymin1+ymax1)/2<=ymax2

    def split_blocks(self, dataset): 
        DATASET = []
        BLOCKS = defaultdict(list)
        
        for page in range(1, self.pages+1):
            blocks, result = [], []
            data = [item for item in dataset if item['page'] == page]
    
            block = []
            for element in data:
                if element['label'] in ['left_block', 'right_block']:
                    block.append(element)

            if len(block)==1:
                blocks = block.copy()
            
            if len(block)>1:
                blok1, blok2 = None, None
                for i in range(len(block)-1):
                    blok1, blok2 = block[i], block[i+1]
                    
                    if blok1['label'] == "right_block" and blok2['label'] == "left_block" and self.collinear_by_Y(blok1, blok2):
                        blocks.append(blok2)
                        blok1,blok2 = blok2.copy(),blok1.copy()
                    else:
                        blocks.append(blok1)        
                blocks.append(blok2)
    
            index = 0
            for element in data:
                if element['label'] not in ['left_block', 'right_block']:
                    blocked = False
                    for block in blocks:
                        if block['box']['xmin'] <= (element['box']['xmin'] + element['box']['xmax']) / 2 and (element['box']['xmin'] + element['box']['xmax']) / 2 <= block['box']['xmax'] and block['box']['ymin'] <= (element['box']['ymin'] + element['box']['ymax']) / 2 and (element['box']['ymin'] + element['box']['ymax']) / 2 <= block['box']['ymax']:
                            BLOCKS[block["ID"]].append(element)
                            blocked = True
                            break
                    if not blocked:
                        result.append(element)
                else:
                    result.append(blocks[index])
                    index+=1
            DATASET.extend(result)
        return DATASET, BLOCKS

    def set_block_id(self, dataset):
        for page in range(1,self.pages+1):
            recto = [data for data in dataset if data['page'] == page]
            
            for item1 in recto:
                unique_id = uuid.uuid1().int>>64
                if item1["label"] in ['left_block', 'right_block']:
                    continue
                
                for item2 in recto:
                    if item1==item2:
                        continue
                    
                    elif item2["label"] in ['left_block', 'right_block']:
                        continue
                
                    elif self.collinear_by_X(item1, item2) and self.collinear_by_Y(item1, item2):
                        if type(item1['ID']) == str and type(item2['ID']) == str:
                            item1['ID'] = unique_id
                            item2['ID'] = unique_id
    
                        elif type(item1['ID']) == str and type(item2['ID']) == int:
                            item1['ID'] = item2['ID']
                
                        elif type(item1['ID']) == int and type(item2['ID']) == str:
                            item2['ID'] = item1['ID']
        return dataset

    def create_groups(self, group):
        group = sorted(group, key=lambda x: x['box']["xmin"])
        for item1 in group:
            uid = uuid.uuid1().int>>64
            for item2 in group:
                if item1==item2:
                    continue
                    
                if not self.collinear_by_X(item1, item2):
                    if type(item1["grID"])==str and type(item2["grID"])==str:
                        item1["grID"] = uid
                        item2["grID"] = uid
    
                    elif type(item1["grID"])==str and type(item2["grID"])==int:
                        item1["grID"] = item2["grID"]
    
                    elif type(item1["grID"])==int and type(item2["grID"])==str:
                        item2["grID"] = item1["grID"]
                
        grouped = defaultdict(list)
        for item in group:
            grouped[item['grID']].append(item)
        new_group = []
        
        for new_id, (old_group_id, items) in enumerate(grouped.items()):
            sorted_items = sorted(items, key=lambda x: x['box']["ymin"])
            for item in sorted_items:
                item['grID'] = new_id
                new_group.append(item)
        return new_group
    
    def set_group_id(self, group):
        grouped_by_id = defaultdict(list)
        for item in group:
            grouped_by_id[item['ID']].append(item)
    
        sorted_groups = []
        for key, items in grouped_by_id.items():
            if len(items)==1:
                sorted_groups.extend(items)
            else:
                items = self.create_groups(items)
                sorted_groups.extend(items)
        return sorted_groups

    def use(self, dataset):
        start = time.time()
        self.pages = dataset[-1]["page"]
        dataset, blocks = self.split_blocks(dataset)
        blocked_dataset = self.set_block_id(dataset)
        DATASET = self.set_group_id(blocked_dataset)

        BLOCK = defaultdict(list)
        for ID, items in blocks.items():
            blocked_block = self.set_block_id(items)
            block = self.set_group_id(blocked_block)
            BLOCK[ID] = block
        total_time = round(time.time() - start, 3)
        return DATASET, BLOCK, total_time