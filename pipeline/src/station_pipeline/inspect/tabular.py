"""Decode and parse tabular resources (CSV). Municipal CSVs are UTF-8 (often with BOM) or CP932."""

import csv
import io
import json

ENCODINGS = ("utf-8-sig", "cp932")


class TabularError(ValueError):
    pass


def decode_text(body: bytes) -> tuple[str, str]:
    # Observed: 新宿区 publishes UTF-16 (LE, with BOM) CSVs.
    if body.startswith((b"\xff\xfe", b"\xfe\xff")):
        return body.decode("utf-16"), "utf-16"
    for enc in ENCODINGS:
        try:
            return body.decode(enc), enc
        except UnicodeDecodeError:
            continue
    raise TabularError(f"cannot decode as any of {ENCODINGS}")


def parse_csv(body: bytes) -> tuple[list[str], list[dict[str, str]], str]:
    """Returns (fields, records, encoding). Blank rows are dropped."""
    text, encoding = decode_text(body)
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        raise TabularError("CSV has no header")
    fields = [f.strip() for f in reader.fieldnames]
    records = []
    for row in reader:
        values = {k.strip(): (v or "").strip() for k, v in row.items() if k is not None}
        if any(values.values()):
            records.append(values)
    return fields, records, encoding


GEOJSON_LAT = "緯度"
GEOJSON_LNG = "経度"


def parse_geojson(body: bytes) -> tuple[list[str], list[dict[str, str]], str]:
    """FeatureCollection -> rows of properties. Point geometry becomes 緯度/経度 columns
    (a geometry is never overridden by a same-named property). Other geometries are ignored."""
    text, encoding = decode_text(body)
    try:
        doc = json.loads(text)
    except ValueError as exc:
        raise TabularError(f"invalid JSON: {exc}") from exc
    features = doc.get("features") if isinstance(doc, dict) else None
    if not isinstance(features, list):
        raise TabularError("not a GeoJSON FeatureCollection")
    fields: list[str] = []
    records = []
    for f in features:
        props = {
            str(k).strip(): "" if v is None else str(v).strip()
            for k, v in (f.get("properties") or {}).items()
        }
        geom = f.get("geometry") or {}
        if geom.get("type") == "Point" and len(geom.get("coordinates") or []) >= 2:
            lng, lat = geom["coordinates"][:2]
            props[GEOJSON_LAT], props[GEOJSON_LNG] = str(lat), str(lng)
        for k in props:
            if k not in fields:
                fields.append(k)
        if any(props.values()):
            records.append(props)
    return fields, records, encoding


def parse_table(body: bytes, fmt: str | None) -> tuple[list[str], list[dict[str, str]], str]:
    fmt = (fmt or "").strip().lower()
    if fmt == "csv":
        return parse_csv(body)
    if fmt in ("geojson", "json"):
        return parse_geojson(body)
    raise TabularError(f"unsupported format: {fmt}")
