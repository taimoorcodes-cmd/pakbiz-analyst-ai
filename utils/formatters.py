# utils/formatters.py
# PKR currency formatting

def format_pkr(amount: float) -> str:
    if amount is None:
        return "N/A"
    try:
        amount = float(amount)
        if amount >= 10_000_000:
            return f"Rs {amount/10_000_000:.2f} Crore"
        elif amount >= 100_000:
            return f"Rs {amount/100_000:.2f} Lakh"
        else:
            return f"Rs {amount:,.0f}"
    except Exception:
        return str(amount)


def format_number(num) -> str:
    try:
        return f"{float(num):,.2f}"
    except Exception:
        return str(num)