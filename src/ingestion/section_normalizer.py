"""
Section Normalizer - Converts between IPC/BNS, CrPC/BNSS, IEA/BSA.
Handles all common formats: "sec. 302", "Section 302", "s.302", "IPC 302", "u/s 302"
"""

import json
import re
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class SectionNormalizer:
    """Normalize and convert section references between old and new criminal codes."""

    def __init__(self, configs_dir: str = "configs"):
        self.configs_dir = Path(configs_dir)
        self.ipc_to_bns = {}
        self.bns_to_ipc = {}
        self.crpc_to_bnss = {}
        self.bnss_to_crpc = {}
        self.iea_to_bsa = {}
        self.bsa_to_iea = {}
        self._load_mappings()

    def _load_mappings(self):
        """Load mapping files from configs directory."""
        mapping_files = {
            "ipc_to_bns_mapping.json": ("ipc_to_bns", "bns_to_ipc"),
            "crpc_to_bnss_mapping.json": ("crpc_to_bnss", "bnss_to_crpc"),
            "iea_to_bsa_mapping.json": ("iea_to_bsa", "bsa_to_iea"),
        }

        for filename, (forward_attr, reverse_attr) in mapping_files.items():
            filepath = self.configs_dir / filename
            if filepath.exists():
                with open(filepath, 'r') as f:
                    forward = json.load(f)
                    setattr(self, forward_attr, forward)
                    reverse = {v: k for k, v in forward.items() if v and v != "None"}
                    setattr(self, reverse_attr, reverse)
                logger.info(f"Loaded {len(forward)} mappings from {filename}")
            else:
                logger.warning(f"Mapping file not found: {filepath}")
                # Use hardcoded fallback for critical mappings
                if "ipc_to_bns" in forward_attr:
                    self._load_hardcoded_ipc_bns()

    def _load_hardcoded_ipc_bns(self):
        """Hardcoded fallback for most common IPC→BNS mappings."""
        self.ipc_to_bns = {
            "302": "103", "304": "105", "304A": "106", "304B": "80",
            "306": "108", "307": "109", "323": "115(2)", "324": "118(1)",
            "325": "117(2)", "326": "118(2)", "326A": "124", "354": "74",
            "354A": "75", "363": "137(2)", "364A": "140(2)", "375": "63",
            "376": "64", "376D": "70", "378": "303", "379": "303(2)",
            "380": "305(a)", "392": "309(2)", "395": "310(2)", "396": "310(3)",
            "403": "316", "406": "316(2)", "409": "316(5)", "415": "318",
            "420": "318(4)", "441": "329", "447": "329(2)", "448": "330(2)",
            "463": "336", "465": "336(2)", "468": "340", "498A": "85",
            "499": "356", "503": "351", "506": "351(2)(3)", "107": "45",
            "109": "48", "114": "52", "120B": "61(2)", "141": "189",
            "147": "190(2)", "148": "190(3)", "149": "191", "153A": "196",
            "299": "100", "300": "101", "309": "None", "511": "62",
        }
        self.bns_to_ipc = {v: k for k, v in self.ipc_to_bns.items() if v != "None"}

    SECTION_PATTERNS = [
        # "Section 302 of IPC" / "Section 302 IPC"
        r'[Ss]ection\s+(\d+[A-Z]?)\s+(?:of\s+)?(?:the\s+)?(IPC|I\.?P\.?C\.?|BNS|B\.?N\.?S\.?|CrPC|Cr\.?P\.?C\.?|BNSS|B\.?N\.?S\.?S\.?|IEA|BSA|NDPS|POCSO)',
        # "IPC Section 302" / "IPC s. 302"
        r'(IPC|I\.?P\.?C\.?|BNS|B\.?N\.?S\.?|CrPC|Cr\.?P\.?C\.?|BNSS|NDPS|POCSO)\s*[Ss](?:ection|ec\.?)\s*(\d+[A-Z]?)',
        # "s. 302 IPC" / "s.302 IPC"
        r'[Ss]\.?\s*(\d+[A-Z]?)\s+(IPC|BNS|CrPC|BNSS|NDPS|POCSO)',
        # "u/s 302 IPC"
        r'[Uu]/[Ss]\s*(\d+[A-Z]?)\s+(IPC|BNS|CrPC|BNSS)',
        # "302 IPC"
        r'(\d+[A-Z]?)\s+(IPC|I\.?P\.?C\.?|BNS)',
    ]

    def parse_section_reference(self, text: str) -> list[dict]:
        """Parse section references from text, return structured output."""
        results = []
        seen = set()

        for pattern in self.SECTION_PATTERNS:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                groups = match.groups()
                # Determine which group is section and which is code
                if groups[0].isdigit() or (groups[0] and groups[0][0].isdigit()):
                    section = groups[0]
                    code = groups[1] if len(groups) > 1 else "IPC"
                else:
                    code = groups[0]
                    section = groups[1] if len(groups) > 1 else ""

                code = self._normalize_code_name(code)
                key = f"{code}:{section}"
                if key in seen or not section:
                    continue
                seen.add(key)

                equivalent = self.convert(section, code)
                results.append({
                    "section": section,
                    "code": code,
                    "full_reference": match.group(0).strip(),
                    "equivalent": equivalent,
                })

        return results

    def _normalize_code_name(self, code: str) -> str:
        """Normalize code name variations."""
        code_upper = re.sub(r'\.', '', code).upper().strip()
        mapping = {
            "IPC": "IPC", "INDPENALCODE": "IPC",
            "BNS": "BNS", "BHARATIYANYAYASANHITA": "BNS",
            "CRPC": "CrPC", "CODEOFCRIMINALPROCEDURE": "CrPC",
            "BNSS": "BNSS",
            "IEA": "IEA", "INDIANEVIDENCEACT": "IEA",
            "BSA": "BSA",
            "NDPS": "NDPS", "POCSO": "POCSO",
        }
        return mapping.get(code_upper, code_upper)

    def convert(self, section: str, from_code: str) -> Optional[dict]:
        """Convert a section to its equivalent in the other code system."""
        from_code = self._normalize_code_name(from_code)

        conversions = {
            "IPC": ("BNS", self.ipc_to_bns),
            "BNS": ("IPC", self.bns_to_ipc),
            "CrPC": ("BNSS", self.crpc_to_bnss),
            "BNSS": ("CrPC", self.bnss_to_crpc),
            "IEA": ("BSA", self.iea_to_bsa),
            "BSA": ("IEA", self.bsa_to_iea),
        }

        if from_code not in conversions:
            return None

        to_code, mapping = conversions[from_code]
        equivalent_section = mapping.get(section)

        if equivalent_section and equivalent_section != "None":
            return {"code": to_code, "section": equivalent_section}
        elif equivalent_section == "None":
            return {"code": to_code, "section": None, "note": "Decriminalized/Removed"}
        return None

    def normalize_all_sections(self, text: str) -> list[dict]:
        """Find and normalize all section references in text, providing both old and new codes."""
        refs = self.parse_section_reference(text)
        normalized = []
        for ref in refs:
            entry = {
                "original": ref["full_reference"],
                ref["code"]: ref["section"],
            }
            if ref["equivalent"]:
                entry[ref["equivalent"]["code"]] = ref["equivalent"]["section"]
                if ref["equivalent"].get("note"):
                    entry["note"] = ref["equivalent"]["note"]
            normalized.append(entry)
        return normalized
