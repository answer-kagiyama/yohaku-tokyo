from station_pipeline.inspect.schema import (
    coord_fill_rate,
    find_field,
    inspect_datastore,
)

from .ckan_fakes import datastore_result

OTA_FIELDS = [
    "全国地方公共団体コード",
    "ID",
    "地方公共団体名",
    "名称",
    "所在地_連結表記",
    "緯度",
    "経度",
    "面積(㎡)",
]


def test_find_field_exact_and_prefix():
    assert find_field(OTA_FIELDS, ("緯度",)) == "緯度"
    assert find_field(["緯度(世界測地系)", "経度(世界測地系)"], ("緯度",)) == "緯度(世界測地系)"
    assert find_field(["Latitude"], ("lat", "latitude")) == "Latitude"
    assert find_field(OTA_FIELDS, ("住所",)) is None


def test_empty_coordinate_columns_have_zero_fill():
    # Real case: Ota ward park list has 緯度/経度 columns but empty values.
    records = [
        {
            "名称": "池上五丁目公園",
            "所在地_連結表記": "東京都大田区池上5-15-18",
            "緯度": "",
            "経度": "",
        }
    ]
    result = inspect_datastore(datastore_result(OTA_FIELDS, records, total=513))
    assert result.latField == "緯度"
    assert result.coordFillRate == 0.0
    assert result.addressField == "所在地_連結表記"
    assert result.addressFillRate == 1.0
    assert result.nameField == "名称"
    assert result.total == 513
    assert "_id" not in result.fields


def test_coord_fill_rate_rejects_invalid_values():
    records = [
        {"lat": "35.68", "lng": "139.76"},
        {"lat": "139.76", "lng": "35.68"},  # swapped
        {"lat": "0", "lng": "0"},
        {"lat": "abc", "lng": "139.7"},
    ]
    assert coord_fill_rate(records, "lat", "lng") == 0.25


def test_no_location_columns():
    result = inspect_datastore(datastore_result(["名称", "面積"], [{"名称": "a", "面積": "1"}]))
    assert result.coordFillRate is None
    assert result.addressField is None


def test_find_field_qualified_suffix():
    fields = ["観光ポイント_名称", "観光ポイント_緯度", "観光ポイント_経度", "観光ポイント_説明"]
    assert find_field(fields, ("緯度",)) == "観光ポイント_緯度"
    assert find_field(fields, ("名称",)) == "観光ポイント_名称"
    assert find_field(fields, ("住所",)) is None


def test_observed_name_columns():
    assert find_field(["自治体名", "館名", "所在地"], ("名称", "施設名", "館名")) == "館名"
    fields = ["最終更新日", "ページタイトル", "分類", "所在地"]
    from station_pipeline.inspect.schema import NAME_NAMES

    assert find_field(fields, NAME_NAMES) == "ページタイトル"
    assert find_field(["地方公共団体名", "名称"], NAME_NAMES) == "名称"
