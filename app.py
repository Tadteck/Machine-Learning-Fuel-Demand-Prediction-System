from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from pymongo import MongoClient
from model import train_model, predict_fuel_demand
import logging
from schemas import PredictionInputSchema, UpdateDataSchema
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from marshmallow import Schema, fields, ValidationError
from redis import Redis

app = Flask(__name__)

@app.before_request
def log_request_info():
    logger.info(f"Request: {request.method} {request.path}")

@app.after_request
def log_response_info(response):
    logger.info(f"Response: {response.status}")
    return response

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure JWT
app.config['JWT_SECRET_KEY'] = 'your-secret-key'  # Change this to a secure key
jwt = JWTManager(app)

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['fuel_demand_db']
predictions_collection = db['predictions']
users_collection = db['users']

# Train the model when the app starts
model = train_model()

# Configure Redis for rate limiting
redis_client = Redis(host='localhost', port=6379)

# Configure rate limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    storage_uri="redis://localhost:6379"
)

# Define the schema for data validation
# class UpdateDataSchema(Schema):
#     temperature = fields.Float(required=True)
#     holiday = fields.Int(required=True)
#     fuel_price = fields.Float(required=True)
#     demand = fields.Int(required=True)

update_data_schema = UpdateDataSchema()

# User registration endpoint
@app.route('/register', methods=['POST'])
def register():
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({'error': 'Username and password are required'}), 400

        # Check if user already exists
        if users_collection.find_one({'username': username}):
            return jsonify({'error': 'Username already exists'}), 400

        # Save user to MongoDB
        users_collection.insert_one({'username': username, 'password': password})
        return jsonify({'message': 'User registered successfully'}), 201
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

# User login endpoint
@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')

        # Check if user exists
        user = users_collection.find_one({'username': username, 'password': password})
        if not user:
            return jsonify({'error': 'Invalid username or password'}), 401

        # Generate JWT token
        access_token = create_access_token(identity=username)
        return jsonify({'access_token': access_token}), 200
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return jsonify({'error': str(e)}), 500
    
#endpoint for update-data
@app.route('/update-data', methods=['POST'])
@jwt_required()
def update_data():
    try:
        logger.info(f"Received request: {request.json}")
        # Validate input data
        data = request.json
        errors = update_data_schema.validate(request.json)
        if errors:
            logger.error(f"Validation errors: {errors}")
            return jsonify({'error': errors}), 400
        data = request.json
        logger.info(f"Data to insert: {data}")
        # Save new data to MongoDB
        db['data'].insert_one(data)
        logger.info("Data inserted into MongoDB")
        # Retrain the model
        global model
        model = train_model()
        logger.info("Model retrained")
        return jsonify({'message': 'Data updated and model retrained'}), 200
    except ValidationError as ve:
        logger.error(f"Validation error: {ve.messages}")
        return jsonify({'error': ve.messages}), 400
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return jsonify({'error': str(e)}), 500     

# Validate prediction input
prediction_schema = PredictionInputSchema()

# Configure rate limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# Protected predict endpoint
@app.route('/predict', methods=['POST'])
@jwt_required()
def predict():
    try:
        # Validate input data
        errors = prediction_schema.validate(request.json)
        if errors:
            return jsonify({'error': errors}), 400
        data = request.json
        # Make a prediction
        prediction = predict_fuel_demand(model, data)
        # Store the prediction in MongoDB
        prediction_record = {
            'input_data': data,
            'prediction': prediction,
            'user': get_jwt_identity()
        }
        predictions_collection.insert_one(prediction_record)
        return jsonify({'prediction': prediction})
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Endpoint for predictions    
@app.route('/predictions', methods=['GET'])
@jwt_required()
def get_predictions():
    try:
        user = get_jwt_identity()
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        skip = (page - 1) * per_page
        predictions = list(predictions_collection.find({'user': user}, {'_id': 0}).skip(skip).limit(per_page))
        return jsonify(predictions), 200
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return jsonify({'error': str(e)}), 500
