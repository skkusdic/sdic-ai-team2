MOCK_DATA = {
    "삼성전자": {
        2022: {"매출액": 302_231, "영업이익": 43_376, "순이익": 55_654},
        2023: {"매출액": 258_935, "영업이익":  6_567, "순이익": 15_487},
        2024: {"매출액": 300_870, "영업이익": 32_726, "순이익": 34_082},
    }
}


def get_financials(company_name: str) -> dict:
    # TODO: dart-fss 연동
    return MOCK_DATA.get(company_name, {})


if __name__ == "__main__":
    data = get_financials("삼성전자")
    print(f"{'연도':<6} {'매출액':>12} {'영업이익':>12} {'순이익':>12}  (단위: 억원)")
    print("-" * 50)
    for year, metrics in sorted(data.items()):
        print(
            f"{year:<6} "
            f"{metrics['매출액']:>12,} "
            f"{metrics['영업이익']:>12,} "
            f"{metrics['순이익']:>12,}"
        )
