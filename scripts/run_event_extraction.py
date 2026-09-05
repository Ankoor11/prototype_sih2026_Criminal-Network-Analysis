"""
NetraLink AI: Batch Event Extraction Runner
Processes all raw digital records (6,000) and FIR narratives (1,200),
extracts structured events, and converts them to temporal graph edges.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pandas as pd
from netralink.nlp.event_extractor import EventExtractor


def main():
    extractor = EventExtractor()
    os.makedirs("data/processed", exist_ok=True)

    # 1. Process Digital Records (6000 multilingual records)
    print("Loading digital_records.csv...")
    dig_df = pd.read_csv("dataset/raw/digital_records.csv")
    print(f"Loaded {len(dig_df)} digital records across {dig_df['language'].nunique()} languages.")

    dig_records = dig_df.to_dict(orient="records")
    dig_events, dig_edges = extractor.process_batch(dig_records)
    print(f"Extracted {len(dig_events)} events and {len(dig_edges)} graph edges from digital records.")

    # 2. Process FIR Narrative Reports (1200 records in English & Hindi)
    print("\nLoading reports.csv (FIR narratives)...")
    rep_df = pd.read_csv("dataset/raw/reports.csv")
    print(f"Loaded {len(rep_df)} police FIR reports.")

    rep_records = rep_df.to_dict(orient="records")
    rep_events, rep_edges = extractor.process_batch(rep_records)
    print(f"Extracted {len(rep_events)} events and {len(rep_edges)} graph edges from FIR reports.")

    # 3. Combine & Save
    all_events = dig_events + rep_events
    all_edges = dig_edges + rep_edges

    events_df = pd.DataFrame(all_events)
    # Simplify assets dictionary for clean CSV export
    events_df["phones"] = events_df["assets"].apply(lambda a: ";".join(a.get("phones", [])))
    events_df["accounts"] = events_df["assets"].apply(lambda a: ";".join(a.get("accounts", [])))
    events_df["vehicles"] = events_df["assets"].apply(lambda a: ";".join(a.get("vehicles", [])))
    events_df = events_df.drop(columns=["assets"])

    edges_df = pd.DataFrame(all_edges)

    events_output_path = "data/processed/extracted_events.csv"
    edges_output_path = "data/processed/extracted_graph_edges.csv"

    events_df.to_csv(events_output_path, index=False)
    edges_df.to_csv(edges_output_path, index=False)

    print("\n=== Event Extraction Summary ===")
    print(f"Total Records Processed: {len(all_events)}")
    print(f"Total Graph Edges Generated: {len(all_edges)}")
    print(f"Event Distribution:\n{events_df['event_type'].value_counts()}")
    print(f"\nSaved events to: {events_output_path}")
    print(f"Saved graph edges to: {edges_output_path}")


if __name__ == "__main__":
    main()
