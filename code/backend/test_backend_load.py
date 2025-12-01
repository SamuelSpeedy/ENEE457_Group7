import sys
import os

# Add the directory containing main.py to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

try:
    from main import load_model, predict_file
    print("Successfully imported load_model and predict_file from main.py")
    model, scaler, pca = load_model()
    if model:
        print("Model loaded successfully!")
    else:
        print("Model loading failed or returned None.")

    # Test predict_file with dummy bytes
    dummy_file_bytes = b"This is a dummy file content for testing."
    label, confidence = predict_file(dummy_file_bytes)
    print(f"Dummy prediction: Label={label}, Confidence={confidence}")

except Exception as e:
    print(f"An error occurred during import or model loading: {e}")
    import traceback
    traceback.print_exc()
