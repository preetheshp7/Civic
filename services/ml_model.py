import tensorflow as tf
from flask import request, jsonify, Blueprint
from PIL import Image, ImageFile
import numpy as np
ml_bp = Blueprint("ml", __name__)
model = tf.keras.models.load_model("civic_issue_model.keras")


CLASSES = ["pothole", "garbage", "water"]

@ml_bp.route("/predict", methods=["POST"])
def predict():
        
    ImageFile.LOAD_TRUNCATED_IMAGES = True

    file = request.files.get("image")

    if not file or file.filename == "":
        return jsonify({"error": "No image file received"}), 400

    img = Image.open(file).convert("RGB").resize((224, 224))

    arr = np.expand_dims(np.array(img) / 255.0, axis=0)

    # 🔥 MODEL PREDICTION (MULTI-CLASS)
    preds = model.predict(arr)[0]        # e.g. [0.12, 0.81, 0.07]
    class_idx = np.argmax(preds)         # index of highest confidence
    confidence = preds[class_idx]

    classes = ["pothole", "garbage", "water"]
    issue = classes[class_idx]

    return jsonify({
        "prediction": issue,
        "confidence": float(confidence),
        "severity_score": round(float(confidence * 10), 2)
    })
