# data/cleaner.py
# DETERMINISTIC cleaning — zero LLM, zero hallucination

import pandas as pd
import numpy as np
import re


class DataCleaner:
    def __init__(self):
        self.cleaning_report = []
        self.pkr_columns = []

    def clean(self, df: pd.DataFrame) -> tuple:
        self.cleaning_report = []
        original_shape = df.shape
        df = df.copy()

        df = self._clean_column_names(df)
        df = self._remove_empty_rows(df)
        df = self._remove_duplicate_rows(df)
        df = self._clean_whitespace(df)
        df = self._detect_and_convert_dates(df)
        df = self._detect_and_convert_numbers(df)
        df = self._handle_null_values(df)
        df = self._detect_pkr_columns(df)
        df = self._remove_invisible_characters(df)

        self.cleaning_report.append(
            f"✅ Done: {original_shape[0]}"
            f" → {len(df)} rows"
        )
        return df, self.cleaning_report

    def _clean_column_names(self, df):
        original = df.columns.tolist()
        new_cols = []
        for col in original:
            new = str(col).lower().strip()
            new = re.sub(r'[^a-z0-9_]', '_', new)
            new = re.sub(r'_+', '_', new).strip('_')
            if not new:
                new = f"col_{len(new_cols)}"
            new_cols.append(new)
        df.columns = new_cols
        changed = sum(
            1 for o, n in zip(original, new_cols) if o != n)
        if changed:
            self.cleaning_report.append(
                f"📋 Renamed {changed} columns")
        return df

    def _remove_empty_rows(self, df):
        before = len(df)
        df = df.dropna(how='all')
        removed = before - len(df)
        if removed:
            self.cleaning_report.append(
                f"🗑️ Removed {removed} empty rows")
        return df

    def _remove_duplicate_rows(self, df):
        before = len(df)
        df = df.drop_duplicates()
        removed = before - len(df)
        if removed:
            self.cleaning_report.append(
                f"🗑️ Removed {removed} duplicate rows")
        return df

    def _clean_whitespace(self, df):
        for col in df.select_dtypes(
                include=['object']).columns:
            df[col] = df[col].astype(str).str.strip()
            df[col] = df[col].replace(
                {'nan': np.nan, 'None': np.nan, '': np.nan})
        return df

    def _detect_and_convert_dates(self, df):
        patterns = [
            r'\d{4}-\d{2}-\d{2}',
            r'\d{2}/\d{2}/\d{4}',
            r'\d{2}-\d{2}-\d{4}'
        ]
        converted = []
        for col in df.select_dtypes(
                include=['object']).columns:
            sample = df[col].dropna().head(10).astype(str)
            for p in patterns:
                if sample.str.match(p).sum() >= 5:
                    try:
                        df[col] = pd.to_datetime(
                            df[col],
                            infer_datetime_format=True,
                            errors='coerce'
                        )
                        converted.append(col)
                        break
                    except Exception:
                        pass
        if converted:
            self.cleaning_report.append(
                f"📅 Converted {len(converted)} date columns")
        return df

    def _detect_and_convert_numbers(self, df):
        converted = []
        for col in df.select_dtypes(
                include=['object']).columns:
            cleaned = df[col].astype(str).str.replace(
                r'[Rs\.,\s₨]', '', regex=True)
            try:
                numeric = pd.to_numeric(cleaned, errors='coerce')
                if numeric.notna().sum() > len(df) * 0.8:
                    df[col] = numeric
                    converted.append(col)
            except Exception:
                pass
        if converted:
            self.cleaning_report.append(
                f"🔢 Converted {len(converted)} numeric cols")
        return df

    def _handle_null_values(self, df):
        actions = 0
        cols_to_drop = []
        for col in df.columns:
            null_pct = df[col].isnull().sum() / len(df) * 100
            if null_pct > 60:
                cols_to_drop.append(col)
                actions += 1
            elif df[col].dtype in ['float64', 'int64']:
                df[col] = df[col].fillna(df[col].median())
                actions += 1
            elif df[col].isnull().any():
                df[col] = df[col].fillna('Unknown')
                actions += 1
        df = df.drop(columns=cols_to_drop)
        if actions:
            self.cleaning_report.append(
                f"🔧 Fixed nulls in {actions} columns")
        return df

    def _detect_pkr_columns(self, df):
        keywords = [
            'price', 'amount', 'cost', 'revenue',
            'salary', 'income', 'payment', 'total',
            'fee', 'sale', 'profit', 'loss', 'budget',
            'qeemat', 'tankhwa'
        ]
        self.pkr_columns = [
            col for col in df.select_dtypes(
                include=['float64', 'int64']).columns
            if any(k in col.lower() for k in keywords)
        ]
        if self.pkr_columns:
            self.cleaning_report.append(
                f"💰 PKR columns: {self.pkr_columns}")
        return df

    def _remove_invisible_characters(self, df):
        for col in df.select_dtypes(
                include=['object']).columns:
            df[col] = df[col].astype(str).apply(
                lambda x: re.sub(
                    r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]',
                    '', x
                ) if x != 'nan' else x
            )
            df[col] = df[col].replace('nan', np.nan)
        return df