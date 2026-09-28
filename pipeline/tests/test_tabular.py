import pytest

from station_pipeline.inspect.tabular import TabularError, parse_csv

CSV = (
    "名称,所在地,緯度,経度\n"
    "宮本公園,東京都千代田区外神田二丁目16番９号,,\n"
    ",,,\n"
    "神田児童公園,東京都千代田区,35.69,139.77\n"
)


@pytest.mark.parametrize("encoding", ["utf-8-sig", "utf-8", "cp932"])
def test_parses_common_encodings(encoding):
    fields, records, detected = parse_csv(CSV.encode(encoding))
    assert fields == ["名称", "所在地", "緯度", "経度"]
    assert [r["名称"] for r in records] == ["宮本公園", "神田児童公園"]  # blank row dropped
    assert detected == ("cp932" if encoding == "cp932" else "utf-8-sig")


def test_strips_header_whitespace():
    fields, records, _ = parse_csv(" 名称 ,緯度\na,1\n".encode())
    assert fields == ["名称", "緯度"]
    assert records == [{"名称": "a", "緯度": "1"}]


def test_empty_file():
    with pytest.raises(TabularError):
        parse_csv(b"")


def test_utf16_with_bom():
    # observed in 新宿区の観光ポイント
    fields, records, enc = parse_csv(
        "観光ポイント_名称,観光ポイント_緯度\n新宿御苑,35.685\n".encode("utf-16")
    )
    assert enc == "utf-16"
    assert fields == ["観光ポイント_名称", "観光ポイント_緯度"]
    assert records == [{"観光ポイント_名称": "新宿御苑", "観光ポイント_緯度": "35.685"}]


def test_geojson_points_become_lat_lng_columns():
    from station_pipeline.inspect.tabular import parse_table

    doc = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"施設名": "芝公園", "分類": "公園"},
                "geometry": {"type": "Point", "coordinates": [139.749, 35.655]},
            },
            {
                "type": "Feature",
                "properties": {"施設名": "有栖川宮記念公園", "分類": None},
                "geometry": {"type": "Polygon", "coordinates": []},
            },
        ],
    }
    import json as _json

    fields, records, _ = parse_table(_json.dumps(doc, ensure_ascii=False).encode(), "GeoJSON")
    assert fields == ["施設名", "分類", "緯度", "経度"]
    assert records[0] == {"施設名": "芝公園", "分類": "公園", "緯度": "35.655", "経度": "139.749"}
    assert "緯度" not in records[1]  # non-point geometry: no coordinates, not guessed
    assert records[1]["分類"] == ""


def test_unsupported_format():
    from station_pipeline.inspect.tabular import parse_table

    with pytest.raises(TabularError, match="unsupported"):
        parse_table(b"", "xlsx")
