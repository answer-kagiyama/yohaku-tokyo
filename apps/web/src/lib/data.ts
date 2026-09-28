import provenanceRaw from "@/data/provenance.json";
import raw from "@/data/stations.json";
import { type Provenance, parseProvenance } from "@/domain/provenance";
import { parseStationsDataset, type Station, type StationsDataset } from "@/domain/schema";

// Parsed once at module load: an invalid stations.json fails `next build` (ADR 0002).
const dataset: StationsDataset = parseStationsDataset(raw);

export function getDataset(): StationsDataset {
  return dataset;
}

export function getAllStations(): Station[] {
  return dataset.stations;
}

export function getStationById(id: string): Station | undefined {
  return dataset.stations.find((s) => s.id === id);
}

/** Observation number: stable position in the dataset (1-based). */
export function getStationIndex(id: string): number {
  return dataset.stations.findIndex((s) => s.id === id);
}

const provenance: Provenance = parseProvenance(provenanceRaw);

export function getProvenance(): Provenance {
  return provenance;
}
