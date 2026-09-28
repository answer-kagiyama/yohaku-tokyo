import pytest

from station_pipeline.normalize.dedupe import dedupe_facilities, haversine_m, name_key


def fac(fid, name, lat, lng, source="source", precision=None):
    return {
        "id": fid,
        "name": name,
        "lat": lat,
        "lng": lng,
        "coordSource": source,
        "geocode": {"precision": precision} if precision else None,
    }


def test_haversine_known_distance():
    # Akihabara -> Kanda stations: ~0.74 km
    assert haversine_m(35.6984, 139.7731, 35.6918, 139.7709) == pytest.approx(760, abs=40)


def test_name_key():
    assert name_key("元町公園（もとまち）") == name_key("元町 公園")


def test_same_name_far_apart_is_kept():
    out = dedupe_facilities(
        [fac("a", "中央公園", 35.70, 139.70), fac("b", "中央公園", 35.60, 139.70)], 150
    )
    assert len(out) == 2


def test_exact_geocode_beats_partial():
    out = dedupe_facilities(
        [
            fac("p", "X公園", 35.7000, 139.7, "geocode", "partial"),
            fac("e", "X公園", 35.7001, 139.7, "geocode", "exact"),
        ],
        150,
    )
    assert [f["id"] for f in out] == ["e"]
    assert out[0]["duplicates"] == ["p"]


def test_unlocated_are_kept():
    u = fac("u", "X公園", None, None, source=None)
    out = dedupe_facilities([fac("a", "X公園", 35.7, 139.7), u], 150)
    assert [f["id"] for f in out] == ["a", "u"]
