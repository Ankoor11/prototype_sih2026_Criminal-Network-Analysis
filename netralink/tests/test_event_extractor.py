"""
Unit tests for NetraLink AI Multilingual Event Extractor.
"""

import unittest
from netralink.nlp.event_extractor import EventExtractor


class TestEventExtractor(unittest.TestCase):
    def setUp(self):
        self.extractor = EventExtractor()

    def test_english_communication(self):
        text = "PERSON_00577 called PERSON_00940 near Zone_0093, Jabalpur. Record time 2026-05-13 11:54:00."
        event = self.extractor.extract_event("DIG000001", text, language="en")
        self.assertEqual(event["event_type"], "communication")
        self.assertEqual(event["subject_person_id"], "P00577")
        self.assertEqual(event["object_person_id"], "P00940")
        self.assertEqual(event["location_id"], "LOC0093")
        self.assertEqual(event["timestamp"], "2026-05-13 11:54:00")
        self.assertGreaterEqual(event["confidence"], 0.90)

    def test_hindi_meeting(self):
        text = "PERSON_00151 और PERSON_00985 ने मिला, Zone_0178, Gwalior के पास। समय 2026-04-05 11:39:00."
        event = self.extractor.extract_event("DIG000002", text, language="hi")
        self.assertEqual(event["event_type"], "meeting")
        self.assertEqual(event["subject_person_id"], "P00151")
        self.assertEqual(event["object_person_id"], "P00985")
        self.assertEqual(event["location_id"], "LOC0178")
        self.assertEqual(event["timestamp"], "2026-04-05 11:39:00")

    def test_tamil_transfer(self):
        text = "PERSON_00788 और PERSON_00510 ने பணம் அனுப்பினார், Zone_0110, Indore के पास। समय 2026-03-04 14:53:00."
        event = self.extractor.extract_event("DIG000003", text, language="ta")
        self.assertEqual(event["event_type"], "transfer")
        self.assertEqual(event["subject_person_id"], "P00788")
        self.assertEqual(event["object_person_id"], "P00510")

    def test_fir_narrative_with_assets(self):
        text = (
            "On 2026-07-25, the record noted that PERSON_00561 was observed with PERSON_00975 "
            "near Zone_0123 in Ujjain. The note references phone PH01018, account ACC00481, "
            "and vehicle VEH00359. Available records indicate activity within the surrounding time window."
        )
        event = self.extractor.extract_event("RPT00001", text, language="en")
        self.assertEqual(event["event_type"], "observation")
        self.assertEqual(event["subject_person_id"], "P00561")
        self.assertEqual(event["object_person_id"], "P00975")
        self.assertEqual(event["location_id"], "LOC0123")
        self.assertIn("PH01018", event["assets"]["phones"])
        self.assertIn("ACC00481", event["assets"]["accounts"])
        self.assertIn("VEH00359", event["assets"]["vehicles"])

        # Graph edge conversion test
        edges = self.extractor.to_graph_edges(event)
        relations = [e["relation"] for e in edges]
        self.assertIn("MENTIONED_WITH", relations)
        self.assertIn("PRESENT_AT", relations)
        self.assertIn("USES_PHONE", relations)
        self.assertIn("OWNS_ACCOUNT", relations)
        self.assertIn("OWNS_VEHICLE", relations)


if __name__ == "__main__":
    unittest.main()
