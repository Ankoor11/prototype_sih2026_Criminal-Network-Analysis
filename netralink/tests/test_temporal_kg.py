"""
Unit tests for NetraLink AI Temporal Knowledge Graph.
"""

import unittest
from netralink.graph.temporal_kg import TemporalKnowledgeGraph


class TestTemporalKnowledgeGraph(unittest.TestCase):
    def setUp(self):
        self.tkg = TemporalKnowledgeGraph()
        # Add sample nodes
        self.tkg.graph.add_node("P00001", entity_type="Person", label="Suspect 1")
        self.tkg.graph.add_node("P00002", entity_type="Person", label="Associate 1")
        self.tkg.graph.add_node("PH00001", entity_type="Phone", label="Phone 1")
        self.tkg.graph.add_node("LOC0001", entity_type="Location", label="Safehouse 1")

        # Add sample edges
        self.tkg.graph.add_edge("P00001", "PH00001", relation="USES_PHONE", timestamp=None)
        self.tkg.graph.add_edge("P00001", "P00002", relation="COMMUNICATED_WITH", timestamp="2026-05-01 10:00:00")
        self.tkg.graph.add_edge("P00001", "LOC0001", relation="PRESENT_AT", timestamp="2026-05-01 12:00:00")

    def test_graph_statistics(self):
        stats = self.tkg.get_statistics()
        self.assertEqual(stats["total_nodes"], 4)
        self.assertEqual(stats["total_edges"], 3)
        self.assertEqual(stats["nodes_by_type"]["Person"], 2)
        self.assertEqual(stats["edges_by_relation"]["COMMUNICATED_WITH"], 1)

    def test_egocentric_subgraph(self):
        sub = self.tkg.get_subgraph("P00001", hops=1)
        self.assertEqual(sub.number_of_nodes(), 4)
        self.assertEqual(sub.number_of_edges(), 3)

    def test_temporal_filtering(self):
        # Filter for only 2026-05-01 11:00:00 and later
        sub = self.tkg.get_subgraph("P00001", hops=1, start_time="2026-05-01 11:00:00")
        # Edge COMMUNICATED_WITH is at 10:00:00 so should be excluded
        relations = [data["relation"] for _, _, data in sub.edges(data=True)]
        self.assertIn("PRESENT_AT", relations)
        self.assertNotIn("COMMUNICATED_WITH", relations)

    def test_cytoscape_export(self):
        cyto = self.tkg.to_cytoscape_json()
        self.assertEqual(len(cyto["nodes"]), 4)
        self.assertEqual(len(cyto["edges"]), 3)
        node_colors = [n["data"]["color"] for n in cyto["nodes"]]
        # Person should be blue (#3B82F6), Phone should be green (#10B981)
        self.assertIn("#3B82F6", node_colors)
        self.assertIn("#10B981", node_colors)


if __name__ == "__main__":
    unittest.main()
