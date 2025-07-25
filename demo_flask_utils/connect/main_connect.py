from typing import List, Dict
from ..lib.rect_interface import RectInterface
from infer_pipeline import main
from .shared_vars import temp_rects_storage

from PIL import Image
import infer_pipeline as pipline_qwen_multisptk_api
import argparse
from transformers import set_seed
import os


def get_ocr_rects() -> List[Dict]:
    """OCR预设识别框"""

    # config_file = './ckpt/damage_detect.py' # 网络模型py文件
    # damage_detect_checkpoint_file = './ckpt/damage_detect.pth'  # 训练好的模型参数
    # model_name_or_path = './ckpt/AutoHDR-Qwen2-1.5B'
    # ocr_det_weights = './ckpt/best.pt'

    config_file = '../../ckpt/damage_detect.py'  # 网络模型py文件
    damage_detect_checkpoint_file = '../../ckpt/damage_detect.pth'  # 训练好的模型参数
    model_name_or_path = '../../ckpt/AutoHDR-Qwen2-1.5B'
    ocr_det_weights = '../../ckpt/best.pt'

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
    
    # # # 修改为正确的输出路径
    # save_path = '../../demo_flask_utils/static/outputs'
    # # 使用传入的图片路径
    # img_path = '/mnt/sdb/sy/AutoHDR/demo_flask_utils/static/images/ex7.png'
    save_path = './results' 
    img_path = 'example.jpg'

    if not os.path.exists(save_path):
        os.makedirs(save_path)

    img_dir = os.path.join(save_path, 'img')
    if not os.path.exists(img_dir):
        os.makedirs(img_dir)

    combined_dir = os.path.join(save_path, 'combined')
    if not os.path.exists(combined_dir):
        os.makedirs(combined_dir)

    print("debug01")
    #暂时注释
    restore_img, combined = main(data=img_path, opt=opt)
    # if restore_img is not None:
    #     restore_img.save(os.path.join(f'{save_path}/img', img_path))
    #     combined.save(os.path.join(f'{save_path}/combined', img_path))
    print("debug02")

    rects = temp_rects_storage.get('last_run_rects', [])

    if rects == []:
        rects = [
            RectInterface.create_rect_data(8, 76, 62, 62, "#7fffd4", "身"),  # 高置信度框
            RectInterface.create_rect_data(607, 70, 65, 55, "#060ac9", "種"),  # 中等置信度框
            RectInterface.create_rect_data(150, 300, 80, 40, "#ff0000", "未识别")  # 低置信度框
        ]
    return rects

# 扩展: 用于连接外部OCR系统的接口
def connect_external_ocr(image_path: str):
    """
    连接外部OCR系统获取识别结果
    这里暂时返回预设数据，后续可以替换为真实的OCR接口
    """
    return get_ocr_rects()
