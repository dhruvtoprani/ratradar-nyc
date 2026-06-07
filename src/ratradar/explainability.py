from __future__ import annotations

import pandas as pd
import shap
from sklearn.pipeline import Pipeline


def compute_shap_values(
    pipeline: Pipeline, features: pd.DataFrame, *, max_rows: int = 5_000
) -> pd.DataFrame:
    sample = features.tail(max_rows)
    preprocessor = pipeline.named_steps["preprocessor"]
    model = pipeline.named_steps["model"]
    transformed = preprocessor.transform(sample)
    if hasattr(transformed, "toarray"):
        transformed = transformed.toarray()
    explainer = shap.TreeExplainer(model)
    values = explainer.shap_values(transformed)
    return pd.DataFrame(values, columns=preprocessor.get_feature_names_out())
