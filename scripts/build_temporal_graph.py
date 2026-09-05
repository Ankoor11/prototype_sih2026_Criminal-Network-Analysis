"""
NetraLink AI: Unified Temporal Knowledge Graph Builder
Ingests multimodal intelligence records and constructs the complete law enforcement graph.
"""

import os
import sys
import json
import pandas as pd

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from netralink.graph.temporal_kg import TemporalKnowledgeGraph


def main():
    print("=" * 70)
    print("      NETRALINK AI — TEMPORAL KNOWLEDGE GRAPH BUILDER")
    print("=" * 70)

    tkg = TemporalKnowledgeGraph()

    # 1. Ingest Canonical Nodes
    print("\n[1/5] Ingesting Canonical Entities (Persons, Phones, Accounts, Vehicles, Locations)...")
    tkg.load_nodes("dataset/raw")
    print(f"      ✓ Loaded {tkg.graph.number_of_nodes()} total nodes.")

    # 2. Ingest Telecom CDRs
    print("\n[2/5] Ingesting Telecom Call Detail Records (communications.csv)...")
    tkg.load_communications("dataset/raw")

    # 3. Ingest Bank Transactions
    print("\n[3/5] Ingesting Financial Banking Transactions (transactions.csv)...")
    tkg.load_transactions("dataset/raw")

    # 4. Ingest Geospatial Presence Logs
    print("\n[4/5] Ingesting Geospatial Presence Logs (geo_events.csv)...")
    tkg.load_geo_events("dataset/raw")

    # 5. Ingest NLP-Extracted Crime Events & Relations
    print("\n[5/5] Ingesting NLP Extracted Event Edges (extracted_graph_edges.csv)...")
    tkg.load_extracted_nlp_edges("data/processed/extracted_graph_edges.csv")

    # Output Statistics
    stats = tkg.get_statistics()
    print("\n" + "=" * 70)
    print("      UNIFIED TEMPORAL KNOWLEDGE GRAPH BUILT SUCCESSFULLY")
    print("=" * 70)
    print(f"Total Nodes: {stats['total_nodes']:,}")
    print(f"Total Edges: {stats['total_edges']:,}")
    print(f"Graph Density: {stats['density']:.6f}")

    print("\nNodes by Entity Type:")
    for ntype, count in stats["nodes_by_type"].items():
        print(f"  • {ntype:<15}: {count:>6,}")

    print("\nEdges by Crime Relation:")
    for rel, count in sorted(stats["edges_by_relation"].items(), key=lambda x: x[1], reverse=True):
        print(f"  • {rel:<22}: {count:>6,}")

    # Export Unified Edge List
    os.makedirs("data/processed", exist_ok=True)
    edge_records = []
    for u, v, data in tkg.graph.edges(data=True):
        edge_records.append({
            "head": u,
            "relation": data.get("relation"),
            "tail": v,
            "timestamp": data.get("timestamp", ""),
            "confidence": data.get("confidence", 1.0),
            "source_id": data.get("source_id", "")
        })
    df_edges = pd.DataFrame(edge_records)
    edges_path = "data/processed/unified_graph_edges.csv"
    df_edges.to_csv(edges_path, index=False)
    print(f"\nSaved unified edge list to: {edges_path}")

    # Test Egocentric Subgraph Query on Suspect P00561 (from FIR RPT00001)
    target_suspect = "P00561"
    print(f"\nExtracting 2-hop Subgraph around Suspect {target_suspect} for Cytoscape.js Visualization...")
    sub = tkg.get_subgraph(target_suspect, hops=2)
    cyto_json = tkg.to_cytoscape_json(sub)
    cyto_path = "data/processed/sample_subgraph_cytoscape.json"
    with open(cyto_path, "w", encoding="utf-8") as f:
        json.dump(cyto_json, f, indent=2)
    print(f"✓ Saved 2-hop Subgraph ({len(cyto_json['nodes'])} nodes, {len(cyto_json['edges'])} edges) to: {cyto_path}")

    # Export Neo4j Bulk Cypher Script (Top sample / schema)
    cypher_path = "data/processed/load_netralink_schema.cypher"
    with open(cypher_path, "w", encoding="utf-8") as f:
        f.write("// NetraLink AI: Neo4j Schema & Constraints\n")
        f.write("CREATE CONSTRAINT IF NOT EXISTS FOR (p:Person) REQUIRE p.id IS UNIQUE;\n")
        f.write("CREATE CONSTRAINT IF NOT EXISTS FOR (ph:Phone) REQUIRE ph.id IS UNIQUE;\n")
        f.write("CREATE CONSTRAINT IF NOT EXISTS FOR (a:Account) REQUIRE a.id IS UNIQUE;\n")
        f.write("CREATE CONSTRAINT IF NOT EXISTS FOR (v:Vehicle) REQUIRE v.id IS UNIQUE;\n")
        f.write("CREATE CONSTRAINT IF NOT EXISTS FOR (l:Location) REQUIRE l.id IS UNIQUE;\n")
    print(f"✓ Saved Neo4j Cypher constraints to: {cypher_path}")


if __name__ == "__main__":
    main()
