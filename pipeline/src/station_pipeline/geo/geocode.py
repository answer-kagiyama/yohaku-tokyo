"""Address -> coordinates (ADR 0007). The GSI API returns a municipality centroid for unknown
addresses, so municipality-level matches are rejected: better unlocated than wrong."""

import re
import unicodedata
from dataclasses import dataclass
from typing import Any, Protocol

from ..http import HttpClient, build_url
from ..inspect.schema import TOKYO_LAT, TOKYO_LNG

GSI_ENDPOINT = "https://msearch.gsi.go.jp/address-search/AddressSearch"
OTHER_PREFECTURES = tuple(
    [
        "北海道",
        "青森県",
        "岩手県",
        "宮城県",
        "秋田県",
        "山形県",
        "福島県",
        "茨城県",
        "栃木県",
        "群馬県",
        "埼玉県",
        "千葉県",
        "神奈川県",
        "新潟県",
        "富山県",
        "石川県",
        "福井県",
        "山梨県",
        "長野県",
        "岐阜県",
        "静岡県",
        "愛知県",
        "三重県",
        "滋賀県",
        "京都府",
        "大阪府",
        "兵庫県",
        "奈良県",
        "和歌山県",
        "鳥取県",
        "島根県",
        "岡山県",
        "広島県",
        "山口県",
        "徳島県",
        "香川県",
        "愛媛県",
        "高知県",
        "福岡県",
        "佐賀県",
        "長崎県",
        "熊本県",
        "大分県",
        "宮崎県",
        "鹿児島県",
        "沖縄県",
    ]
)


def is_outside_tokyo(address: str) -> bool:
    """e.g. 千代田区's 軽井沢少年自然の家 is listed with a 長野県 address."""
    return normalize_address(address).startswith(OTHER_PREFECTURES)


PREFECTURE = "東京都"
# All 62 municipalities of Tokyo. An explicit list, because a suffix regex mis-splits names
# such as 武蔵村山市 (-> 武蔵村) and would let municipality-level centroids through.
TOKYO_MUNICIPALITIES = [
    "千代田区",
    "中央区",
    "港区",
    "新宿区",
    "文京区",
    "台東区",
    "墨田区",
    "江東区",
    "品川区",
    "目黒区",
    "大田区",
    "世田谷区",
    "渋谷区",
    "中野区",
    "杉並区",
    "豊島区",
    "北区",
    "荒川区",
    "板橋区",
    "練馬区",
    "足立区",
    "葛飾区",
    "江戸川区",
    "八王子市",
    "立川市",
    "武蔵野市",
    "三鷹市",
    "青梅市",
    "府中市",
    "昭島市",
    "調布市",
    "町田市",
    "小金井市",
    "小平市",
    "日野市",
    "東村山市",
    "国分寺市",
    "国立市",
    "福生市",
    "狛江市",
    "東大和市",
    "清瀬市",
    "東久留米市",
    "武蔵村山市",
    "多摩市",
    "稲城市",
    "羽村市",
    "あきる野市",
    "西東京市",
    "瑞穂町",
    "日の出町",
    "檜原村",
    "奥多摩町",
    "大島町",
    "利島村",
    "新島村",
    "神津島村",
    "三宅村",
    "御蔵島村",
    "八丈町",
    "青ヶ島村",
    "小笠原村",
]
# Longest first so that e.g. 東村山市 is not shadowed by a shorter prefix.
_MUNICIPALITIES_BY_LENGTH = sorted(TOKYO_MUNICIPALITIES, key=len, reverse=True)
COUNTY_RE = re.compile(r"^[^\s]{1,4}郡")


@dataclass(frozen=True)
class GeocodeResult:
    lat: float
    lng: float
    matched: str
    precision: str  # exact | partial
    provider: str

    def to_dict(self) -> dict[str, Any]:
        return {"provider": self.provider, "matched": self.matched, "precision": self.precision}


class Geocoder(Protocol):
    def geocode(self, address: str, municipality: str | None = None) -> GeocodeResult | None: ...


def normalize_address(text: str) -> str:
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", text))


_KANJI_DIGITS = {c: i for i, c in enumerate("〇一二三四五六七八九")}
_HYPHENS = re.compile(r"[‐‑‒–—―−ーｰ－-]")


def _kanji_number(text: str) -> int:
    """一 .. 九十九 (enough for 丁目)."""
    if "十" in text:
        tens, _, ones = text.partition("十")
        return (_KANJI_DIGITS.get(tens, 1) if tens else 1) * 10 + (
            _KANJI_DIGITS.get(ones, 0) if ones else 0
        )
    return _KANJI_DIGITS[text]


def canonical_address(text: str) -> str:
    """One spelling for 三丁目１３番９号 / 3-13-9 / 3丁目13-9 so they can be compared."""
    a = normalize_address(text)
    a = re.sub(r"([〇一二三四五六七八九十]+)丁目", lambda m: f"{_kanji_number(m.group(1))}丁目", a)
    a = _HYPHENS.sub("-", a)
    a = re.sub(r"(丁目|番地|番|号)", "-", a)
    a = re.sub(r"-+", "-", a)
    return a.rstrip("-")


def strip_trailing_place_name(address: str) -> str:
    """'豊島区長崎1-9-2　金剛院' -> '豊島区長崎1-9-2'. After the block number (a token with digits),
    a following token without digits is a place name, not part of the address. Spaces between
    address components ('東京都 千代田区 外神田2-16-9') are kept."""
    tokens = [t for t in re.split(r"[\s\u3000]+", unicodedata.normalize("NFKC", address)) if t]
    kept: list[str] = []
    seen_number = False
    for t in tokens:
        has_digit = any(c.isdigit() for c in t)
        if seen_number and not has_digit:
            break
        kept.append(t)
        seen_number = seen_number or has_digit
    return "".join(kept)


def _starts_with_municipality(address: str) -> bool:
    rest = COUNTY_RE.sub("", address)
    return any(rest.startswith(m) for m in _MUNICIPALITIES_BY_LENGTH)


def complete_address(address: str, organization: str | None) -> str:
    """Clean a listing address and prefix a missing prefecture / municipality.

    Park lists spanning areas use forms such as "港区六本木七丁目ほか" or "A市X/B市Yほか";
    the first area is geocoded. `organization` is only used as a municipality if it is one.
    """
    a = strip_trailing_place_name(address)
    a = normalize_address(a)
    a = re.split(r"[/／、・;；]", a, maxsplit=1)[0]
    a = re.sub(r"(ほか|他|外)$", "", a)
    a = re.sub(r"先$", "", a)  # "1-19-13先" = in front of 1-19-13
    a = a.removeprefix(PREFECTURE)
    for m in _MUNICIPALITIES_BY_LENGTH:  # "千代田区千代田区富士見" (duplicated in source)
        if a.startswith(m + m):
            a = a[len(m) :]
            break
    if not _starts_with_municipality(a) and organization in TOKYO_MUNICIPALITIES:
        a = organization + a
    return PREFECTURE + a


def below_municipality(matched: str) -> str:
    """The part of a matched address below the municipality (empty = too coarse)."""
    rest = COUNTY_RE.sub("", normalize_address(matched).removeprefix(PREFECTURE))
    for name in _MUNICIPALITIES_BY_LENGTH:
        if rest.startswith(name):
            return rest[len(name) :]
    return rest


def classify_match(query: str, matched: str) -> str | None:
    if not below_municipality(matched):
        return None
    q, t = canonical_address(query), canonical_address(matched)
    if q == t:
        return "exact"
    # Prefix only at a component boundary: 銀座1-2 must not match 銀座1-25-2,
    # and the town 芝 must not match 芝公園1.
    if q.startswith(t):
        nxt = q[len(t)]
        if nxt == "-" or (not t[-1].isdigit() and nxt.isdigit()):
            return "partial"
    return None


class GsiGeocoder:
    provider = "gsi"

    def __init__(self, client: HttpClient, endpoint: str = GSI_ENDPOINT) -> None:
        self.client = client
        self.endpoint = endpoint
        self.calls = 0

    def geocode(self, address: str, municipality: str | None = None) -> GeocodeResult | None:
        query = complete_address(address, municipality)
        self.calls += 1
        features = self.client.get_json(build_url(self.endpoint, {"q": query}))
        for f in features or []:
            lng, lat = f["geometry"]["coordinates"]
            title = f.get("properties", {}).get("title", "")
            precision = classify_match(query, title)
            if precision is None:
                continue
            if not (TOKYO_LAT[0] <= lat <= TOKYO_LAT[1] and TOKYO_LNG[0] <= lng <= TOKYO_LNG[1]):
                continue
            return GeocodeResult(
                lat=lat, lng=lng, matched=title, precision=precision, provider=self.provider
            )
        return None
