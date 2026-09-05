"""
NetraLink AI: Event Extraction Engine
Transforms multilingual police FIRs, narratives, and digital intelligence records
into canonical timestamped crime events and knowledge graph edges.
"""

import re
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

from .triggers_data import MULTILINGUAL_TRIGGERS, EVENT_TYPES


class EventExtractor:
    """
    Multilingual Crime Event Extraction Engine.
    Detects event triggers, classifies event types, and binds entity arguments
    (Subject, Object, Location, Assets, Timestamp).
    """

    def __init__(self, custom_triggers: Optional[Dict] = None):
        self.triggers = custom_triggers or MULTILINGUAL_TRIGGERS
        # Precompile regex patterns for entities & timestamps
        self.person_pattern = re.compile(r'PERSON_(\d{3,5})|P(\d{5})', re.IGNORECASE)
        self.phone_pattern = re.compile(r'PH(\d{4,5})', re.IGNORECASE)
        self.account_pattern = re.compile(r'ACC(\d{4,5})', re.IGNORECASE)
        self.vehicle_pattern = re.compile(r'VEH(\d{4,5})', re.IGNORECASE)
        self.zone_pattern = re.compile(r'Zone_(\d{3,4})|LOC(\d{3,4})', re.IGNORECASE)
        self.time_pattern = re.compile(r'\b\d{4}-\d{2}-\d{2}(?:[ T]\d{2}:\d{2}:\d{2})?\b')

    def detect_event_type(self, text: str, lang: Optional[str] = None) -> Tuple[str, str, float]:
        """
        Detects event type and matched trigger from text.
        Returns: (event_type, matched_trigger, confidence)
        """
        text_lower = text.lower()

        # If language is provided, search language-specific triggers first
        candidate_matches = []
        for event_type, lang_dict in self.triggers.items():
            # Check specified language first if available
            if lang and lang in lang_dict:
                for kw in lang_dict[lang]:
                    if kw.lower() in text_lower:
                        candidate_matches.append((event_type, kw, 0.96))

            # Search all languages as fallback or for mixed texts
            for l_key, keywords in lang_dict.items():
                if l_key == lang:
                    continue
                for kw in keywords:
                    if kw.lower() in text_lower:
                        candidate_matches.append((event_type, kw, 0.92))

        if candidate_matches:
            # Sort by trigger string length (longer phrases are more specific)
            candidate_matches.sort(key=lambda x: (len(x[1]), x[2]), reverse=True)
            return candidate_matches[0]

        # Default fallback if no specific trigger phrase is detected
        if "observed with" in text_lower or "उल्लेख" in text:
            return "observation", "observed", 0.85
        return "observation", "context_cooccurrence", 0.65

    def extract_entities_from_text(self, text: str) -> Dict[str, List[str]]:
        """
        Extracts canonical entity mentions directly from text using standard police record patterns.
        """
        entities: Dict[str, List[str]] = {
            "persons": [],
            "phones": [],
            "accounts": [],
            "vehicles": [],
            "locations": []
        }

        # Persons: e.g. PERSON_00577 -> P00577
        for match in self.person_pattern.finditer(text):
            num = match.group(1) or match.group(2)
            pid = f"P{int(num):05d}"
            if pid not in entities["persons"]:
                entities["persons"].append(pid)

        # Phones: e.g. PH01018
        for match in self.phone_pattern.finditer(text):
            entities["phones"].append(f"PH{int(match.group(1)):05d}")

        # Accounts: e.g. ACC00481
        for match in self.account_pattern.finditer(text):
            entities["accounts"].append(f"ACC{int(match.group(1)):05d}")

        # Vehicles: e.g. VEH00359
        for match in self.vehicle_pattern.finditer(text):
            entities["vehicles"].append(f"VEH{int(match.group(1)):05d}")

        # Locations: e.g. Zone_0123 -> LOC0123
        for match in self.zone_pattern.finditer(text):
            loc_num = match.group(1) or match.group(2)
            entities["locations"].append(f"LOC{int(loc_num):04d}")

        return entities

    def extract_timestamp(self, text: str, fallback_time: Optional[str] = None) -> str:
        """Extracts ISO timestamp from text or uses fallback."""
        match = self.time_pattern.search(text)
        if match:
            val = match.group(0).strip()
            if len(val) == 10:  # YYYY-MM-DD
                return f"{val} 00:00:00"
            return val
        return fallback_time or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def extract_event(
        self,
        record_id: str,
        text: str,
        language: Optional[str] = None,
        resolved_entities: Optional[Dict[str, Any]] = None,
        timestamp: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extracts a single structured event from a text record.
        Integrates resolved entities from prior NER & Entity Resolution step if provided.
        """
        # 1. Event Type Detection
        event_type, trigger, confidence = self.detect_event_type(text, lang=language)

        # 2. Entity Argument Extraction
        text_entities = self.extract_entities_from_text(text)
        
        # Merge with pre-resolved entities (NER + Entity Resolution layer)
        if resolved_entities:
            persons = resolved_entities.get("persons", text_entities["persons"])
            phones = resolved_entities.get("phones", text_entities["phones"])
            accounts = resolved_entities.get("accounts", text_entities["accounts"])
            vehicles = resolved_entities.get("vehicles", text_entities["vehicles"])
            locations = resolved_entities.get("locations", text_entities["locations"])
            subject_id = resolved_entities.get("person1_id") or (persons[0] if len(persons) > 0 else None)
            object_id = resolved_entities.get("person2_id") or (persons[1] if len(persons) > 1 else None)
            loc_id = resolved_entities.get("location_id") or (locations[0] if len(locations) > 0 else None)
        else:
            persons = text_entities["persons"]
            phones = text_entities["phones"]
            accounts = text_entities["accounts"]
            vehicles = text_entities["vehicles"]
            locations = text_entities["locations"]
            subject_id = persons[0] if len(persons) > 0 else None
            object_id = persons[1] if len(persons) > 1 else None
            loc_id = locations[0] if len(locations) > 0 else None

        # 3. Timestamp Extraction
        event_time = self.extract_timestamp(text, fallback_time=timestamp)

        # Calibrate confidence based on argument completeness
        if subject_id and object_id and loc_id:
            confidence = min(0.99, confidence + 0.03)
        elif not subject_id or not object_id:
            confidence = max(0.50, confidence - 0.15)

        event_record = {
            "event_id": f"EVT_{record_id}",
            "event_type": event_type,
            "subject_person_id": subject_id,
            "object_person_id": object_id,
            "location_id": loc_id,
            "timestamp": event_time,
            "confidence": round(confidence, 2),
            "source_record_id": record_id,
            "trigger_word": trigger,
            "assets": {
                "phones": phones,
                "accounts": accounts,
                "vehicles": vehicles
            }
        }
        return event_record

    def to_graph_edges(self, event: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Converts an extracted event into typed Temporal Knowledge Graph edges.
        """
        edges = []
        subj = event["subject_person_id"]
        obj = event["object_person_id"]
        loc = event["location_id"]
        ts = event["timestamp"]
        conf = event["confidence"]
        src = event["source_record_id"]
        evt_type = event["event_type"]

        # Map event type to primary graph edge relation
        type_to_relation = {
            "communication": "COMMUNICATED_WITH",
            "meeting": "MET_WITH",
            "movement": "MOVED_WITH",
            "transfer": "TRANSFERRED_TO",
            "vehicle_use": "USED_VEHICLE_WITH",
            "item_handoff": "EXCHANGED_ITEM_WITH",
            "account_access": "ACCESSED_ACCOUNT_WITH",
            "observation": "MENTIONED_WITH",
        }
        rel = type_to_relation.get(evt_type, "ASSOCIATED_WITH")

        # 1. Subject -> Object interaction edge
        if subj and obj:
            edges.append({
                "head": subj,
                "relation": rel,
                "tail": obj,
                "timestamp": ts,
                "confidence": conf,
                "source_id": src,
                "event_type": evt_type
            })

        # 2. Location co-presence edge
        if subj and loc:
            edges.append({
                "head": subj,
                "relation": "PRESENT_AT",
                "tail": loc,
                "timestamp": ts,
                "confidence": conf,
                "source_id": src,
                "event_type": evt_type
            })
        if obj and loc:
            edges.append({
                "head": obj,
                "relation": "PRESENT_AT",
                "tail": loc,
                "timestamp": ts,
                "confidence": conf,
                "source_id": src,
                "event_type": evt_type
            })

        # 3. Asset linkage edges (from FIR reports)
        assets = event.get("assets", {})
        if subj:
            for ph in assets.get("phones", []):
                edges.append({
                    "head": subj,
                    "relation": "USES_PHONE",
                    "tail": ph,
                    "timestamp": ts,
                    "confidence": conf,
                    "source_id": src,
                    "event_type": "asset_link"
                })
            for acc in assets.get("accounts", []):
                edges.append({
                    "head": subj,
                    "relation": "OWNS_ACCOUNT",
                    "tail": acc,
                    "timestamp": ts,
                    "confidence": conf,
                    "source_id": src,
                    "event_type": "asset_link"
                })
            for veh in assets.get("vehicles", []):
                edges.append({
                    "head": subj,
                    "relation": "OWNS_VEHICLE",
                    "tail": veh,
                    "timestamp": ts,
                    "confidence": conf,
                    "source_id": src,
                    "event_type": "asset_link"
                })

        return edges

    def process_batch(self, records: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Processes a batch of records (e.g. from a DataFrame or JSON API payload).
        Returns: (extracted_events, graph_edges)
        """
        all_events = []
        all_edges = []
        for rec in records:
            rid = rec.get("record_id") or rec.get("digital_id") or rec.get("report_id") or "UNKNOWN"
            text = rec.get("text", "")
            lang = rec.get("language")
            ts = rec.get("timestamp")
            resolved = {
                "person1_id": rec.get("person1_id"),
                "person2_id": rec.get("person2_id"),
                "location_id": rec.get("location_id"),
                "phones": [rec["phone_id"]] if "phone_id" in rec and rec["phone_id"] else [],
                "accounts": [rec["account_id"]] if "account_id" in rec and rec["account_id"] else [],
                "vehicles": [rec["vehicle_id"]] if "vehicle_id" in rec and rec["vehicle_id"] else []
            }
            evt = self.extract_event(rid, text, language=lang, resolved_entities=resolved, timestamp=ts)
            all_events.append(evt)
            all_edges.extend(self.to_graph_edges(evt))
        return all_events, all_edges
