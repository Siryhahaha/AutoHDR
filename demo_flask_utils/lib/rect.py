import json
import os
from PIL import Image

class Rect:
    def __init__(self, x, y, width, height, color, id=None, label=None):
        self.x = int(x)
        self.y = int(y)
        self.width = int(width)
        self.height = int(height)
        self.color = color
        self.id = id
        self.label = label

    def to_dict(self):
        return vars(self)

    @classmethod
    def from_dict(cls, data):
        return cls(**data)

class RectManager:
    def __init__(self):
        self.rects = []
        self.next_id = 1

    def add(self, rect):
        if rect.id is None:
            rect.id = self.next_id
            self.next_id += 1
        self.rects.append(rect)
        return rect.id
    
    def remove(self, rect_id):
        self.rects = [r for r in self.rects if r.id != rect_id]
    
    def get_all(self):
        return [rect.to_dict() for rect in self.rects]

    def to_json(self):
        return json.dumps(self.get_all(), ensure_ascii=False)

    @classmethod
    def from_json(cls, json_str): 
        if not json_str:
            return cls()
        manager = cls()
        for data in json.loads(json_str):
            manager.add(Rect.from_dict(data))
        return manager

    def process_image(self, input_path, output_dir, filename):
        """基础图片处理方法"""
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"processed_{filename}")
        img = Image.open(input_path).convert('L')
        img.save(output_path)
        return output_path, self.to_json()

    def process_ocr_result(self, ocr_result):
        """处理OCR结果并添加框"""
        for bbox_str, (labels, confs) in ocr_result.items():
            bbox = eval(bbox_str)
            x1, y1, x2, y2 = bbox
            width = x2 - x1
            height = y2 - y1
            first_char = labels[0] if labels else ""
            confidence = confs[0] if confs else 0
            
            if confidence > 0.95:
                color = "#7fffd4"
            elif confidence > 0.9:
                color = "#060ac9"
            else:
                color = "#ff0000"
            
            rect = Rect(x1, y1, width, height, color, label=first_char)
            self.add(rect)
