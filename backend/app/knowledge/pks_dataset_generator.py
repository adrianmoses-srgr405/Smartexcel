import pandas as pd
import numpy as np

def generate_pks_cpo_dataset() -> pd.DataFrame:
    """
    Generates realistic, rich monthly PKS (Pabrik Kelapa Sawit) CPO production dataset
    for PTPN operational tutup buku reporting.
    """
    dates = pd.date_range(start="2024-02-01", end="2024-02-29", freq="D")
    kebun_list = ["Kebun Tandun", "Kebun Sei Galuh", "Kebun Terantam", "Kebun Lubuk Dalam", "Kebun Sei Rokan"]
    
    rows = []
    np.random.seed(42)
    
    for dt in dates:
        date_str = dt.strftime("%A, %d %B %Y")
        for kebun in kebun_list:
            # Typical TBS Olah per kebun daily: 45,000 - 120,000 Kg
            tbs_olah = int(np.random.randint(450, 1200) * 100)
            
            # Rendemen CPO (OER) typically 21.0% - 24.5%
            oer_pct = round(np.random.uniform(21.5, 24.2), 2)
            cpo_prod = int(round(tbs_olah * (oer_pct / 100.0)))
            
            # Kernel Rendemen typically 4.5% - 6.0%
            ker_pct = round(np.random.uniform(4.8, 5.8), 2)
            kernel_prod = int(round(tbs_olah * (ker_pct / 100.0)))
            
            # Quality metrics
            ffa_alb = round(np.random.uniform(2.8, 4.2), 2)  # Asam Lemak Bebas (%)
            kadar_air = round(np.random.uniform(0.15, 0.25), 2) # Kadar Air (%)
            jam_olah = round(np.random.uniform(14.0, 22.5), 1)
            
            rows.append({
                "Tanggal": date_str,
                "Kode PKS": "PKS-TDN01",
                "Asal Kebun": kebun,
                "TBS Olah (Kg)": tbs_olah,
                "Produksi CPO (Kg)": cpo_prod,
                "Rendemen CPO (%)": oer_pct,
                "Produksi Kernel (Kg)": kernel_prod,
                "Kadar ALB / FFA (%)": ffa_alb,
                "Kadar Air (%)": kadar_air,
                "Jam Olah (Jam)": jam_olah
            })
            
    return pd.DataFrame(rows)

if __name__ == "__main__":
    df = generate_pks_cpo_dataset()
    print(f"Generated PKS dataset with {len(df)} rows and {len(df.columns)} columns.")
