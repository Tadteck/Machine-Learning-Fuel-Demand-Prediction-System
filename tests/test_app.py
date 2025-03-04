import pytest
import sys
import os
from pymongo import MongoClient

# Add the backend directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture(autouse=True)
def cleanup_db():
    client = MongoClient('mongodb://localhost:27017/')
    db = client['fuel_demand_test_db']
    db['data'].delete_many({})
    db['predictions'].delete_many({})
    db['users'].delete_many({})

def test_register(client):
    response = client.post('/register', json={
        'username': 'Tadiwa',
        'password': '12345'
    })
    assert response.status_code == 201
    assert 'message' in response.json

def test_login(client):
    client.post('/register', json={
        'username': 'Tadiwa',
        'password': '12345'
    })
    response = client.post('/login', json={
        'username': 'Tadiwa',
        'password': '12345'
    })
    assert response.status_code == 200
    assert 'access_token' in response.json

def test_predict(client):
    client.post('/register', json={
        'username': 'Tadiwa',
        'password': '12345'
    })
    response = client.post('/login', json={
        'username': 'Tadiwa',
        'password': '12345'
    })
    token = response.json['access_token']
    response = client.post('/predict', json={
        'temperature': 22.0,
        'holiday': 0,
        'fuel_price': 1.3
    }, headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200
    assert 'prediction' in response.json

def test_get_predictions(client):
    client.post('/register', json={
        'username': 'Tadiwa',
        'password': '12345'
    })
    response = client.post('/login', json={
        'username': 'Tadiwa',
        'password': '12345'
    })
    token = response.json['access_token']
    response = client.get('/predictions', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200

def test_update_data(client):
    client.post('/register', json={
        'username': 'Tadiwa',
        'password': '12345'
    })
    response = client.post('/login', json={
        'username': 'Tadiwa',
        'password': '12345'
    })
    token = response.json['access_token']
    response = client.post('/update-data', json={
        'temperature': 25.0,
        'holiday': 1,
        'fuel_price': 1.5,
        'demand': 1000.0
    }, headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200
    assert 'message' in response.json