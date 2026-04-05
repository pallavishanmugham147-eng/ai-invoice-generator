# 🧾 Smart AI Invoice Generator

An intelligent, full-stack web application that automatically generates professional invoices for products. The system leverages a **Machine Learning model** to dynamically predict product prices, apply appropriate GST and discount algorithms, and reliably compile the final invoice total instantly.

This project sits at the intersection of Frontend Engineering, Backend API Design, and Applied Machine Learning to flawlessly automate the manual process of reading data and forming structured invoices. 

---

## 🚀 Key Features

* **Interactive Drag & Drop Interface:** Easily upload entire CSV files or drag specific products from your dataset directly onto your invoice canvas to intuitively generate rows. 
* **Drag-to-Reorder:** Visual grab handles allow you to rapidly sort and organize invoice item rows effortlessly.
* **Intelligent Auto-Calculation:** AI instantly calculates and predicts:
  * Baseline product price
  * Regional GST percentage algorithms
  * Dynamic category-specific discount rules
* **Customer Details Handling:** Accepts input for specific end-user context matching (Name and Phone) seamlessly injected into generated invoices.
* **Persistent Excel Storage (`.xlsx`):** Invoices aren't just one-offs; successfully generated invoices are permanently routed and recorded to a secure Excel workbook (`invoices.xlsx`. 
* **Download Hub & History:** Click seamlessly through the `View Invoices` interface and download your entire ledger directly onto your machine.
* **Premium UI/UX System:** Completely styled with modern glassmorphism elements, micro-animations, structured alerts, and interactive states to make navigation satisfying.

---

## 🧠 How It Works

1. **Supply Data**: Start by uploading/dragging a `.csv` file. The backend utilizes `pandas` to immediately cleanse the data, strip away anomalies, and train a specialized `RandomForestRegressor`. 
2. **Setup the Details**: Type in the Customer's Name and Phone Number directly onto the `New Invoice` dashboard.
3. **Assemble items**: Start manually typing rows, or visually **drag-and-drop** specific product badges into the collection area to instantly bind them!
4. **Predict & Display**: Hitting "Generate" pushes your data against the Scikit-learn Random Forest model, validating sub-pricing, evaluating GST percentages, and dynamically applying discounts. 
5. **Persistence Logs**: The backend logs your finalized document directly into an `invoices.xlsx` file accessible live across the frontend history pane.

---

## 🛠️ Tech Stack

### Frontend Architecture
- **Vanilla HTML5 + CSS3**: Sleek, fully responsive components written from scratch avoiding massive framework payloads.
- **Dynamic JavaScript**: Powerful DOM manipulation relying on the standard Drag & Drop API, native iterators, and `fetch` controllers.

### Backend Routing
- **Python + Flask**: High-performance HTTP server handling asynchronous interactions.
- **Pandas + OpenPyXL**: Powerful pipeline for mapping, aggregating, exporting, and parsing data models smoothly from CSV to Excel datasets.

### Machine Learning
- **Scikit-learn**: Leveraging label encoders and a `RandomForestRegressor` initialized explicitly for optimized large-dataset parsing.


