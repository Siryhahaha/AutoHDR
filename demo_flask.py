from flask import Flask, render_template, request, url_for
import os
from demo_flask_utils.lib.rect_interface import RectInterface
from demo_flask_utils.connect.main_connect import get_ocr_rects  # 修改导入路径

######################################################
from typing import List, Dict
from demo_flask_utils.lib.rect_interface import RectInterface
from infer_pipeline_api import main
from demo_flask_utils.connect.shared_vars import *

from PIL import Image
import infer_pipeline_api as pipline_qwen_multisptk_api
import argparse
from transformers import set_seed
import os
import shutil
######################################################


app = Flask(__name__, 
           template_folder='demo_flask_utils/templates',
           static_folder='demo_flask_utils/static')

# 简化配置
STATIC_SUBFOLDERS = ['uploads', 'outputs']
for folder in STATIC_SUBFOLDERS:
    os.makedirs(os.path.join(app.static_folder, folder), exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}

@app.route('/')
def index():
    images_dir = os.path.join(app.static_folder, 'images')
    example_images = []
    if os.path.exists(images_dir):
        example_images = [(f, i) for i, f in enumerate(sorted(os.listdir(images_dir))) 
                         if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif'))]
    return render_template('upload.html', example_images=example_images)

@app.route('/upload', methods=['POST'])
def upload_file():
    logs = []
    original = None
    try:
        is_example = request.form.get('is_example', '0') == '1'
        

        if is_example:
            filename = request.form.get('example_filename')
            if not filename:
                return render_template('ocr_result.html', logs=["错误：未指定例子图片文件名"])
            filepath = os.path.join(app.static_folder, 'images', filename)
            if not os.path.exists(filepath):
                return render_template('ocr_result.html', logs=["错误：例子图片不存在"])
            logs.append(f"[选择例子图片] {filename}")
            
        else:
            file = request.files.get('file')
            if not file or file.filename == '' or not allowed_file(file.filename):
                return render_template('ocr_result.html', logs=["错误：无效的文件"])
            filename = file.filename
            filepath = os.path.join(app.static_folder, 'uploads', filename)
            file.save(filepath)
            logs.append(f"[上传成功] {filename}")
        
        # 获取OCR预设识别框
        # ocr_rects = get_ocr_rects()

        #########################################################
        print(filepath)
        
        config_file = './ckpt/damage_detect.py' # 网络模型py文件
        damage_detect_checkpoint_file = './ckpt/damage_detect.pth'  # 训练好的模型参数
        model_name_or_path = './ckpt/AutoHDR-Qwen2-1.5B'
        ocr_det_weights = './ckpt/best.pt'

        parser = argparse.ArgumentParser(prog='test.py')
        parser.add_argument('--ocr_det_weights', nargs='+', type=str, default=ocr_det_weights, help='model.pt path(s)')
        parser.add_argument('--vague_det_weights', nargs='+', type=str, default=damage_detect_checkpoint_file, help='model.pth path(s)')
        parser.add_argument('--vague_det_config', nargs='+', type=str, default=config_file, help='mmdetection config.py path(s)')
        parser.add_argument('--model_name_or_path', nargs='+', type=str, default=model_name_or_path, help='llm weight path(s)')
        

        parser.add_argument('--det-batch-size', type=int, default=1, help='size of each image batch')
        parser.add_argument('--reg-batch-size', type=int, default=36, help='size of each image batch')
        parser.add_argument('--img-size', type=int, default=2048, help='inference size (pixels)')
        parser.add_argument('--conf-thres', type=float, default=0.45, help='object confidence threshold')
        parser.add_argument('--iou-thres', type=float, default=0.2, help='IOU threshold for NMS')
        parser.add_argument('--device', default='0', help='cuda device, i.e. 0 or 0,1,2,3 or cpu')
        parser.add_argument("--seed", type=int, default=123)

        # model
        parser.add_argument("--image_channel", type=int, default=3)
        # pipeline setting
        parser.add_argument("--pipeline", type=str, default="DPM-Solver++",
                            choices=['DDPM', 'DPM-Solver', 'DPM-Solver++'])
        parser.add_argument("--classifier_free", action="store_false", \
                            help="Whether to use classifier-free guidance sampling.")
        parser.add_argument(
            "--content_mask_guidance_scale", type=float, default=1.5, help="The guidance scale for contnet and mask image.")
        parser.add_argument(
            "--degraded_guidance_scale", type=float, default=1.2, help="The guidance scale for degraded image.")
        parser.add_argument(
            "--solver_order", type=int, default=2, help="If use DPM-Solver, set this parameter.")
        parser.add_argument("--num_inference_steps", type=int, default=20)
        parser.add_argument("--ddpm_num_steps", type=int, default=1000)
        parser.add_argument("--ddpm_beta_schedule", type=str, default="linear")
        parser.add_argument("--prediction_type", type=str, default="sample")
        
        parser.add_argument("--batch_infer", action="store_true", \
                            help="Whether to use batch type inference.")
        # If single image inference, should make sure the image size is 512
        parser.add_argument("--gt_image_path", type=str, default=None)
        # If batch image inference
        parser.add_argument("--data_dir", type=str, default=None, \
                            help="The folder should be consistent with train data dir.")
        parser.add_argument("--degrade_modes", nargs='+', default=['removal', 'hole', 'ink'])
        parser.add_argument("--batch_size", type=int, default=8)
        parser.add_argument("--shuffle", action="store_true")
        parser.add_argument("--num_workers", type=int, default=8)

        opt = parser.parse_args()

        if opt.seed is not None:
            set_seed(opt.seed)
        
        
        save_path = './results' 
        img_path = filepath

        if not os.path.exists(save_path):
            os.makedirs(save_path)

        img_dir = os.path.join(save_path, 'img')
        if not os.path.exists(img_dir):
            os.makedirs(img_dir)

        combined_dir = os.path.join(save_path, 'combined')
        if not os.path.exists(combined_dir):
            os.makedirs(combined_dir)

        print("debug01")
        restore_img, combined = main(data=img_path, opt=opt)
        # if restore_img is not None:
        #     restore_img.save(os.path.join(f'{save_path}/img', img_path))
        #     combined.save(os.path.join(f'{save_path}/combined', img_path))

        normal_ocr_result = connect_normal_ocr_result.get('result', [])
        vague_high_result = connect_vague_high_result.get('result', [])
        vague_low_result = connect_vague_low_result.get('result', [])
        all_ocr_results = {
            'normal_ocr': normal_ocr_result,
            'vague_high': vague_high_result,
            'vague_low': vague_low_result
        }

        rects = []
        id_counter = 1
        
        ##############################
        for result_type, ocr_result_dict in all_ocr_results.items():
            if not ocr_result_dict: # 检查结果集是否为空
                continue
            for bbox_str, (labels, confs) in ocr_result_dict.items():
                # 解析边界框字符串
                bbox = eval(bbox_str)
                x1, y1, x2, y2 = bbox
                # 计算宽度和高度
                width = x2 - x1
                height = y2 - y1
                # 提取第一个字符作为标签
                first_char = labels[0] if labels else ""
                # 根据置信度确定颜色
                if result_type == 'normal_ocr':
                    color = "#7fffd4"#绿色
                    pass
                elif result_type == 'vague_high':
                    color = "#060ac9"#蓝色
                    pass
                elif result_type == 'vague_low':
                    color = "#ff0000"#红色
                    pass
                
                # 创建矩形对象
                rect = {
                    "x": x1,
                    "y": y1,
                    "width": width,
                    "height": height,
                    "color": color,
                    "label": first_char,
                    "id": id_counter
                }
                rects.append(rect)
                id_counter += 1

        if rects == []:
            rects = [
                RectInterface.create_rect_data(150, 300, 80, 40, "#ff0000", "没看到字")
            ]

        ocr_rects = rects
        ########################################################
        
        # 传入OCR识别框数据
        output_path, rects_json = RectInterface.process_with_rects(
            filepath, 
            os.path.join(app.static_folder, 'outputs'), 
            filename,
            ocr_rects
        )
        image_url = url_for('static', filename=os.path.relpath(output_path, app.static_folder))
        
        return render_template('ocr_result.html',
                             original=filename,
                             processed=os.path.basename(output_path),
                             logs=logs,
                             image_url=image_url,
                             initial_rects=rects_json)
    except Exception as e:
        return render_template('ocr_result.html', 
                             original=original, 
                             logs=[f"异常：{str(e)}"])

if __name__ == '__main__':
    app.run(host='0.0.0.0',port=5001,  debug=True)