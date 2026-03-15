import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import joblib
import os

MODEL_PATH = "../database/deal_model.pkl"
DATA_PATH = "../database/training_data.csv"


def preprocess_data(data):
    """
    Clean dataset before training
    """

    # Fill missing values
    data = data.fillna({
        "price": 0,
        "discount": 0,
        "rating": 0,
        "offer": 0,
        "availability": 1,
        "chosen": 0
    })

    # Convert availability True/False → 1/0
    data["availability"] = data["availability"].apply(lambda x: 1 if x in [1, True, "True", "true"] else 0)

    return data


def train_model():

    if not os.path.exists(DATA_PATH):
        print("❌ training_data.csv not found")
        return

    # Load dataset
    data = pd.read_csv(DATA_PATH)

    # Clean dataset
    data = preprocess_data(data)

    # Features (IMPORTANT: must match scorer.py)
    X = data[["price", "discount", "rating", "offer", "availability"]]
    y = data["chosen"]

    # RandomForest (best for this project)
    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=6,
        random_state=42
    )

    # Train model
    model.fit(X, y)

    # Save model
    joblib.dump(model, MODEL_PATH)

    print("✅ ML Model trained and saved successfully.")


def load_model():
    """
    Safely load model without crashing system
    """
    if not os.path.exists(MODEL_PATH):
        print("⚠ Model not found. Training new model...")
        train_model()

    try:
        return joblib.load(MODEL_PATH)
    except:
        print("⚠ Failed to load model. Using fallback.")
        return None


if __name__ == "__main__":
    train_model()