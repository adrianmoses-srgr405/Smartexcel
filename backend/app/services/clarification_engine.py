from typing import Any, Dict, List, Optional

class ClarificationEngine:
    """
    Generates intelligent clarification options when:
    1. Query is underspecified / ambiguous (e.g., 'Hitung data Andi')
    2. An entity matches multiple columns (e.g., 'Andi' in Sales vs Manager)
    3. Composite confidence score drops below threshold (< 0.65)
    """

    @classmethod
    def generate_clarification(
        cls,
        query: str,
        reason: Optional[str] = None,
        ambiguity_type: str = "ambiguous_query",
        candidate_columns: Optional[List[str]] = None,
        entity_value: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Builds structured clarification payload.
        """
        options = []

        # Case 1: Ambiguous Parameter (Entity matches multiple columns)
        if ambiguity_type == "ambiguous_parameter" and candidate_columns and entity_value:
            for col in candidate_columns:
                options.append({
                    "id": f"select_col_{col.lower()}",
                    "label": f"Gunakan kolom '{col}' untuk '{entity_value}'",
                    "description": f"Hitung dengan filter {col} = '{entity_value}'",
                    "suggested_override": {"column": col, "value": entity_value}
                })

        # Case 2: Ambiguous Operation / Underspecified Target (e.g. 'Hitung data Andi')
        elif "hitung data" in query.lower() or ambiguity_type == "ambiguous_query":
            entity_name = entity_value or "Andi"
            options = [
                {
                    "id": "opt_sum",
                    "label": f"Hitung Total Nilai/Penjualan {entity_name} (SUMIFS)",
                    "description": f"Menjumlahkan seluruh nilai numerik untuk {entity_name}",
                    "suggested_formula": "SUMIFS",
                    "operation": "SUM"
                },
                {
                    "id": "opt_average",
                    "label": f"Hitung Rata-rata Penjualan {entity_name} (AVERAGEIFS)",
                    "description": f"Menghitung rata-rata nilai transaksi untuk {entity_name}",
                    "suggested_formula": "AVERAGEIFS",
                    "operation": "AVERAGE"
                },
                {
                    "id": "opt_count",
                    "label": f"Hitung Jumlah Transaksi/Baris {entity_name} (COUNTIF)",
                    "description": f"Menghitung frekuensi atau total kemunculan {entity_name}",
                    "suggested_formula": "COUNTIF",
                    "operation": "COUNT"
                }
            ]

        # Case 3: Missing Target Column
        elif ambiguity_type == "missing_target" and candidate_columns:
            for col in candidate_columns[:4]:
                options.append({
                    "id": f"target_col_{col.lower()}",
                    "label": f"Gunakan kolom '{col}' sebagai target perhitungan",
                    "description": f"Operasi akan dihitung terhadap nilai pada kolom {col}",
                    "suggested_override": {"target_column": col}
                })

        # Fallback default options
        if not options:
            options = [
                {
                    "id": "opt_total",
                    "label": "Hitung Total (SUM)",
                    "description": "Menjumlahkan kolom data",
                    "suggested_formula": "SUM"
                },
                {
                    "id": "opt_count",
                    "label": "Hitung Jumlah Transaksi (COUNT)",
                    "description": "Menghitung banyaknya baris transaksi",
                    "suggested_formula": "COUNT"
                }
            ]

        return {
            "needed": True,
            "status": "needs_clarification",
            "ambiguity_type": ambiguity_type,
            "reason": reason or "Query membutuhkan klarifikasi lebih lanjut untuk menentukan rumus yang tepat.",
            "options": options
        }
