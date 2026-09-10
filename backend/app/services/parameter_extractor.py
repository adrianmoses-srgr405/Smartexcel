import re
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd
from app.knowledge.domain_synonyms import DOMAIN_SYNONYMS, INDONESIAN_STOPWORDS

class ParameterExtractor:
    """
    Context-Aware Parameter & Entity Extraction Layer for Natural Language Excel Queries.
    Verified against:
    1. Natural language query
    2. Dataset schema
    3. Column names
    4. Column data types
    5. Existing values in dataset
    6. Domain synonyms
    """

    MONTH_NAMES = [
        "januari", "februari", "maret", "april", "mei", "juni",
        "juli", "agustus", "september", "oktober", "november", "desember",
        "jan", "feb", "mar", "apr", "jun", "jul", "agu", "sep", "okt", "nov", "des"
    ]

    MONTH_CANONICAL = {
        "jan": "Januari", "feb": "Februari", "mar": "Maret", "apr": "April",
        "mei": "Mei", "jun": "Juni", "jul": "Juli", "agu": "Agustus",
        "sep": "September", "okt": "Oktober", "nov": "November", "des": "Desember"
    }

    @classmethod
    def extract_parameters(
        cls,
        query: str,
        columns_profile: Optional[List[Dict[str, Any]]] = None,
        sample_df: Optional[pd.DataFrame] = None,
        task_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Main context-aware parameter extraction routine.
        Supports optional task_context for multi-task pipeline inheritance and overrides.
        """
        clean_q = query.strip()
        lower_q = clean_q.lower()

        # 1. Detect Base Operation Intent
        operation = cls._detect_operation(lower_q)
        if task_context and task_context.get("operation") and task_context["operation"] != "UNKNOWN":
            operation = task_context["operation"]
        
        # 2. Check for Ambiguous Query (Under-specified requirements)
        # e.g. "Hitung data Andi", "Data produksi", "Hitung Andi"
        ambiguous, ambig_reason = cls._check_query_ambiguity(lower_q, columns_profile, sample_df)
        if ambiguous and not task_context:
            return {
                "operation": operation if operation != "UNKNOWN" else "AMBIGUOUS",
                "target_term": None,
                "conditions": [],
                "logical_branches": [],
                "is_ambiguous": True,
                "ambiguity_status": "ambiguous_query",
                "ambiguity_reason": ambig_reason,
                "confidence": 0.40
            }

        # 3. Detect IF / IFS logical expressions
        logical_branches = []
        if operation in ["IF", "IFS"] or lower_q.startswith("jika") or " maka " in lower_q or " lebih dari " in lower_q:
            logical_branches = cls._parse_logical_expression(clean_q)
            if len(logical_branches) > 1:
                operation = "IFS"
            elif len(logical_branches) == 1:
                operation = "IF"

        # 4. Extract Target Column Term (with Domain Synonyms & Schema Types)
        is_retrieval_op = (operation in ["FILTER", "RETRIEVAL"] or (task_context and task_context.get("task_type") == "retrieval"))
        if is_retrieval_op:
            target_term = task_context.get("target_term") if task_context else None
        else:
            target_term = cls._extract_target_term(lower_q, columns_profile, sample_df)
            if task_context and task_context.get("target_term"):
                target_term = task_context["target_term"]

        # 5. Extract Filter Entities Context-Aware against Schema and Dataset Values
        if task_context and task_context.get("filters") is not None and len(task_context.get("filters", [])) > 0:
            conditions = []
            has_ambiguous_param = False
            param_ambig_reason = None
            for f in task_context["filters"]:
                f_field = f.get("field") or "Kolom"
                f_op = f.get("operator", "=")
                f_val = f.get("value")
                is_ambig = bool(f.get("is_ambiguous", False))
                if is_ambig:
                    has_ambiguous_param = True
                    param_ambig_reason = f"Parameter '{f_val}' ambigu, ditemukan di beberapa kolom: {f.get('ambiguous_columns')}"
                conditions.append({
                    "column_hint": f_field,
                    "operator": f_op,
                    "value": f_val,
                    "data_type": "date" if isinstance(f_val, dict) or "tgl" in str(f_field).lower() or "tanggal" in str(f_field).lower() else "text",
                    "is_ambiguous": is_ambig,
                    "verified_in_dataset": True
                })
        else:
            conditions, has_ambiguous_param, param_ambig_reason = cls._extract_conditions_context_aware(
                clean_q, columns_profile, sample_df
            )

        # For COUNT/COUNTA queries without specific target term or when counting table rows,
        # Excel criteria range replaces target column.
        if operation in ["COUNT", "COUNTA"]:
            if not task_context or not task_context.get("target_term") or task_context.get("target_term") in ["Penjualan", "Transaksi"]:
                target_term = None

        confidence = 0.90
        ambiguity_status = "ok"
        if has_ambiguous_param:
            confidence = 0.45
            ambiguity_status = "ambiguous_parameter"
        elif not target_term and operation in ["SUM", "AVERAGE"]:
            confidence = 0.65
            ambiguity_status = "missing_target"
        elif conditions and all(c.get("verified_in_dataset", False) for c in conditions):
            confidence = 0.98

        return {
            "operation": operation,
            "target_term": target_term,
            "conditions": conditions,
            "logical_branches": logical_branches,
            "is_ambiguous": ambiguous or has_ambiguous_param,
            "ambiguity_status": ambiguity_status,
            "ambiguity_reason": ambig_reason or param_ambig_reason,
            "confidence": confidence
        }

    @classmethod
    def _detect_operation(cls, lower_q: str) -> str:
        # 1. Logical / Conditional
        if lower_q.startswith("jika ") or " maka " in lower_q or "jika" in lower_q:
            return "IF"

        # 2. Statistical: Average
        if any(w in lower_q for w in ["rata-rata", "rerata", "rata rata", "average", "mean"]):
            return "AVERAGE"

        # 3. Statistical: Extremes
        if any(w in lower_q for w in ["tertinggi", "maksimal", "maksimum", "terbesar", "paling tinggi", "rekor tertinggi", "paling besar"]):
            return "MAX"
        if any(w in lower_q for w in ["terendah", "minimal", "minimum", "terkecil", "paling rendah", "paling sedikit"]):
            return "MIN"

        # 4. Lookup
        if any(w in lower_q for w in ["cari", "ambil", "temukan", "lookup", "berdasarkan id", "berdasarkan kode", "berdasarkan nip"]):
            return "LOOKUP"

        # 5. Counting: Count / Counta / Countif / Countifs
        count_keywords = [
            "jumlah transaksi", "jumlah data", "jumlah baris", "jumlah record",
            "jumlah pegawai", "jumlah karyawan", "jumlah nama", "jumlah item",
            "jumlah sales", "berapa sales", "ada berapa", "hitung ada berapa",
            "berapa banyak", "berapa kali", "berapa jumlah", "banyaknya data",
            "banyaknya", "frekuensi", "hitung banyaknya", "hitung transaksi", "berapa transaksi"
        ]
        if any(w in lower_q for w in count_keywords):
            return "COUNT"

        # If query starts with 'hitung ' without financial/numeric target words -> COUNT
        if lower_q.startswith("hitung ") and not any(k in lower_q for k in ["total", "omzet", "penjualan", "biaya", "tonase", "produksi", "cpo", "tbs", "rupiah", "harga"]):
            return "COUNT"

        # 6. Aggregation: Sum
        sum_keywords = ["total", "jumlahkan", "akumulasi", "omzet", "penjualan", "revenue", "biaya", "tonase", "produksi", "rekap", "jumlah"]
        if any(w in lower_q for w in sum_keywords):
            return "SUM"

        if "hitung" in lower_q:
            return "COUNT"

        return "UNKNOWN"

    @classmethod
    def _check_query_ambiguity(
        cls,
        lower_q: str,
        columns_profile: Optional[List[Dict[str, Any]]] = None,
        sample_df: Optional[pd.DataFrame] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Identifies whether a query lacks necessary operation or target clarity.
        e.g., 'Hitung data Andi', 'Berapa data produksi?', 'Hitung Andi'
        """
        clean = lower_q.strip()

        # Exact underspecified 'data' patterns
        if re.match(r"^hitung\s+data\s+[a-zA-Z0-9_]+$", clean):
            return True, "Query tidak menyebutkan jenis operasi perhitungan (apakah total penjualan, rata-rata, atau jumlah transaksi)."

        if re.match(r"^(berapa|ambil|tolong\s+olah)\s+data\s+[a-zA-Z0-9_]+$", clean):
            return True, "Target kolom yang ingin dihitung tidak spesifik."

        # Check 'hitung [single_word]'
        m_single = re.match(r"^hitung\s+([a-zA-Z0-9_]+)$", clean)
        if m_single:
            word = m_single.group(1)
            # Check if this word is an existing column in the active dataset
            existing_cols = []
            if sample_df is not None:
                existing_cols = [c.lower() for c in sample_df.columns]
            elif columns_profile:
                existing_cols = [c.get("original_name", "").lower() for c in columns_profile]

            if word in existing_cols:
                # Valid counting on dataset column (e.g. "hitung nama", "hitung gaji")
                return False, None
            else:
                # Unspecified entity (e.g. "hitung andi")
                return True, f"Query 'hitung {word}' tidak menyebutkan jenis perhitungan secara spesifik."

        if ("hitung data " in lower_q or "berapa data " in lower_q) and not any(
            k in lower_q for k in ["penjualan", "omzet", "produksi", "biaya", "harga", "transaksi", "tonase", "target"]
        ):
            return True, "Target kolom yang ingin dihitung tidak spesifik."

        return False, None

    @classmethod
    def _extract_target_term(
        cls,
        lower_q: str,
        columns_profile: Optional[List[Dict[str, Any]]] = None,
        sample_df: Optional[pd.DataFrame] = None
    ) -> Optional[str]:
        """Extracts the intended measurement term from the query."""
        # 1. Direct Column Name Check if columns_profile provided (longest name first with word boundary)
        if columns_profile:
            sorted_cols = sorted(columns_profile, key=lambda c: len(c.get("original_name", "")), reverse=True)
            for col in sorted_cols:
                col_name = col.get("original_name", "")
                norm_c = col_name.lower().replace("_", " ")
                if re.search(rf"\b{re.escape(norm_c)}\b", lower_q) or re.search(rf"\b{re.escape(col_name.lower())}\b", lower_q):
                    return col_name

        if sample_df is not None:
            sorted_cols = sorted(list(sample_df.columns), key=lambda c: len(c), reverse=True)
            for c in sorted_cols:
                norm_c = str(c).lower().replace("_", " ")
                if re.search(rf"\b{re.escape(norm_c)}\b", lower_q) or re.search(rf"\b{re.escape(str(c).lower())}\b", lower_q):
                    return str(c)

        # 2. Check Domain Synonyms (longest synonym phrases first with word boundaries)
        all_synonym_pairs: List[Tuple[str, Any]] = []
        for syn, canon_val in DOMAIN_SYNONYMS.items():
            all_synonym_pairs.append((syn, canon_val))
            canon_items = canon_val if isinstance(canon_val, list) else [canon_val]
            for item in canon_items:
                all_synonym_pairs.append((str(item), syn))

        all_synonym_pairs.sort(key=lambda x: len(x[0]), reverse=True)

        for syn_phrase, canon_target in all_synonym_pairs:
            if re.search(rf"\b{re.escape(syn_phrase.lower())}\b", lower_q):
                # If columns_profile provided, match against exact column name or its synonyms
                if columns_profile:
                    for col in columns_profile:
                        c_orig = col.get("original_name", "")
                        c_norm = c_orig.lower().replace("_", " ")
                        canon_str = str(canon_target).lower().replace("_", " ")
                        if c_norm == canon_str or c_orig.lower() == str(canon_target).lower() or syn_phrase.lower() == c_norm:
                            return c_orig
                return str(canon_target)

        # 3. Known business target candidates (longest first)
        candidates = [
            "total penjualan", "nilai penjualan", "penjualan", "total omzet", "omzet", "revenue",
            "produksi cpo", "produksi tbs", "tonase tbs", "tonase", "produksi", "rendemen oer", "rendemen cpo", "rendemen", "oer", "ker",
            "biaya operasional", "biaya pupuk", "biaya", "harga satuan", "harga netto", "harga bersih", "harga jual", "harga",
            "kadar ffa", "ffa", "luas areal", "luas panen", "luas lahan", "stok akhir", "stok", "transaksi", "dp", "uang muka"
        ]
        candidates.sort(key=lambda x: len(x), reverse=True)
        for c in candidates:
            if re.search(rf"\b{re.escape(c)}\b", lower_q):
                if columns_profile:
                    for col in columns_profile:
                        c_orig = col.get("original_name", "")
                        if col.get("original_name", "").lower().replace("_", " ") == c:
                            return c_orig
                return c

        return None

    @classmethod
    def _extract_conditions_context_aware(
        cls,
        raw_query: str,
        columns_profile: Optional[List[Dict[str, Any]]] = None,
        sample_df: Optional[pd.DataFrame] = None
    ) -> Tuple[List[Dict[str, Any]], bool, Optional[str]]:
        """
        Extracts filter conditions and verifies them against dataset context:
        - Schema column names
        - Column data types
        - Existing values in dataset (multi-word n-gram scanning)
        Detects ambiguous parameters if a value matches multiple columns without clarification.
        """
        conditions: List[Dict[str, Any]] = []
        lower_q = raw_query.lower()
        has_ambiguous_param = False
        param_ambig_reason = None
        matched_spans: List[Tuple[int, int]] = []

        # Build column index / schema knowledge
        available_cols = []
        col_type_map = {}
        if sample_df is not None:
            available_cols = list(sample_df.columns)
            for c in available_cols:
                col_type_map[c] = "numeric" if pd.api.types.is_numeric_dtype(sample_df[c]) else (
                    "date" if pd.api.types.is_datetime64_any_dtype(sample_df[c]) else "text"
                )
        elif columns_profile:
            available_cols = [c.get("original_name") for c in columns_profile if c.get("original_name")]
            for c in columns_profile:
                col_type_map[c.get("original_name")] = (c.get("inferred_type") or "text").lower()

        # 1. Month detection (e.g. "Januari", "bulan Januari", "di Januari")
        for m in cls.MONTH_NAMES:
            pattern = rf"\b(?:bulan|di|pada)?\s*({m})\b"
            match = re.search(pattern, lower_q)
            if match:
                matched_spans.append(match.span())
                canonical_m = cls.MONTH_CANONICAL.get(m, m.capitalize())
                month_col = "Bulan"
                for c in available_cols:
                    if c.lower() in ["bulan", "month", "periode_bulan"]:
                        month_col = c
                        break
                conditions.append({
                    "column_hint": month_col,
                    "operator": "=",
                    "value": canonical_m,
                    "data_type": "text",
                    "is_ambiguous": False,
                    "verified_in_dataset": True
                })
                break

        # 2. Year detection (e.g. "tahun 2026", "2025")
        year_match = re.search(r"\b(?:tahun\s*)?(202[0-9]|201[0-9])\b", lower_q)
        if year_match:
            matched_spans.append(year_match.span())
            year_col = "Tahun"
            for c in available_cols:
                if c.lower() in ["tahun", "year", "periode_tahun"]:
                    year_col = c
                    break
            conditions.append({
                "column_hint": year_col,
                "operator": "=",
                "value": year_match.group(1),
                "data_type": "text",
                "is_ambiguous": False,
                "verified_in_dataset": True
            })

        # 3. Build Multi-Word Dataset Value Index from DataFrame and Columns Profile
        dataset_val_map: Dict[str, List[Tuple[str, str]]] = {}
        if sample_df is not None:
            for col in sample_df.columns:
                if pd.api.types.is_numeric_dtype(sample_df[col]):
                    continue
                uniques = sample_df[col].dropna().astype(str).unique()
                for u in uniques:
                    u_clean = u.strip()
                    if len(u_clean) >= 2 and u_clean.lower() not in INDONESIAN_STOPWORDS and u_clean.lower() not in cls.MONTH_NAMES:
                        dataset_val_map.setdefault(u_clean.lower(), []).append((col, u_clean))
        elif columns_profile:
            for col_prof in columns_profile:
                col_name = col_prof.get("original_name", "")
                if not col_name:
                    continue
                inferred = (col_prof.get("inferred_type") or "").lower()
                if "num" in inferred or "int" in inferred or "float" in inferred:
                    continue
                s_vals = col_prof.get("sample_values") or []
                for sv in s_vals:
                    sv_clean = str(sv).strip()
                    if len(sv_clean) >= 2 and sv_clean.lower() not in INDONESIAN_STOPWORDS and sv_clean.lower() not in cls.MONTH_NAMES:
                        existing = dataset_val_map.setdefault(sv_clean.lower(), [])
                        if not any(item[0] == col_name for item in existing):
                            existing.append((col_name, sv_clean))

        # 4. Multi-word N-Gram Dataset Scanning (Longest match first)
        sorted_dataset_vals = sorted(dataset_val_map.keys(), key=lambda v: len(v), reverse=True)
        for cand_val in sorted_dataset_vals:
            cand_pattern = rf"\b{re.escape(cand_val)}\b"
            for m in re.finditer(cand_pattern, lower_q):
                span = m.span()
                overlap = any(max(span[0], s[0]) < min(span[1], s[1]) for s in matched_spans)
                if overlap:
                    continue

                col_entries = dataset_val_map[cand_val]
                unique_cols = list(dict.fromkeys([c[0] for c in col_entries]))
                exact_val = col_entries[0][1]

                if len(unique_cols) == 1:
                    matched_spans.append(span)
                    conditions.append({
                        "column_hint": unique_cols[0],
                        "operator": "=",
                        "value": exact_val,
                        "data_type": "text",
                        "is_ambiguous": False,
                        "verified_in_dataset": True
                    })
                else:
                    # Multiple columns match this value; check for explicit column mentions in query
                    resolved_col = None
                    for uc in unique_cols:
                        if re.search(rf"\b{re.escape(uc.lower())}\b", lower_q):
                            resolved_col = uc
                            break
                    if resolved_col:
                        matched_spans.append(span)
                        conditions.append({
                            "column_hint": resolved_col,
                            "operator": "=",
                            "value": exact_val,
                            "data_type": "text",
                            "is_ambiguous": False,
                            "verified_in_dataset": True
                        })
                    else:
                        matched_spans.append(span)
                        has_ambiguous_param = True
                        param_ambig_reason = (
                            f"Entity '{exact_val}' ditemukan pada beberapa kolom: {', '.join(unique_cols)}. "
                            "Mohon klarifikasi kolom mana yang dimaksud."
                        )
                        conditions.append({
                            "column_hint": unique_cols[0],
                            "candidate_columns": unique_cols,
                            "operator": "=",
                            "value": exact_val,
                            "data_type": "text",
                            "is_ambiguous": True,
                            "verified_in_dataset": True
                        })

        # 5. Structural Pattern Fallback (for entities not in dataset sample or unknown names)
        # 5a. Automotive entity pattern: 'mobil <X>' or 'model <X>' or 'merek <X>'
        auto_matches = re.finditer(r"\b(?:mobil|model|tipe\s+mobil|kendaraan)\s+([A-Za-z0-9_]+)\b", lower_q)
        for am in auto_matches:
            val_cand = am.group(1).strip()
            if val_cand.lower() not in INDONESIAN_STOPWORDS and val_cand.lower() not in ["ini", "itu", "yang", "dan", "data", "nya"]:
                am_span = (am.start(1), am.end(1))
                if not any(max(am_span[0], s[0]) < min(am_span[1], s[1]) for s in matched_spans):
                    # Determine target column: check if 'Model' exists in available_cols
                    target_auto_col = "Model"
                    for c in available_cols:
                        if c.lower() in ["model", "tipe", "varian"]:
                            target_auto_col = c
                            break
                    matched_spans.append(am_span)
                    conditions.append({
                        "column_hint": target_auto_col,
                        "operator": "=",
                        "value": val_cand.title(),
                        "data_type": "text",
                        "is_ambiguous": False,
                        "verified_in_dataset": False
                    })

        structural_matches = re.finditer(
            r"\b(sales|cabang|merek|model|kebun|afdeling|divisi|produk|wilayah)\s+([A-Za-z0-9_]+(?:\s+[A-Za-z0-9_]+)?)\b",
            lower_q
        )
        for sm in structural_matches:
            val_candidate = sm.group(2).strip()
            val_lower = val_candidate.lower()
            if val_lower in INDONESIAN_STOPWORDS or val_lower in ["di", "pada", "ini", "itu", "yang", "dan", "data", "mobil", "nya"]:
                continue
            sm_span = (sm.start(2), sm.end(2))
            if any(max(sm_span[0], s[0]) < min(sm_span[1], s[1]) for s in matched_spans):
                continue

            col_mention = sm.group(1).capitalize()
            matched_c = col_mention
            for c in available_cols:
                if c.lower() == col_mention.lower():
                    matched_c = c
                    break

            matched_spans.append(sm_span)
            conditions.append({
                "column_hint": matched_c,
                "operator": "=",
                "value": val_candidate.title(),
                "data_type": "text",
                "is_ambiguous": False,
                "verified_in_dataset": False
            })

        # 6. Common Indonesian Given Names Fallback
        for name in ["Andi", "Budi", "Siti", "Dewi", "Rian", "Agus", "Hendra", "Mega", "Doni", "Eko"]:
            name_pat = rf"\b{name.lower()}\b"
            nm = re.search(name_pat, lower_q)
            if nm:
                span = nm.span()
                if not any(max(span[0], s[0]) < min(span[1], s[1]) for s in matched_spans):
                    matched_spans.append(span)
                    sales_col = "Sales"
                    for c in available_cols:
                        if c.lower() in ["sales", "nama_sales", "salesman", "karyawan"]:
                            sales_col = c
                            break
                    conditions.append({
                        "column_hint": sales_col,
                        "operator": "=",
                        "value": name,
                        "data_type": "text",
                        "is_ambiguous": False,
                        "verified_in_dataset": False
                    })

        return conditions, has_ambiguous_param, param_ambig_reason

    @classmethod
    def _parse_logical_expression(cls, query: str) -> List[Dict[str, Any]]:
        """
        Parses IF / IFS logical condition branches from text.
        Supports: >, <, >=, <=, =, <>, AND, OR.
        Values: numeric, text, date.
        """
        branches = []
        lower_q = query.lower()

        # Extract fallback outcome before branch splitting
        fallback_outcome = "Rendah"
        fallback_match = re.search(r"(?:selain\s+itu|else|lainnya)\s+[\"']?([A-Za-z0-9_]+)[\"']?", lower_q)
        if fallback_match:
            fallback_outcome = fallback_match.group(1).capitalize()
            lower_q = re.sub(r",?\s*(?:selain\s+itu|else|lainnya)\s+[\"']?[A-Za-z0-9_]+[\"']?", "", lower_q)

        # Split multi-branch expressions by comma, 'jika', 'atau', 'dan'
        parts = re.split(r",\s*jika\s+|\s+jika\s+", lower_q)
        
        # Clean first part if starts with 'jika '
        cleaned_parts = []
        for p in parts:
            p_clean = re.sub(r"^jika\s+", "", p.strip())
            if p_clean:
                cleaned_parts.append(p_clean)

        for part in cleaned_parts:
            op = "="
            if ">=" in part or "lebih dari sama dengan" in part or "minimal" in part:
                op = ">="
            elif "<=" in part or "kurang dari sama dengan" in part or "maksimal" in part:
                op = "<="
            elif "<>" in part or "!=" in part or "tidak sama dengan" in part:
                op = "<>"
            elif ">" in part or "lebih dari" in part or "di atas" in part:
                op = ">"
            elif "<" in part or "kurang dari" in part or "di bawah" in part:
                op = "<"
            elif "=" in part or "sama dengan" in part:
                op = "="

            connector = "AND" if " dan " in part else ("OR" if " atau " in part else None)

            num_match = re.search(r"(\d+(?:\.\d+)?)\s*(juta|ribu|rb|jt|ton|%)?", part)
            val: Any = 0
            val_type = "numeric"
            if num_match:
                raw_num = float(num_match.group(1))
                unit = num_match.group(2)
                if unit in ["juta", "jt"]:
                    raw_num *= 1000000
                elif unit in ["ribu", "rb"]:
                    raw_num *= 1000
                val = int(raw_num) if raw_num.is_integer() else raw_num
            else:
                val_type = "text"
                val = "Valid"

            outcome = "Tinggi"
            maka_match = re.search(r"maka\s+([A-Za-z0-9_]+)", part)
            if maka_match:
                outcome = maka_match.group(1).capitalize()
            else:
                words = part.split()
                if len(words) >= 2:
                    outcome = words[-1].capitalize()

            field_name = "Penjualan"
            for w in ["penjualan", "omzet", "produksi", "rendemen", "ffa", "biaya", "tonase", "nilai"]:
                if w in part:
                    field_name = w.capitalize()
                    break

            branches.append({
                "field": field_name,
                "operator": op,
                "value": val,
                "value_type": val_type,
                "connector": connector,
                "outcome": outcome,
                "fallback_outcome": fallback_outcome,
                "raw_branch": part
            })

        return branches
