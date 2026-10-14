# tests/test_cleaning.py
import sys
import os
sys.path.insert(0, os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from data.cleaner import DataCleaner
from data.database import DatabaseManager
from security.sql_guard import SQLGuard

def test_cleaning():
    print("\n1️⃣  Testing Data Cleaning...")
    df = pd.DataFrame({
        'Product Name': ['Laptop', 'Phone', None, 'Laptop'],
        'Price Rs': ['50,000', '25000', '15000', '50,000'],
        'Empty Col': [None, None, None, None]
    })
    cleaner = DataCleaner()
    clean_df, report = cleaner.clean(df)
    print("Clean DataFrame:")
    print(clean_df)
    print("Report:")
    for r in report:
        print(f"  {r}")
    assert len(clean_df) == 3
    assert 'product_name' in clean_df.columns
    print("✅ Cleaning tests passed!")

def test_database():
    print("\n2️⃣  Testing Database...")
    df = pd.DataFrame({
        'product': ['Laptop', 'Phone', 'Tablet'],
        'sales': [50000, 25000, 15000],
        'region': ['Karachi', 'Lahore', 'Islamabad']
    })
    db = DatabaseManager('test_123')
    assert db.load_dataframe(df)
    result = db.execute_query(
        "SELECT * FROM user_data WHERE sales > 20000")
    assert len(result) == 2
    db.cleanup()
    print("✅ Database tests passed!")

def test_security():
    print("\n3️⃣  Testing SQL Security...")
    guard = SQLGuard()
    dangerous = [
        "DROP TABLE user_data",
        "DELETE FROM user_data",
        "INSERT INTO user_data VALUES (1,2,3)"
    ]
    for sql in dangerous:
        is_safe, _ = guard.validate(sql)
        assert not is_safe
        print(f"  ✅ Blocked: {sql[:40]}")
    safe = "SELECT * FROM user_data LIMIT 10"
    is_safe, _ = guard.validate(safe)
    assert is_safe
    print("✅ Security tests passed!")

if __name__ == "__main__":
    print("🧪 Running Tests...")
    print("=" * 40)
    test_cleaning()
    test_database()
    test_security()
    print("\n" + "=" * 40)
    print("✅ ALL TESTS PASSED!")
    print("Run app: streamlit run app.py")