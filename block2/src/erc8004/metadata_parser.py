"""
Metadata Resolution and Service Extraction for ERC-8004 Agents
"""

import base64
import json
import os
import pandas as pd
from typing import Dict, Any, Optional, List, Tuple


class MetadataResolver:
    def __init__(self, dataverse_dir: str = "data/raw/dataverse"):
        self.dataverse_dir = dataverse_dir
        self.dv_metadata: Dict[int, Dict[str, Any]] = {}
        self.dv_services: Dict[int, List[Dict[str, Any]]] = {}
        self.dv_snapshot: Dict[int, Dict[str, Any]] = {}
        self._load_dataverse()

    def _load_dataverse(self):
        """Loads baseline metadata from Harvard Dataverse if present."""
        meta_tab = os.path.join(self.dataverse_dir, "agent_metadata.tab")
        if os.path.exists(meta_tab):
            try:
                df = pd.read_csv(meta_tab, sep="\t")
                for _, row in df.iterrows():
                    aid = int(row["agent_id"])
                    self.dv_metadata[aid] = {
                        "name": str(row.get("name", "")) if pd.notna(row.get("name")) else None,
                        "description": str(row.get("description", "")) if pd.notna(row.get("description")) else None,
                        "x402_support": bool(row.get("x402_support", False)) if pd.notna(row.get("x402_support")) else False,
                        "service_count": int(row.get("service_count", 0)) if pd.notna(row.get("service_count")) else 0,
                        "active": bool(row.get("active", True)) if pd.notna(row.get("active")) else True,
                    }
            except Exception as e:
                print(f"Warning loading agent_metadata.tab: {e}")

        serv_tab = os.path.join(self.dataverse_dir, "agent_services.tab")
        if os.path.exists(serv_tab):
            try:
                df_s = pd.read_csv(serv_tab, sep="\t")
                for _, row in df_s.iterrows():
                    aid = int(row["agent_id"])
                    if aid not in self.dv_services:
                        self.dv_services[aid] = []
                    sname = str(row.get("service_name", "")) if pd.notna(row.get("service_name")) else ""
                    self.dv_services[aid].append({
                        "service_name": sname,
                        "endpoint": str(row.get("endpoint", "")) if pd.notna(row.get("endpoint")) else None,
                        "version": str(row.get("version", "")) if pd.notna(row.get("version")) else None
                    })
            except Exception as e:
                print(f"Warning loading agent_services.tab: {e}")

        snap_jsonl = os.path.join(self.dataverse_dir, "metadata_raw_snapshot.jsonl")
        if os.path.exists(snap_jsonl):
            try:
                with open(snap_jsonl, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        obj = json.loads(line)
                        aid = obj.get("agent_id")
                        if aid is not None:
                            self.dv_snapshot[int(aid)] = obj
            except Exception as e:
                print(f"Warning loading metadata_raw_snapshot.jsonl: {e}")

    def parse_uri(self, uri: str) -> Optional[Dict[str, Any]]:
        """Parses inline data URIs or returns None if external/unsupported."""
        if not uri or not isinstance(uri, str):
            return None
        uri_clean = uri.strip()
        if uri_clean.startswith("data:application/json;base64,"):
            b64_data = uri_clean[len("data:application/json;base64,"):]
            try:
                decoded = base64.b64decode(b64_data).decode("utf-8", errors="ignore")
                return json.loads(decoded)
            except Exception:
                return None
        elif uri_clean.startswith("data:application/json,") or uri_clean.startswith("data:text/json,"):
            raw_data = uri_clean.split(",", 1)[1]
            try:
                return json.loads(raw_data)
            except Exception:
                return None
        return None

    def resolve_agent_metadata(self, chain_id: int, agent_id: int, latest_uri: Optional[str]) -> Dict[str, Any]:
        """
        Resolves metadata, declared services, and declared operating wallet.
        """
        result = {
            "name": None,
            "description": None,
            "x402_support": False,
            "declared_services": [],
            "service_count": 0,
            "active": None,
            "declared_wallet": None
        }

        # Check inline URI first
        parsed = self.parse_uri(latest_uri) if latest_uri else None
        if parsed and isinstance(parsed, dict):
            result["name"] = parsed.get("name")
            result["description"] = parsed.get("description")
            result["x402_support"] = bool(parsed.get("x402Support") or parsed.get("x402_support") or False)
            result["active"] = bool(parsed.get("active", True))

            # Services extraction
            services_raw = parsed.get("services")
            if isinstance(services_raw, list):
                service_names = []
                for s in services_raw:
                    if isinstance(s, dict) and "name" in s:
                        service_names.append(s["name"])
                    elif isinstance(s, str):
                        service_names.append(s)
                result["declared_services"] = service_names
                result["service_count"] = len(service_names)

            # Check if operating wallet declared in metadata JSON
            declared_w = parsed.get("agentWallet") or parsed.get("agent_wallet") or parsed.get("operating_wallet") or parsed.get("wallet")
            if declared_w and isinstance(declared_w, str) and declared_w.startswith("0x") and len(declared_w) == 42:
                result["declared_wallet"] = declared_w

            return result

        # For Ethereum (Chain 1), fall back to Dataverse tables
        if chain_id == 1:
            if agent_id in self.dv_metadata:
                m = self.dv_metadata[agent_id]
                result["name"] = m["name"]
                result["description"] = m["description"]
                result["x402_support"] = m["x402_support"]
                result["active"] = m["active"]
            if agent_id in self.dv_services:
                services = [s["service_name"] for s in self.dv_services[agent_id] if s.get("service_name")]
                result["declared_services"] = services
                result["service_count"] = len(services)

            if agent_id in self.dv_snapshot:
                snap = self.dv_snapshot[agent_id]
                snap_body = snap.get("metadata") or snap
                if isinstance(snap_body, dict):
                    declared_w = snap_body.get("agentWallet") or snap_body.get("agent_wallet") or snap_body.get("operating_wallet")
                    if declared_w and isinstance(declared_w, str) and declared_w.startswith("0x") and len(declared_w) == 42:
                        result["declared_wallet"] = declared_w

        return result
