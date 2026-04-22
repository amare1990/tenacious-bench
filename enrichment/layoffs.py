def get_layoffs_mock(company_name: str) -> dict:
    # Simple mock: no layoffs by default
    return {"recent_layoff": False, "details": []}
