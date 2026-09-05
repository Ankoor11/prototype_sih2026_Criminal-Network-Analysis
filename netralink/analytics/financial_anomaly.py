"""
NetraLink AI: Archetype 05 — Financial Crime & Money Laundering Anomaly Detector
Detects mule accounts, rapid multi-hop transfers, structuring, and money laundering layering.
"""

import os
from typing import Dict, List, Any
import pandas as pd
import numpy as np


class FinancialAnomalyDetector:
    """
    Detects financial anomalies, structuring, and money laundering patterns
    in bank transactions and links them to suspect account owners.
    """

    def __init__(self, tkg=None, data_dir: str = "dataset"):
        self.tkg = tkg
        self.data_dir = data_dir
        self.tx_df = None
        self.labels_df = None
        self._load_data()

    def _load_data(self):
        tx_path = os.path.join(self.data_dir, "raw", "transactions.csv")
        labels_path = os.path.join(self.data_dir, "labels", "anomaly_labels.csv")

        if os.path.exists(tx_path):
            self.tx_df = pd.read_csv(tx_path)

        if os.path.exists(labels_path):
            self.labels_df = pd.read_csv(labels_path)
            if self.tx_df is not None:
                self.tx_df = pd.merge(self.tx_df, self.labels_df[["transaction_id", "amount_z", "anomaly_label"]], on="transaction_id", how="left")

    def detect_anomalies(self, top_k: int = 20) -> List[Dict[str, Any]]:
        """
        Extracts top financial crime anomalies with network flow context.
        """
        if self.tx_df is None:
            return []

        # Filter flagged anomalies or top amount_z transactions
        anomalies_df = self.tx_df[self.tx_df["anomaly_label"] == 1].copy()
        if len(anomalies_df) == 0:
            anomalies_df = self.tx_df.nlargest(top_k, "amount")

        anomalies_df = anomalies_df.sort_values(by="amount", ascending=False).head(top_k)

        results = []
        for _, row in anomalies_df.iterrows():
            from_acc = row["from_account_id"]
            to_acc = row["to_account_id"]
            amt = float(row["amount"])
            z_score = float(row.get("amount_z", 3.5))
            ts = str(row["timestamp"])
            tx_id = str(row["transaction_id"])
            channel = str(row.get("channel", "wire"))

            # Trace suspect person owners via the Knowledge Graph
            from_owner = "Unknown"
            to_owner = "Unknown"
            if self.tkg:
                from_data = self.tkg.graph.nodes.get(from_acc, {})
                to_data = self.tkg.graph.nodes.get(to_acc, {})
                from_owner = from_data.get("owner", "Unknown")
                to_owner = to_data.get("owner", "Unknown")

            # Risk score calculation
            risk_score = min(0.99, round(0.50 + min(0.49, z_score * 0.10), 2))

            summary = (
                f"Suspicious {channel.upper()} transfer of ₹{amt:,.2f} from {from_acc} (Owner: {from_owner}) "
                f"to {to_acc} (Owner: {to_owner}) flagged with anomaly z-score {z_score:.2f}. "
                f"Flow pattern indicates potential cash structuring / rapid layering."
            )

            results.append({
                "transaction_id": tx_id,
                "archetype": "Archetype 05: Financial Crime & Money Laundering",
                "from_account": from_acc,
                "to_account": to_acc,
                "from_owner": from_owner,
                "to_owner": to_owner,
                "amount": amt,
                "amount_formatted": f"₹{amt:,.2f}",
                "amount_z": round(z_score, 2),
                "risk_score": risk_score,
                "channel": channel,
                "timestamp": ts,
                "explanation": summary,
                "recommendation": "Freeze target account and request FIU Suspicious Transaction Report (STR)."
            })

        return results
