import io
from PIL import Image, UnidentifiedImageError

def _process_and_save(img, fmt=None, quality=None):
    format_name = (fmt or img.format or "JPEG").upper()
    if format_name == "JPG":
        format_name = "JPEG"
    
    if format_name == "JPEG" and img.mode in ("RGBA", "P", "LA"):
        img = img.convert("RGB")
    
    out = io.BytesIO()
    kwargs = {}
    if quality is not None and format_name in ("JPEG", "WEBP"):
        kwargs["quality"] = quality
        
    img.save(out, format=format_name, **kwargs)
    
    mimetype = f"image/{format_name.lower()}"
    return out.getvalue(), mimetype

def resize(img_bytes: bytes, width: int, height: int):
    with Image.open(io.BytesIO(img_bytes)) as img:
        img_resized = img.resize((width, height))
        return _process_and_save(img_resized, fmt=img.format)

def compress(img_bytes: bytes, quality: int, format: str):
    with Image.open(io.BytesIO(img_bytes)) as img:
        return _process_and_save(img, fmt=format, quality=quality)

def convert(img_bytes: bytes, target_format: str):
    with Image.open(io.BytesIO(img_bytes)) as img:
        return _process_and_save(img, fmt=target_format)

def grayscale(img_bytes: bytes):
    with Image.open(io.BytesIO(img_bytes)) as img:
        img_gray = img.convert("L")
        return _process_and_save(img_gray, fmt=img.format)
