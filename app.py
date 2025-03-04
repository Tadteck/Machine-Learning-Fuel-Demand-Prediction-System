from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from pymongo import MongoClient
from model import train_model, predict_fuel_demand
import logging
from schemas import PredictionInputSchema, UpdateDataSchema
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from marshmallow import Schema, fields, ValidationError
from flask_swagger_ui import get_swaggerui_blueprint

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

# Configure rate limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# Define the schema for data validation
class UpdateDataSchema(Schema):
    temperature = fields.Float(required=True)
    holiday = fields.Int(required=True)
    fuel_price = fields.Float(required=True)
    demand = fields.Int(required=True)

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

# Validate prediction input
prediction_schema = PredictionInputSchema()

@app.route('/predict', methods=['POST'])
@jwt_required()
def predict():
    try:
        # Validate input data
        errors = prediction_schema.validate(request.json)
        if errors:
            return jsonify({'error': errors}), 400
        data = request.json
        # Make a prediction (using cached function)
        prediction = predict_fuel_demand(model, data['temperature'], data['holiday'], data['fuel_price'])
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

@app.route('/update-data', methods=['POST'])
@jwt_required()
def update_data():
    try:
        # Validate input data
        errors = update_data_schema.validate(request.json)
        if errors:
            return jsonify({'error': errors}), 400
        data = request.json
        # Save new data to MongoDB
        db['data'].insert_one(data)
        # Retrain the model
        global model
        model = train_model()
        return jsonify({'message': 'Data updated and model retrained'}), 200
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Swagger UI configuration
SWAGGER_URL = '/api/docs'  # URL for accessing Swagger UI
API_URL = '/swagger.yaml'  # URL for the Swagger YAML file

# Create Swagger UI blueprint
swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={'app_name': "Fuel Demand Prediction API"}
)

# Register the blueprint
app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

# Serve the Swagger YAML file
@app.route('/swagger.yaml')
def serve_swagger():
    return app.send_static_file('swagger.yaml')

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
