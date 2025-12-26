# Test Images

This directory contains sample images for testing the image processing system.

## Generate Sample Image

```bash
python generate_sample.py
```

This will create a `sample.jpg` file that you can use for testing.

## Usage Examples

### Upload single image
```bash
curl -X POST "http://localhost:8000/upload" \
  -F "file=@sample.jpg" \
  -F "operations=resize,watermark"
```

### Check job status
```bash
curl "http://localhost:8000/status/{job_id}"
```
