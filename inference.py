import pandas as pd
import joblib
from typing import Dict,Any

class ModelRunner:
    def __init__(self,model_path : str, version : str = "v.1.0.0"):
        self.model = joblib.load(model_path)
        self.version = version

    def predict(self, features : Dict[str,Any]):
        df = pd.DataFrame([features])
        y = self.model.predict(df)[0]
        prob = max(self.model.predict_proba(df)[0])
        return int(y),float(prob)