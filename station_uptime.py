from __future__ import annotations
import sys
from typing import List, Tuple, Dict, Set

def parse_input(path: str):
    with open(path, 'r', encoding='utf-8') as f:
        lines = [ln.strip() for ln in f]

    state = 0
    station_to_chargers: Dict[int, Set[int]] = {}
    charger_to_station: Dict[int, int] = {}
    reports: Dict[int, List[Tuple[int,int,bool]]] = {}

    i = 0
    while i < len(lines):
        ln = lines[i]
        i += 1
        if not ln:
            continue
        if ln.startswith('#'):
            # comment
            continue
        if ln == '[Stations]':
            state = 1
            continue
        if ln == '[Charger Availability Reports]':
            state = 2
            continue

        if state == 1:
            
            parts = ln.split()
            if not parts:
                continue
            try:
                station_id = int(parts[0])
            except ValueError:
                raise ValueError(f"Invalid station line (station id): {ln}")
            charger_ids = []
            for tok in parts[1:]:
                try:
                    charger_ids.append(int(tok))
                except ValueError:
                    raise ValueError(f"Invalid charger id on station line: {ln}")
            if station_id not in station_to_chargers:
                station_to_chargers[station_id] = set()
            for cid in charger_ids:
                if cid in charger_to_station and charger_to_station[cid] != station_id:
                    raise ValueError(f"Charger {cid} appears under multiple stations.")
                charger_to_station[cid] = station_id
                station_to_chargers[station_id].add(cid)

        elif state == 2:
            parts = ln.split()
            if not parts:
                continue
            if parts[0].startswith('['):
                continue
            if len(parts) != 4:
                raise ValueError(f"Invalid report line (need 4 fields): {ln}")
            try:
                cid = int(parts[0])
                start = int(parts[1])
                end = int(parts[2])
            except ValueError:
                raise ValueError(f"Invalid numeric field in report line: {ln}")
            up_str = parts[3].lower()
            if up_str not in ('true','false'):
                raise ValueError(f"Invalid up flag (must be true/false): {ln}")
            up = (up_str == 'true')
            reports.setdefault(cid, []).append((start, end, up))
        else:
            continue

    return station_to_chargers, charger_to_station, reports

def merge_intervals(intervals: List[Tuple[int,int]]) -> List[Tuple[int,int]]:
    if not intervals:
        return []
    norm = [(s,e) for s,e in intervals if e > s]
    if not norm:
        return []
    norm.sort()
    merged = []
    cs, ce = norm[0]
    for s,e in norm[1:]:
        if s <= ce:
            if e > ce:
                ce = e
        else:
            merged.append((cs,ce))
            cs, ce = s, e
    merged.append((cs,ce))
    return merged

def clipped_total(intervals: List[Tuple[int,int]], clip_start: int, clip_end: int) -> int:
    total = 0
    for s,e in intervals:
        a = max(s, clip_start)
        b = min(e, clip_end)
        if b > a:
            total += (b - a)
    return total

def compute_station_uptime(station_to_chargers, reports):
    results: Dict[int, int] = {}
    for station_id in sorted(station_to_chargers.keys()):
        chargers = station_to_chargers.get(station_id, set())
        all_starts = []
        all_ends = []
        up_intervals: List[Tuple[int,int]] = []
        for cid in chargers:
            for (s,e,up) in reports.get(cid, []):
                all_starts.append(s)
                all_ends.append(e)
                if up:
                    up_intervals.append((s,e))
        if not all_starts or not all_ends:
            results[station_id] = 0
            continue
        window_start = min(all_starts)
        window_end = max(all_ends)
        if window_end <= window_start:
            results[station_id] = 0
            continue
        up_merged = merge_intervals(up_intervals)
        up_time = clipped_total(up_merged, window_start, window_end)
        total = window_end - window_start
        pct = int((up_time * 100) // total)
        if pct < 0: pct = 0
        if pct > 100: pct = 100
        results[station_id] = pct
    return results

def main(argv: List[str]):
    if len(argv) != 2:
        print("Usage: station_uptime.py <input_file_path>", file=sys.stderr)
        return 2
    path = argv[1]
    try:
        station_to_chargers, charger_to_station, reports = parse_input(path)
        results = compute_station_uptime(station_to_chargers, reports)
        for station_id in sorted(results.keys()):
            print(f"{station_id} {results[station_id]}")
        return 0
    except Exception as e:
        print("error")
        print(f"Error: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main(sys.argv))
