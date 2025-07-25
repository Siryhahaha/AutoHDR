from typing import List, Dict, Union, Tuple
from .rect import Rect, RectManager

class RectInterface:
    @staticmethod
    def create_rect_data(x: int, y: int, width: int, height: int, 
                        color: str = "#7fffd4", label: str = None) -> dict:
        """创建框数据的标准格式"""
        return {
            "x": x,
            "y": y,
            "width": width,
            "height": height,
            "color": color,
            "label": label
        }

    @staticmethod
    def convert_external_data(data: List[Dict[str, Union[int, str]]]) -> str:
        """转换外部数据为JSON字符串"""
        manager = RectManager()
        for rect_data in data:
            rect = Rect(**rect_data)
            manager.add(rect)
        return manager.to_json()

    @staticmethod
    def process_with_rects(input_path: str, output_dir: str, filename: str,
                          rect_data: List[Dict[str, Union[int, str]]] = None) -> Tuple[str, str]:
        """处理图片并添加框"""
        manager = RectManager()
        output_path = manager.process_image(input_path, output_dir, filename)[0]
        
        if rect_data:
            for rect_info in rect_data:
                rect = Rect(**rect_info)
                manager.add(rect)
        
        return output_path, manager.to_json()

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
