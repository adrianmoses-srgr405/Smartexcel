"""
Skrip Pelatihan Ulang (Retraining) AI Formula Classifier Smart Excel.

Cara Penggunaan:
    cd backend
    python train_model.py
"""

import sys
from pathlib import Path

# Pastikan folder backend ada di sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd
from sklearn.metrics import classification_report, accuracy_score
from app.services.ml_classifier import ml_classifier

def main():
    print("=" * 60)
    print("  PELATIHAN MODEL AI - SMART EXCEL FORMULA CLASSIFIER")
    print("=" * 60)
    
    csv_path = ml_classifier.training_csv_path
    print(f"\n[1] Membaca dataset latihan dari:")
    print(f"    -> {csv_path}")
    
    if not csv_path.exists():
        print(f"[ERROR] File dataset {csv_path} tidak ditemukan!")
        return

    df = pd.read_csv(csv_path)
    print(f"    -> Total data latih: {len(df)} baris")
    print(f"    -> Distribusi Formula: {df['formula_label'].value_counts().to_dict()}")

    print("\n[2] Memulai proses training Random Forest...")
    success = ml_classifier.train_model()
    
    if success:
        print("\n[3] Model berhasil dilatih dan disimpan!")
        print(f"    -> Lokasi model: {ml_classifier.model_path}")
        print(f"    -> Jumlah fitur: {len(ml_classifier.feature_columns)}")
        print(f"    -> Kelas formula yang dipelajari: {list(ml_classifier.model.classes_)}")

        # Evaluasi akurasi pada dataset
        X_rows = []
        for _, row in df.iterrows():
            feat = {
                "operation": row.get("operation", "SUM"),
                "intent": row.get("intent", "aggregation"),
                "filter_count": row.get("filter_count", 0),
                "grouping_count": row.get("grouping_count", 0),
                "has_date_filter": row.get("has_date_filter", 0),
                "has_multiple_criteria": row.get("has_multiple_criteria", 0),
                "target_data_type": row.get("target_data_type", "numeric"),
                "filter_data_type": "date" if row.get("has_date_filter", 0) else "categorical"
            }
            X_rows.append(ml_classifier._extract_feature_vector(feat))
        
        X = pd.concat(X_rows, ignore_index=True)
        for col in ml_classifier.feature_columns:
            if col not in X.columns:
                X[col] = 0
        X = X[ml_classifier.feature_columns]
        y_true = df["formula_label"].values
        y_pred = ml_classifier.model.predict(X)

        acc = accuracy_score(y_true, y_pred)
        print(f"\n[4] Metrik Evaluasi Model:")
        print(f"    -> Training Accuracy: {acc * 100:.2f}%")
        print("\nClassification Report:")
        print(classification_report(y_true, y_pred, zero_division=0))
        print("=" * 60)
        print("  SELESAI: AI Siap digunakan untuk prediksi formula Excel!")
        print("=" * 60)
    else:
        print("\n[ERROR] Pelatihan model gagal. Pastikan scikit-learn terinstall.")

if __name__ == "__main__":
    main()
