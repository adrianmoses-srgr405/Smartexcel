import os
import re
import json
import logging
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

class TaskDecomposer:
    """
    Semantic Multi-Task Decomposer for Smart Excel.
    Decomposes complex natural language queries into independent, structured tasks:
    - Preserves user task order
    - Inherits shared context (target terms, date ranges, global filters)
    - Supports task-specific context overrides
    - Deduplicates identical tasks deterministically
    - Works both with Gemini online and robust offline semantic heuristic parser
    """

    MONTH_MAP = {
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

    DAYS_IN_MONTH = {
        "01": "31", "02": "28", "03": "31", "04": "30",
        "05": "31", "06": "30", "07": "31", "08": "31",
        "09": "30", "10": "31", "11": "30", "12": "31"
    }

    OPERATION_PATTERNS = [
        # (Operation, Regex pattern to match in text)
        ("FILTER", r"\b(rangkap\s+data|rangkap|ambil\s+data|filter\s+data|tampilkan\s+data|ekstrak\s+data|lihat\s+data|retrieve)\b"),
        ("COUNT", r"\b(jumlah\s+data|banyaknya\s+data|banyaknya|frekuensi|jumlah\s+transaksi|jumlah\s+unit|banyak\s+unit|unit|berapa\s+banyak|berapa\s+jumlah|berapa\s+kali|ada\s+berapa|hitung\s+data|hitung\s+nama|hitung\s+karyawan|hitung\s+pegawai|hitung\s+banyaknya|count)\b"),
        ("AVERAGE", r"\b(rata-rata|rata\s+rata|rerata|average|mean)\b"),
        ("MAX", r"\b(tertinggi|maksimal|maksimum|terbesar|paling\s+tinggi|paling\s+besar|rekor\s+tertinggi|max)\b"),
        ("MIN", r"\b(terendah|minimal|minimum|terkecil|paling\s+rendah|paling\s+kecil|min)\b"),
        ("SUM", r"\b(total|total\s+kan|totalkan|jumlah\s+produksi|omzet|omset|penjualan|biaya|tonase|sum)\b"),
        ("LOOKUP", r"\b(cari|lookup|temukan|vlookup|xlookup)\b"),
    ]

    CONJUNCTIONS = [
        r"\bserta\s+hitung\b",
        r"\blalu\s+hitung\b",
        r"\bkemudian\s+hitung\b",
        r"\bdan\s+hitung\b",
        r"\bserta\b",
        r"\bkemudian\b",
        r"\bjuga\b",
        r"\bbeserta\b",
        r"\blalu\b",
        r"\bberikutnya\b",
        r"\bdan\b"
    ]

    @classmethod
    def decompose(
        cls,
        query: str,
        columns_profile: Optional[List[Dict[str, Any]]] = None,
        sample_df: Any = None
    ) -> List[Dict[str, Any]]:
        """
        Decomposes query into a list of structured task dicts.
        Tries Gemini online semantic parser first (if available), then falls back to
        the robust offline semantic heuristic parser.
        """
        clean_q = (query or "").strip()
        if not clean_q:
            return []

        # Empty/irrelevant check
        if cls._is_irrelevant_or_greeting(clean_q):
            return [{
                "task_id": "task_1",
                "operation": "UNKNOWN",
                "target_term": None,
                "filters": [],
                "group_by": [],
                "confidence": 0.20,
                "status": "unsupported_intent"
            }]

        # Try Gemini online parsing if configured
        gemini_tasks = cls._try_gemini_decomposition(clean_q, columns_profile, sample_df)
        if gemini_tasks and cls._validate_tasks_schema(gemini_tasks):
            return gemini_tasks

        # Offline local semantic decomposition
        return cls._decompose_offline(clean_q, columns_profile, sample_df)

    @classmethod
    def _is_irrelevant_or_greeting(cls, query: str) -> bool:
        lower_q = query.lower().strip()
        greetings = ["halo", "hello", "hi", "hai", "selamat pagi", "selamat siang", "selamat sore", "selamat malam", "test", "ping", "buat sesuatu"]
        if lower_q in greetings:
            return True
        if len(lower_q.split()) <= 2 and not any(
            op_term in lower_q for op_term in ["total", "rata", "tbs", "cpo", "hitung", "max", "min", "cari", "jumlah"]
        ):
            return True
        return False

    @classmethod
    def _try_gemini_decomposition(
        cls,
        query: str,
        columns_profile: Optional[List[Dict[str, Any]]],
        sample_df: Any
    ) -> Optional[List[Dict[str, Any]]]:
        """Attempts decomposition via AIService with Gemini structured output."""
        try:
            from app.services.ai_service import AIService
            tasks = AIService.parse_tasks_with_gemini(query, columns_profile, sample_df)
            if tasks:
                return tasks
        except Exception as e:
            logger.debug(f"[TaskDecomposer] Gemini decomposition not available: {e}")
        return None

    @classmethod
    def _decompose_offline(
        cls,
        query: str,
        columns_profile: Optional[List[Dict[str, Any]]] = None,
        sample_df: Any = None
    ) -> List[Dict[str, Any]]:
        """
        High-precision offline deterministic semantic parser.
        Detects operations, targets, filters, inheritance, and overrides.
        """
        clean_q = query.strip()
        lower_q = clean_q.lower()

        # Step 1: Detect global shared context (Date range, Group By, global Target, global Filters)
        global_target = cls._detect_target_term(lower_q, columns_profile)
        global_date_filter = cls._extract_date_filter(lower_q, columns_profile, sample_df)
        global_group_by = cls._extract_group_by(lower_q, columns_profile, sample_df)
        global_filters = cls._extract_categorical_filters(clean_q, columns_profile, sample_df)

        if global_date_filter:
            # Combine with global filters
            global_filters = [f for f in global_filters if f.get("field") != global_date_filter.get("field")]
            global_filters.append(global_date_filter)

        # Step 2: Find all operations requested and their occurrence order in query
        op_occurrences = cls._find_operation_occurrences(lower_q)

        # If no explicit operations found, check if it's general query
        if not op_occurrences:
            if lower_q.startswith("hitung "):
                if not any(k in lower_q for k in ["total", "omzet", "penjualan", "biaya", "tonase", "produksi", "cpo", "tbs", "rupiah", "harga"]):
                    op_occurrences = [(0, "COUNT")]
                else:
                    op_occurrences = [(0, "SUM")]
            else:
                op_occurrences = [(0, "SUM")]

        # Step 3: Segment query by conjunctions or clauses if multiple operations exist
        raw_tasks: List[Dict[str, Any]] = []
        
        # If there are multiple distinct operations requested:
        if len(op_occurrences) > 1:
            # Extract sub-clauses for each operation to detect context overrides
            clauses = cls._segment_by_operations(clean_q, op_occurrences)
            for idx, (op_name, clause_text) in enumerate(clauses):
                clause_lower = clause_text.lower()
                task_id = f"task_{idx + 1}"

                # Target term: check clause-specific target first (override), else inherit global_target
                clause_targets = cls._detect_multiple_targets(clause_lower, columns_profile)
                task_target = clause_targets[0] if clause_targets else global_target

                # Filters: check clause-specific filters (override), else inherit global_filters
                clause_date_filter = cls._extract_date_filter(clause_lower, columns_profile, sample_df)
                clause_filters = cls._extract_categorical_filters(clause_text, columns_profile, sample_df)
                if clause_date_filter:
                    clause_filters = [f for f in clause_filters if f.get("field") != clause_date_filter.get("field")]
                    clause_filters.append(clause_date_filter)

                # Merge filters: clause-specific filter overrides global filter with same field
                task_filters = cls._merge_filters(global_filters, clause_filters)

                # Group by: inherit global or clause-specific
                clause_group_by = cls._extract_group_by(clause_lower, columns_profile, sample_df)
                task_group_by = clause_group_by if clause_group_by else global_group_by

                is_retrieval = (op_name == "FILTER")
                if is_retrieval:
                    raw_tasks.append({
                        "task_id": task_id,
                        "task_type": "retrieval",
                        "operation": "FILTER",
                        "target_term": None,
                        "filters": task_filters,
                        "group_by": task_group_by,
                        "confidence": 0.95
                    })
                elif len(clause_targets) > 1:
                    # Multi-target expansion for this calculation operation
                    for t_idx, target_item in enumerate(clause_targets):
                        sub_id = f"{task_id}_{t_idx + 1}"
                        raw_tasks.append({
                            "task_id": sub_id,
                            "task_type": "calculation",
                            "operation": op_name,
                            "target_term": target_item,
                            "filters": task_filters,
                            "group_by": task_group_by,
                            "confidence": 0.95
                        })
                else:
                    raw_tasks.append({
                        "task_id": task_id,
                        "task_type": "calculation",
                        "operation": op_name,
                        "target_term": task_target,
                        "filters": task_filters,
                        "group_by": task_group_by,
                        "confidence": 0.95
                    })
        else:
            # Single operation query: check if there are multiple targets under this operation
            op_name = op_occurrences[0][1]
            is_retrieval = (op_name == "FILTER")
            multi_targets = cls._detect_multiple_targets(lower_q, columns_profile) if not is_retrieval else []

            if len(multi_targets) > 1:
                for t_idx, target_item in enumerate(multi_targets):
                    raw_tasks.append({
                        "task_id": f"task_{t_idx + 1}",
                        "task_type": "calculation",
                        "operation": op_name,
                        "target_term": target_item,
                        "filters": global_filters,
                        "group_by": global_group_by,
                        "confidence": 0.95
                    })
            else:
                if is_retrieval:
                    target_for_task = None
                elif op_name in ["COUNT", "COUNTA"]:
                    target_for_task = global_target if not global_filters else None
                else:
                    target_for_task = global_target
                raw_tasks.append({
                    "task_id": "task_1",
                    "task_type": "retrieval" if is_retrieval else "calculation",
                    "operation": op_name,
                    "target_term": target_for_task,
                    "filters": global_filters,
                    "group_by": global_group_by,
                    "confidence": 0.95
                })

        # Step 4: Re-number task IDs sequentially & Deduplicate identical tasks deterministically
        unique_tasks = cls._deduplicate_tasks(raw_tasks)
        return unique_tasks

    @classmethod
    def _find_operation_occurrences(cls, lower_q: str) -> List[Tuple[int, str]]:
        """
        Finds all operations and their start positions in the query, preserving user order.
        """
        occurrences: List[Tuple[int, str]] = []
        matched_spans = set()

        for op, pattern in cls.OPERATION_PATTERNS:
            for match in re.finditer(pattern, lower_q):
                start, end = match.span()
                # Ensure no overlapping match with an existing longer match
                if any(start >= m_start and end <= m_end for m_start, m_end in matched_spans):
                    continue
                occurrences.append((start, op))
                matched_spans.add((start, end))

        # Sort occurrences by start position to preserve exact user order
        occurrences.sort(key=lambda x: x[0])

        # Filter out target nouns (penjualan, omzet, biaya, tonase) mistakenly captured as SUM when they directly follow another operation
        filtered_occurrences = []
        for pos, op in occurrences:
            if op == "SUM":
                if filtered_occurrences:
                    prev_pos, prev_op = filtered_occurrences[-1]
                    between_text = lower_q[prev_pos:pos].strip()
                    has_conj = any(re.search(rf"\b{c}\b", between_text) for c in ["dan", "serta", "lalu", "kemudian"]) or "," in between_text
                    if not has_conj and prev_op in ["AVERAGE", "COUNT", "COUNTA", "MAX", "MIN", "LOOKUP"]:
                        continue
            filtered_occurrences.append((pos, op))
        occurrences = filtered_occurrences

        # If MAX or MIN is present, do not treat 'cari' as a separate LOOKUP operation
        has_extreme = any(op in ["MAX", "MIN"] for _, op in occurrences)
        if has_extreme:
            occurrences = [(pos, op) for pos, op in occurrences if op != "LOOKUP"]

        return occurrences

    @classmethod
    def _segment_by_operations(
        cls,
        text: str,
        op_occurrences: List[Tuple[int, str]]
    ) -> List[Tuple[str, str]]:
        """
        Splits text into sub-clauses corresponding to each operation.
        """
        segments = []
        for i in range(len(op_occurrences)):
            curr_pos, curr_op = op_occurrences[i]
            # End position is next operation's start position, or end of text
            next_pos = op_occurrences[i + 1][0] if i + 1 < len(op_occurrences) else len(text)
            clause_str = text[curr_pos:next_pos].strip()
            segments.append((curr_op, clause_str))
        return segments

    @classmethod
    def _detect_multiple_targets(
        cls,
        text_lower: str,
        columns_profile: Optional[List[Dict[str, Any]]]
    ) -> List[str]:
        """
        Detects multiple target measurement terms in a clause, ordered by appearance.
        e.g., 'total kan harga nya, harga netto dan dp' -> ['Harga', 'Harga_Netto', 'DP']
        """
        detected = []
        # First gather candidate columns from profile (Only Numeric columns, or columns explicitly counted)
        candidates = []
        if columns_profile:
            for col in columns_profile:
                col_orig = col.get("original_name", "")
                inferred = (col.get("inferred_type") or "").lower()
                is_num = "num" in inferred or "int" in inferred or "float" in inferred
                # Allow text column as target candidate ONLY IF query explicitly has 'hitung <col>'
                if is_num or re.search(rf"\b(hitung|banyaknya)\s+{re.escape(col_orig.lower())}\b", text_lower):
                    candidates.append((col_orig, col_orig))

        # Add domain synonym mappings for common numeric columns
        domain_targets = [
            ("harga netto", "Harga_Netto"),
            ("harga bersih", "Harga_Netto"),
            ("netto", "Harga_Netto"),
            ("harga jual", "Harga"),
            ("harga", "Harga"),
            ("uang muka", "DP"),
            ("down payment", "DP"),
            ("dp", "DP"),
            ("diskon", "Diskon"),
            ("tbs", "TBS"),
            ("cpo", "CPO"),
            ("pk", "PK"),
            ("produksi", "Produksi"),
            ("omzet", "Omzet"),
            ("penjualan", "Penjualan"),
            ("biaya", "Biaya"),
            ("tonase", "Tonase")
        ]

        # Scan text for occurrences with position
        found_matches: List[Tuple[int, int, str]] = [] # (start, end, target_name)
        
        # Check actual dataset candidate columns first (longer names first)
        sorted_candidates = sorted(candidates, key=lambda x: len(x[0]), reverse=True)
        for orig, mapped in sorted_candidates:
            col_pat = rf"\b{re.escape(orig.lower().replace('_', ' '))}\b"
            for m in re.finditer(col_pat, text_lower):
                found_matches.append((m.start(), m.end(), orig))

        for syn, mapped_name in domain_targets:
            syn_pat = rf"\b{re.escape(syn)}\b"
            for m in re.finditer(syn_pat, text_lower):
                found_matches.append((m.start(), m.end(), mapped_name))

        # Sort matches by start position
        found_matches.sort(key=lambda x: (x[0], -(x[1] - x[0])))

        # Filter out overlaps (longer match takes precedence)
        chosen_spans: List[Tuple[int, int]] = []
        for start, end, name in found_matches:
            # If name is Tahun/Tanggal but used in filter context like 'tahun 2024', ignore as target
            if name.lower() in ["tahun", "year", "tanggal", "tgl", "date"]:
                surrounding = text_lower[max(0, start-10):min(len(text_lower), end+15)]
                if re.search(r"\b(tahun\s+\d{4}|\d{4})\b", surrounding):
                    continue

            if any(max(start, s) < min(end, e) for s, e in chosen_spans):
                continue
            chosen_spans.append((start, end))
            # Resolve name to exact column name in columns_profile if available
            final_name = name
            if columns_profile:
                for c in columns_profile:
                    c_orig = c.get("original_name", "")
                    if c_orig.lower() == name.lower() or c_orig.lower().replace('_', '') == name.lower().replace('_', ''):
                        final_name = c_orig
                        break
            if final_name not in detected:
                detected.append(final_name)

        return detected

    @classmethod
    def _detect_target_term(
        cls,
        text_lower: str,
        columns_profile: Optional[List[Dict[str, Any]]]
    ) -> Optional[str]:
        """Detects primary target measurement term."""
        multi = cls._detect_multiple_targets(text_lower, columns_profile)
        return multi[0] if multi else None

    @classmethod
    def _extract_date_filter(
        cls,
        text_lower: str,
        columns_profile: Optional[List[Dict[str, Any]]] = None,
        sample_df: Any = None
    ) -> Optional[Dict[str, Any]]:
        """Extracts date range filter ONLY IF dataset has a Date column or if no schema provided."""
        date_col = None
        has_month_col = False

        if sample_df is not None and hasattr(sample_df, "columns"):
            for col in sample_df.columns:
                c_str = str(col).lower()
                if pd_is_datetime(sample_df[col]) or c_str in ["tanggal", "tgl", "date", "waktu"]:
                    date_col = col
                    break
                if c_str in ["bulan", "month"]:
                    has_month_col = True
        elif columns_profile:
            for col in columns_profile:
                c_orig = col.get("original_name", "")
                c_str = c_orig.lower()
                if col.get("inferred_type") == "Date" or c_str in ["tanggal", "tgl", "date", "waktu"]:
                    date_col = c_orig
                    break
                if c_str in ["bulan", "month"]:
                    has_month_col = True

        # If dataset schema is provided and has a 'Bulan' column but NO Date column,
        # do NOT create a date range filter on a non-existent Tanggal column!
        if (sample_df is not None or columns_profile) and has_month_col and not date_col:
            return None

        # If no schema was provided at all (e.g. unit testing task decomposition on pure text), fallback to 'Tanggal'
        if not date_col:
            if sample_df is None and not columns_profile:
                date_col = "Tanggal"
            else:
                return None

        for m_name, m_num in cls.MONTH_MAP.items():
            match_year = re.search(rf"\b{m_name}\s+(\d{{4}})\b", text_lower)
            match_stand = re.search(rf"\b{m_name}\b", text_lower)
            if match_year or match_stand:
                year = match_year.group(1) if match_year else "2026"
                if int(year) % 4 == 0 and m_num == "02":
                    last_day = "29"
                else:
                    last_day = cls.DAYS_IN_MONTH.get(m_num, "30")

                start_date = f"{year}-{m_num}-01"
                end_date = f"{year}-{m_num}-{last_day}"
                return {
                    "field": date_col,
                    "operator": "between",
                    "value": {
                        "start": start_date,
                        "end": end_date
                    }
                }
        return None

    @classmethod
    def _extract_group_by(
        cls,
        text_lower: str,
        columns_profile: Optional[List[Dict[str, Any]]] = None,
        sample_df: Any = None
    ) -> List[str]:
        """Detects group by clauses like 'setiap tipe mobil', 'per afdeling', 'berdasarkan cabang'."""
        group_by = []
        patterns = [
            r"\b(?:setiap|tiap|masing-masing|masing\s+masing|per|berdasarkan|dikelompokkan\s+berdasarkan|dikelompokkan\s+per)\s+([a-zA-Z0-9_]+(?:\s+[a-zA-Z0-9_]+)?)\b"
        ]
        stopwords = {
            "dan", "serta", "bulan", "tahun", "tanggal", "data", "seluruh", "semua",
            "ini", "itu", "yang", "dari", "pada", "di", "ke", "untuk", "dengan"
        }
        for pat in patterns:
            for m in re.finditer(pat, text_lower):
                raw_dim = m.group(1).strip()
                dim_words = [w for w in raw_dim.split() if w not in stopwords]
                dim = " ".join(dim_words)
                if not dim or dim in stopwords:
                    continue

                matched_col = None
                dim_l = dim.lower()

                # Special domain synonyms for cars: 'tipe mobil', 'model mobil', 'nama mobil'
                if dim_l in ["tipe mobil", "model mobil", "nama mobil", "mobil", "model", "tipe"]:
                    # Prioritize 'Model' if available in columns (which contains car models e.g. Avanza, Fortuner, etc.)
                    if sample_df is not None and hasattr(sample_df, "columns"):
                        for c in sample_df.columns:
                            if c.lower() == "model":
                                matched_col = c
                                break
                    if not matched_col and columns_profile:
                        for col in columns_profile:
                            c_name = col.get("original_name", "")
                            if c_name.lower() == "model":
                                matched_col = c_name
                                break
                    if not matched_col and sample_df is not None and hasattr(sample_df, "columns"):
                        for c in sample_df.columns:
                            if c.lower() == "tipe":
                                matched_col = c
                                break
                    if not matched_col and columns_profile:
                        for col in columns_profile:
                            c_name = col.get("original_name", "")
                            if c_name.lower() == "tipe":
                                matched_col = c_name
                                break

                # Check exact or partial match with dataset columns
                if not matched_col and sample_df is not None and hasattr(sample_df, "columns"):
                    for c in sample_df.columns:
                        c_clean = str(c).lower().replace("_", " ")
                        if c_clean == dim_l or dim_l == str(c).lower():
                            matched_col = c
                            break
                        elif dim_words and (dim_words[0].lower() == c_clean or dim_words[0].lower() == str(c).lower()):
                            matched_col = c
                            break

                if not matched_col and columns_profile:
                    for col in columns_profile:
                        c_orig = col.get("original_name", "")
                        c_clean = c_orig.lower().replace("_", " ")
                        if c_clean == dim_l or dim_l == c_orig.lower():
                            matched_col = c_orig
                            break
                        elif dim_words and (dim_words[0].lower() == c_clean or dim_words[0].lower() == c_orig.lower()):
                            matched_col = c_orig
                            break

                if not matched_col:
                    matched_col = dim.title()

                if matched_col not in group_by:
                    group_by.append(matched_col)

        return group_by

    @classmethod
    def _extract_categorical_filters(
        cls,
        text: str,
        columns_profile: Optional[List[Dict[str, Any]]],
        sample_df: Any
    ) -> List[Dict[str, Any]]:
        """Extracts categorical filters like 'afdeling A', 'Pekanbaru', etc."""
        filters: List[Dict[str, Any]] = []
        text_lower = text.lower()

        # 1. Look for 'afdeling <X>' or '<field> <value>'
        afdeling_col = "Afdeling"
        if columns_profile:
            for col in columns_profile:
                if "afdeling" in col.get("original_name", "").lower():
                    afdeling_col = col.get("original_name")
                    break

        match_afd = re.search(r"\bafdeling\s+([a-zA-Z0-9]+)\b", text_lower)
        if match_afd:
            afd_val = match_afd.group(1).upper()
            filters.append({
                "field": afdeling_col,
                "operator": "=",
                "value": afd_val
            })

        # 2. Check sample_df unique values or sample_values in columns_profile
        matched_vals_seen = set()
        if sample_df is not None and hasattr(sample_df, "columns"):
            for col_name in sample_df.columns:
                if str(col_name).lower() == afdeling_col.lower():
                    continue
                s_col = sample_df[col_name]
                if not pd_is_numeric(s_col):
                    unique_vals = [str(x).strip() for x in s_col.dropna().unique() if str(x).strip()]
                    sorted_vals = sorted(unique_vals, key=lambda x: len(x), reverse=True)
                    for val in sorted_vals:
                        val_l = val.lower()
                        if len(val) >= 3 and val_l not in matched_vals_seen and re.search(rf"\b{re.escape(val_l)}\b", text_lower):
                            matched_vals_seen.add(val_l)
                            # Check if this exact value appears in multiple non-numeric columns
                            cols_with_val = []
                            for c_cand in sample_df.columns:
                                if not pd_is_numeric(sample_df[c_cand]):
                                    if (sample_df[c_cand].astype(str).str.strip().str.lower() == val_l).any():
                                        cols_with_val.append(c_cand)
                            
                            is_ambig = len(cols_with_val) > 1
                            filters.append({
                                "field": col_name,
                                "operator": "=",
                                "value": val,
                                "is_ambiguous": is_ambig,
                                "ambiguous_columns": cols_with_val if is_ambig else []
                            })
                            break
        elif columns_profile:
            for col_prof in columns_profile:
                col_name = col_prof.get("original_name", "")
                inferred = (col_prof.get("inferred_type") or "").lower()
                if "num" in inferred or "int" in inferred or "float" in inferred:
                    continue
                s_vals = col_prof.get("sample_values") or []
                sorted_vals = sorted([str(v).strip() for v in s_vals if str(v).strip()], key=lambda x: len(x), reverse=True)
                for val in sorted_vals:
                    val_l = val.lower()
                    if len(val) >= 3 and val_l not in matched_vals_seen and re.search(rf"\b{re.escape(val_l)}\b", text_lower):
                        matched_vals_seen.add(val_l)
                        filters.append({
                            "field": col_name,
                            "operator": "=",
                            "value": val,
                            "is_ambiguous": False,
                            "ambiguous_columns": []
                        })
                        break

        # 3. Structural entity matching fallback (e.g. 'mobil Avanza', 'model Avanza', 'sales Budi')
        non_entity_words = {
            "ini", "itu", "yang", "dan", "data", "nya", "dari", "seluruh", "semua", "setiap",
            "tiap", "masing", "masing-masing", "apa", "berapa", "di", "ke", "pada", "untuk",
            "dengan", "rekap", "total", "laporan", "tipe", "model", "mobil", "tipe mobil"
        }
        auto_pat = re.finditer(r"\b(?:mobil|model|tipe\s+mobil)\s+([A-Za-z0-9_]+)\b", text_lower)
        for am in auto_pat:
            val_cand = am.group(1).strip()
            if val_cand.lower() not in non_entity_words and val_cand.lower() not in matched_vals_seen:
                matched_vals_seen.add(val_cand.lower())
                target_col = "Model"
                if columns_profile:
                    for c in columns_profile:
                        c_name = c.get("original_name", "")
                        if c_name.lower() in ["model", "tipe", "varian"]:
                            target_col = c_name
                            break
                filters.append({
                    "field": target_col,
                    "operator": "=",
                    "value": val_cand.title(),
                    "is_ambiguous": False,
                    "ambiguous_columns": []
                })

        # 4. Explicit Year filter: 'tahun 2024' or standalone 4-digit year
        year_match = re.search(r"\btahun\s+(\d{4})\b", text_lower)
        if year_match:
            year_val = year_match.group(1)
            year_col = "Tahun"
            if columns_profile:
                for c in columns_profile:
                    c_name = c.get("original_name", "")
                    if c_name.lower() in ["tahun", "year"]:
                        year_col = c_name
                        break
            filters.append({
                "field": year_col,
                "operator": "=",
                "value": year_val,
                "is_ambiguous": False,
                "ambiguous_columns": []
            })

        return filters

    @classmethod
    def _merge_filters(
        cls,
        global_filters: List[Dict[str, Any]],
        clause_filters: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Merges global filters and clause-specific filters.
        Clause-specific filters take precedence over global filters with the same field.
        """
        result = []
        clause_fields = {f.get("field", "").lower(): f for f in clause_filters}

        # Add global filters unless overridden by clause filter
        for gf in global_filters:
            f_field = gf.get("field", "").lower()
            if f_field in clause_fields:
                result.append(clause_fields[f_field])
            else:
                result.append(gf)

        # Add any clause-specific filters not in global
        for cf in clause_filters:
            if not any(f.get("field", "").lower() == cf.get("field", "").lower() for f in result):
                result.append(cf)

        return result

    @classmethod
    def _deduplicate_tasks(cls, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Deduplicates tasks that have identical operation, target, and filters."""
        seen = set()
        deduped = []
        for t in tasks:
            key = (
                t.get("operation"),
                t.get("target_term"),
                json.dumps(t.get("filters", []), sort_keys=True),
                json.dumps(t.get("group_by", []), sort_keys=True)
            )
            if key not in seen:
                seen.add(key)
                # Reassign sequential task_id
                t["task_id"] = f"task_{len(deduped) + 1}"
                deduped.append(t)
        return deduped

    @classmethod
    def _validate_tasks_schema(cls, tasks: Any) -> bool:
        """Validates that tasks conform to structured schema."""
        if not isinstance(tasks, list) or len(tasks) == 0:
            return False
        for t in tasks:
            if not isinstance(t, dict):
                return False
            if not t.get("task_id") or not t.get("operation"):
                return False
            if not isinstance(t.get("filters", []), list):
                return False
        return True


def pd_is_numeric(series: Any) -> bool:
    try:
        import pandas as pd
        return pd.api.types.is_numeric_dtype(series)
    except Exception:
        return False

def pd_is_datetime(series: Any) -> bool:
    try:
        import pandas as pd
        return pd.api.types.is_datetime64_any_dtype(series)
    except Exception:
        return False
