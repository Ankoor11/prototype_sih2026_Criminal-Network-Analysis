"""
NetraLink AI: Interactive Event Extraction Demo CLI
For testing real-time event extraction on investigator inputs, FIR narratives, or digital intercepts.
"""

import os
import sys
import json

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from netralink.nlp.event_extractor import EventExtractor


def run_demo():
    extractor = EventExtractor()

    test_cases = [
        {
            "title": "Case 1: Multilingual FIR Narrative (English with Crime Assets)",
            "lang": "en",
            "text": (
                "On 2026-07-25, the record noted that PERSON_00561 was observed with PERSON_00975 "
                "near Zone_0123 in Ujjain. The note references phone PH01018, account ACC00481, "
                "and vehicle VEH00359. Available records indicate suspicious activity in time window."
            ),
        },
        {
            "title": "Case 2: Hindi Police Intercept (Secret Meeting)",
            "lang": "hi",
            "text": "PERSON_00151 और PERSON_00985 ने मिला, Zone_0178, Gwalior के पास। समय 2026-04-05 11:39:00.",
        },
        {
            "title": "Case 3: Tamil Intercept (Coordinated Hawala / Money Transfer)",
            "lang": "ta",
            "text": "PERSON_00788 और PERSON_00510 ने பணம் அனுப்பினார், Zone_0110, Indore के पास। समय 2026-03-04 14:53:00.",
        },
        {
            "title": "Case 4: Urdu Cyber Extortion / Communication Record",
            "lang": "ur",
            "text": "PERSON_00811 और PERSON_00637 ने رابطہ کیا, Zone_0051, Bhopal کے پاس। समय 2026-08-30 11:56:00.",
        }
    ]

    print("=" * 70)
    print("      NETRALINK AI — REAL-TIME EVENT EXTRACTION ENGINE DEMO")
    print("=" * 70)

    for case in test_cases:
        print(f"\n▶ {case['title']}")
        print(f"  Input Text: {case['text']}")
        print(f"  Detected Language: {case['lang']}")

        event = extractor.extract_event(
            record_id="DEMO_REC",
            text=case["text"],
            language=case["lang"]
        )

        edges = extractor.to_graph_edges(event)

        print("\n  [1] Extracted Canonical Event:")
        print(f"      • Event ID:        {event['event_id']}")
        print(f"      • Event Type:      {event['event_type']} (Trigger: '{event['trigger_word']}')")
        print(f"      • Initiator / Subj:{event['subject_person_id']}")
        print(f"      • Recipient / Obj: {event['object_person_id']}")
        print(f"      • Location ID:     {event['location_id']}")
        print(f"      • Timestamp:       {event['timestamp']}")
        print(f"      • AI Confidence:   {event['confidence'] * 100}%")

        if any(event["assets"].values()):
            print(f"      • Linked Assets:   {event['assets']}")

        print("\n  [2] Generated Temporal Graph Edges:")
        for edge in edges:
            print(f"      ({edge['head']}) ──[{edge['relation']}]──► ({edge['tail']}) | Conf: {edge['confidence']}")

        print("-" * 70)


if __name__ == "__main__":
    run_demo()
