from flask import Flask, request, jsonify, render_template
import pickle
import uuid
from datetime import datetime
import os
import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestRegressor
from werkzeug.utils import secure_filename

app = Flask(__name__)

# ✅ Get correct base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = (
    500 * 1024 * 1024
)  # 500MB max file size for large datasets

# ✅ Allowed file extensions
ALLOWED_EXTENSIONS = {"csv"}

# ✅ Global variables for dynamic data
current_data = None
model = None
encoder = None


# ✅ Load initial model & encoder
def load_initial_model():
    global model, encoder, current_data
    model_path = os.path.join(BASE_DIR, "model.pkl")
    encoder_path = os.path.join(BASE_DIR, "encoder.pkl")

    if os.path.exists(model_path) and os.path.exists(encoder_path):
        with open(model_path, "rb") as f:
            model = pickle.load(f)
        with open(encoder_path, "rb") as f:
            encoder = pickle.load(f)
    else:
        # Fallback: train from default CSV if pickles don't exist
        products_path = os.path.join(BASE_DIR, "products.csv")
        if os.path.exists(products_path):
            retrain_model(products_path)


# ✅ Helper function to check allowed file extensions
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ✅ Default GST percentage if not provided in CSV
DEFAULT_GST = 18  # Standard GST percentage


def normalize_column_name(col_name):
    """Normalize column name by lowercasing, stripping, and removing underscores/spaces.

    Converts variations like 'unit_price', 'unit price', 'UnitPrice' to 'unitprice'.
    """
    normalized = col_name.strip().lower()
    # Remove spaces and underscores to match 'unitprice' with 'unit_price'
    normalized = normalized.replace("_", "").replace(" ", "")
    return normalized


def find_column(data, possible_names):
    """Find a column in dataframe using fuzzy matching of possible column names.

    Handles variations: 'unit_price', 'unitprice', 'Unit Price', 'UNITPRICE' all match.

    Args:
        data: DataFrame to search
        possible_names: List of possible column names to match

    Returns:
        str: The actual column name if found, None otherwise
    """
    normalized_data_cols = {normalize_column_name(col): col for col in data.columns}

    for possible_name in possible_names:
        normalized_name = normalize_column_name(possible_name)
        if normalized_name in normalized_data_cols:
            return normalized_data_cols[normalized_name]

    return None


def map_csv_columns(data):
    """Map CSV columns to standard column names (product, price, gst).

    Handles variations like:
    - product_name, itemname, product, item
    - unit_price, price, cost
    - gst, tax, tax_percentage

    Args:
        data: DataFrame loaded from CSV

    Returns:
        tuple: (mapped_data, warnings) where mapped_data is DataFrame with standard columns
    """
    # Possible column name variations (handles uppercase/lowercase/spaces/underscores)
    product_names = [
        "product",
        "Product"
        "product_name",
        "productname",
        "itemname",
        "item_name",
        "item",
        "product name",
        "item names",
        "item name",
        "name",
    ]
    price_names = [
        "price",
        "unit_price",
        "unitprice",
        "unit price",
        "cost",
        "amount",
        "rate",
        "selling_price",
        "sellingprice",
        "selling price",
        "unit_cost",
        "unitcost",
        "unit cost",
    ]
    gst_names = [
        "gst",
        "tax",
        "tax_percentage",
        "tax_pct",
        "gst_percentage",
        "gst_pct",
        "taxpercentage",
        "taxrate",
        "tax rate",
        "gst_rate",
        "gstrate",
        "gst rate",
        "percent",
        "percentage",
    ]

    warnings = []

    # Find product column (required)
    product_col = find_column(data, product_names)
    if not product_col:
        raise ValueError(f"Product column not found. Tried: {product_names}")

    # Find price column (required)
    price_col = find_column(data, price_names)
    if not price_col:
        raise ValueError(f"Price column not found. Tried: {price_names}")

    # Find GST column (optional - use default if not found)
    gst_col = find_column(data, gst_names)

    # Select only required columns for memory efficiency
    cols_to_select = [product_col, price_col]
    if gst_col:
        cols_to_select.append(gst_col)

    mapped_data = data[cols_to_select].copy()
    mapped_data.columns = ["product", "price"] + (["gst"] if gst_col else [])

    # ✅ Use default GST if column not found
    if not gst_col:
        mapped_data["gst"] = DEFAULT_GST
        warnings.append(f"GST/Tax column not found. Using default: {DEFAULT_GST}%")

    # ✅ Data type optimization for memory efficiency
    mapped_data["price"] = pd.to_numeric(mapped_data["price"], errors="coerce").astype(
        "float32"
    )
    mapped_data["gst"] = pd.to_numeric(mapped_data["gst"], errors="coerce").astype(
        "float32"
    )
    mapped_data["product"] = mapped_data["product"].astype("string")

    return mapped_data, warnings


# ✅ Function to retrain model with new data
def retrain_model(csv_path, chunksize=50000):
    """Retrain model with CSV data, optimized for large datasets.

    Args:
        csv_path: Path to CSV file
        chunksize: Number of rows to process at a time (for memory efficiency)
    """
    global model, encoder, current_data
    try:
        # ✅ Load CSV in chunks for memory efficiency
        chunks = []
        for chunk in pd.read_csv(csv_path, chunksize=chunksize):
            chunks.append(chunk)

        data = pd.concat(chunks, ignore_index=True)

        # ✅ Map flexible column names to standard format
        data, col_warnings = map_csv_columns(data)

        # ✅ Remove duplicates based on product name
        initial_rows = len(data)
        data = data.drop_duplicates(subset=["product"], keep="first")
        removed_duplicates = initial_rows - len(data)
        if removed_duplicates > 0:
            col_warnings.append(f"Removed {removed_duplicates} duplicate products")

        # ✅ Remove rows with missing values
        data = data.dropna()

        current_data = data.copy()

        # Encode product names
        encoder = LabelEncoder()
        data_copy = data.copy()
        data_copy["product"] = encoder.fit_transform(data["product"])

        # ✅ Features: product, Target: price and gst only (discount is dynamic)
        X = data_copy[["product"]].values
        y = data_copy[["price", "gst"]].values

        # ✅ Optimized RandomForest for large datasets:
        # - n_jobs=-1: Use all CPU cores in parallel
        # - max_depth: Limit depth to prevent overfitting on large datasets
        # - n_estimators: Reasonable number of trees
        # - min_samples_split: Prevent small leaf nodes
        model = RandomForestRegressor(
            n_estimators=100,
            max_depth=15,
            min_samples_split=10,
            min_samples_leaf=5,
            n_jobs=-1,  # ✅ Parallel processing
            random_state=42,
            verbose=0,
        )
        model.fit(X, y)

        return True, "Model retrained successfully", col_warnings
    except Exception as e:
        return False, str(e), []


# Initialize model
load_initial_model()

# ✅ Discount Rules based on product category
# If a product doesn't match any category, default discount is 0
DISCOUNT_RULES = {
    "Electronics": 15,  # 15% discount on electronics
    "Clothing": 20,  # 20% discount on clothing
    "Food": 5,  # 5% discount on food items
    "Stationery": 10,  # 10% discount on stationery
    "Office": 12,  # 12% discount on office supplies
}


def get_default_discount(product_name):
    """
    Get default discount percentage based on product name and category rules.

    Args:
        product_name: Name of the product

    Returns:
        float: Default discount percentage (0 if no match found)
    """
    product_lower = product_name.lower()

    # Check if product name contains category keywords
    for category, discount in DISCOUNT_RULES.items():
        category_keywords = {
            "Electronics": ["phone", "laptop", "computer", "tablet", "calculator"],
            "Clothing": ["shirt", "pants", "dress", "jacket", "coat"],
            "Food": ["food", "snack", "candy", "chocolate"],
            "Stationery": [
                "pen",
                "pencil",
                "notebook",
                "eraser",
                "marker",
                "file",
                "highlighter",
                "stapler",
                "scale",
            ],
            "Office": ["desk", "chair", "cabinet", "lamp"],
        }

        if category in category_keywords:
            if any(keyword in product_lower for keyword in category_keywords[category]):
                return discount

    # Default discount if no match
    return 0


def validate_discount(discount_value):
    """
    Validate discount percentage is within valid range (0-100).

    Args:
        discount_value: Discount percentage value

    Returns:
        tuple: (is_valid, error_message)
    """
    if discount_value is None:
        return True, None

    try:
        discount_float = float(discount_value)
        if discount_float < 0 or discount_float > 100:
            return False, f"Discount must be between 0 and 100, got {discount_float}"
        return True, None
    except (ValueError, TypeError):
        return False, f"Invalid discount value: {discount_value}"


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/products", methods=["GET"])
def get_products():
    global encoder
    if encoder is None:
        return jsonify({"products": [], "error": "No model loaded"}), 400

    known_products = list(encoder.classes_)
    return jsonify({"products": known_products})


@app.route("/upload_csv", methods=["POST"])
def upload_csv():
    try:
        # Check if file is present in request
        if "file" not in request.files:
            return jsonify({"error": "No file provided"}), 400

        file = request.files["file"]

        if file.filename == "":
            return jsonify({"error": "No file selected"}), 400

        if not allowed_file(file.filename):
            return jsonify({"error": "Only CSV files are allowed"}), 400

        # Save uploaded file
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)

        # Retrain model with new data
        success, message, warnings = retrain_model(filepath)

        if not success:
            return jsonify({"error": f"Failed to retrain model: {message}"}), 400

        return (
            jsonify(
                {
                    "success": True,
                    "message": message,
                    "warnings": warnings,
                    "products": list(encoder.classes_),
                }
            ),
            200,
        )

    except Exception as e:
        return jsonify({"error": f"Upload failed: {str(e)}"}), 500


@app.route("/current_csv", methods=["GET"])
def get_current_csv():
    global current_data
    if current_data is None:
        return jsonify({"data": []}), 200

    return (
        jsonify(
            {
                "data": current_data.to_dict(orient="records"),
                "columns": list(current_data.columns),
            }
        ),
        200,
    )


@app.route("/predict", methods=["POST"])
def predict():
    """Generate invoice with custom discount support.

    API Endpoint: POST /predict

    Request JSON format:
    {
        "items": [
            {
                "product": "product_name",
                "quantity": 1,
                "discount": 10
            }
        ]
    }
    """
    global model, encoder

    # Check if model is loaded
    if model is None or encoder is None:
        return (
            jsonify({"error": "No model loaded. Please upload a CSV file first."}),
            400,
        )

    data = request.json
    items = data.get("items", [])

    if not items:
        return jsonify({"error": "No items provided"}), 400

    result_items = []
    grand_subtotal = 0
    grand_gst_amount = 0
    grand_discount_amount = 0

    # ✅ Batch process all products for efficiency
    products_to_predict = []
    product_info = {}

    # First pass: validate all items and prepare batch
    for idx, item in enumerate(items):
        product = item["product"]
        quantity = int(item["quantity"])
        custom_discount = item.get("discount", None)

        # Validate custom discount if provided
        if custom_discount is not None:
            is_valid, error_msg = validate_discount(custom_discount)
            if not is_valid:
                return jsonify({"error": error_msg}), 400

        # Validate product exists
        try:
            product_encoded = encoder.transform([product])[0]
            products_to_predict.append([product_encoded])
            product_info[idx] = {
                "product": product,
                "quantity": quantity,
                "custom_discount": custom_discount,
            }
        except ValueError:
            return (
                jsonify({"error": f"Product '{product}' not found in current dataset"}),
                400,
            )

    # ✅ Batch prediction (MUCH faster than loop)
    X_batch = np.array(products_to_predict)
    predictions = model.predict(X_batch)

    # Second pass: calculate totals with predictions
    for idx, prediction in enumerate(predictions):
        info = product_info[idx]
        product = info["product"]
        quantity = info["quantity"]
        custom_discount = info["custom_discount"]

        unit_price = float(prediction[0])
        gst_pct = float(prediction[1])

        # Determine discount percentage
        if custom_discount is not None:
            discount_pct = float(custom_discount)
        else:
            discount_pct = get_default_discount(product)

        # ✅ Calculations with custom discount
        subtotal = unit_price * quantity
        gst_amount = subtotal * gst_pct / 100
        discount_amount = subtotal * discount_pct / 100
        item_total = subtotal + gst_amount - discount_amount

        # Accumulate totals
        grand_subtotal += subtotal
        grand_gst_amount += gst_amount
        grand_discount_amount += discount_amount

        result_items.append(
            {
                "product": product,
                "quantity": quantity,
                "unit_price": round(unit_price, 2),
                "subtotal": round(subtotal, 2),
                "gst_pct": round(gst_pct, 2),
                "gst_amount": round(gst_amount, 2),
                "discount_pct": round(discount_pct, 2),
                "discount_amount": round(discount_amount, 2),
                "item_total": round(item_total, 2),
            }
        )

    grand_total = grand_subtotal + grand_gst_amount - grand_discount_amount

    return jsonify(
        {
            "customer_id": "CUST-" + str(uuid.uuid4())[:8].upper(),
            "date": datetime.now().strftime("%d %b %Y, %I:%M %p"),
            "items": result_items,
            "summary": {
                "subtotal": round(grand_subtotal, 2),
                "total_gst": round(grand_gst_amount, 2),
                "total_discount": round(grand_discount_amount, 2),
                "grand_total": round(grand_total, 2),
            },
        }
    )


if __name__ == "__main__":
    app.run(debug=True)
