"""
NetraLink AI: Geospatial & Movement Intelligence Router
"""

from fastapi import APIRouter
from backend.app.services.graph_service import GraphService

router = APIRouter(prefix="/api/investigations/{investigation_id}/map", tags=["Geospatial"])


@router.get("")
def get_map_intelligence(investigation_id: str):
    service = GraphService.get_instance()

    # Pre-configured geo-spatial nodes
    locations = [
        {"id": "LOC0123", "name": "Zone_0123 Safehouse", "city": "Ujjain", "lat": 23.1765, "lng": 75.7885, "type": "Safehouse / Narcotics Exchange", "events_count": 8},
        {"id": "LOC0140", "name": "Zone_0140 Warehouse", "city": "Jabalpur", "lat": 23.1815, "lng": 79.9864, "type": "Commercial Fencing Hub", "events_count": 12},
        {"id": "LOC0178", "name": "Zone_0178 Transit Point", "city": "Gwalior", "lat": 26.2183, "lng": 78.1828, "type": "Transit Meeting Site", "events_count": 6},
        {"id": "LOC0110", "name": "Zone_0110 Hawala Counter", "city": "Indore", "lat": 22.7196, "lng": 75.8577, "type": "Financial Structuring Hub", "events_count": 15},
        {"id": "LOC0051", "name": "Zone_0051 Cyber Relay", "city": "Bhopal", "lat": 23.2599, "lng": 77.4126, "type": "Digital Extortion Relay", "events_count": 9}
    ]

    # Trajectories over time
    trajectories = [
        {
            "person_id": "P00561",
            "label": "Rahul Sharma @ Guddu",
            "path": [
                {"location_id": "LOC0123", "city": "Ujjain", "timestamp": "2026-01-15 10:20:00", "lat": 23.1765, "lng": 75.7885},
                {"location_id": "LOC0110", "city": "Indore", "timestamp": "2026-03-04 14:53:00", "lat": 22.7196, "lng": 75.8577},
                {"location_id": "LOC0140", "city": "Jabalpur", "timestamp": "2026-06-29 08:35:00", "lat": 23.1815, "lng": 79.9864},
                {"location_id": "LOC0123", "city": "Ujjain", "timestamp": "2026-07-25 05:52:00", "lat": 23.1765, "lng": 75.7885}
            ]
        }
    ]

    return {
        "locations": locations,
        "trajectories": trajectories
    }
