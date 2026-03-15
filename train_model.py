import pandas as pd
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestRegressor
import pickle

# load dataset
data = pd.read_csv("products.csv")

# encode product names
encoder = LabelEncoder()
data["product"] = encoder.fit_transform(data["product"])

# features and target
X = data[["product"]]
y = data[["price", "gst", "discount"]]

# train model
model = RandomForestRegressor()
model.fit(X, y)

# save model
pickle.dump(model, open("model.pkl", "wb"))
pickle.dump(encoder, open("encoder.pkl", "wb"))

print("Model trained successfully")