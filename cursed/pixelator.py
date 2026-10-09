from PIL import Image

def pixelate_image(image: Image.Image, grid_size: int = 64, palette_colors: int = 16, output_size: int = 512) -> Image.Image:
    """
    Converts a standard image into a retro 16-bit pixel art style.
    """
    # Convert to RGB to ensure smooth palette quantization
    img = image.convert("RGB")

    # Crop to square to fit the standard card template
    width, height = img.size
    min_dim = min(width, height)
    left = (width - min_dim) / 2
    top = (height - min_dim) / 2
    img = img.crop((left, top, left + min_dim, top + min_dim))

    # 1. Downscale to pixel grid
    small_img = img.resize((grid_size, grid_size), Image.Resampling.BILINEAR)

    # 2. Quantize the color palette to mimic retro hardware
    quantized_img = small_img.quantize(colors=palette_colors)

    # 3. Upscale using Nearest Neighbor to retain hard edges
    pixel_art = quantized_img.resize((output_size, output_size), Image.Resampling.NEAREST)

    # Convert back to RGB for compatibility with Streamlit and final card rendering
    return pixel_art.convert("RGB")
