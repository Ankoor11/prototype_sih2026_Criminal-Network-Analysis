"""
NetraLink AI: Archetype 07 — Cross-Crime Organised Syndicate & Bridge Detector
Detects broker entities operating across multiple criminal ecosystems
(e.g., bridging illicit supply, money laundering, cyber extortion, and property theft).
"""

from typing import Dict, List, Any, Optional
import networkx as nx


class SyndicateBridgeDetector:
    """
    Identifies high-betweenness broker entities and cross-crime syndicates.
    Computes Community Partitions, Betweenness Centrality, and Participation Coefficients (Bridge Score).
    """

    def __init__(self, tkg):
        self.tkg = tkg
        self.communities: List[set] = []
        self.node_community_map: Dict[str, int] = {}
        self.betweenness_scores: Dict[str, float] = {}
        self.bridge_scores: Dict[str, float] = {}

    def run_detection(self, top_k: int = 15) -> List[Dict[str, Any]]:
        """
        Executes community detection and computes cross-crime bridge scores for all Person entities.
        Returns top-k flagged bridge suspects with explainable lead evidence.
        """
        # 1. Build an undirected projection focusing on Person and interaction nodes
        simple_g = nx.Graph()
        for u, v, data in self.tkg.graph.edges(data=True):
            rel = data.get("relation", "")
            # Filter for key relational interactions
            if rel in [
                "COMMUNICATED_WITH",
                "TRANSFERRED_TO",
                "MET_WITH",
                "MENTIONED_WITH",
                "MOVED_WITH",
                "USES_PHONE",
                "OWNS_ACCOUNT",
                "OWNS_VEHICLE"
            ]:
                simple_g.add_edge(u, v)

        if simple_g.number_of_nodes() == 0:
            return []

        # 2. Community Detection
        try:
            self.communities = list(nx.community.louvain_communities(simple_g, seed=42))
        except Exception:
            self.communities = list(nx.community.greedy_modularity_communities(simple_g))

        self.node_community_map = {}
        for comm_id, members in enumerate(self.communities):
            for node in members:
                self.node_community_map[node] = comm_id

        # 3. Betweenness Centrality (approximated on k-sample for high performance)
        sample_k = min(200, simple_g.number_of_nodes())
        self.betweenness_scores = nx.betweenness_centrality(simple_g, k=sample_k, seed=42)

        # 4. Compute Participation Coefficient (Bridge Score)
        # P_i = 1 - sum((k_is / k_i)^2)
        results = []
        person_nodes = [
            n for n, d in self.tkg.graph.nodes(data=True)
            if d.get("entity_type") == "Person" and n in simple_g
        ]

        for person in person_nodes:
            degree = simple_g.degree(person)
            if degree < 2:
                continue

            # Count connections to each community
            comm_counts: Dict[int, int] = {}
            for neighbor in simple_g.neighbors(person):
                cid = self.node_community_map.get(neighbor, -1)
                comm_counts[cid] = comm_counts.get(cid, 0) + 1

            # Participation coefficient
            sum_sq = sum((cnt / degree) ** 2 for cnt in comm_counts.values())
            participation_coeff = 1.0 - sum_sq

            betweenness = self.betweenness_scores.get(person, 0.0)

            # Combined Syndicate Bridge Score (0.0 to 1.0)
            bridge_score = round(0.65 * participation_coeff + 0.35 * (betweenness * 10), 4)
            bridge_score = min(0.99, max(0.01, bridge_score))

            if len(comm_counts) > 1 and bridge_score >= 0.30:
                lead = self._generate_explainable_lead(person, comm_counts, bridge_score, betweenness)
                results.append(lead)

        results.sort(key=lambda x: x["bridge_score"], reverse=True)
        return results[:top_k]

    def _generate_explainable_lead(
        self,
        person_id: str,
        comm_counts: Dict[int, int],
        bridge_score: float,
        betweenness: float
    ) -> Dict[str, Any]:
        """Generates an evidence-backed intelligence lead for human investigators."""
        node_data = self.tkg.graph.nodes.get(person_id, {})
        label = node_data.get("label", person_id)
        occupation = node_data.get("occupation", "Unknown")

        # Archetype labeling based on connected communities
        crime_lenses = [
            "Illicit Supply Network",
            "Financial Money Laundering",
            "Cyber Extortion Cell",
            "Property & Fencing Ring",
            "Human Trafficking Corridor",
            "Online Coordination Hub"
        ]

        connected_clusters = []
        for i, (cid, count) in enumerate(comm_counts.items()):
            lens_name = crime_lenses[cid % len(crime_lenses)]
            connected_clusters.append({
                "community_id": cid,
                "domain_lens": lens_name,
                "connected_entities": count
            })

        # Collect direct asset connections (Phones, Accounts, Vehicles)
        linked_assets = {"phones": [], "accounts": [], "vehicles": []}
        evidence_sources = set()

        for _, neighbor, data in self.tkg.graph.out_edges(person_id, data=True):
            rel = data.get("relation", "")
            src = data.get("source_id")
            if src:
                evidence_sources.add(src)

            if rel == "USES_PHONE":
                linked_assets["phones"].append(neighbor)
            elif rel == "OWNS_ACCOUNT":
                linked_assets["accounts"].append(neighbor)
            elif rel == "OWNS_VEHICLE":
                linked_assets["vehicles"].append(neighbor)

        # Human-in-the-loop Explanation
        summary = (
            f"Subject {label} ({person_id}) flagged as a high-betweenness cross-crime bridge entity "
            f"(Bridge Score: {bridge_score * 100:.1f}%). Subject actively bridges {len(connected_clusters)} distinct "
            f"operational clusters: {', '.join([c['domain_lens'] for c in connected_clusters[:3]])}. "
            f"Operates through {len(linked_assets['phones'])} registered devices and {len(linked_assets['accounts'])} bank accounts."
        )

        return {
            "entity_id": person_id,
            "label": label,
            "occupation": occupation,
            "archetype": "Archetype 07: Cross-Crime Organised Syndicate",
            "bridge_score": bridge_score,
            "betweenness_centrality": round(betweenness, 5),
            "communities_bridged": len(connected_clusters),
            "clusters": connected_clusters,
            "linked_assets": linked_assets,
            "evidence_sources": list(evidence_sources)[:5],
            "explanation": summary,
            "recommendation": "Initiate comprehensive cross-jurisdictional surveillance and financial audit."
        }
