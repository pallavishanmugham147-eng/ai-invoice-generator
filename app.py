from flask import Flask, request, jsonify, render_template
import pickle
import uuid
from datetime import datetime
import os

app = Flask(__name__)

# ✅ Get correct base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ✅ Correct file paths
model_path = os.path.join(BASE_DIR, "model.pkl")
encoder_path = os.path.join(BASE_DIR, "encoder.pkl")

# ✅ Load model & encoder safely
with open(model_path, "rb") as f:
    model = pickle.load(f)

with open(encoder_path, "rb") as f:
    encoder = pickle.load(f)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/products", methods=["GET"])
def get_products():
    known_products = list(encoder.classes_)
    return jsonify({"products": known_products})


@app.route("/predict", methods=["POST"])
def predict():
    data = request.json
    items = data.get("items", [])

    if not items:
        return jsonify({"error": "No items provided"}), 400

    result_items = []
    grand_subtotal = 0
    grand_gst_amount = 0
    grand_discount_amount = 0

    for item in items:
        product = item["product"]
        quantity = int(item["quantity"])

        # Encode product
        product_encoded = encoder.transform([product])[0]

        # Predict
        prediction = model.predict([[product_encoded]])

        unit_price = prediction[0][0]
        gst_pct = prediction[0][1]
        discount_pct = prediction[0][2]

        # Calculations
        subtotal = unit_price * quantity
        gst_amount = subtotal * gst_pct / 100
        discount_amount = subtotal * discount_pct / 100
        item_total = subtotal + gst_amount - discount_amount

        grand_subtotal += subtotal
        grand_gst_amount += gst_amount
        grand_discount_amount += discount_amount

        result_items.append({
            "product": product,
            "quantity": quantity,
            "unit_price": round(unit_price, 2),
            "subtotal": round(subtotal, 2),
            "gst_pct": round(gst_pct, 2),
            "gst_amount": round(gst_amount, 2),
            "discount_pct": round(discount_pct, 2),
            "discount_amount": round(discount_amount, 2),
            "item_total": round(item_total, 2),
        })

    grand_total = grand_subtotal + grand_gst_amount - grand_discount_amount

    return jsonify({
        "customer_id": "CUST-" + str(uuid.uuid4())[:8].upper(),
        "date": datetime.now().strftime("%d %b %Y, %I:%M %p"),
        "items": result_items,
        "summary": {
            "subtotal": round(grand_subtotal, 2),
            "total_gst": round(grand_gst_amount, 2),
            "total_discount": round(grand_discount_amount, 2),
            "grand_total": round(grand_total, 2),
        }
    })


if __name__ == "__main__":
    app.run(debug=True)