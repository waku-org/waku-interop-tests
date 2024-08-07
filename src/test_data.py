from time import time
from datetime import datetime, timedelta

NOW = datetime.now()

SAMPLE_INPUTS = [
    {"description": "A simple string", "value": "Hello World!"},
    {"description": "An integer", "value": "1234567890"},
    {"description": "A dictionary", "value": '{"key": "value"}'},
    {"description": "Chinese characters", "value": "这是一些中文"},
    {"description": "Emojis", "value": "🚀🌟✨"},
    {"description": "Lorem ipsum text", "value": "Lorem ipsum dolor sit amet"},
    {"description": "HTML content", "value": "<html><body>Hello</body></html>"},
    {"description": "Cyrillic characters", "value": "\u041f\u0440\u0438\u0432\u0435\u0442"},
    {"description": "Base64 encoded string", "value": "Base64==dGVzdA=="},
    {"description": "Binary data", "value": "d29ya2luZyB3aXRoIGJpbmFyeSBkYXRh: \x50\x51"},
    {"description": "Special characters with whitespace", "value": "\t\nSpecial\tCharacters\n"},
    {"description": "Boolean false as a string", "value": "False"},
    {"description": "A float number", "value": "3.1415926535"},
    {"description": "A list", "value": "[1, 2, 3, 4, 5]"},
    {"description": "Hexadecimal number as a string", "value": "0xDEADBEEF"},
    {"description": "Email format", "value": "user@example.com"},
    {"description": "URL format", "value": "http://example.com"},
    {"description": "Date and time in ISO format", "value": "2023-11-01T12:00:00Z"},
    {"description": "String with escaped quotes", "value": '"Escaped" \\"quotes\\"'},
    {"description": "A regular expression", "value": "Regular expression: ^[a-z0-9_-]{3,16}$"},
    {"description": "A very long string", "value": "x" * 1000},
    {"description": "A JSON string", "value": '{"name": "John", "age": 30, "city": "New York"}'},
    {"description": "A Unix path", "value": "/usr/local/bin"},
    {"description": "A Windows path", "value": "C:\\Windows\\System32"},
    {"description": "An SQL query", "value": "SELECT * FROM users WHERE id = 1;"},
    {"description": "JavaScript code snippet", "value": "function test() { console.log('Hello World'); }"},
    {"description": "A CSS snippet", "value": "body { background-color: #fff; }"},
    {"description": "A Python one-liner", "value": "print('Hello World')"},
    {"description": "An IP address", "value": "192.168.1.1"},
    {"description": "A domain name", "value": "www.example.com"},
    {"description": "A user agent string", "value": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
    {"description": "A credit card number", "value": "1234-5678-9012-3456"},
    {"description": "A phone number", "value": "+1234567890"},
    {"description": "A UUID", "value": "123e4567-e89b-12d3-a456-426614174000"},
    {"description": "A hashtag", "value": "#helloWorld"},
    {"description": "A Twitter handle", "value": "@username"},
    {"description": "A password", "value": "P@ssw0rd!"},
    {"description": "A date in common format", "value": "01/11/2023"},
    {"description": "A time string", "value": "12:00:00"},
    {"description": "A mathematical equation", "value": "E = mc^2"},
]

INVALID_PAYLOADS = [
    {"description": "Empty string", "value": ""},
    {"description": "Unecoded text", "value": "Hello World!"},
    {"description": "A dictionary", "value": {"key": "YWFh"}},
    {"description": "An integer", "value": 1234567890},
    {"description": "A list", "value": ["YWFh"]},
    {"description": "A bool", "value": True},
]

INVALID_CONTENT_TOPICS = [
    {"description": "Empty string", "value": ""},
    {"description": "A dictionary", "value": {"key": "YWFh"}},
    {"description": "An integer", "value": 1234567890},
    {"description": "A list", "value": ["YWFh"]},
    {"description": "A bool", "value": True},
]

CONTENT_TOPICS_DIFFERENT_SHARDS = [
    "/myapp/1/latest/proto",  # resolves to shard 0
    "/waku/2/content/test.js",  # resolves to shard 1
    "/app/22/sometopic/someencoding",  # resolves to shard 2
    "/toychat/2/huilong/proto",  # resolves to shard 3
    "/statusim/1/community/cbor",  # resolves to shard 4
    "/app/27/sometopic/someencoding",  # resolves to shard 5
    "/app/29/sometopic/someencoding",  # resolves to shard 6
    "/app/20/sometopic/someencoding",  # resolves to shard 7
]

CONTENT_TOPICS_SHARD_0 = [
    "/newsService/1.0/weekly/protobuf",
    "/newsService/1.0/alerts/xml",
    "/newsService/1.0/updates/json",
    "/newsService/2.0/alerts/json",
    "/newsService/2.0/summaries/xml",
    "/newsService/2.0/highlights/yaml",
    "/newsService/3.0/weekly/json",
    "/newsService/3.0/summaries/xml",
]

CONTENT_TOPICS_SHARD_7 = [
    "/newsService/2.0/alerts/yaml",
    "/newsService/2.0/highlights/xml",
    "/newsService/3.0/daily/protobuf",
    "/newsService/3.0/alerts/xml",
    "/newsService/3.0/updates/protobuf",
    "/newsService/3.0/reviews/xml",
    "/newsService/4.0/alerts/yaml",
    "/newsService/4.0/updates/yaml",
]

DEFAULT_CLUSTER_ID = "3"
VALID_PUBSUB_TOPICS = [
    f"/waku/2/rs/{DEFAULT_CLUSTER_ID}/0",
    f"/waku/2/rs/{DEFAULT_CLUSTER_ID}/1",
    f"/waku/2/rs/{DEFAULT_CLUSTER_ID}/9",
    f"/waku/2/rs/{DEFAULT_CLUSTER_ID}/25",
    f"/waku/2/rs/{DEFAULT_CLUSTER_ID}/1000",
]

PUBSUB_TOPICS_STORE = [
    f"/waku/2/rs/{DEFAULT_CLUSTER_ID}/0",
    f"/waku/2/rs/{DEFAULT_CLUSTER_ID}/1",
    f"/waku/2/rs/{DEFAULT_CLUSTER_ID}/2",
    f"/waku/2/rs/{DEFAULT_CLUSTER_ID}/3",
    f"/waku/2/rs/{DEFAULT_CLUSTER_ID}/4",
    f"/waku/2/rs/{DEFAULT_CLUSTER_ID}/5",
    f"/waku/2/rs/{DEFAULT_CLUSTER_ID}/6",
    f"/waku/2/rs/{DEFAULT_CLUSTER_ID}/7",
    f"/waku/2/rs/{DEFAULT_CLUSTER_ID}/8",
]

INVALID_PUBSUB_TOPICS = ["/test/2/rs/0/1", "/waku/3/rs/0/1", "/waku/2/test/0/1", "/waku/2/rs/3/b", "/waku/2/rs/0"]

PUBSUB_TOPICS_DIFFERENT_CLUSTERS = [
    "/waku/2/rs/2/0",
    "/waku/2/rs/2/1",
    "/waku/2/rs/5/0",
    "/waku/2/rs/5/1",
    "/waku/2/rs/5/999",
    "/waku/2/rs/8/0",
    "/waku/2/rs/999/999",
]

PUBSUB_TOPICS_SAME_CLUSTER = [
    "/waku/2/rs/2/0",
    "/waku/2/rs/2/1",
    "/waku/2/rs/2/2",
    "/waku/2/rs/2/3",
    "/waku/2/rs/2/4",
    "/waku/2/rs/2/5",
    "/waku/2/rs/2/6",
    "/waku/2/rs/2/7",
]

PUBSUB_TOPICS_WRONG_FORMAT = [
    {"description": "A dictionary", "value": {"key": "YWFh"}},
    {"description": "An integer", "value": 1234567890},
    {"description": "A list", "value": ["YWFh"]},
    {"description": "A bool", "value": True},
]

SAMPLE_TIMESTAMPS = [
    {"description": "Now", "value": int(time() * 1e9), "valid_for": ["nwaku", "gowaku"]},
    {
        "description": "Far future",
        "value": int((NOW + timedelta(days=365 * 10)).timestamp() * 1e9),
        "valid_for": ["nwaku", "gowaku"],
    },  # 10 years from now
    {"description": "Recent past", "value": int((NOW - timedelta(hours=1)).timestamp() * 1e9), "valid_for": ["nwaku", "gowaku"]},  # 1 hour ago
    {"description": "Near future", "value": int((NOW + timedelta(hours=1)).timestamp() * 1e9), "valid_for": ["nwaku", "gowaku"]},  # 1 hour ahead
    {"description": "Positive number", "value": 1, "valid_for": ["nwaku", "gowaku"]},
    {"description": "Negative number", "value": -1, "valid_for": ["nwaku", "gowaku"]},
    {"description": "DST change", "value": int(datetime(2020, 3, 8, 2, 0, 0).timestamp() * 1e9), "valid_for": ["nwaku", "gowaku"]},  # DST starts
    {"description": "Timestamp as string number", "value": str(int(time() * 1e9)), "valid_for": []},
    {"description": "Invalid large number", "value": 2**63, "valid_for": []},
    {"description": "Float number", "value": float(time() * 1e9), "valid_for": []},
    {"description": "Array instead of timestamp", "value": [int(time() * 1e9)], "valid_for": []},
    {"description": "Object instead of timestamp", "value": {"time": int(time() * 1e9)}, "valid_for": []},
    {"description": "ISO 8601 timestamp", "value": "2023-12-26T10:58:51", "valid_for": []},
    {"description": "Missing", "value": None, "valid_for": ["gowaku"]},
]

PUBSUB_TOPICS_RLN = ["/waku/2/rs/1/0"]
