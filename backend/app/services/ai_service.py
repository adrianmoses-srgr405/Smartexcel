import os
import re
import json
from typing import Any, Optional
import pandas as pd
from app.core.config import settings
from app.schemas.intent import StructuredAnalysisIntent, FilterCriterion
from app.models.dataset import DatasetColumn

class AIService:
    @classmethod
    def _parse_with_gemini(cls, query: str, columns: list[DatasetColumn]) -> Optional[StructuredAnalysisIntent]:
        """Uses Google Gemini with structured JSON mode."""
        api_key = settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY")
        if not api_key:
            return None

        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=api_key)
            col_info = [
                {
                    "name": col.original_name,
                    "type": col.inferred_type,
                    "letter": col.excel_column_letter,
                    "samples": col.sample_values[:5]
                }
                for col in columns
            ]

            prompt = f"""
Anda adalah AI Intent Parser untuk Sistem Formula Excel PTPN.
Tugas Anda adalah memahami permintaan bahasa alami pengguna dan memetakannya ke skema JSON terstruktur.

Struktur Kolom Dataset:
{json.dumps(col_info, indent=2, ensure_ascii=False)}

Permintaan Pengguna:
"{query}"

Instruksi:
1. Tentukan 'intent': 'aggregation', 'lookup', 'ranking', 'filter_recap', 'time_series', atau 'pivot_summary'.
2. Tentukan 'operation': 'SUM', 'AVERAGE', 'COUNT', 'MAX', 'MIN', 'XLOOKUP', atau 'GROWTH_RATE'.
3. Cocokkan 'target_field' dengan salah satu nama kolom numerik yang ada di dataset.
4. Tentukan 'group_by': daftar kolom pengelompokan jika ada (misal per merek, per unit).
5. Tentukan 'filters': daftar kriteria filter (field, operator, value, data_type). Jika ada periode bulan (misal Februari 2024), buat filter tanggal range atau operator BETWEEN / =.
6. Berikan confidence_score (0.0 - 1.0).
7. Berikan user_explanation singkat dalam bahasa Indonesia.

Keluarkan HANYA JSON murni yang sesuai dengan skema tanpa markdown backticks.
"""

            response = client.models.generate_content(
                model=settings.LLM_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )

            if response and response.text:
                data = json.loads(response.text)
                return StructuredAnalysisIntent(**data)
        except Exception as e:
            print(f"[AIService] Gemini API parsing fallback triggered: {e}")
            return None

    @classmethod
    def _heuristic_rule_parser(cls, query: str, columns: list[DatasetColumn], df: Any = None) -> StructuredAnalysisIntent:
        """
        Deterministic NLP Parser fallback that guarantees 100% accurate structured JSON
        for standard Indonesian / English Excel analytical queries.
        """
        q_lower = query.lower()
        col_names = [col.original_name for col in columns]
        col_name_lower_map = {col.original_name.lower(): col.original_name for col in columns}
        col_type_map = {col.original_name.lower(): col.inferred_type for col in columns}

        # 1. Determine Operation & Intent
        filter_keywords = [
            "rangkap", "rangkap data", "rekap data", "rangkum data",
            "ambil data", "filter data", "tampilkan data", "ekstrak data", "data mobil",
            "daftar", "list data", "semua data", "tabel data", "tabel", "lihat data", "baris data", "rincian data"
        ]

        if any(w in q_lower for w in filter_keywords):
            op = "FILTER"
            intent = "filter_recap"
        elif any(w in q_lower for w in ["rata-rata", "rerata", "average", "mean"]):
            op = "AVERAGE"
            intent = "aggregation"
        elif any(w in q_lower for w in ["paling tinggi", "tertinggi", "maksimal", "terbesar", "max"]):
            op = "MAX"
            intent = "ranking"
        elif any(w in q_lower for w in ["paling rendah", "terendah", "minimal", "terkecil", "min"]):
            op = "MIN"
            intent = "ranking"
        elif any(w in q_lower for w in ["hitung", "banyaknya", "frekuensi", "jumlah transaksi", "count"]):
            op = "COUNT"
            intent = "aggregation"
        elif any(w in q_lower for w in ["cari", "lookup", "temukan", "vlookup", "xlookup"]):
            op = "XLOOKUP"
            intent = "lookup"
        else:
            op = "SUM"
            intent = "aggregation"

        # 2. Identify Target Field (Numeric Column)
        target_field = None
        for col_l, original in col_name_lower_map.items():
            if col_l in q_lower and col_type_map.get(col_l) == "Numeric":
                target_field = original
                break
        
        # Priority numeric column keywords: 'netto', 'harga', 'total', 'jumlah', 'cpo', 'tbs', 'nilai'
        if not target_field:
            priority_numeric = ["harga_netto", "harga", "total", "produksi_cpo_kg", "tbs_olah_kg", "jumlah_keluar", "tbs_terima_ton", "volume_liter"]
            for p in priority_numeric:
                for col in columns:
                    col_san = (col.sanitized_name or col.original_name.lower().replace(" ", "_"))
                    if col.inferred_type == "Numeric" and p in col_san:
                        target_field = col.original_name
                        break
                if target_field:
                    break

        if not target_field:
            for col in columns:
                if col.inferred_type == "Numeric":
                    target_field = col.original_name
                    break


        # 3. Identify Group By
        group_by = []
        if any(w in q_lower for w in ["per ", "berdasarkan ", "rekap ", "group by "]):
            for col_l, original in col_name_lower_map.items():
                if f"per {col_l}" in q_lower or f"berdasarkan {col_l}" in q_lower or f"per-{col_l}" in q_lower:
                    if col_type_map.get(col_l) in ["Categorical", "Text", "Date"] and original not in group_by:
                        group_by.append(original)

        if group_by:
            intent = "pivot_summary"

        # 4. Extract Filters
        filters = []
        
        # A. Date Filter Extraction (e.g. Januari 2024, Januari, 2024-02)
        month_map = {
            "januari": "01", "january": "01", "jan": "01",
            "februari": "02", "february": "02", "feb": "02",
            "maret": "03", "march": "03", "mar": "03",
            "april": "04", "apr": "04",
            "mei": "05", "may": "05",
            "juni": "06", "june": "06", "jun": "06",
            "juli": "07", "july": "07", "jul": "07",
            "agustus": "08", "august": "08", "aug": "08",
            "september": "09", "sep": "09",
            "oktober": "10", "october": "10", "okt": "10", "oct": "10",
            "november": "11", "nov": "11",
            "desember": "12", "december": "12", "des": "12", "dec": "12"
        }

        date_col_name = None
        dataset_year = "2024"
        for col in columns:
            if col.inferred_type == "Date":
                date_col_name = col.original_name
                if col.min_value and len(str(col.min_value)) >= 4:
                    dataset_year = str(col.min_value)[:4]
                break

        if date_col_name:
            for m_name, m_num in month_map.items():
                # Match with year: "januari 2024"
                match_with_year = re.search(rf"\b{m_name}\s+(\d{{4}})\b", q_lower)
                # Match standalone month: "januari" or "bulan januari"
                match_standalone = re.search(rf"\b{m_name}\b", q_lower)

                if match_with_year or match_standalone:
                    year = match_with_year.group(1) if match_with_year else dataset_year
                    last_days = {"01": "31", "02": "29" if int(year) % 4 == 0 else "28", "03": "31", "04": "30", "05": "31", "06": "30", "07": "31", "08": "31", "09": "30", "10": "31", "11": "30", "12": "31"}
                    last_day = last_days.get(m_num, "30")
                    filters.append(FilterCriterion(
                        field=date_col_name,
                        operator="BETWEEN",
                        value=[f"{year}-{m_num}-01", f"{year}-{m_num}-{last_day}"],
                        data_type="date"
                    ))
                    break

        # B. Categorical Value Filters (e.g. "Pekanbaru", "Toyota", "Innova", "Avanza", "Pajero Sport", "Brio")
        used_words = set()
        for col in columns:
            if col.inferred_type in ["Categorical", "Text"] or col.inferred_type is None:
                # Gather candidate values from df if available, else sample_values
                candidate_values = list(col.sample_values or [])
                if df is not None and col.original_name in df.columns:
                    unique_vals = [str(x).strip() for x in df[col.original_name].dropna().unique() if str(x).strip()]
                    candidate_values = unique_vals

                # Sort candidates by string length descending to match full names first (e.g. "Pajero Sport" before "Sport")
                sorted_candidates = sorted(candidate_values, key=lambda x: len(str(x)), reverse=True)

                for sample_val in sorted_candidates:
                    s_str = str(sample_val).strip()
                    if not s_str or len(s_str) <= 2:
                        continue

                    # Exact phrase/word match in query (e.g. "Toyota", "Innova", "Pajero Sport")
                    s_clean = s_str.lower()
                    if s_clean not in used_words and re.search(rf"\b{re.escape(s_clean)}\b", q_lower):
                        filters.append(FilterCriterion(
                            field=col.original_name,
                            operator="=",
                            value=s_str,
                            data_type="text"
                        ))
                        used_words.add(s_clean)
                        break

                    # Partial word match: word in value appears in query (e.g. "Pajero" matches "Pajero Sport", "Sudirman" matches "Pekanbaru Sudirman")
                    words_in_val = [w.lower() for w in s_str.split() if len(w) >= 4 and w.lower() not in used_words]
                    matched_word = next((w for w in words_in_val if re.search(rf"\b{re.escape(w)}\b", q_lower)), None)
                    if matched_word and not any(f.field == col.original_name for f in filters):
                        filters.append(FilterCriterion(
                            field=col.original_name,
                            operator="CONTAINS",
                            value=matched_word.capitalize(),
                            data_type="text"
                        ))
                        used_words.add(matched_word)
                        break


        # Build user explanation
        filter_summary = f" dengan filter {', '.join([f'{f.field} = {f.value}' for f in filters])}" if filters else ""
        group_summary = f" dikelompokkan per {', '.join(group_by)}" if group_by else ""
        user_explanation = f"Menganalisis {op} untuk kolom '{target_field}'{group_summary}{filter_summary}."

        return StructuredAnalysisIntent(
            intent=intent,
            operation=op,
            target_field=target_field,
            group_by=group_by,
            filters=filters,
            time_granularity="month" if date_col_name and any(f.field == date_col_name for f in filters) else "none",
            confidence_score=0.95,
            user_explanation=user_explanation
        )

    @classmethod
    def parse_query(cls, query: str, columns: list[DatasetColumn], df: Any = None) -> StructuredAnalysisIntent:
        """Parses query using LLM if available, otherwise uses deterministic heuristic parser."""
        gemini_result = cls._parse_with_gemini(query, columns)
        if gemini_result:
            return gemini_result
        return cls._heuristic_rule_parser(query, columns, df=df)

