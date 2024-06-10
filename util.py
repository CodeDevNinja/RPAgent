import os
import string
import random
import time
from PIL import Image
import re

def generate_random_string(length):
    letters_and_digits = string.ascii_letters + string.digits
    return ''.join(random.choices(letters_and_digits, k=length))

def save_image(pil_image):
    os.makedirs('images', exist_ok=True)
    timestamp = time.strftime("%Y%m%d%H%M%S")
    random_string = generate_random_string(10)
    img_path = os.path.join('images', f"{random_string}_{timestamp}.png")
    pil_image.save(img_path)
    return img_path

def remove_unicode(text):
    # Remove newline characters
    text = text.replace('\n', '')
    # Compile regex pattern to match the specific Unicode sequence
    pattern = re.compile(r'\xef\xbf\xbc'.encode().decode('unicode_escape'))
    # Remove the matched Unicode sequences
    result_str = pattern.sub('', text)
    return result_str

def bezier_curve(p0, p1, p2, t):
    """
    Calculate a point on a quadratic Bézier curve.
    p0, p1, p2 are control points, and t is the parameter (0 <= t <= 1).
    """
    x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t ** 2 * p2[0]
    y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t ** 2 * p2[1]
    return x, y