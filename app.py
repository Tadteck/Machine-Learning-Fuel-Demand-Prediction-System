from flask import Flask, request, jsonify
from pymongo import MongoClient
from model import train_model, predict_fuel_demand
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['fuel_demand_db']
predictions_collection = db['predictions']

# Train the model when the app starts
model = train_model()

# Define a route for predictions
@app.route('/predict', methods=['POST'])
def predict():
    try:
        # Log the request
        logger.info(f"Received request: {request.json}")
        # Get data from the request
        data = request.json
        # Validate input data
        if not data or 'temperature' not in data or 'holiday' not in data or 'fuel_price' not in data:
            logger.error("Invalid input data")
            return jsonify({'error': 'Invalid input data'}), 400
        # Make a prediction
        prediction = predict_fuel_demand(model, data)
        # Log the prediction
        logger.info(f"Prediction: {prediction}")
        # Store the prediction in MongoDB
        prediction_record = {
            'input_data': data,
            'prediction': prediction
        }
        predictions_collection.insert_one(prediction_record)
        # Return the prediction as JSON
        return jsonify({'prediction': prediction})
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Run the app
if __name__ == '__main__':
    app.run(debug=True)