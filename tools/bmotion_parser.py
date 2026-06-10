import re
import json
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional


# ----------------------------
# DATA MODELS
# ----------------------------

@dataclass
class Trigger:
    trigger_type: str          # keyword | event | unknown
    pattern: str               # match string
    responses: List[str]
    probability: float = 1.0


# ----------------------------
# MAIN PARSER
# ----------------------------

class BMotionTclParser:

    def __init__(self):
        self.triggers: List[Trigger] = []

    # -------------------------
    # ENTRY POINT
    # -------------------------

    def parse_file(self, path: str) -> List[Trigger]:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()

        self._parse_binds(text)
        self._parse_response_blocks(text)

        return self.triggers

    # -------------------------
    # 1. PARSE BIND TRIGGERS
    # -------------------------

    def _parse_binds(self, text: str):
        """
        Extract:
        bind pubm - "*" trigger_name
        """
        pattern = re.compile(
            r"bind\s+(pubm|msg|join|part|quit)\s+\S+\s+\"?(.*?)\"?$",
            re.MULTILINE
        )

        for match in pattern.finditer(text):
            event_type = match.group(1)
            handler = match.group(2)

            self.triggers.append(
                Trigger(
                    trigger_type="event" if event_type != "pubm" else "keyword",
                    pattern=handler.strip(),
                    responses=[]
                )
            )

    # -------------------------
    # 2. PARSE RESPONSE LISTS
    # -------------------------

    def _parse_response_blocks(self, text: str):
        """
        Extract Tcl-style response arrays:
        set responses { "a" "b" "c" }
        """

        pattern = re.compile(
            r"set\s+(\w+)\s+\{([^}]*)\}",
            re.MULTILINE | re.DOTALL
        )

        matches = pattern.findall(text)

        for name, block in matches:
            responses = self._extract_strings(block)

            if not responses:
                continue

            # attach to last trigger (simple heuristic)
            if self.triggers:
                self.triggers[-1].responses.extend(responses)

    # -------------------------
    # STRING EXTRACTION
    # -------------------------

    def _extract_strings(self, block: str) -> List[str]:
        return re.findall(r"\"(.*?)\"", block)

    # -------------------------
    # EXPORT
    # -------------------------

    def to_json(self) -> str:
        return json.dumps([asdict(t) for t in self.triggers], indent=2)


# ----------------------------
# CLI USAGE
# ----------------------------

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python bmotion_parser.py file.tcl")
        exit(1)

    parser = BMotionTclParser()
    triggers = parser.parse_file(sys.argv[1])

    print(json.dumps([asdict(t) for t in triggers], indent=2))