import json

import pytest
from pyproj import Geod

from station_pipeline.aggregate.coverage import municipality_coverage, station_status
from station_pipeline.aggregate.run import aggregate_feature
from station_pipeline.aggregate.spatial import facilities_within
from station_pipeline.geo.municipalities import (
    GsiReverseGeocoder,
    Municipality,
    municipalities_within,
    sample_points,
)
from station_pipeline.http import HttpClient

GEOD = Geod(ellps="GRS80")
AKIBA = {"id": "akihabara", "lat": 35.6984, "lng": 139.7731}


def at(distance_m, azimuth=90.0, fid="f", **kw):
    lng, lat, _ = GEOD.fwd(AKIBA["lng"], AKIBA["lat"], azimuth, distance_m)
    return {
        "id": fid,
        "name": fid,
        "lat": lat,
        "lng": lng,
        "coordSource": "source",
        "datasetId": kw.get("datasetId", "d"),
        "organization": kw.get("organization", "千代田区"),
    }


class TestFacilitiesWithin:
    @pytest.mark.parametrize("azimuth", [0, 90, 180, 270, 45])
    def test_radius_is_metric_in_every_direction(self, azimuth):
        # lat/lng arithmetic would treat N-S and E-W differently; projected distance does not
        found = facilities_within([AKIBA], [at(495, azimuth, "in"), at(505, azimuth, "out")], 500)[
            "akihabara"
        ]
        assert [f["id"] for f in found] == ["in"]
        assert found[0]["distanceM"] == pytest.approx(495, abs=1.0)

    def test_sorted_by_distance_and_unlocated_ignored(self):
        unlocated = {**at(10, fid="u"), "lat": None, "lng": None}
        found = facilities_within([AKIBA], [at(300, fid="b"), at(100, fid="a"), unlocated], 500)[
            "akihabara"
        ]
        assert [f["id"] for f in found] == ["a", "b"]

    def test_station_without_facilities(self):
        assert facilities_within([AKIBA], [], 500) == {"akihabara": []}


def test_sample_points_are_on_the_circles():
    pts = sample_points(AKIBA["lat"], AKIBA["lng"], 500)
    assert len(pts) == 25
    dists = sorted(round(GEOD.inv(AKIBA["lng"], AKIBA["lat"], lng, lat)[2]) for lat, lng in pts)
    assert dists == [0] + [250] * 8 + [500] * 16


def test_reverse_geocoder_parses_and_handles_water(tmp_path):
    answers = iter([b'{"results":{"muniCd":"13106","lv01Nm":"x"}}', b"{}"])
    rg = GsiReverseGeocoder(HttpClient(lambda url: next(answers), sleep=lambda s: None))
    assert rg.municipality(35.69, 139.78) == Municipality("13106", "台東区")
    assert rg.municipality(35.60, 139.95) is None


def test_municipalities_within_dedupes():
    class Fake:
        def municipality(self, lat, lng):
            return (
                Municipality("13101", "千代田区")
                if lng < 139.7731
                else Municipality("13106", "台東区")
            )

    found = municipalities_within(Fake(), AKIBA["lat"], AKIBA["lng"], 500)
    assert [m.name for m in found] == ["千代田区", "台東区"]


def report(*datasets):
    return {"datasets": list(datasets)}


def ds(org, status="ok", unlocated=0, dataset_id=None, rows=100):
    return {
        "datasetId": dataset_id or f"{org}-{status}",
        "organization": org,
        "status": status,
        "rows": rows,
        "unlocated": unlocated,
    }


class TestCoverage:
    def test_states(self):
        cov = municipality_coverage(
            report(
                ds("千代田区"),
                ds("台東区", unlocated=2),
                ds("港区", status="out-of-scope"),
                ds("新宿区", status="failed"),
                ds("東京都建設局"),
            )
        )
        assert {k: v["coverage"] for k, v in cov.items()} == {
            "千代田区": "covered",
            "台東区": "partial",
        }  # others: uncovered

    def test_one_good_dataset_is_enough_unless_another_has_unlocated(self):
        cov = municipality_coverage(
            report(ds("文京区"), ds("文京区", status="failed", dataset_id="x"))
        )
        assert cov["文京区"]["coverage"] == "covered"

    def test_tolerance(self):
        rep = report(ds("台東区", unlocated=7, rows=190))  # 3.7%
        assert municipality_coverage(rep)["台東区"]["coverage"] == "partial"
        tolerated = municipality_coverage(rep, unlocated_tolerance=0.05)["台東区"]
        assert tolerated == {"coverage": "covered", "rows": 190, "unlocated": 7}
        rep = report(ds("墨田区", unlocated=17, rows=171))  # 9.9%
        assert municipality_coverage(rep, 0.05)["墨田区"]["coverage"] == "partial"

    def test_station_status(self):
        assert station_status(["covered", "covered"]) == "complete"
        assert station_status(["covered", "uncovered"]) == "incomplete"


class TestAggregateFeature:
    def run(self, municipalities, rep, facilities):
        return aggregate_feature(
            "park",
            [AKIBA],
            facilities,
            rep,
            lambda lat, lng, r: municipalities,
            500,
            "2026-09-28T00:00:00Z",
        )["stations"][0]

    def test_complete_count(self):
        s = self.run(
            [Municipality("13101", "千代田区"), Municipality("13106", "台東区")],
            report(ds("千代田区", dataset_id="c"), ds("台東区", dataset_id="t")),
            [at(100, fid="a", datasetId="c"), at(900, fid="far", datasetId="c")],
        )
        assert s["status"] == "complete"
        assert s["count"] == 1
        assert [f["name"] for f in s["facilities"]] == ["a"]
        # 台東区 found nothing here but its completeness backs the count -> it is a source
        assert s["datasets"] == ["c", "t"]

    def test_zero_is_a_real_zero_only_when_covered(self):
        s = self.run([Municipality("13101", "千代田区")], report(ds("千代田区")), [])
        assert (s["status"], s["count"]) == ("complete", 0)

    def test_uncovered_municipality_makes_count_missing(self):
        s = self.run(
            [Municipality("13101", "千代田区"), Municipality("13103", "港区")],
            report(ds("千代田区")),
            [at(100, fid="a")],
        )
        assert s["status"] == "incomplete"
        assert s["count"] is None  # never 0 / never the partial number
        assert s["lowerBound"] == 1
        assert {m["name"]: m["coverage"] for m in s["municipalities"]} == {
            "千代田区": "covered",
            "港区": "uncovered",
        }

    def test_no_municipality_found_is_incomplete(self):
        s = self.run([], report(ds("千代田区")), [at(100)])
        assert s["status"] == "incomplete"


def test_output_is_json_serializable():
    s = aggregate_feature(
        "park",
        [AKIBA],
        [at(100)],
        report(ds("千代田区")),
        lambda *a: [Municipality("13101", "千代田区")],
        500,
        "t",
    )
    json.dumps(s, ensure_ascii=False)
