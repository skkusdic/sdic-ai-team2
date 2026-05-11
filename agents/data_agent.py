import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from data import get_financials


def run_data_agent(state: dict) -> dict:
    company = state["company"]
    financials = get_financials(company)
    return {
        **state,
        "financials": financials,
        "next_agent": "analysis_agent" if financials else "no_data",
    }


if __name__ == "__main__":
    import pprint
    mock_state = {"company": "삼성전자"}
    result = run_data_agent(mock_state)
    pprint.pprint(result)
