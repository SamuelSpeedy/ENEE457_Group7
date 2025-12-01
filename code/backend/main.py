# backend/main.py
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# ====== PLACEHOLDER FOR YOUR MODEL IMPORTS ======
import xgboost as xgb
import ember
import numpy as np
import os
from pathlib import Path
from sklearn.feature_extraction import FeatureHasher

# --- MONKEY PATCH START: Fix ember compatibility with recent scikit-learn ---
# The default ember library uses FeatureHasher with single strings, which recent scikit-learn rejects.
# We patch the class method to wrap inputs in a list, ensuring compatibility.
def fixed_section_info_process_raw_features(self, raw_obj):
    sections = raw_obj['sections']
    general = [
        len(sections),
        sum(1 for s in sections if s['size'] == 0),
        sum(1 for s in sections if s['name'] == ""),
        sum(1 for s in sections if 'MEM_READ' in s['props'] and 'MEM_EXECUTE' in s['props']),
        sum(1 for s in sections if 'MEM_WRITE' in s['props'])
    ]
    section_sizes = [(s['name'], s['size']) for s in sections]
    section_sizes_hashed = FeatureHasher(50, input_type="pair").transform([section_sizes]).toarray()[0]
    section_entropy = [(s['name'], s['entropy']) for s in sections]
    section_entropy_hashed = FeatureHasher(50, input_type="pair").transform([section_entropy]).toarray()[0]
    section_vsize = [(s['name'], s['vsize']) for s in sections]
    section_vsize_hashed = FeatureHasher(50, input_type="pair").transform([section_vsize]).toarray()[0]

    # PATCH: wrap raw_obj['entry'] in a list -> [[raw_obj['entry']]]
    entry_name_hashed = FeatureHasher(50, input_type="string").transform([[raw_obj['entry']]]).toarray()[0]

    characteristics = [p for s in sections for p in s['props'] if s['name'] == raw_obj['entry']]
    characteristics_hashed = FeatureHasher(50, input_type="string").transform([characteristics]).toarray()[0]

    return np.hstack([
        general, section_sizes_hashed, section_entropy_hashed, section_vsize_hashed, entry_name_hashed,
        characteristics_hashed
    ]).astype(np.float32)

# Apply the patch immediately after import
try:
    if hasattr(ember.features, 'SectionInfo'):
        ember.features.SectionInfo.process_raw_features = fixed_section_info_process_raw_features
        print("Monkey patch applied to ember.features.SectionInfo.process_raw_features.")
    else:
        print("Warning: Could not apply patch (SectionInfo not found).")
except Exception as e:
    print(f"Error applying monkey patch: {e}")
# --- MONKEY PATCH END ---

app = FastAPI()

# CORS so your React app (localhost:3000 or 5173 etc.) can call this API
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Malware Detection API is running. Send POST requests to /predict."}

class PredictionResponse(BaseModel):
    label: str
    confidence: float

import joblib

# ====== YOUR MODEL HOOKS ======
def load_model():
    """
    Load your trained malware detection model, scaler, and PCA.
    This runs once when the server starts.
    """
    current_dir = Path(os.path.dirname(__file__))
    project_root = current_dir.parent.parent  # Go up to ENEE457_Group7 root
    results_dir = project_root / "models"
    
    model_path = results_dir / "xgboost_pca_model.pkl"
    scaler_path = results_dir / "scaler.pkl"
    pca_path = results_dir / "pca_transform.pkl"

    if not (model_path.exists() and scaler_path.exists() and pca_path.exists()):
        print(f"Warning: Model files not found in {results_dir}")
        return None, None, None

    try:
        model = joblib.load(model_path)
        scaler = joblib.load(scaler_path)
        pca = joblib.load(pca_path)
            
        print(f"Model pipeline loaded from {results_dir}")
        return model, scaler, pca
    except Exception as e:
        print(f"Error loading model pipeline: {e}")
        return None, None, None

model, scaler, pca = load_model()

def predict_file(file_bytes: bytes):
    """
    Given file bytes, extract features and run model.predict / predict_proba.

    Return:
      (label: str, confidence: float)
    """
    if model is None:
        return "Model not loaded", 0.0

    try:
        # Extract features using EMBER
        extractor = ember.PEFeatureExtractor(2)
        features = np.array(extractor.feature_vector(file_bytes), dtype=np.float32)
        
        # Reshape for sklearn-like pipeline (1 sample, N features)
        features = features.reshape(1, -1)
        
        # Apply Scaling
        features_scaled = scaler.transform(features)
        
        # Apply PCA
        features_pca = pca.transform(features_scaled)
        
        # Predict
        # model.predict returns class labels, predict_proba returns probabilities
        if hasattr(model, "predict_proba"):
            probs = model.predict_proba(features_pca)
            malicious_prob = float(probs[0][1]) # Probability of class 1 (Malicious)
        else:
            # Fallback if predict_proba is not available
            prediction = model.predict(features_pca)
            malicious_prob = float(prediction[0])
        
        # Threshold tuned for better recall (default 0.5 was too conservative)
        THRESHOLD = 0.35
        label = "malicious" if malicious_prob > THRESHOLD else "benign"
        return label, malicious_prob
        
    except Exception as e:
        print(f"Error during prediction: {e}")
        import traceback
        traceback.print_exc()
        return "Processing Error", 0.0

# ====== API ENDPOINT ======
@app.post("/predict", response_model=PredictionResponse)
async def predict(file: UploadFile = File(...)):
    
    try:
        file_bytes = await file.read()
        if not file_bytes:
            raise HTTPException(status_code=400, detail="Empty file")

        label, confidence = predict_file(file_bytes)

        return PredictionResponse(
            label=label,
            confidence=confidence
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {e}")

if __name__ == "__main__":
    print("Starting server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
