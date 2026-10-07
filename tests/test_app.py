import io
import pytest
from app import app
from PIL import Image

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def create_test_image(format='JPEG', mode='RGB', size=(100, 100), color='red'):
    img = Image.new(mode, size, color=color)
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format=format)
    return img_byte_arr.getvalue()

def test_health_returns_healthy_status(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "healthy"}

def test_resize_success(client):
    img_bytes = create_test_image()
    rv = client.post('/resize', data={
        'image': (io.BytesIO(img_bytes), 'test.jpg'),
        'width': '50',
        'height': '50'
    })
    assert rv.status_code == 200
    assert rv.mimetype == 'image/jpeg'
    
    img = Image.open(io.BytesIO(rv.data))
    assert img.size == (50, 50)

def test_resize_missing_image(client):
    rv = client.post('/resize', data={'width': '50', 'height': '50'})
    assert rv.status_code == 400
    assert 'error' in rv.json

def test_resize_bad_params(client):
    img_bytes = create_test_image()
    rv = client.post('/resize', data={
        'image': (io.BytesIO(img_bytes), 'test.jpg'),
        'width': '-50',
        'height': '50'
    })
    assert rv.status_code == 400
    assert 'error' in rv.json

def test_compress_success(client):
    img_bytes = create_test_image()
    rv = client.post('/compress', data={
        'image': (io.BytesIO(img_bytes), 'test.jpg'),
        'quality': '50',
        'format': 'JPEG'
    })
    assert rv.status_code == 200
    assert rv.mimetype == 'image/jpeg'

def test_convert_success(client):
    img_bytes = create_test_image(format='PNG')
    rv = client.post('/convert', data={
        'image': (io.BytesIO(img_bytes), 'test.png'),
        'format': 'WEBP'
    })
    assert rv.status_code == 200
    assert rv.mimetype == 'image/webp'

def test_grayscale_success(client):
    img_bytes = create_test_image(format='JPEG')
    rv = client.post('/grayscale', data={
        'image': (io.BytesIO(img_bytes), 'test.jpg')
    })
    assert rv.status_code == 200
    assert rv.mimetype == 'image/jpeg'
    img = Image.open(io.BytesIO(rv.data))
    assert img.mode == 'L'

def test_invalid_image(client):
    rv = client.post('/resize', data={
        'image': (io.BytesIO(b"not an image"), 'test.jpg'),
        'width': '50',
        'height': '50'
    })
    assert rv.status_code == 400
    assert 'error' in rv.json

def test_404(client):
    rv = client.get('/invalid-endpoint')
    assert rv.status_code == 404

def test_file_too_large(client):
    app.config['MAX_CONTENT_LENGTH'] = 100
    img_bytes = create_test_image(size=(100, 100)) 
    rv = client.post('/grayscale', data={
        'image': (io.BytesIO(img_bytes), 'test.jpg')
    })
    assert rv.status_code == 400
    assert 'error' in rv.json
