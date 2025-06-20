# src/api/awarding.py
"""
Parse the Stirnubuks podium API and save a clean JSON.
"""

from __future__ import annotations

import os
import re
import json
import requests
from typing import List, Dict
from bs4 import BeautifulSoup, Tag

# --------------------------------------------------------------------------- #
# 1.  group title mapping  (raw ⟶ full marketing title)
# --------------------------------------------------------------------------- #
DISPLAY_TITLE: dict[str, str] = {
    "VĀVERE": "STAR FM VĀVERE",
    "ZAĶIS": "KARTE VESELĪBA ZAĶIS",
    "SUSURS": "GARDU MUTI SUSURS",
    "VILKS": "GARMIN FĒNIX VILKS",
    "STIRNU BUKS": "VENDEN STIRNU BUKS",
    "SKOLU ČEMPIONĀTS": "LVM ČEMPIONĀTS SKOLU JAUNIEŠIEM",
    "LŪSIS": "GARMIN LŪSIS",
}

SKIP_GROUPS = {"KOMANDAS", "SKOLAS"}        # ignore these blocks entirely


# --------------------------------------------------------------------------- #
# 2.  helper functions
# --------------------------------------------------------------------------- #
DASH = r"[-–—]"   #  ASCII hyphen OR en-dash OR em-dash

CELL_RE = re.compile(
    rf"(\d+)\.\s*(.+?)\s*{DASH}\s*([\d:,]+)(?:\s*\([^)]+\))?$"
)

def parse_cell(text: str) -> Dict[str, str] | None:
    """Return {'Position','Name','Laiks'} or None if the text isn't valid."""
    m = CELL_RE.match(text)
    if not m:
        return None
    pos, name, tm = m.groups()
    name = name.strip()
    if name == "-nav-":          # empty slot used in some tables
        return None
    return {"Position": pos, "Name": name, "Laiks": tm}


def top_three(entries: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Return list of exactly three dicts, padding with empties if needed."""
    full: List[Dict[str, str]] = []
    for i in range(1, 4):
        found = next((e for e in entries if e["Position"] == str(i)), None)
        if found:
            full.append(found)
        else:
            full.append({"Name": "", "Laiks": ""})
    return full


# --------------------------------------------------------------------------- #
# 3.  main routine
# --------------------------------------------------------------------------- #
def fetch_and_save_awards(
    output_dir: str = "output",
    filename: str = "awarding_results.json",
) -> str:
    # --- 3A. fetch & soup ---------------------------------------------------
    html = requests.get("https://www.stirnubuks.lv/api/?module=podium").text
    soup = BeautifulSoup(html, "html.parser")
    page = soup.find("page")

    elements: List[Tag] = [
        el for el in page.contents
        if isinstance(el, Tag) and el.name in {"p", "table"}
    ]

    current_group_raw: str | None = None
    results: List[Dict[str, str]] = []

    # --- 3B. iterate through <p>/<table> sequence ---------------------------
    for el in elements:
        # ---------- group heading <p> ----------
        if el.name == "p":
            grp = el.get_text(strip=True)
            current_group_raw = None if grp.upper() in SKIP_GROUPS else grp
            continue

        # ---------- podium table ----------
        if current_group_raw is None:
            continue

        # rows & (optional) subgroup header
        rows = el.find_all("tr")
        if not rows:
            continue

        subgroup_code = ""
        first_cells = rows[0].find_all("td")
        if first_cells and first_cells[0].has_attr("colspan"):
            raw = first_cells[0].get_text(strip=True)
            if "KOPVĒRTĒJUMS" in raw.upper():
                subgroup_code = "KOPVĒRTĒJUMS"
            else:
                subgroup_code = raw.split()[0].rstrip(".")
            rows = rows[1:]  # discard header row

        # collect women / men podium lists
        women, men = [], []
        for row in rows:
            td = row.find_all("td")
            if len(td) < 2:
                continue
            left = parse_cell(td[0].get_text(strip=True))
            right = parse_cell(td[1].get_text(strip=True))
            if left:
                women.append(left)
            if right:
                men.append(right)

        women = top_three(women)
        men   = top_three(men)

        # ---------- write two JSON records ----------
        full_title = DISPLAY_TITLE.get(current_group_raw, current_group_raw)

        for gender, podium in (("Sievietes", women), ("Vīrieši", men)):
            if not any(p["Name"] for p in podium):
                continue          # skip gender with no names at all

            rec: Dict[str, str] = {
                "Group1": full_title,
                "Subgroup1": (f"{subgroup_code} {gender}").strip(),
            }
            for idx, p in enumerate(podium, 1):
                rec[f"Name{idx}"]  = p["Name"]
                rec[f"Laiks{idx}"] = p["Laiks"]
            results.append(rec)

    # --- 3C. save -----------------------------------------------------------
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    return path


# --------------------------------------------------------------------------- #
# 4.  run standalone
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    out = fetch_and_save_awards()
    print(f"✓ JSON written → {out}")
