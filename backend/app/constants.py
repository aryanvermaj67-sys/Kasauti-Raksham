"""Word lists for name matching (SEBI, NSE/BSE, RBI connectors and broker rules)."""

# Security (share) names for ISIN mapping: only these suffixes are stripped, never words like capital or stock.
SECURITY_SUFFIXES = frozenset({"ltd", "limited", "pvt", "private"})

# Firm names (brokers, RBI list). Dropped before an exact match: legal form only ("Pvt. Ltd." = "Private Limited").
LEGAL_WORDS = frozenset({"limited", "ltd", "pvt", "p", "private", "the", "co", "inc", "llp"})

# Also dropped before the similarity score: words any broker name may carry, which say nothing about who it is.
GENERIC_WORDS = LEGAL_WORDS | frozenset(
    {
        "and", "company", "corporation", "corp", "india", "indian", "global", "international", "group",
        "capital", "wealth", "money", "finance", "financial", "finserv", "fintech", "fiscal",
        "securities", "security", "stock", "stocks", "share", "shares", "equity", "equities", "commodities",
        "commodity", "derivatives", "broking", "broker", "brokers", "brokerage", "trading", "trade", "traders",
        "markets", "market", "investments", "investment", "invest", "investors", "fund", "funds", "asset",
        "assets", "portfolio", "advisors", "advisers", "advisory", "consultants", "consultancy", "research",
        "analyst", "analysts", "management", "services", "service", "solutions", "ventures", "holdings",
        "enterprises", "associates", "club",
    }
)  # fmt: skip
