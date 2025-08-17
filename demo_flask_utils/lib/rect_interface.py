from typing import List, Dict, Union, Tuple
import os
import shutil
import json

class RectInterface:
    @staticmethod
    def create_rect_data(x: int, y: int, width: int, height: int, 
                        color: str = "#7fffd4", label: str = None, 
                        alternatives: List[str] = None) -> dict:
        """创建框数据的标准格式，支持备选项"""
        if alternatives is None:
            alternatives = [label] if label else [""]
        # 确保有5个选项
        while len(alternatives) < 5:
            alternatives.append(f"备选{len(alternatives)}")
            
        return {
            "x": x,
            "y": y,
            "width": width,
            "height": height,
            "color": color,
            "label": label or alternatives[0],
            "alternatives": alternatives,
            "selectedIndex": 0
        }

    @staticmethod
    def convert_external_data(data: List[Dict[str, Union[int, str]]]) -> str:
        """转换外部数据为JSON字符串"""
        # 直接使用字典数据，不需要创建Rect实例
        return json.dumps(data)

    @staticmethod
    def process_with_rects(input_path: str, output_dir: str, filename: str,
                          rect_data: List[Dict[str, Union[int, str]]] = None) -> Tuple[str, str]:
        """处理图片并添加框"""
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        # 简单复制图片到输出目录
        output_path = os.path.join(output_dir, filename)
        shutil.copy2(input_path, output_path)
        
        # 直接返回框数据的JSON
        rects_json = json.dumps(rect_data) if rect_data else "[]"
        
        return output_path, rects_json

# 使用示例:
"""
from demo_flask_utils.lib.rect_interface import RectInterface

# 创建框数据
rects_data = [
    RectInterface.create_rect_data(100, 100, 200, 150, "#7fffd4", "区域1"),
    RectInterface.create_rect_data(350, 200, 100, 100, "#ff0000", "区域2")
]

# 处理图片并添加框
output_path, rects_json = RectInterface.process_with_rects(
    'input.jpg',
    'output_dir',
    'output.jpg',
    rects_data
)
"""
