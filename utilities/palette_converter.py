import colorsys
from PIL import Image, ImageColor

loc = './'

im = r'C:\Users\Patrick\Documents\Github\memento-mori\extra_resources\Portraits\Anna.png'

def hsv2rgb(h: float, s: float, v: float) -> tuple:
    return tuple(round(i * 255) for i in colorsys.hsv_to_rgb(h, s, v))

def rgb2hsv(r: int, g: int, b: int) -> tuple:
    return tuple(colorsys.rgb_to_hsv(r, g, b))

def clamp(i, bound_a, bound_b):
    max_ = max(bound_a, bound_b)
    min_ = min(bound_a, bound_b)
    return min(max_, max(min_, i))

def lerp(a: float, b: float, t: float) -> float:
    """Linear interpolation

    Args:
        a, b (float): values to lerp between
        t (float): time or proportion to lerp for, must be in range [0, 1]

    Returns:
        [float]: lerped value
    """
    t = clamp(t, 0, 1)
    return (b - a) * t + a

def change_saturation(value):
    return lerp(2.0, 0.8, value)

def change_value(value):
    return lerp(0.3, 0.8, value)

colors = ['#0d2b45', '#203c56', '#544e68', '#8d697a', '#d08159', '#ffaa5e', '#ffd4a3', '#ffecd6']
colors = [ImageColor.getcolor(c, "RGB") for c in colors]
hue = [rgb2hsv(*c)[0] for c in colors]
saturation = [rgb2hsv(*c)[1] for c in colors]
values = [rgb2hsv(*c)[2]/255 for c in colors]
print(hue)
print(saturation)
print(values)

def transform_color(color):
    h, s, v = rgb2hsv(*color[:3])
    value = v / 255
    if color[:3] == (128, 160, 128):
        return color[:3]
    if value < .28:
        return colors[0]
    elif value < .43:
        return colors[1]
    elif value < .58:
        return colors[2]
    elif value < .68:
        return colors[3]
    elif value < .78:
        return colors[4]
    elif value < .88:
        return colors[5]
    elif value < .98:
        return colors[6]
    else:
        return colors[7]

def convert_palette(im):
    width, height = im.size
    for x in range(width):
        for y in range(height):
            color = im.getpixel((x, y))
            new_color = transform_color(color)
            im.putpixel((x, y), new_color)
    return im

convert_palette(Image.open(im)).convert('RGB').save(im)
