"""Command line entry point: `station-pipeline <command>`."""

import argparse
import json
import logging
from datetime import UTC, datetime
from pathlib import Path

from .aggregate.run import aggregate_feature
from .build import build_from_fixture
from .discover.catalog import DEFAULT_CATALOG, CkanCatalog
from .discover.definitions import load_definitions
from .discover.manifest import (
    apply_overrides,
    load_overrides,
    merge_manifest,
    read_manifest,
    write_manifest,
)
from .discover.run import discover_feature
from .export import export_web, write_dataset
from .geo.geocode import GsiGeocoder
from .geo.municipalities import GsiReverseGeocoder, municipalities_within
from .http import HttpClient, JsonClient
from .ingest import ingest_feature, write_json
from .settings import load_settings

REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURE = REPO_ROOT / "data" / "fixtures" / "stations.raw.json"
MASTER = REPO_ROOT / "data" / "processed" / "stations.master.json"
STATIONS_CONFIG = REPO_ROOT / "pipeline" / "config" / "stations.yaml"
STATIONS_RAW = REPO_ROOT / "data" / "raw" / "stations"
PROCESSED = REPO_ROOT / "data" / "processed" / "stations.json"
WEB_DATA = REPO_ROOT / "apps" / "web" / "src" / "data" / "stations.json"
WEB_PROVENANCE = REPO_ROOT / "apps" / "web" / "src" / "data" / "provenance.json"
DEFINITIONS = REPO_ROOT / "pipeline" / "config" / "feature_definitions.yaml"
SETTINGS = REPO_ROOT / "pipeline" / "config" / "pipeline.yaml"
MANIFEST = REPO_ROOT / "data" / "manifests" / "datasets.json"
OVERRIDES = REPO_ROOT / "data" / "manifests" / "overrides.json"
CATALOG_CACHE = REPO_ROOT / "data" / "interim" / "catalog-cache"
GEOCODE_CACHE = REPO_ROOT / "data" / "interim" / "geocode-cache"
RAW_DIR = REPO_ROOT / "data" / "raw"
INTERIM = REPO_ROOT / "data" / "interim"
AGGREGATES = REPO_ROOT / "data" / "processed" / "aggregates"
REVERSE_CACHE = REPO_ROOT / "data" / "interim" / "reverse-geocode-cache"


def station_base() -> Path:
    """The station master when built (make data), else the 5-station fixture."""
    return MASTER if MASTER.exists() else FIXTURE


def _now_iso(now: datetime) -> str:
    return now.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def cmd_discover(features: list[str] | None, refresh: bool) -> None:
    definitions = load_definitions(DEFINITIONS)
    targets = features or [k for k, d in definitions.items() if d.enabled]
    unknown = [f for f in targets if f not in definitions]
    if unknown:
        raise SystemExit(f"unknown feature(s): {unknown}. defined: {sorted(definitions)}")

    client = JsonClient(cache_dir=CATALOG_CACHE, refresh=refresh)
    catalog = CkanCatalog(client, DEFAULT_CATALOG)
    overrides = load_overrides(OVERRIDES)
    now = datetime.now(UTC)
    manifest = read_manifest(MANIFEST)

    for key in targets:
        d = definitions[key]
        print(f"[discover] {key}: keywords={list(d.keywords)}")
        entries = apply_overrides(discover_feature(catalog, d, now), overrides)
        meta = {"label": d.label, "keywords": list(d.keywords)}
        manifest = merge_manifest(manifest, key, meta, entries, _now_iso(now), DEFAULT_CATALOG)
        stats = manifest["features"][key]
        print(
            f"[discover] {key}: {stats['candidates']} candidates -> "
            f"accepted {stats['accepted']} / review {stats['review']} / "
            f"rejected {stats['rejected']}"
        )

    assert manifest is not None
    write_manifest(manifest, MANIFEST)
    print(
        f"wrote {MANIFEST.relative_to(REPO_ROOT)} "
        f"(network calls: {client.network_calls}, cache: {CATALOG_CACHE.relative_to(REPO_ROOT)})"
    )


def resolve_scope(settings) -> frozenset[str]:
    if settings.geocode_scope is not None:
        return settings.geocode_scope | settings.geocode_extra
    from .stations.master import geocode_scope

    master = json.loads(station_base().read_text(encoding="utf-8"))
    if "areaMunicipalities" not in master["stations"][0]:
        raise SystemExit("geocode.scope is auto but the station master is missing: run `stations`")
    return geocode_scope(master, sorted(settings.geocode_extra))


def cmd_stations(refresh: bool) -> None:
    import yaml

    from . import ridership as rs
    from .config import DEFAULT_RADIUS_METERS
    from .stations.master import build_master, load_n02

    config = yaml.safe_load(STATIONS_CONFIG.read_text(encoding="utf-8"))
    src = config["source"]
    client = HttpClient(cache_dir=CATALOG_CACHE, refresh=refresh)
    zip_path = STATIONS_RAW / Path(src["url"]).name
    if refresh or not zip_path.exists():
        zip_path.parent.mkdir(parents=True, exist_ok=True)
        zip_path.write_bytes(client.get_bytes(src["url"]))
    features = load_n02(zip_path, src["member"])
    _, _, parsed = rs.load_tables(CkanCatalog(client, DEFAULT_CATALOG))
    reverse = GsiReverseGeocoder(HttpClient(cache_dir=REVERSE_CACHE, refresh=refresh))
    master = build_master(
        config["stations"],
        config["operator"],
        features,
        rs.english_names(parsed),
        reverse.municipality,
        lambda lat, lng, r: municipalities_within(reverse, lat, lng, r),
        DEFAULT_RADIUS_METERS,
        src,
    )
    write_json(master, MASTER)
    scope = sorted({m for s in master["stations"] for m in s["areaMunicipalities"]})
    print(f"[stations] {len(master['stations'])} stations from N02; area: {', '.join(scope)}")
    print(f"wrote {MASTER.relative_to(REPO_ROOT)}")


def feature_filters(d) -> dict:
    if d is None:
        return {}
    return {
        "exclude_names": d.exclude_facility_names,
        "exclude_markers": d.exclude_name_markers,
        "exclude_categories": d.exclude_categories,
        "same_place_m": d.same_place_m,
        "include_names": d.include_name_keywords,
        "feature_keywords": d.keywords,
    }


def cmd_ingest(features: list[str] | None, refresh: bool) -> None:
    manifest = read_manifest(MANIFEST)
    if manifest is None:
        raise SystemExit(f"{MANIFEST.relative_to(REPO_ROOT)} not found. Run `make discover` first.")
    settings = load_settings(SETTINGS)
    definitions = load_definitions(DEFINITIONS)
    # Facility features only (stationUsage comes from a station table, see `ridership`).
    targets = features or sorted(k for k in manifest["features"] if k in definitions)
    client = HttpClient(cache_dir=CATALOG_CACHE, refresh=refresh)
    geocoder = GsiGeocoder(HttpClient(cache_dir=GEOCODE_CACHE, refresh=refresh))
    now = datetime.now(UTC)
    for key in targets:
        facilities, report = ingest_feature(
            manifest,
            key,
            client,
            geocoder,
            RAW_DIR,
            now,
            geocode_scope=resolve_scope(settings),
            dedupe_max_distance_m=settings.dedupe_max_distance_m,
            **feature_filters(definitions.get(key)),
        )
        write_json(facilities, INTERIM / key / "facilities.json")
        write_json(report, INTERIM / key / "report.json")
        t = report["totals"]
        print(
            f"[ingest] {key}: {t['datasets']} datasets (failed {t['failed']}, "
            f"degraded {t['degraded']}, out-of-scope {t['outOfScope']}) -> {t['rows']} rows, "
            f"{t['mergedDuplicates']} duplicates merged -> {t['facilities']} facilities, "
            f"located {t['located']}, unlocated {t['unlocated']} {t['unlocatedByReason']} "
            f"(geocoder calls: {geocoder.calls})"
        )
        print(f"wrote {(INTERIM / key).relative_to(REPO_ROOT)}/facilities.json, report.json")


def cmd_aggregate(features: list[str] | None, refresh: bool) -> None:
    from .config import DEFAULT_RADIUS_METERS

    stations = json.loads(station_base().read_text(encoding="utf-8"))["stations"]
    targets = features or sorted(p.name for p in INTERIM.iterdir() if (p / "report.json").exists())
    reverse = GsiReverseGeocoder(HttpClient(cache_dir=REVERSE_CACHE, refresh=refresh))

    def municipalities_of(lat: float, lng: float, radius: float):
        return municipalities_within(reverse, lat, lng, radius)

    for key in targets:
        facilities = json.loads((INTERIM / key / "facilities.json").read_text(encoding="utf-8"))
        report = json.loads((INTERIM / key / "report.json").read_text(encoding="utf-8"))
        result = aggregate_feature(
            key,
            stations,
            facilities,
            report,
            municipalities_of,
            DEFAULT_RADIUS_METERS,
            _now_iso(datetime.now(UTC)),
            unlocated_tolerance=load_settings(SETTINGS).unlocated_tolerance,
        )
        write_json(result, AGGREGATES / f"{key}.json")
        for s in result["stations"]:
            munis = ", ".join(f"{m['name']}:{m['coverage']}" for m in s["municipalities"])
            print(f"[aggregate] {key} {s['stationId']}: {s['status']} count={s['count']} ({munis})")
        print(f"wrote {(AGGREGATES / f'{key}.json').relative_to(REPO_ROOT)}")


def cmd_ridership(refresh: bool) -> None:
    from . import ridership as rs

    stations = json.loads(station_base().read_text(encoding="utf-8"))["stations"]
    client = HttpClient(cache_dir=CATALOG_CACHE, refresh=refresh)
    catalog = CkanCatalog(client, DEFAULT_CATALOG)
    package, tables, parsed = rs.load_tables(catalog)
    now = _now_iso(datetime.now(UTC))
    result = rs.aggregate_ridership(stations, parsed, package["name"], now)
    write_json(result, AGGREGATES / "stationUsage.json")

    entry = rs.manifest_entry(catalog, package, tables)
    meta = {"label": "駅利用", "keywords": [rs.YEARBOOK_QUERY]}
    manifest = merge_manifest(
        read_manifest(MANIFEST), "stationUsage", meta, [entry], now, DEFAULT_CATALOG
    )
    write_manifest(manifest, MANIFEST)
    print(f"[ridership] {package['title']} FY{result['fiscalYear']} ({len(tables)} tables)")
    for s in result["stations"]:
        lines = ", ".join(f"{x['operator']} {x['line']}" for x in s["lines"])
        print(f"[ridership] {s['stationId']}: {s['count']} /day ({lines})")


def load_aggregates() -> dict[str, dict]:
    if not AGGREGATES.exists():
        return {}
    return {
        p.stem: json.loads(p.read_text(encoding="utf-8")) for p in sorted(AGGREGATES.glob("*.json"))
    }


def main(argv: list[str] | None = None) -> None:
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(prog="station-pipeline")
    sub = parser.add_subparsers(dest="command", required=True)
    b = sub.add_parser("build-fixture", help="fixture raw values -> processed stations.json")
    b.add_argument("--generated-at", help="override timestamp (for reproducible output)")
    sub.add_parser("export-web", help="copy processed stations.json into apps/web")
    st = sub.add_parser("stations", help="build the station master (N02 + yearbook)")
    st.add_argument("--refresh", action="store_true", help="re-download / ignore caches")
    rid = sub.add_parser("ridership", help="stationUsage from the statistical yearbook")
    rid.add_argument("--refresh", action="store_true", help="ignore the HTTP cache")
    agg = sub.add_parser("aggregate", help="count facilities within the station radius")
    agg.add_argument("--feature", action="append", help="feature key (repeatable)")
    agg.add_argument("--refresh", action="store_true", help="ignore the reverse geocode cache")
    d = sub.add_parser("discover", help="search the open data catalog and write the manifest")
    d.add_argument("--feature", action="append", help="feature key (repeatable). default: enabled")
    d.add_argument("--refresh", action="store_true", help="ignore the HTTP cache")
    ing = sub.add_parser("ingest", help="fetch accepted datasets, normalize and geocode")
    ing.add_argument("--feature", action="append", help="feature key (repeatable)")
    ing.add_argument("--refresh", action="store_true", help="ignore HTTP / geocode caches")
    args = parser.parse_args(argv)

    if args.command == "build-fixture":
        data = build_from_fixture(
            station_base(),
            generated_at=args.generated_at,
            aggregates=load_aggregates(),
            manifest=read_manifest(MANIFEST),
        )
        write_dataset(data, PROCESSED)
        print(
            f"wrote {PROCESSED.relative_to(REPO_ROOT)} ({len(data['stations'])} stations; "
            f"real: {[f for f in data['stations'][0]['evidence']]}, "
            f"fixture: {data['fixtureFeatures']})"
        )
    elif args.command == "export-web":
        export_web(PROCESSED, WEB_DATA)
        print(f"copied -> {WEB_DATA.relative_to(REPO_ROOT)}")
        from .provenance import build_provenance

        manifest = read_manifest(MANIFEST) or {"datasets": [], "features": {}}
        reports = {
            p.parent.name: json.loads(p.read_text(encoding="utf-8"))
            for p in sorted(INTERIM.glob("*/report.json"))
        }
        write_json(build_provenance(manifest, reports, _now_iso(datetime.now(UTC))), WEB_PROVENANCE)
        print(f"wrote {WEB_PROVENANCE.relative_to(REPO_ROOT)}")
    elif args.command == "discover":
        cmd_discover(args.feature, args.refresh)
    elif args.command == "ingest":
        cmd_ingest(args.feature, args.refresh)
    elif args.command == "aggregate":
        cmd_aggregate(args.feature, args.refresh)
    elif args.command == "ridership":
        cmd_ridership(args.refresh)
    elif args.command == "stations":
        cmd_stations(args.refresh)


if __name__ == "__main__":
    main()
