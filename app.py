from flask import Flask, request, jsonify, render_template
import pickle

app = Flask(__name__)

model = pickle.load(open("model.pkl", "rb"))
encoder = pickle.load(open("encoder.pkl", "rb"))


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/predict", methods=["POST"])
def predict():

    data = request.json
    product = data["product"]
    quantity = int(data["quantity"])

    product_encoded = encoder.transform([product])[0]

    prediction = model.predict([[product_encoded]])

    price = prediction[0][0]
    gst = prediction[0][1]
    discount = prediction[0][2]

    subtotal = price * quantity
    gst_amount = subtotal * gst / 100
    discount_amount = subtotal * discount / 100

    total = subtotal + gst_amount - discount_amount

    return jsonify(
        {
            # Return the subtotal (unit price * quantity) as the displayed "price".
            # This makes the UI update the shown price based on quantity.
            "price": round(subtotal, 2),
            "gst": round(gst, 2),
            "discount": round(discount, 2),
            "total": round(total, 2),
        }
    )


if __name__ == "__main__":
    app.run(debug=True)
