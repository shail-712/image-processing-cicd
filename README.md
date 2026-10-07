# Image Processing CI/CD Project

A Flask-based image processing service with Docker support and CI/CD pipelines.

## Endpoints

### `GET /health`
Returns the health status of the application.

```bash
curl http://localhost:5000/health
```

### `POST /resize`
Resizes an image to the specified width and height.

```bash
curl -X POST -F "image=@your_image.jpg" -F "width=200" -F "height=200" http://localhost:5000/resize --output resized.jpg
```

### `POST /compress`
Compresses an image to the specified quality (1-100).

```bash
curl -X POST -F "image=@your_image.jpg" -F "quality=50" -F "format=jpeg" http://localhost:5000/compress --output compressed.jpg
```

### `POST /convert`
Converts an image to the specified format (jpeg, png, webp).

```bash
curl -X POST -F "image=@your_image.png" -F "format=webp" http://localhost:5000/convert --output converted.webp
```

### `POST /grayscale`
Converts an image to grayscale.

```bash
curl -X POST -F "image=@your_image.jpg" http://localhost:5000/grayscale --output grayscale.jpg
```