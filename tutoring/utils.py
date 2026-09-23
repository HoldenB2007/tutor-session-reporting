import datetime


def fiscal_year_for(date: datetime.date) -> int:
    """LVAEP's fiscal year runs July–June and is named by the year it ends (Jul 2026 → FY 2027)."""
    return date.year + 1 if date.month >= 7 else date.year


def fiscal_year_label(date: datetime.date) -> str:
    fy = fiscal_year_for(date)
    return f"FY {fy - 1}-{fy}"
