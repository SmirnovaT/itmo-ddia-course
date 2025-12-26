from PIL import Image, ImageDraw, ImageFont
from io import BytesIO


def add_watermark(image_data: bytes, text: str = "PROCESSED") -> bytes:
    """
    Add watermark text to image
    
    Args:
        image_data: Original image bytes
        text: Watermark text
        
    Returns:
        Watermarked image bytes
    """
    img = Image.open(BytesIO(image_data))
    
    # Convert to RGBA for transparency
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    
    # Create transparent overlay
    overlay = Image.new('RGBA', img.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(overlay)
    
    # Calculate text size and position
    try:
        # Try to use a better font
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 40)
    except:
        # Fallback to default font
        font = ImageFont.load_default()
    
    # Get text bounding box
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    # Position in bottom right corner
    x = img.width - text_width - 20
    y = img.height - text_height - 20
    
    # Draw semi-transparent text
    draw.text((x, y), text, fill=(255, 255, 255, 180), font=font)
    
    # Composite overlay onto image
    watermarked = Image.alpha_composite(img, overlay)
    
    # Convert back to RGB
    watermarked = watermarked.convert('RGB')
    
    # Save to bytes
    output = BytesIO()
    watermarked.save(output, format='JPEG', quality=85)
    output.seek(0)
    
    return output.read()
