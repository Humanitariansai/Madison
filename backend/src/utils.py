from PIL import Image


def downsample_image(image: Image.Image, max_dimension: int = 1024) -> Image.Image:
    """
    Downsample the image so that its largest dimension does not exceed max_dimension.
    Preserves aspect ratio.
    """
    width, height = image.size
    if max(width, height) <= max_dimension:
        return image

    if width > height:
        new_width = max_dimension
        new_height = int(height * (max_dimension / width))
    else:
        new_height = max_dimension
        new_width = int(width * (max_dimension / height))

    return image.resize((new_width, new_height), Image.Resampling.LANCZOS)
