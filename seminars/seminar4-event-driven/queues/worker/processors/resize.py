from PIL import Image
from io import BytesIO


def resize_image(image_data: bytes, width: int = 800, height: int = 600) -> bytes:
    """
    Resize image to specified dimensions
    
    Args:
        image_data: Original image bytes
        width: Target width
        height: Target height
        
    Returns:
        Resized image bytes
    """
    img = Image.open(BytesIO(image_data))
    
    # Convert RGBA to RGB if needed
    if img.mode in ('RGBA', 'LA', 'P'):
        background = Image.new('RGB', img.size, (255, 255, 255))
        if img.mode == 'P':
            img = img.convert('RGBA')
        background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
        img = background
    
    # Resize maintaining aspect ratio
    img.thumbnail((width, height), Image.Resampling.LANCZOS)
    
    # Save to bytes
    output = BytesIO()
    img.save(output, format='JPEG', quality=85)
    output.seek(0)
    
    return output.read()
