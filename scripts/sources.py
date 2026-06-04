"""Source configuration for the incident watcher.

Sources are tiered by reliability/authority. Each candidate incident gets
tagged with the tier of the source that surfaced it, which becomes the
`confidence` field on the PR.
"""

# Tier 1: security firms with formal incident reporting.
# These are the highest-signal sources; nearly every entry is a real incident.
TIER_1_SOURCES = [
    {
        "name": "SlowMist Hacked DB (Solana)",
        "type": "html_scrape",
        "url": "https://hacked.slowmist.io/?c=Solana",
        "scraper": "slowmist",
    },
    {
        "name": "Halborn Blog",
        "type": "rss",
        # rss.xml returns the blog HTML shell; feed.xml is the actual RSS.
        "url": "https://www.halborn.com/blog/feed.xml",
    },
    {
        "name": "Elliptic Connect",
        "type": "rss",
        "url": "https://www.elliptic.co/blog/rss.xml",
    },
    {
        "name": "TRM Labs Blog",
        "type": "rss",
        "url": "https://www.trmlabs.com/post/rss.xml",
    },
    {
        "name": "Chainalysis Blog",
        "type": "rss",
        "url": "https://www.chainalysis.com/blog/rss/",
    },
]

# Tier 2: established crypto news outlets.
# Most Solana-tagged stories about exploits are real, but watch for noise
# (price commentary, recaps of older incidents, etc).
TIER_2_SOURCES = [
    {
        "name": "The Block",
        "type": "rss",
        "url": "https://www.theblock.co/rss.xml",
    },
    {
        "name": "CoinDesk",
        "type": "rss",
        "url": "https://www.coindesk.com/arc/outboundfeeds/rss/",
    },
    {
        "name": "Decrypt",
        "type": "rss",
        "url": "https://decrypt.co/feed",
    },
    {
        "name": "DL News",
        "type": "rss",
        "url": "https://www.dlnews.com/arc/outboundfeeds/rss/",
    },
    {
        "name": "CryptoSlate",
        "type": "rss",
        "url": "https://cryptoslate.com/feed/",
    },
]

# Tier 3: web search fallback for anything the feeds missed.
# Treat with skepticism — could be aggregator spam.
TIER_3_SEARCH_QUERIES = [
    "Solana exploit hack",
    "Solana DeFi drained million",
    "Solana protocol security incident",
    "Solana rug pull",
    # Keep queries broad; the LLM filter will narrow.
]

# Keywords that flag a feed item as potentially relevant.
# Conservative: we want recall over precision at this stage. The LLM does
# the precision work in the next step.
RELEVANCE_KEYWORDS = [
    "solana", "sol ",  # space after sol to avoid matching "sole", "sold", etc
    " spl ",
]

# Action keywords — at least one must appear alongside a Solana keyword.
ACTION_KEYWORDS = [
    "exploit", "exploited", "hack", "hacked", "drained", "drain",
    "stolen", "theft", "compromised", "breach", "rug pull", "rugpull",
    "vulnerability", "attack", "phishing", "scam", "siphoned",
]
