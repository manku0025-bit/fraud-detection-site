import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, IsolationForest
import joblib
import os

# Fake transaction dataset (demo)
data = pd.DataFrame({
    "amount": np.random.randint(100, 50000, 1000),
    "type": np.random.randint(0, 2, 1000),
    "device": np.random.randint(0, 2, 1000),
    "fraud": np.random.randint(0, 2, 1000)
})

X = data[["amount", "type", "device"]]
y = data["fraud"]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

# Models
lr = LogisticRegression()
rf = RandomForestClassifier()
iso = IsolationForest(contamination=0.2)

lr.fit(X_train, y_train)
rf.fit(X_train, y_train)
iso.fit(X_train)

os.makedirs("models", exist_ok=True)
joblib.dump(lr, "models/model_lr.pkl")
joblib.dump(rf, "models/model_rf.pkl")
joblib.dump(iso, "models/model_if.pkl")

print("✅ Models trained & saved")
