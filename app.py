from flask import Flask, request, jsonify, Response
from PIL import UnidentifiedImageError
import image_processor

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB

def get_image_bytes():
    if 'image' not in request.files:
        return None, "No image file provided in 'image' field"
    file = request.files['image']
    if not file or file.filename == '':
        return None, "Empty file"
    return file.read(), None

@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({"error": "File too large, max size is 5MB"}), 400

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({"error": "Method not allowed"}), 405

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

@app.get("/health")
def health():
    return {"status": "healthy"}, 200

@app.post("/resize")
def resize_endpoint():
    img_bytes, err = get_image_bytes()
    if err:
        return jsonify({"error": err}), 400
    
    try:
        width = int(request.form.get('width', 0))
        height = int(request.form.get('height', 0))
        if width <= 0 or height <= 0:
            return jsonify({"error": "width and height must be positive integers"}), 400
    except ValueError:
        return jsonify({"error": "width and height must be valid integers"}), 400
        
    try:
        out_bytes, mimetype = image_processor.resize(img_bytes, width, height)
        return Response(out_bytes, mimetype=mimetype)
    except UnidentifiedImageError:
        return jsonify({"error": "Invalid or corrupt image file"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.post("/compress")
def compress_endpoint():
    img_bytes, err = get_image_bytes()
    if err:
        return jsonify({"error": err}), 400
        
    try:
        quality = int(request.form.get('quality', 0))
        if not (1 <= quality <= 100):
            return jsonify({"error": "quality must be an integer between 1 and 100"}), 400
    except ValueError:
        return jsonify({"error": "quality must be a valid integer"}), 400
        
    fmt = request.form.get('format', 'JPEG')
    supported = ['jpeg', 'png', 'webp']
    if fmt.lower() not in supported:
        return jsonify({"error": f"Unsupported format. Supported: {supported}"}), 400
        
    try:
        out_bytes, mimetype = image_processor.compress(img_bytes, quality, fmt)
        return Response(out_bytes, mimetype=mimetype)
    except UnidentifiedImageError:
        return jsonify({"error": "Invalid or corrupt image file"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.post("/convert")
def convert_endpoint():
    img_bytes, err = get_image_bytes()
    if err:
        return jsonify({"error": err}), 400
        
    fmt = request.form.get('format', '')
    supported = ['jpeg', 'png', 'webp']
    if not fmt or fmt.lower() not in supported:
        return jsonify({"error": f"Unsupported format. Supported: {supported}"}), 400
        
    try:
        out_bytes, mimetype = image_processor.convert(img_bytes, fmt)
        return Response(out_bytes, mimetype=mimetype)
    except UnidentifiedImageError:
        return jsonify({"error": "Invalid or corrupt image file"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.post("/grayscale")
def grayscale_endpoint():
    img_bytes, err = get_image_bytes()
    if err:
        return jsonify({"error": err}), 400
        
    try:
        out_bytes, mimetype = image_processor.grayscale(img_bytes)
        return Response(out_bytes, mimetype=mimetype)
    except UnidentifiedImageError:
        return jsonify({"error": "Invalid or corrupt image file"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
