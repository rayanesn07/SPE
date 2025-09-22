import os
import sys
import pandas as pd
import numpy as np
import lightgbm as lgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    confusion_matrix, classification_report, roc_auc_score, f1_score, average_precision_score
)
from sklearn.preprocessing import OrdinalEncoder
import joblib

# --------- 1) Trouver le dataset d'entraînement ----------
candidates = ["prediction.xlsx", "prediciton.xlsx", "dataset_commandes.xlsx"]
data_path = None
for c in candidates:
    if os.path.exists(c):
        data_path = c
        break

if data_path is None:
    print("❌ Erreur : aucun dataset trouvé pour l’entraînement.")
    sys.exit(1)

print(f"📖 Lecture du fichier d’entraînement : {data_path}")
df = pd.read_excel(data_path)

# --------- 2) Normaliser les noms de colonnes ----------
df.columns = (
    df.columns.str.strip()
              .str.replace(" ", "_")
              .str.replace("-", "_")
              .str.replace("'", "_")
)

# --------- 3) Détection colonne cible ----------
possible_targets = ["fausse_commande", "fausse-commande", "fausse commande", "is_fake", "is fake", "isfake"]
target_col = None
for t in possible_targets:
    if t in df.columns.str.lower():
        target_col = [c for c in df.columns if c.lower() == t][0]
        break

if target_col is None:
    print("❌ Erreur : impossible de trouver la colonne cible (ex: 'is_fake').")
    sys.exit(1)

df = df.rename(columns={target_col: "is_fake"})
target = "is_fake"

# --------- 4) Features temporelles ----------
date_cols = [c for c in df.columns if "date" in c.lower() or "creation" in c.lower()]
if len(date_cols) > 0:
    date_col = date_cols[0]
    print("🕒 Colonne date trouvée :", date_col)
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df["year"] = df[date_col].dt.year.fillna(-1).astype(int)
    df["month"] = df[date_col].dt.month.fillna(-1).astype(int)
    df["day"] = df[date_col].dt.day.fillna(-1).astype(int)
    df["dayofweek"] = df[date_col].dt.dayofweek.fillna(-1).astype(int)
    df = df.drop(columns=[date_col])

# --------- 5) Préparation X / y ----------
y = df[target].astype(int)
X = df.drop(columns=[target])

# Nettoyage NaN
num_cols = X.select_dtypes(include=[np.number]).columns.tolist()
cat_cols = X.select_dtypes(include=["object", "category"]).columns.tolist()
X[num_cols] = X[num_cols].fillna(-999)
X[cat_cols] = X[cat_cols].fillna("NA")

# Encodage catégoriel
enc = None
if len(cat_cols) > 0:
    enc = OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)
    X[cat_cols] = enc.fit_transform(X[cat_cols])

X = X.astype(float)

# --------- 6) Split ----------
X_train, X_tmp, y_train, y_tmp = train_test_split(X, y, test_size=0.30, stratify=y, random_state=42)
X_val, X_test, y_val, y_test = train_test_split(X_tmp, y_tmp, test_size=0.5, stratify=y_tmp, random_state=42)

print("📊 Taille des sets -> train:", X_train.shape, "val:", X_val.shape, "test:", X_test.shape)

# --------- 7) Modèle ----------
model = lgb.LGBMClassifier(
    objective="binary",
    n_estimators=1000,
    learning_rate=0.05,
    num_leaves=31,
    class_weight="balanced",
    random_state=42,
    n_jobs=-1
)

model.fit(
    X_train, y_train,
    eval_set=[(X_val, y_val)],
    eval_metric="auc",
    callbacks=[lgb.early_stopping(50)]
)

# --------- 8) Sauvegarde ----------
joblib.dump(model, "lgb_model.joblib")
print("✅ Modèle sauvegardé -> lgb_model.joblib")

if enc is not None:
    joblib.dump(enc, "ordinal_encoder.joblib")
    print("✅ Encodeur sauvegardé -> ordinal_encoder.joblib")

print("\n🎉 Entraînement terminé avec succès !")
