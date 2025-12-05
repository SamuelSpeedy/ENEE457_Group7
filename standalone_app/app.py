#!/usr/bin/env python3
"""
Standalone Malware Scanner Application
EMBER 2024 XGBoost Model with built-in web UI
"""

import os
import sys
from pathlib import Path

# Determine base path for bundled app or dev mode
if getattr(sys, 'frozen', False):
    # Running as PyInstaller bundle
    BASE_DIR = Path(sys._MEIPASS)
    APP_DIR = Path(os.path.dirname(sys.executable))
else:
    # Running as script
    BASE_DIR = Path(__file__).parent
    APP_DIR = BASE_DIR

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import uvicorn
import xgboost as xgb
import numpy as np
import joblib

# Import thrember for v3 feature extraction
try:
    import thrember
    THREMBER_AVAILABLE = True
    print("✓ thrember loaded for EMBER 2024 (v3 features)")
except ImportError:
    THREMBER_AVAILABLE = False
    print("✗ thrember not available")

app = FastAPI(title="Malware Scanner - EMBER 2024")

# CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PredictionResponse(BaseModel):
    label: str
    confidence: float
    model_version: str = "ember2024"

# ====== MODEL LOADING ======
def load_model():
    """Load EMBER 2024 XGBoost model and scaler."""
    # Look for models in multiple locations
    search_paths = [
        BASE_DIR / "models",
        APP_DIR / "models",
        BASE_DIR.parent / "models" / "ember2024",
        Path(__file__).parent.parent / "models" / "ember2024",
    ]
    
    model_path = None
    scaler_path = None
    
    for search_dir in search_paths:
        if not search_dir.exists():
            continue
        
        # Try to find model
        for name in ["model_ember2024_latest.json", "model_ember2024.json", "model.json"]:
            if (search_dir / name).exists():
                model_path = search_dir / name
                break
        
        # Try to find scaler
        for name in ["scaler_ember2024_latest.pkl", "scaler_ember2024.pkl", "scaler.pkl"]:
            if (search_dir / name).exists():
                scaler_path = search_dir / name
                break
        
        if model_path and scaler_path:
            break
    
    if not model_path:
        print(f"✗ Model not found. Searched: {[str(p) for p in search_paths]}")
        return None, None
    
    if not scaler_path:
        print(f"✗ Scaler not found")
        return None, None
    
    try:
        model = xgb.XGBClassifier()
        model.load_model(str(model_path))
        scaler = joblib.load(scaler_path)
        print(f"✓ Model loaded: {model_path}")
        print(f"✓ Scaler loaded: {scaler_path}")
        return model, scaler
    except Exception as e:
        print(f"✗ Error loading model: {e}")
        return None, None

model, scaler = load_model()

# ====== FEATURE EXTRACTION ======
def extract_features(file_bytes: bytes) -> np.ndarray:
    """Extract EMBER v3 features (2,568 dimensions)."""
    if not THREMBER_AVAILABLE:
        raise RuntimeError("thrember not installed")
    extractor = thrember.PEFeatureExtractor()
    features = np.array(extractor.feature_vector(file_bytes), dtype=np.float32)
    return features

# ====== PREDICTION ======
def predict_file(file_bytes: bytes):
    """Extract features and predict."""
    if model is None:
        return "Model not loaded", 0.0
    
    if not THREMBER_AVAILABLE:
        return "Feature extractor not available", 0.0
    
    try:
        features = extract_features(file_bytes)
        features = features.reshape(1, -1)
        features = np.nan_to_num(features, nan=0.0, posinf=1e10, neginf=-1e10)
        features_scaled = scaler.transform(features)
        
        if hasattr(model, "predict_proba"):
            probs = model.predict_proba(features_scaled)
            malicious_prob = float(probs[0][1])
        else:
            prediction = model.predict(features_scaled)
            malicious_prob = float(prediction[0])
        
        label = "malicious" if malicious_prob > 0.5 else "benign"
        return label, malicious_prob
        
    except Exception as e:
        print(f"Error during prediction: {e}")
        import traceback
        traceback.print_exc()
        return "Processing Error", 0.0

# ====== API ENDPOINTS ======
@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "model_loaded": model is not None,
        "thrember_available": THREMBER_AVAILABLE
    }

@app.post("/predict", response_model=PredictionResponse)
async def predict(file: UploadFile = File(...)):
    try:
        file_bytes = await file.read()
        if not file_bytes:
            raise HTTPException(status_code=400, detail="Empty file")
        
        label, confidence = predict_file(file_bytes)
        
        return PredictionResponse(
            label=label,
            confidence=confidence,
            model_version="ember2024"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {e}")

# ====== STATIC FILE SERVING ======
# Look for static files in multiple locations
static_paths = [
    BASE_DIR / "static",
    APP_DIR / "static",
    BASE_DIR.parent / "code" / "frontend" / "malware-ui" / "dist",
]

static_dir = None
for path in static_paths:
    if path.exists() and (path / "index.html").exists():
        static_dir = path
        break

if static_dir:
    print(f"✓ Serving static files from: {static_dir}")
    app.mount("/assets", StaticFiles(directory=str(static_dir / "assets")), name="assets")
    
    @app.get("/")
    async def serve_index():
        return FileResponse(str(static_dir / "index.html"))
    
    @app.get("/{path:path}")
    async def serve_static(path: str):
        file_path = static_dir / path
        if file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(static_dir / "index.html"))
else:
    print("⚠ No static files found - API only mode")
    
    @app.get("/")
    def read_root():
        return {"message": "Malware Scanner API", "docs": "/docs"}

def main():
    print("\n" + "="*50)
    print("  MALWARE SCANNER - EMBER 2024")
    print("="*50)
    print(f"\n  Open your browser to: http://localhost:8000\n")
    print("="*50 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

if __name__ == "__main__":
    main()
