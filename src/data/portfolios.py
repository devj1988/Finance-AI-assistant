sample_portfolio_json = {
        "base_currency": "USD",
        "horizon_years": 15,
        "risk_tolerance": "moderate",
        "holdings": [
            {
                "ticker": "VTI",
                "name": "Vanguard Total Stock Market ETF",
                "asset_class": "Equity",
                "region": "US",
                "sector": "Broad Market",
                "weight_percent": 50.0,
                "current_value": 25000,
            },
            {
                "ticker": "BND",
                "name": "Vanguard Total Bond Market ETF",
                "asset_class": "Bond",
                "region": "US",
                "sector": "Bonds",
                "weight_percent": 30.0,
                "current_value": 15000,
            },
            {
                "ticker": "VXUS",
                "name": "Vanguard Total International Stock ETF",
                "asset_class": "Equity",
                "region": "International",
                "sector": "Broad Market",
                "weight_percent": 20.0,
                "current_value": 10000,
            },
        ],
    }
simple_portfolio = {
        "base_currency": "USD",
        "horizon_years": 5,
        "holdings": [
            {
                "ticker": "NVDA",
                "weight_percent": 60.0,
                "current_value": 25000
            },
            {
                "ticker": "VOO",
                "weight_percent": 40.0,
                "current_value": 15000
            }
        ]
}