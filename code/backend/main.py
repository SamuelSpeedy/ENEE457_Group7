# backend/main.py
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# ====== PLACEHOLDER FOR YOUR MODEL IMPORTS ======
# Example:
# import joblib
# model = joblib.load("path/to/model.joblib")

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

class PredictionResponse(BaseModel):
    label: str
    confidence: float

# ====== YOUR MODEL HOOKS ======
def load_model():
    """
    Load your trained malware detection model here.
    This runs once when the server starts.
    """
    # Example:
    # import joblib
    # return joblib.load("model.pkl")
    return None  # Replace with the real model

model = load_model()

def predict_file(file_bytes: bytes):
    """
    Given file bytes, extract features and run model.predict / predict_proba.

    Return:
      (label: str, confidence: float)
    """

    # ---- TODO: your feature extraction here ----
    # Example pseudo-code:
    # features = extract_features_from_bytes(file_bytes)
    # proba = model.predict_proba([features])[0]
    # malicious_prob = float(proba[1])
    # label = "malicious" if malicious_prob > 0.5 else "benign"
    # return label, malicious_prob

    # TEMP dummy logic so the app runs:
    # Mark files larger than 1MB "malicious"
    size = len(file_bytes)
    if size > 1_000_000:
        return "malicious", 0.85
    else:
        return "benign", 0.90

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
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
