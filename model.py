from sklearn.ensemble import RandomForestRegressor

def train_model():
    df = load_data()
    X = df[['temperature', 'holiday', 'fuel_price']]
    y = df['demand']
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X, y)
    return model