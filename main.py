from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import re
from datetime import datetime

REPORTS_DIR = Path(__file__).parent / "Reports"
PARSER_VERSION = "1.0"

KEY_VALUE = re.compile(r"^\s*([^:]{1,60}?)\s*:\s*(.+?)\s*$")
POSTCODE = re.compile(r"\b([A-Z]{1,2}\d[A-Z\d]?)\s*(\d[A-Z]{2})\b", re.I)


class FillStatus(str, Enum):
    FULL = "full"
    PARTIAL = "partial"
    EMPTY = "empty"
    UNKNOWN = "unknown"


class InsulationType(str, Enum):
    MINERAL_FIBRE = "mineral_fibre"
    EPS_BEADS = "eps_beads"
    POLYURETHANE_FOAM = "polyurethane_foam"
    OTHER = "other"
    NONE = "none"
    UNSPECIFIED = "unspecified"


# Keyword tables for matching
FILL_PHRASES = [
    (FillStatus.PARTIAL, ["partial", "inconsistent", "void"]),
    (FillStatus.EMPTY, ["unfilled", "no insulation", "not present"]),
    (FillStatus.FULL, ["fully filled", "full"]),
]

INSULATION_KEYWORDS = [
    (InsulationType.MINERAL_FIBRE, ["mineral fibre", "mineral wool"]),
    (InsulationType.EPS_BEADS, ["polystyrene", "bead"]),
    (InsulationType.POLYURETHANE_FOAM, ["polyurethane", "foam"]),
]


@dataclass(slots=True)
class Observation:
    fill_status: FillStatus = FillStatus.UNKNOWN
    location: Optional[str] = None
    floor: Optional[str] = None
    cavity_width_min_mm: Optional[float] = None
    cavity_width_max_mm: Optional[float] = None
    insulation_type: Optional[InsulationType] = None
    insulation_type_raw: Optional[str] = None
    coverage_pct: Optional[float] = None
    voids: Optional[bool] = None
    debris: Optional[bool] = None
    notes: Optional[str] = None


@dataclass(slots=True)
class BorescopeReport:
    source_file: str
    parser_version: str
    address: Optional[str] = None
    postcode: Optional[str] = None
    inspection_date: Optional[str] = None
    wall_type: Optional[str] = None
    recommended_action: Optional[str] = None
    needs_review: bool = False
    warnings: list[str] = field(default_factory=list)
    observations: list[Observation] = field(default_factory=list)


def load_reports(directory: Path = REPORTS_DIR) -> dict[str, str]:
    """Read every .txt file in `directory`, returning {filename: text}."""
    if not directory.is_dir():
        raise FileNotFoundError(f"Reports folder not found: {directory}")

    reports = {}
    for path in sorted(directory.glob("*.txt")):
        reports[path.name] = path.read_text(encoding="utf-8")
    return reports


def split_key_values(text):
    """Split 'Key: value' lines from everything else."""
    fields, remaining = {}, []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        m = KEY_VALUE.match(line)
        if m:
            fields.setdefault(m.group(1).lower(), m.group(2))
        else:
            remaining.append(line)
    return fields, remaining


def find_match(text, table, default=None):
    """Return the first label in `table` with a keyword found in `text`."""
    text = text.lower()
    for label, keywords in table:
        if any(k in text for k in keywords):
            return label
    return default


def parse_report(text: str, source_file: str) -> BorescopeReport:
    """Parse a borescope report."""
    record = BorescopeReport(source_file=source_file, parser_version=PARSER_VERSION)

    if not text.strip():
        record.needs_review = True
        record.warnings.append("Empty input")
        return record

    fields, remaining = split_key_values(text)

    # header fields
    record.address = fields.get("property")
    record.wall_type = fields.get("wall type")

    m = POSTCODE.search(record.address or "")
    if m:
        record.postcode = f"{m.group(1)} {m.group(2)}".upper()

    date_raw = fields.get("inspection date")
    if date_raw:
        try:
            record.inspection_date = datetime.strptime(date_raw, "%d/%m/%Y").date().isoformat()
        except ValueError:
            record.warnings.append(f"Could not parse inspection date: {date_raw!r}")

    # observation: keyword search over everything except the header values
    header_keys = {"property", "wall type", "inspection date"}
    body = " ".join(
        [v for k, v in fields.items() if k not in header_keys] + remaining
    )

    obs = Observation(
        fill_status=find_match(body, FILL_PHRASES, FillStatus.UNKNOWN),
        insulation_type=find_match(body, INSULATION_KEYWORDS),
        insulation_type_raw=fields.get("insulation type"),
    )

    record.observations.append(obs)

    if obs.fill_status == FillStatus.UNKNOWN:
        record.needs_review = True

    return record


def main():
    reports = load_reports()
    if not reports:
        print(f"No .txt files found in {REPORTS_DIR}")
        return

    for name, text in reports.items():
        print(parse_report(text, name))


if __name__ == "__main__":
    main()
