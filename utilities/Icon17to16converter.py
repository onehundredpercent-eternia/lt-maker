from PIL import Image

# Converts a 17x17 arrangement of 16x16 icons to 16x16

fn = 'ArchaneaIconProject-BG_2019.png'
img = Image.open(fn)
width, height = img.size
new_img = Image.new('RGB', (width, height))
for x in range(width // 18):
    for y in range(height // 18):
        i, j = x * 18 + 2, y * 18 + 2
        cropped = img.crop((i, j, i + 16, j + 16))
        new_img.paste(cropped, (x * 16, y * 16))
new_img.save(fn[:-4] + '_new.png')
