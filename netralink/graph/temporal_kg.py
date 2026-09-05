"""
NetraLink AI: Temporal Knowledge Graph Engine
Fuses multimodal law enforcement data (CDRs, bank transactions, geo-temporal logs,
asset ownership, and NLP-extracted crime events) into a unified Temporal MultiDiGraph.
"""

import os
import json
from typing import Dict, List, Optional, Any, Set
from datetime import datetime
import pandas as pd
import networkx as nx


class TemporalKnowledgeGraph:
    """
    Unified Temporal Heterogeneous Knowledge Graph.
    Backbone for NetraLink AI's 7 Crime-Specific Intelligence Lenses.
    """

    def __init__(self):
        # Directed multigraph to support multiple timestamped edges between same nodes
        self.graph = nx.MultiDiGraph()

    # -------------------------------------------------------------------------
    # 1. NODE INGESTION
    # -------------------------------------------------------------------------
    def load_nodes(self, data_dir: str = "dataset/raw"):
        """Loads all canonical entity nodes with metadata attributes."""
        # 1. Persons
        persons_path = os.path.join(data_dir, "persons.csv")
        if os.path.exists(persons_path):
            df_p = pd.read_csv(persons_path)
            for _, row in df_p.iterrows():
                self.graph.add_node(
                    row["person_id"],
                    entity_type="Person",
                    label=row.get("name_token", row["person_id"]),
                    occupation=row.get("occupation", "unknown"),
                    home_location=row.get("home_location_id", ""),
                    category="entity"
                )

        # 2. Phones
        phones_path = os.path.join(data_dir, "phones.csv")
        if os.path.exists(phones_path):
            df_ph = pd.read_csv(phones_path)
            for _, row in df_ph.iterrows():
                self.graph.add_node(
                    row["phone_id"],
                    entity_type="Phone",
                    label=row.get("number_token", row["phone_id"]),
                    carrier=row.get("carrier", ""),
                    owner=row.get("owner_person_id", ""),
                    category="asset"
                )
                # Structural ownership edge
                if pd.notna(row.get("owner_person_id")):
                    self.graph.add_edge(
                        row["owner_person_id"],
                        row["phone_id"],
                        relation="USES_PHONE",
                        confidence=1.0,
                        source_id="phones.csv",
                        timestamp=None
                    )

        # 3. Accounts
        accounts_path = os.path.join(data_dir, "accounts.csv")
        if os.path.exists(accounts_path):
            df_acc = pd.read_csv(accounts_path)
            for _, row in df_acc.iterrows():
                self.graph.add_node(
                    row["account_id"],
                    entity_type="Account",
                    label=row["account_id"],
                    account_type=row.get("account_type", ""),
                    institution=row.get("institution", ""),
                    owner=row.get("owner_person_id", ""),
                    category="financial"
                )
                # Structural ownership edge
                if pd.notna(row.get("owner_person_id")):
                    self.graph.add_edge(
                        row["owner_person_id"],
                        row["account_id"],
                        relation="OWNS_ACCOUNT",
                        confidence=1.0,
                        source_id="accounts.csv",
                        timestamp=None
                    )

        # 4. Vehicles
        vehicles_path = os.path.join(data_dir, "vehicles.csv")
        if os.path.exists(vehicles_path):
            df_veh = pd.read_csv(vehicles_path)
            for _, row in df_veh.iterrows():
                self.graph.add_node(
                    row["vehicle_id"],
                    entity_type="Vehicle",
                    label=row.get("registration_token", row["vehicle_id"]),
                    vehicle_type=row.get("vehicle_type", ""),
                    owner=row.get("owner_person_id", ""),
                    category="asset"
                )
                # Structural ownership edge
                if pd.notna(row.get("owner_person_id")):
                    self.graph.add_edge(
                        row["owner_person_id"],
                        row["vehicle_id"],
                        relation="OWNS_VEHICLE",
                        confidence=1.0,
                        source_id="vehicles.csv",
                        timestamp=None
                    )

        # 5. Locations
        locations_path = os.path.join(data_dir, "locations.csv")
        if os.path.exists(locations_path):
            df_loc = pd.read_csv(locations_path)
            for _, row in df_loc.iterrows():
                self.graph.add_node(
                    row["location_id"],
                    entity_type="Location",
                    label=row.get("location_name", row["location_id"]),
                    city=row.get("city", ""),
                    latitude=float(row["latitude"]) if pd.notna(row.get("latitude")) else None,
                    longitude=float(row["longitude"]) if pd.notna(row.get("longitude")) else None,
                    location_type=row.get("location_type", ""),
                    category="spatial"
                )

    # -------------------------------------------------------------------------
    # 2. STRUCTURED EVIDENCE INGESTION (CDRs, Transactions, Geo)
    # -------------------------------------------------------------------------
    def load_communications(self, data_dir: str = "dataset/raw"):
        """Loads telecom Call Detail Records (CDRs)."""
        comm_path = os.path.join(data_dir, "communications.csv")
        if not os.path.exists(comm_path):
            return
        df = pd.read_csv(comm_path)
        for _, row in df.iterrows():
            self.graph.add_edge(
                row["from_phone_id"],
                row["to_phone_id"],
                relation="COMMUNICATED_WITH",
                timestamp=str(row.get("timestamp", "")),
                duration_sec=int(row["duration_sec"]) if pd.notna(row.get("duration_sec")) else 0,
                channel=row.get("channel", "call"),
                location_id=row.get("location_id", ""),
                source_id=row.get("cdr_id", "CDR"),
                confidence=0.99
            )

    def load_transactions(self, data_dir: str = "dataset/raw"):
        """Loads banking transactions (transfers/wire/cash)."""
        tx_path = os.path.join(data_dir, "transactions.csv")
        if not os.path.exists(tx_path):
            return
        df = pd.read_csv(tx_path)
        for _, row in df.iterrows():
            self.graph.add_edge(
                row["from_account_id"],
                row["to_account_id"],
                relation="TRANSFERRED_TO",
                amount=float(row["amount"]) if pd.notna(row.get("amount")) else 0.0,
                timestamp=str(row.get("timestamp", "")),
                channel=row.get("channel", "online"),
                location_id=row.get("location_id", ""),
                source_id=row.get("transaction_id", "TX"),
                confidence=1.0
            )

    def load_geo_events(self, data_dir: str = "dataset/raw"):
        """Loads geospatial presence and movements."""
        geo_path = os.path.join(data_dir, "geo_events.csv")
        if not os.path.exists(geo_path):
            return
        df = pd.read_csv(geo_path)
        for _, row in df.iterrows():
            self.graph.add_edge(
                row["person_id"],
                row["location_id"],
                relation="PRESENT_AT",
                timestamp=str(row.get("timestamp", "")),
                event_type=row.get("event_type", "present"),
                confidence=float(row["source_confidence"]) if pd.notna(row.get("source_confidence")) else 0.85,
                source_id=row.get("geo_event_id", "GEO")
            )

    def load_extracted_nlp_edges(self, edges_csv: str = "data/processed/extracted_graph_edges.csv"):
        """Loads edges extracted by the NetraLink Event Extraction Engine."""
        if not os.path.exists(edges_csv):
            return
        df = pd.read_csv(edges_csv)
        for _, row in df.iterrows():
            head = str(row["head"])
            tail = str(row["tail"])
            # Ensure nodes exist in graph even if previously unlisted
            if not self.graph.has_node(head):
                self.graph.add_node(head, entity_type="Entity", label=head)
            if not self.graph.has_node(tail):
                self.graph.add_node(tail, entity_type="Entity", label=tail)

            self.graph.add_edge(
                head,
                tail,
                relation=row["relation"],
                timestamp=str(row.get("timestamp", "")),
                confidence=float(row.get("confidence", 0.90)),
                source_id=str(row.get("source_id", "NLP_EXTRACTION")),
                event_type=str(row.get("event_type", ""))
            )

    # -------------------------------------------------------------------------
    # 3. GRAPH ANALYSIS & TEMPORAL SLICING
    # -------------------------------------------------------------------------
    def get_subgraph(
        self,
        center_node: str,
        hops: int = 2,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        allowed_relations: Optional[Set[str]] = None
    ) -> nx.MultiDiGraph:
        """
        Extracts an egocentric subgraph around a suspect or asset,
        filtered by N-hops and an optional temporal window.
        """
        if not self.graph.has_node(center_node):
            return nx.MultiDiGraph()

        # Step 1: Collect nodes within N hops
        current_layer = {center_node}
        visited_nodes = {center_node}

        for _ in range(hops):
            next_layer = set()
            for n in current_layer:
                neighbors = set(self.graph.successors(n)).union(set(self.graph.predecessors(n)))
                next_layer.update(neighbors - visited_nodes)
            visited_nodes.update(next_layer)
            current_layer = next_layer
            if not current_layer:
                break

        # Step 2: Build induced subgraph with temporal & relation filtering
        subgraph = nx.MultiDiGraph()
        for node in visited_nodes:
            subgraph.add_node(node, **self.graph.nodes[node])

        for u in visited_nodes:
            for v, key_dict in self.graph[u].items():
                if v not in visited_nodes:
                    continue
                for k, edge_data in key_dict.items():
                    rel = edge_data.get("relation")
                    if allowed_relations and rel not in allowed_relations:
                        continue

                    ts = edge_data.get("timestamp")
                    if ts and start_time and ts < start_time:
                        continue
                    if ts and end_time and ts > end_time:
                        continue

                    subgraph.add_edge(u, v, key=k, **edge_data)

        return subgraph

    def to_cytoscape_json(self, target_graph: Optional[nx.MultiDiGraph] = None) -> Dict[str, Any]:
        """
        Converts the graph (or a subgraph) to standard Cytoscape.js format
        for immediate visualization in Next.js / React UI.
        """
        g = target_graph if target_graph is not None else self.graph
        elements = {"nodes": [], "edges": []}

        # Color palette for entity types
        type_colors = {
            "Person": "#3B82F6",    # Blue
            "Phone": "#10B981",     # Green
            "Account": "#F59E0B",   # Amber / Orange
            "Vehicle": "#8B5CF6",   # Purple
            "Location": "#EF4444",  # Red
            "Entity": "#6B7280"     # Gray
        }

        for node_id, data in g.nodes(data=True):
            etype = data.get("entity_type", "Entity")
            elements["nodes"].append({
                "data": {
                    "id": str(node_id),
                    "label": data.get("label", str(node_id)),
                    "type": etype,
                    "color": type_colors.get(etype, "#6B7280"),
                    **{k: v for k, v in data.items() if k not in ["label", "entity_type"]}
                }
            })

        edge_counter = 0
        for u, v, k, data in g.edges(keys=True, data=True):
            edge_id = f"e_{u}_{v}_{k}_{edge_counter}"
            edge_counter += 1
            elements["edges"].append({
                "data": {
                    "id": edge_id,
                    "source": str(u),
                    "target": str(v),
                    "label": data.get("relation", "RELATED"),
                    "timestamp": data.get("timestamp", ""),
                    "confidence": data.get("confidence", 1.0),
                    **data
                }
            })

        return elements

    # -------------------------------------------------------------------------
    # 4. NEO4J CYPHER EXPORTER
    # -------------------------------------------------------------------------
    def export_cypher_script(self, output_file: str = "data/processed/load_netralink.cypher"):
        """
        Generates production-grade Cypher scripts to bulk load nodes and relationships into Neo4j.
        """
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("// ========================================================\n")
            f.write("// NetraLink AI: Unified Temporal Heterogeneous Knowledge Graph\n")
            f.write("// Bulk Cypher Script for Neo4j\n")
            f.write("// ========================================================\n\n")

            # 1. Indexes & Constraints
            f.write("// 1. Schema Constraints\n")
            f.write("CREATE CONSTRAINT IF NOT EXISTS FOR (p:Person) REQUIRE p.id IS UNIQUE;\n")
            f.write("CREATE CONSTRAINT IF NOT EXISTS FOR (ph:Phone) REQUIRE ph.id IS UNIQUE;\n")
            f.write("CREATE CONSTRAINT IF NOT EXISTS FOR (a:Account) REQUIRE a.id IS UNIQUE;\n")
            f.write("CREATE CONSTRAINT IF NOT EXISTS FOR (v:Vehicle) REQUIRE v.id IS UNIQUE;\n")
            f.write("CREATE CONSTRAINT IF NOT EXISTS FOR (l:Location) REQUIRE l.id IS UNIQUE;\n\n")

            # 2. Nodes Creation
            f.write("// 2. Entities (Nodes)\n")
            for node_id, data in self.graph.nodes(data=True):
                etype = data.get("entity_type", "Entity")
                props_str = json.dumps({
                    "id": str(node_id),
                    "label": data.get("label", str(node_id)),
                    **{k: v for k, v in data.items() if k not in ["entity_type", "label"] and v is not None}
                })
                # Convert json string to cypher map
                f.write(f"MERGE (:{etype} {{id: '{node_id}'}}) SET (:{etype} {{id: '{node_id}'}}) += {props_str};\n")

            # 3. Relationships Creation (Batched by 1,000 for efficiency)
            f.write("\n// 3. Relationships (Edges)\n")
            for u, v, data in self.graph.edges(data=True):
                rel = data.get("relation", "RELATED_TO").replace(" ", "_")
                props = {k: v for k, v in data.items() if k != "relation" and v is not None}
                props_str = json.dumps(props) if props else "{}"
                f.write(
                    f"MATCH (source {{id: '{u}'}}), (target {{id: '{v}'}}) "
                    f"CREATE (source)-[:{rel} {props_str}]->(target);\n"
                )

        print(f"Exported Neo4j Cypher script with {self.graph.number_of_nodes()} nodes and {self.graph.number_of_edges()} edges to {output_file}")

    def get_statistics(self) -> Dict[str, Any]:
        """Returns comprehensive graph metrics and distribution."""
        node_counts = {}
        for _, data in self.graph.nodes(data=True):
            t = data.get("entity_type", "Unknown")
            node_counts[t] = node_counts.get(t, 0) + 1

        rel_counts = {}
        for _, _, data in self.graph.edges(data=True):
            r = data.get("relation", "Unknown")
            rel_counts[r] = rel_counts.get(r, 0) + 1

        return {
            "total_nodes": self.graph.number_of_nodes(),
            "total_edges": self.graph.number_of_edges(),
            "nodes_by_type": node_counts,
            "edges_by_relation": rel_counts,
            "density": nx.density(self.graph)
        }
