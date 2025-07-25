from PIL import Image

def convert_to_grayscale(input_path, output_path):
    img = Image.open(input_path).convert('L')
    img.save(output_path)
