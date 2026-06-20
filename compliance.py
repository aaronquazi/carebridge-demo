"""
CareBridge — Dokumentations-Compliance-Engine
Überwacht Pflichtdokumentationen und berechnet Warnstufen.
DEMO-PROJEKT: Alle Daten sind fiktiv.
"""

import os
import json
from datetime import datetime, date, timedelta

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

# Pflichtintervalle in Minuten
INTERVALS_MIN = {
    "vitals":   120,
    "beatmung": 120,
    "lagerung": 120,
}

# Welche Kurven-Keys zu welcher Intervall-Gruppe gehören
KEY_GROUPS = {
    "vitals":   ["spo2", "hf", "bd_sys", "af"],
    "beatmung": ["ipap", "epap", "vt", "leckage", "amv"],
    "lagerung": ["lagerung"],
}

# Feste Einnahmezeiten (Stunden)
FIXED_SCHEDULE = {
    "inhalation":  [8, 14, 20],
    "medikamente": [7, 13, 19, 22],
}

# Kurven-Key für feste Zeiten
KURVE_KEY = {
    "inhalation":  "inhalation",
    "medikamente": "med_plan",
}

LABELS = {
    "vitals":      "Vitalzeichen",
    "beatmung":    "Beatmungskontrolle",
    "lagerung":    "Lagerung",
    "inhalation":  "Inhalation",
    "medikamente": "Medikamentengabe",
}

HINTS = {
    "vitals":      "SpO₂, HF, BD, AF in Intensivkurve → Gruppe 1 eintragen",
    "beatmung":    "IPAP, EPAP, Vt, Leckage in Intensivkurve → Gruppe 2 eintragen",
    "lagerung":    "Lagerungsfeld in Intensivkurve → Gruppe 6 eintragen",
    "inhalation":  "Inhalations-Feld in Intensivkurve → Gruppe 4 bestätigen (✓)",
    "medikamente": "Medikamentengabe in Intensivkurve → Gruppe 8 bestätigen (✓)",
}

# Demo-Modus: simulierte Minuten seit letzter Dokumentation
DEMO_ELAPSED = {
    "vitals":   150,   # 2h 30min → 30 Min. überfällig → gelb
    "beatmung": 90,    # 1h 30min → noch ok → grün
    "lagerung": 135,   # 2h 15min → 15 Min. überfällig → gelb
}


class DocumentationCompliance:
    """Wertet Dokumentationspflichten aus und gibt Warnstufen zurück."""

    def __init__(self):
        self.now   = datetime.now()
        self.today = date.today().strftime("%Y-%m-%d")
        self.kurve = self._load_kurve()
        self._cache = None

    # ── Datenzugriff ────────────────────────────────────────

    def _load_kurve(self):
        fname = os.path.join(DATA_DIR, f"kurve_{self.today}.json")
        if os.path.exists(fname):
            try:
                with open(fname, encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return None  # None → Demo-Modus

    def _last_hour_with_value(self, keys):
        """Höchste Stunde, in der mindestens ein Key einen Wert hat."""
        if not self.kurve:
            return None
        best = None
        for key in keys:
            for h_str, val in self.kurve.get(key, {}).items():
                if val and str(val).strip():
                    try:
                        h = int(h_str)
                        if best is None or h > best:
                            best = h
                    except ValueError:
                        pass
        return best

    # ── Hilfsfunktionen ─────────────────────────────────────

    def _severity(self, overdue_min):
        if overdue_min <= 0:
            return "green"
        if overdue_min < 60:
            return "yellow"
        return "red"

    def _overdue_str(self, minutes):
        if minutes <= 0:
            return None
        h, m = divmod(int(minutes), 60)
        if h and m:
            return f"{h}h {m:02d}min überfällig"
        if h:
            return f"{h}h überfällig"
        return f"{m} Min. überfällig"

    # ── Intervall-Checks ────────────────────────────────────

    def _check_interval(self, group):
        interval = INTERVALS_MIN[group]
        use_demo = self.kurve is None

        if use_demo:
            elapsed_min = DEMO_ELAPSED[group]
            last_dt = self.now - timedelta(minutes=elapsed_min)
            last_str = f"zuletzt {last_dt.strftime('%H:%M')} Uhr (Demo)"
        else:
            last_h = self._last_hour_with_value(KEY_GROUPS[group])
            if last_h is None:
                shift_start = self.now.replace(hour=7, minute=0, second=0, microsecond=0)
                elapsed_min = max(0.0, (self.now - shift_start).total_seconds() / 60) if self.now >= shift_start else 0.0
                last_str = "noch nicht dokumentiert"
            else:
                last_dt = self.now.replace(hour=last_h, minute=0, second=0, microsecond=0)
                if last_dt > self.now:
                    last_dt -= timedelta(days=1)
                elapsed_min = (self.now - last_dt).total_seconds() / 60
                last_str = f"zuletzt {last_dt.strftime('%H:%M')} Uhr"

        overdue = max(0.0, elapsed_min - interval)
        return {
            "id":          group,
            "label":       LABELS[group],
            "severity":    self._severity(overdue),
            "overdue_min": int(overdue),
            "overdue_str": self._overdue_str(overdue),
            "last_str":    last_str,
            "hint":        HINTS[group],
            "is_demo":     use_demo,
        }

    # ── Feste-Zeiten-Checks ─────────────────────────────────

    def _check_fixed(self, schedule_key):
        hours     = FIXED_SCHEDULE[schedule_key]
        kurve_key = KURVE_KEY[schedule_key]
        use_demo  = self.kurve is None

        passed = [
            h for h in hours
            if self.now >= self.now.replace(hour=h, minute=0, second=0, microsecond=0)
        ]

        if not passed:
            return {
                "id":          schedule_key,
                "label":       LABELS[schedule_key],
                "severity":    "green",
                "overdue_min": 0,
                "overdue_str": None,
                "last_str":    "noch nicht fällig",
                "hint":        HINTS[schedule_key],
                "is_demo":     use_demo,
            }

        slot_results = []
        for h in passed:
            due_dt  = self.now.replace(hour=h, minute=0, second=0, microsecond=0)
            elapsed = (self.now - due_dt).total_seconds() / 60

            if use_demo:
                # Erstes Slot jeder Gruppe + 13:00-Medikamente → erledigt
                done = h == hours[0] or (schedule_key == "medikamente" and h == 13)
                overdue = 0 if done else max(0, int(elapsed) - 10)
            else:
                val  = self.kurve.get(kurve_key, {}).get(str(h), "").strip()
                done = bool(val)
                overdue = 0 if done else max(0, int(elapsed))

            slot_results.append({"hour": h, "done": done, "overdue": overdue})

        worst = max(s["overdue"] for s in slot_results)
        pending  = [f"{s['hour']:02d}:00" for s in slot_results if not s["done"]]
        done_lst = [f"{s['hour']:02d}:00" for s in slot_results if s["done"]]

        if pending:
            last_str = f"Offen: {', '.join(pending)}"
        elif done_lst:
            last_str = f"bestätigt: {', '.join(done_lst)}"
        else:
            last_str = "—"

        return {
            "id":          schedule_key,
            "label":       LABELS[schedule_key],
            "severity":    self._severity(worst),
            "overdue_min": int(worst),
            "overdue_str": self._overdue_str(worst),
            "last_str":    last_str,
            "hint":        HINTS[schedule_key],
            "is_demo":     use_demo,
        }

    # ── Öffentliche API ──────────────────────────────────────

    def get_status(self):
        """Liste aller Pflichtkontrollen mit Warnstufe."""
        if self._cache is not None:
            return self._cache
        self._cache = [
            self._check_interval("vitals"),
            self._check_interval("beatmung"),
            self._check_interval("lagerung"),
            self._check_fixed("inhalation"),
            self._check_fixed("medikamente"),
        ]
        return self._cache

    def get_overall_status(self):
        """'green', 'yellow' oder 'red'."""
        sevs = {r["severity"] for r in self.get_status()}
        if "red"    in sevs: return "red"
        if "yellow" in sevs: return "yellow"
        return "green"

    def get_overdue_count(self):
        """Anzahl der nicht-grünen Positionen."""
        return sum(1 for r in self.get_status() if r["severity"] != "green")

    def get_next_due(self):
        """Nächste fällige Dokumentationspflicht als lesbarer String."""
        now_min = self.now.hour * 60 + self.now.minute
        candidates = []

        for group in KEY_GROUPS:
            if self.kurve is None:
                last_min = now_min - DEMO_ELAPSED[group]
            else:
                lh = self._last_hour_with_value(KEY_GROUPS[group])
                last_min = lh * 60 if lh is not None else 7 * 60
            next_min = last_min + INTERVALS_MIN[group]
            if next_min > now_min:
                h, m = divmod(int(next_min), 60)
                candidates.append((next_min, f"{LABELS[group]} um {h:02d}:{m:02d} Uhr"))

        for sched_key, hours in FIXED_SCHEDULE.items():
            for h in hours:
                if h * 60 > now_min:
                    candidates.append((h * 60, f"{LABELS[sched_key]} um {h:02d}:00 Uhr"))
                    break

        if not candidates:
            return "Alle Pflichten für heute erfüllt"
        candidates.sort()
        return candidates[0][1]
