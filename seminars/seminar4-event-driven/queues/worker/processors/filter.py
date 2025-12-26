from PIL import Image, ImageFilter
from io import BytesIO


def apply_filter(image_data: bytes, filter_type: str = "blur") -> bytes:
    """
    Apply filter to image
    
    Args:
        image_data: Original image bytes
        filter_type: Type of filter (blur, sharpen, contour, emboss)
        
    Returns:
        Filtered image bytes
    """
    img = Image.open(BytesIO(image_data))
    
    # Convert to RGB if needed
    if img.mode in ('RGBA', 'LA', 'P'):
        img = img.convert('RGB')
    
    # Apply filter based on type
    filters = {
        'blur': ImageFilter.BLUR,
        'sharpen': ImageFilter.SHARPEN,
        'contour': ImageFilter.CONTOUR,
        'emboss': ImageFilter.EMBOSS,
        'edge': ImageFilter.FIND_EDGES,
        'smooth': ImageFilter.SMOOTH
    }
    
    filter_obj = filters.get(filter_type.lower(), ImageFilter.BLUR)
    filtered_img = img.filter(filter_obj)
    
    # Save to bytes
    output = BytesIO()
    filtered_img.save(output, format='JPEG', quality=85)
    output.seek(0)
    
    return output.read()
