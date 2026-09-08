from fastapi import APIRouter

router = APIRouter()

PRESET_TEMPLATES = [
    {
        "id": "tutup-buku-pks-cpo-kebun",
        "name": "Laporan Tutup Buku Produksi CPO Bulanan per Asal Kebun",
        "category": "Tutup Buku PKS",
        "description": "Menghitung rekapitulasi total Produksi CPO (Kg) per Asal Kebun untuk periode bulan tertentu menggunakan formula SUMIFS / Pivot Agregasi PKS.",
        "default_query": "Buat rekap produksi CPO per asal kebun untuk Februari 2024",
        "operation": "SUM",
        "group_by": ["Asal Kebun"],
        "target_field": "Produksi CPO (Kg)",
        "time_filter": "monthly"
    },
    {
        "id": "rekap-tbs-olah-kebun",
        "name": "Rekapitulasi Total TBS Olah per Kebun",
        "category": "Operasional PKS",
        "description": "Menghitung total tonase Tandan Buah Segar (TBS) yang diolah per Asal Kebun di PKS.",
        "default_query": "Berapa total TBS Olah per asal kebun pada Februari 2024?",
        "operation": "SUM",
        "group_by": ["Asal Kebun"],
        "target_field": "TBS Olah (Kg)",
        "time_filter": "monthly"
    },
    {
        "id": "evaluasi-rendemen-oer",
        "name": "Evaluasi Rata-Rata Rendemen CPO (OER %) per Kebun",
        "category": "Efisiensi PKS",
        "description": "Menghitung rerata persentase Rendemen CPO (OER %) per Asal Kebun menggunakan formula AVERAGEIF / AVERAGEIFS.",
        "default_query": "Berapa rata-rata rendemen CPO per asal kebun?",
        "operation": "AVERAGE",
        "group_by": ["Asal Kebun"],
        "target_field": "Rendemen CPO (%)",
        "time_filter": "none"
    },
    {
        "id": "monitoring-mutu-alb-ffa",
        "name": "Monitoring Kualitas Mutu CPO: Kadar ALB / FFA (%)",
        "category": "Quality Control PKS",
        "description": "Mengevaluasi rata-rata kadar Asam Lemak Bebas (ALB / FFA %) dari CPO yang dihasilkan.",
        "default_query": "Berapa rata-rata kadar ALB per asal kebun?",
        "operation": "AVERAGE",
        "group_by": ["Asal Kebun"],
        "target_field": "Kadar ALB / FFA (%)",
        "time_filter": "none"
    },
    {
        "id": "rekor-produksi-cpo-puncak",
        "name": "Puncak Rekor Produksi CPO Harian PKS",
        "category": "Kinerja Produksi",
        "description": "Mendeteksi hari dengan pencapaian output Produksi CPO harian tertinggi menggunakan formula MAX.",
        "default_query": "Cari data dengan produksi CPO paling tinggi",
        "operation": "MAX",
        "group_by": [],
        "target_field": "Produksi CPO (Kg)",
        "time_filter": "none"
    }
]

@router.get("")
def list_report_templates():
    """List preset and custom report modeling templates."""
    return PRESET_TEMPLATES
