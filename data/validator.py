# data/validator.py
# Validates CSV files before processing

import pandas as pd
import os
from pathlib import Path

MAX_ROWS = int(os.getenv("MAX_ROWS", 100000))
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", 50))


class FileValidator:
    def __init__(self):
        self.errors = []
        self.warnings = []

    def validate(self, uploaded_file) -> dict:
        self.errors = []
        self.warnings = []
        metadata = {}

        if not self._check_extension(uploaded_file.name):
            return self._result(False, metadata)

        file_size_mb = uploaded_file.size / (1024 * 1024)
        if not self._check_size(file_size_mb):
            return self._result(False, metadata)

        metadata['file_size_mb'] = round(file_size_mb, 2)

        try:
            df, encoding, delimiter = self._read_file(
                uploaded_file)
        except Exception as e:
            self.errors.append(f"Cannot read file: {str(e)}")
            return self._result(False, metadata)

        if df.empty:
            self.errors.append("File is empty")
            return self._result(False, metadata)

        if not self._check_rows(len(df)):
            return self._result(False, metadata)

        if len(df.columns) < 2:
            self.warnings.append(
                "Only 1 column — limited analysis")

        null_cols = [
            c for c in df.columns if df[c].isnull().all()]
        if null_cols:
            self.warnings.append(
                f"Completely empty columns: {null_cols}")

        metadata.update({
            'rows': len(df),
            'columns': len(df.columns),
            'column_names': df.columns.tolist(),
            'encoding': encoding,
            'delimiter': delimiter,
            'null_percentage': round(
                df.isnull().sum().sum() /
                (df.shape[0] * df.shape[1]) * 100, 2
            )
        })
        return self._result(True, metadata, df)

    def _check_extension(self, filename: str) -> bool:
        if Path(filename).suffix.lower() != '.csv':
            self.errors.append("Only CSV files allowed")
            return False
        return True

    def _check_size(self, size_mb: float) -> bool:
        if size_mb > MAX_FILE_SIZE_MB:
            self.errors.append(
                f"File too large: {size_mb:.1f}MB. "
                f"Max: {MAX_FILE_SIZE_MB}MB")
            return False
        return True

    def _check_rows(self, row_count: int) -> bool:
        if row_count > MAX_ROWS:
            self.errors.append(
                f"Too many rows: {row_count:,}. "
                f"Max: {MAX_ROWS:,}")
            return False
        return True

    def _read_file(self, uploaded_file):
        encodings = ['utf-8', 'windows-1252', 'latin-1']
        delimiters = [',', ';', '|', '\t']
        for enc in encodings:
            for delim in delimiters:
                try:
                    uploaded_file.seek(0)
                    df = pd.read_csv(
                        uploaded_file,
                        encoding=enc,
                        sep=delim,
                        low_memory=False,
                        nrows=MAX_ROWS
                    )
                    if len(df.columns) > 1:
                        return df, enc, delim
                except Exception:
                    continue
        uploaded_file.seek(0)
        df = pd.read_csv(uploaded_file, low_memory=False)
        return df, 'utf-8', ','

    def _result(self, success, metadata, df=None):
        return {
            'success': success,
            'errors': self.errors,
            'warnings': self.warnings,
            'metadata': metadata,
            'dataframe': df
        }