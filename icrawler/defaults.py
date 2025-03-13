MAX_RETRIES = 3
BACKOFF_BASE = 1.2

ACCEPT_LANGUAGES = "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
)

DEFAULT_HEADERS = {
    "Accept-Language": ACCEPT_LANGUAGES,
    "User-Agent": USER_AGENT,
}
