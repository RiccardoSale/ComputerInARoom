from PIL import Image
import PIL.Image
import imageio

PIL.Image.MAX_IMAGE_PIXELS = None


def convert_to_webp(source,format):
    image = Image.open(source+format)  # Open image
    image.save(source+'.webp', format='webp')  # Convert image to webp

    return source+'.webp'


def main():
    print(PIL.__file__)
    img = imageio.imread_v2("base.png")
    print(img.shape)
    height, width, depth = img.shape
    width_cutoff = width // 2
    s1 = img[:, :width_cutoff]
    s2 = img[:, width_cutoff:]
    print("LI")
    imageio.imwrite("base_1.png",s1)
    imageio.imwrite("base_2.png",s2)
    print("QUI")
    convert_to_webp('base_1','.png')
    convert_to_webp('base_2','.png')




main()