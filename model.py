from sklearn.ensemble import RandomForestRegressor
import pandas as pd
import logging
from functools import lru_cache

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_data():
    try:
        df = pd.read_csv('data/historical_data.csv')
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        logger.info("Data loaded successfully from historical_data.csv")
        return df
    except Exception as error:
        logger.error(f"Error loading data: {str(error)}")
        return None

def train_model():
    try:
        df = load_data()
        if df is None:
            raise ValueError("Data loading failed")
        X = df[['temperature', 'holiday', 'fuel_price']]
        y = df['demand']
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X, y)
        logger.info("Model trained successfully")
        return model
    except Exception as error:
        logger.error(f"Error training model: {str(error)}")
        return None

@lru_cache(maxsize=100)  # Cache up to 100 predictions
def predict_fuel_demand(model, temperature, holiday, fuel_price):
    try:
        input_data = pd.DataFrame([{
            'temperature': temperature,
            'holiday': holiday,
            'fuel_price': fuel_price
        }])
        prediction = model.predict(input_data)
        return prediction[0]
    except Exception as e:
        logger.error(f"Error predicting fuel demand: {str(e)}")
        return None