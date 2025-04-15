from collections import Counter
import io
import os
from PIL import Image
import dotenv

import nsarchive

dotenv.load_dotenv(override = True)
entities = nsarchive.EntityInstance(os.getenv('URL'), os.getenv('NSARCHIVE_TOKEN'))

def get_primary_color(img: io.BytesIO, top_n = 5) -> int:
    image = Image.open(img)
    image = image.convert("RGB")
    pixels = list(image.getdata())

    color_counts = Counter(pixels)
    most_common = color_counts.most_common(top_n)
    result = sorted(most_common, key = lambda c : -c[1])
    result: int = [ c[0] for c in result ]

    for color in result:
        if not(all(c >= 240 for c in color) or all(c <= 32 for c in color)): # On exclut la couleur de fond si elle ne sert à rien
            final = color
    else:
        final = result[0]

    r, g, b = final
    return (r << 16) + (g << 8) + b