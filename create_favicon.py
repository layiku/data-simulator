from PIL import Image, ImageDraw, ImageFont
import os

# 确保static目录存在
static_dir = "static"
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

# 创建一个16x16像素的图像（favicon标准大小）
image = Image.new("RGB", (32, 32), color=(49, 125, 237))  # 使用蓝色背景
draw = ImageDraw.Draw(image)

# 绘制一个简单的计数器图标
# 中心圆
draw.ellipse((8, 8, 24, 24), fill=(255, 255, 255))  # 白色圆
draw.ellipse((10, 10, 22, 22), fill=(49, 125, 237))  # 内部蓝色圆

# 指针
draw.line((16, 16, 16, 10), fill=(255, 255, 255), width=2)  # 垂直指针
draw.line((16, 16, 20, 18), fill=(255, 255, 255), width=2)  # 对角线指针

# 保存为favicon.ico
favicon_path = os.path.join(static_dir, "favicon.ico")
image.save(favicon_path, format="ICO", sizes=[(16, 16), (32, 32), (64, 64)])

print(f"Favicon created at: {favicon_path}") 