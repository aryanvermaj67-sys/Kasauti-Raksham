"""Facts about one claimed ISIN across the depository RecordResponses. No decision here; verdict/rules.py decides."""


def compare(isin: str, records) -> dict:
    ok = [r for r in records if r.status == "OK"]
    units, accounts = 0, 0
    for r in ok:
        for acc in r.payload["accounts"]:
            accounts += 1
            holdings = acc["Account"].get("Summary", {}).get("Investment", {}).get("Holdings", {}).get("Holding", [])
            units += sum(h["units"] for h in holdings if h["isin"] == isin)
    return {"ok_depositories": [r.payload["depository"] for r in ok], "units_found": units, "has_account": accounts > 0}
