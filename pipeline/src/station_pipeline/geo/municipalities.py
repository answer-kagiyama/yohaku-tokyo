"""Which municipalities does a station's radius touch? (ADR 0008)"""

from dataclasses import dataclass

from pyproj import Geod

from ..http import HttpClient, build_url

REVERSE_ENDPOINT = "https://mreversegeocoder.gsi.go.jp/reverse-geocoder/LonLatToAddress"

# 全国地方公共団体コード (5 digits, without check digit) for Tokyo.
TOKYO_MUNICIPALITY_CODES: dict[str, str] = {
    "13101": "千代田区", "13102": "中央区", "13103": "港区", "13104": "新宿区", "13105": "文京区",
    "13106": "台東区", "13107": "墨田区", "13108": "江東区", "13109": "品川区", "13110": "目黒区",
    "13111": "大田区", "13112": "世田谷区", "13113": "渋谷区", "13114": "中野区", "13115": "杉並区",
    "13116": "豊島区", "13117": "北区", "13118": "荒川区", "13119": "板橋区", "13120": "練馬区",
    "13121": "足立区", "13122": "葛飾区", "13123": "江戸川区",
    "13201": "八王子市", "13202": "立川市", "13203": "武蔵野市", "13204": "三鷹市", "13205": "青梅市",
    "13206": "府中市", "13207": "昭島市", "13208": "調布市", "13209": "町田市", "13210": "小金井市",
    "13211": "小平市", "13212": "日野市", "13213": "東村山市", "13214": "国分寺市", "13215": "国立市",
    "13218": "福生市", "13219": "狛江市", "13220": "東大和市", "13221": "清瀬市",
    "13222": "東久留米市", "13223": "武蔵村山市", "13224": "多摩市", "13225": "稲城市",
    "13227": "羽村市", "13228": "あきる野市", "13229": "西東京市",
    "13303": "瑞穂町", "13305": "日の出町", "13307": "檜原村", "13308": "奥多摩町",
    "13361": "大島町", "13362": "利島村", "13363": "新島村", "13364": "神津島村",
    "13381": "三宅村", "13382": "御蔵島村", "13401": "八丈町", "13402": "青ヶ島村", "13421": "小笠原村",
}  # fmt: skip

GEOD = Geod(ellps="GRS80")


@dataclass(frozen=True)
class Municipality:
    code: str
    name: str


def sample_points(lat: float, lng: float, radius_m: float) -> list[tuple[float, float]]:
    """Center + 8 points at r/2 + 16 points at r (geodesic, not lat/lng arithmetic)."""
    points = [(lat, lng)]
    for distance, n in ((radius_m / 2, 8), (radius_m, 16)):
        for i in range(n):
            lon2, lat2, _ = GEOD.fwd(lng, lat, 360 * i / n, distance)
            points.append((lat2, lon2))
    return points


class GsiReverseGeocoder:
    def __init__(self, client: HttpClient, endpoint: str = REVERSE_ENDPOINT) -> None:
        self.client = client
        self.endpoint = endpoint

    def municipality(self, lat: float, lng: float) -> Municipality | None:
        # Rounded so that the cache key is stable across float noise.
        url = build_url(self.endpoint, {"lat": f"{lat:.6f}", "lon": f"{lng:.6f}"})
        body = self.client.get_json(url) or {}
        code = (body.get("results") or {}).get("muniCd")
        if not code:
            return None  # e.g. on water
        code = str(code)[:5]
        name = TOKYO_MUNICIPALITY_CODES.get(code)
        return Municipality(code, name) if name else Municipality(code, f"(都外 {code})")


def municipalities_within(
    geocoder: GsiReverseGeocoder, lat: float, lng: float, radius_m: float
) -> list[Municipality]:
    found: dict[str, Municipality] = {}
    for plat, plng in sample_points(lat, lng, radius_m):
        m = geocoder.municipality(plat, plng)
        if m is not None:
            found.setdefault(m.code, m)
    return sorted(found.values(), key=lambda m: m.code)
