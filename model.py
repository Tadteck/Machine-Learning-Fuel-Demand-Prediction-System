import pandas as pd
from sklearn.linear_model import LinearRegression

# Load and preprocess data
def load_data():
    # Dummy dataset (replace with your actual data)
    data = {
        'temperature': [20, 25, 30, 15, 10],
        'holiday': [0, 1, 0, 0, 1],  # 0 = no holiday, 1 = holiday
        'fuel_price': [1.0, 1.2, 1.5, 0.9, 1.1],
        'demand': [800, 1000, 1200, 700, 900]  # Target variable
    }
    df = pd.DataFrame(data)
    return df

# Train the model
def train_model():
    df = load_data()
    X = df[['temperature', 'holiday', 'fuel_price']]
    y = df['demand']
    model = LinearRegression()
    model.fit(X, y)
    return model

# Make a prediction
def predict_fuel_demand(model, data):
    input_data = pd.DataFrame([data])
    prediction = model.predict(input_data)
    return prediction[0]