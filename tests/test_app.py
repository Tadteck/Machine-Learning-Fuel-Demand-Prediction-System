import pytest
from app import app, create_access_token

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def token(client):
    response = client.post('/login', json={
        'username': 'testuser',
        'password': 'testpassword'
    })
    return response.json['access_token']

def test_predict(client, token):
    response = client.post('/predict', json={
        'temperature': 22,
        'holiday': 0,
        'fuel_price': 1.3
    }, headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200
    assert 'prediction' in response.json

def test_get_predictions(client, token):
    response = client.get('/predictions', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200