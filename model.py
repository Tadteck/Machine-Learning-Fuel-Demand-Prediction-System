from sklearn.ensemble import RandomForestRegressor
import pandas as pd
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_data():
    # Placeholder function to load data
    # Replace this with your actual data loading logic
    data = {
        'temperature': [20, 21, 19, 22, 20],
        'holiday': [0, 1, 0, 0, 1],
        'fuel_price': [3.5, 3.6, 3.4, 3.7, 3.5],
        'demand': [100, 150, 90, 200, 120]
    }
    df = pd.DataFrame(data)
    return df

def train_model():
    try:
        df = load_data()
        X = df[['temperature', 'holiday', 'fuel_price']]
        y = df['demand']
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X, y)
        logger.info("Model trained successfully")
        return model
    except Exception as error:
        logger.error(f"Error training model: {str(error)}")
        return None

def predict_fuel_demand(model, data):
    try:
        X_new = pd.DataFrame([data])
        prediction = model.predict(X_new)
        return prediction[0]
    except Exception as e:
        logger.error(f"Error predicting fuel demand: {str(e)}")
        return None