import xgboost as xgb
import numpy as np
import os
from pathlib import Path

# EMBER 2018 (version 2) has 2381 features
NUM_FEATURES = 2381

def create_dummy_model():
    print("Creating dummy model with 2381 features...")
    # Create random training data
    X = np.random.rand(10, NUM_FEATURES)
    y = np.random.randint(0, 2, 10)

    # Train a small model
    model = xgb.XGBClassifier(n_estimators=10, max_depth=3)
    model.fit(X, y)

    # Save to backend/malware_model.json
    output_path = Path("xgboost_model_results") / "malware_model.json"
    # Ensure backend dir exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    model.save_model(str(output_path))
    print(f"Dummy model saved to {output_path}")

if __name__ == "__main__":
    create_dummy_model()