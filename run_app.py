"""
NetraLink AI: Master Application Launcher
Launches the full-stack system locally:
- Initializes SQLite database and seeds demonstration case 'Operation Eclipse'
- Pre-warms the 56,750-edge Temporal Knowledge Graph
- Starts the FastAPI REST backend on http://127.0.0.1:8000
- Opens the interactive Investigative Web Dashboard in your browser
100% self-contained and offline-ready with zero external API dependencies.
"""

import os
import sys
import time
import webbrowser
import threading
import uvicorn

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))


def open_browser():
    """Opens the web browser automatically after server initializes."""
    time.sleep(2.0)
    url = "http://127.0.0.1:8000"
    print(f"\n[NetraLink AI] Opening dashboard in browser: {url}")
    webbrowser.open(url)


def main():
    print("=" * 75)
    print("        NETRALINK AI: UNIFIED CRIME INTELLIGENCE PLATFORM")
    print("      From Fragmented Crime Records to Connected Intelligence")
    print("=" * 75)
    print("\n[System] Starting self-contained law enforcement server...")
    print("  • Backend: FastAPI (Python)")
    print("  • Database: SQLite Relational Store")
    print("  • Graph Engine: Unified Temporal Heterogeneous MultiDiGraph (56,750 edges)")
    print("  • ML / Analytics: 7 Crime Lenses + Cross-Crime Bridge Radar (Archetype 07)")
    print("  • Frontend: Multi-View Law Enforcement Dashboard (Cytoscape Canvas)")
    print("  • Server Address: http://127.0.0.1:8000\n")

    # Start browser opener in background thread
    threading.Thread(target=open_browser, daemon=True).start()

    # Start Uvicorn Server on port 8000
    uvicorn.run(
        "backend.app.main:app",
        host="127.0.0.1",
        port=8000,
        log_level="info"
    )


if __name__ == "__main__":
    main()
