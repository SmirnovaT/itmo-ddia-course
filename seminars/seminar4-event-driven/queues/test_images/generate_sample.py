#!/usr/bin/env python3
"""
Generate a sample test image
"""
from PIL import Image, ImageDraw, ImageFont
import random


def create_sample_image(width=1920, height=1080, filename="sample.jpg"):
    """Create a colorful sample image"""
    
    # Create base image
    img = Image.new('RGB', (width, height))
    draw = ImageDraw.Draw(img)
    
    # Random gradient background
    for y in range(height):
        r = int(255 * (y / height))
        g = int(128 + 127 * (1 - y / height))
        b = int(200 * (y / height))
        draw.line([(0, y), (width, y)], fill=(r, g, b))
    
    # Draw some shapes
    for _ in range(20):
        x1 = random.randint(0, width)
        y1 = random.randint(0, height)
        x2 = random.randint(x1, min(x1 + 200, width))
        y2 = random.randint(y1, min(y1 + 200, height))
        
        color = (
            random.randint(0, 255),
            random.randint(0, 255),
            random.randint(0, 255)
        )
        
        shape = random.choice(['rectangle', 'ellipse'])
        if shape == 'rectangle':
            draw.rectangle([x1, y1, x2, y2], fill=color, outline=(255, 255, 255), width=2)
        else:
            draw.ellipse([x1, y1, x2, y2], fill=color, outline=(255, 255, 255), width=2)
    
    # Add text
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)
    except:
        font = ImageFont.load_default()
    
    text = "Sample Test Image"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_x = (width - text_width) // 2
    text_y = height // 2
    
    # Text shadow
    draw.text((text_x + 3, text_y + 3), text, fill=(0, 0, 0), font=font)
    # Main text
    draw.text((text_x, text_y), text, fill=(255, 255, 255), font=font)
    
    # Save image
    img.save(filename, 'JPEG', quality=90)
    print(f"Created {filename} ({width}x{height})")


if __name__ == "__main__":
    create_sample_image()
