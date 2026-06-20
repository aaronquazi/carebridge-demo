"""
CareBridge Demo — Flask Hauptanwendung
Digitale Dokumentation für die außerklinische Beatmungspflege
DEMO-PROJEKT: Alle Daten sind fiktiv
"""

import os
import json
import random
from datetime import datetime, date, timedelta
from flask import Flask, render_template, jsonify, request, redirect, url_for, session
from compliance import DocumentationCompliance

app = Flask(__name__)
app.config['SECRET_KEY'] = 'carebridge-demo-2026'

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)
CONFIG_FILE = os.path.join(DATA_DIR, "config.json")

# ──────────────────────────────────────────
# STAMMDATEN (fiktiv, für Verordnungen etc.)
# ──────────────────────────────────────────

DEMO_PATIENTEN = {
    "P-2024-0042": {
        "id": "P-2024-0042",
        "name": "Max Mustermann",
        "geburtsdatum": "14.03.1958",
        "geburtsdatum_iso": "1958-03-14",
        "alter": 68,
        "diagnose": "Chronisch respiratorische Insuffizienz bei ALS",
        "diagnose_kurz": "ALS",
        "beatmungspflichtig": True,
        "beatmungspflichtig_seit": "2022-11-01",
        "beatmungsgeraet": "Astral 150 (ResMed)",
        "station": "Beatmungs-WG Musterstadt",
        "zimmer": "Zimmer 3",
        "arzt": "Dr. Elisabeth Hoffmann",
        "pflegeleitung": "Sandra Krause, examinierte Pflegefachfrau",
        "notfallkontakt": "Maria Mustermann (Ehefrau) — 0151 12345678"
    },
    "P-2024-0043": {
        "id": "P-2024-0043",
        "name": "Maria Musterfrau",
        "geburtsdatum": "22.07.1945",
        "geburtsdatum_iso": "1945-07-22",
        "alter": 80,
        "diagnose": "COPD Gold IV mit hyperkapnischer Insuffizienz",
        "diagnose_kurz": "COPD Gold IV",
        "beatmungspflichtig": True,
        "beatmungspflichtig_seit": "2024-03-15",
        "beatmungsgeraet": "Lumis 150 VPAP ST-A (ResMed)",
        "station": "Beatmungs-WG Musterstadt",
        "zimmer": "Zimmer 5",
        "arzt": "Dr. Elisabeth Hoffmann",
        "pflegeleitung": "Sandra Krause, examinierte Pflegefachfrau",
        "notfallkontakt": "Peter Musterfrau (Sohn) — 0152 98765432"
    }
}

DEMO_BEATMUNGSVERORDNUNGEN = {
    "P-2024-0042": {
        "verordnet_von": "Dr. Elisabeth Hoffmann",
        "datum": "2026-06-01",
        "gueltig_bis": "2026-07-01",
        "geraet": "Astral 150 (ResMed)",
        "modus": "S/T (Spontan/Timed)",
        "parameter": {
            "IPAP": "22 mbar",
            "EPAP": "6 mbar",
            "Atemfrequenz_backup": "14 /min",
            "Inspirationszeit": "1,2 s",
            "FiO2": "0,30 (30%)",
            "Zielvolumen": "600 ml"
        },
        "alarmgrenzen": {
            "SpO2_min": "88%",
            "AF_min": "8 /min",
            "AF_max": "30 /min",
            "Leckage_max": "40 L/min",
            "Apnoe_intervall": "20 s"
        },
        "o2_gabe": {
            "soll": "2 L/min",
            "bedarf": "bis 4 L/min",
            "geraet": "Sauerstoffkonzentrator",
            "hinweis": "O₂ nur bei SpO₂ < 88% erhöhen gemäß Verordnung"
        },
        "trachealkanüle": {
            "typ": "Shiley 8.0 gecufft",
            "groesse": "8.0 mm ID",
            "letzter_wechsel": "2026-06-12",
            "naechster_wechsel": "2026-07-12",
            "cuffdruck_soll": "20–25 cmH₂O",
            "cuffdruck_einheit": "cmH₂O",
            "cuffdruck_alternativ": "Füllvolumen ca. 3–5 ml Luft",
            "cuffdruck_hinweis": "Messung mit Cuffdruckmesser bevorzugt. Alternativ: Fingerprobe oder ml-Angabe möglich."
        },
        "bemerkung": "Nächtliche Beatmung 22:00–08:00 Uhr. Tagsüber nach Toleranz."
    },
    "P-2024-0043": {
        "verordnet_von": "Dr. Elisabeth Hoffmann",
        "datum": "2026-05-15",
        "gueltig_bis": "2026-08-15",
        "geraet": "Lumis 150 VPAP ST-A (ResMed)",
        "modus": "VPAP ST-A (Spontan/Timed mit Autotitration)",
        "parameter": {
            "IPAP": "18 mbar",
            "EPAP": "8 mbar",
            "Atemfrequenz_backup": "16 /min",
            "Inspirationszeit": "1,0 s",
            "FiO2": "0,35 (35%)",
            "Zielvolumen": "520 ml"
        },
        "alarmgrenzen": {
            "SpO2_min": "88%",
            "AF_min": "10 /min",
            "AF_max": "35 /min",
            "Leckage_max": "35 L/min",
            "Apnoe_intervall": "20 s"
        },
        "trachealkanüle": {
            "typ": "NIV — Nasenmaske (kein TK)",
            "groesse": "—",
            "letzter_wechsel": "—",
            "naechster_wechsel": "—",
            "cuffdruck_soll": "—"
        },
        "bemerkung": "Nachtbeatmung NIV 22:00–09:00 Uhr über Nasenmaske. Tagsüber O₂-Brille nach Bedarf."
    }
}

DEMO_MEDIKAMENTENPLAN = [
    {
        "name": "Baclofen",
        "dosierung": "10 mg",
        "zeiten": ["07:00", "13:00", "20:00"],
        "grund": "Spastik bei ALS",
        "indikation_detail": "Zentral wirkende Muskelrelaxans. Reduziert Spastik und Muskelsteife.",
        "form": "Tablette",
        "nuechtern": False,
        "nuechtern_hinweis": "Kann mit oder ohne Mahlzeit eingenommen werden",
        "wechselwirkungen": "Verstärkte Wirkung mit anderen ZNS-dämpfenden Mitteln. Kein Alkohol.",
        "besonderheiten": "Nicht abrupt absetzen — ausschleichen!"
    },
    {
        "name": "Riluzol (Rilutek)",
        "dosierung": "50 mg",
        "zeiten": ["07:00", "19:00"],
        "grund": "ALS-Therapie (neuroprotektiv)",
        "indikation_detail": "Einziges zugelassenes Medikament zur Verlangsamung der ALS-Progression.",
        "form": "Tablette",
        "nuechtern": True,
        "nuechtern_hinweis": "Mindestens 1 Stunde vor oder 2 Stunden nach dem Essen einnehmen!",
        "wechselwirkungen": "Wechselwirkung mit Koffein und fettreichen Mahlzeiten möglich.",
        "besonderheiten": "Regelmäßige Leberwertkontrollen notwendig."
    },
    {
        "name": "Pantoprazol",
        "dosierung": "40 mg",
        "zeiten": ["07:00"],
        "grund": "Magenschutz (Protonenpumpenhemmer)",
        "indikation_detail": "Schutz der Magenschleimhaut, besonders bei Kombination mit anderen Medikamenten.",
        "form": "Tablette",
        "nuechtern": True,
        "nuechtern_hinweis": "30 Minuten VOR dem Frühstück einnehmen — nüchtern für optimale Wirkung!",
        "wechselwirkungen": "Kann Resorption von Ketoconazol und Itraconazol vermindern.",
        "besonderheiten": "Tablette nicht zerkauen oder zerdrücken."
    },
    {
        "name": "Lorazepam",
        "dosierung": "0,5 mg",
        "zeiten": ["22:00"],
        "grund": "Anxiolyse / Schlafunterstützung",
        "indikation_detail": "Kurzfristige Behandlung von Angstzuständen und Schlafstörungen bei ALS.",
        "form": "Tablette",
        "nuechtern": False,
        "nuechtern_hinweis": "Einnahme unabhängig von Mahlzeiten",
        "wechselwirkungen": "KEINE Kombination mit Alkohol! Verstärkte Sedierung mit anderen ZNS-Dämpfern.",
        "besonderheiten": "BTM-pflichtig! Nur bei Bedarf. Abhängigkeitspotenzial beachten.",
        "btm": True
    },
    {
        "name": "NaCl 0,9%",
        "dosierung": "5 ml",
        "zeiten": ["08:00", "14:00", "20:00"],
        "grund": "Sekretmobilisation",
        "indikation_detail": "Isotone Kochsalzlösung zur Befeuchtung der Atemwege und Sekretverflüssigung.",
        "form": "Inhalation",
        "nuechtern": False,
        "nuechtern_hinweis": "Unabhängig von Mahlzeiten",
        "wechselwirkungen": "Keine bekannt.",
        "besonderheiten": "Immer zuerst inhalieren, dann Ambroxol."
    },
    {
        "name": "Ambroxol",
        "dosierung": "30 mg/5 ml",
        "zeiten": ["08:00", "20:00"],
        "grund": "Sekretolytikum",
        "indikation_detail": "Fördert die Verflüssigung und Ausscheidung von zähem Bronchialsekret.",
        "form": "Inhalation",
        "nuechtern": False,
        "nuechtern_hinweis": "Nach NaCl inhalieren",
        "wechselwirkungen": "Kombination mit Antibiotika kann deren Konzentration im Bronchialsekret erhöhen.",
        "besonderheiten": "Reihenfolge beachten: erst NaCl, dann Ambroxol."
    },
]

# ──────────────────────────────────────────
# KONFIGURATION (Stammdaten aus JSON)
# ──────────────────────────────────────────

DEMO_CONFIG = {
    "patienten": [
        {
            "id": "P-2024-0042",
            "name": "Max Mustermann",
            "geburtsdatum": "1958-03-14",
            "alter": 68,
            "diagnose": "Chronisch respiratorische Insuffizienz bei ALS",
            "zimmer": "Zimmer 3",
            "station": "Beatmungs-WG Musterstadt",
            "beatmungspflichtig": True,
            "beatmungsgeraet": "Astral 150 (ResMed)",
            "beatmungspflichtig_seit": "2022-11-01",
            "arzt": "Dr. Elisabeth Hoffmann",
            "aktiv": True,
            "intervalle": {
                "spo2": 2, "hf": 2, "bd_sys": 4, "bd_dia": 4,
                "af": 2, "beatmung": 2, "vt": 2, "leckage": 2, "lagerung": 2
            }
        },
        {
            "id": "P-2024-0043",
            "name": "Maria Musterfrau",
            "geburtsdatum": "1945-07-22",
            "alter": 80,
            "diagnose": "COPD Gold IV mit hyperkapnischer Insuffizienz",
            "zimmer": "Zimmer 5",
            "station": "Beatmungs-WG Musterstadt",
            "beatmungspflichtig": True,
            "beatmungsgeraet": "Lumis 150 VPAP ST-A (ResMed)",
            "beatmungspflichtig_seit": "2024-03-15",
            "arzt": "Dr. Elisabeth Hoffmann",
            "aktiv": True,
            "intervalle": {
                "spo2": 2, "hf": 3, "bd_sys": 4, "bd_dia": 4,
                "af": 2, "beatmung": 2, "vt": 2, "leckage": 2, "lagerung": 2
            }
        },
    ],
    "personal": [
        {"name": "A. Berger",     "kuerzel": "AB", "rolle": "Pflegefachmann"},
        {"name": "Sandra Krause", "kuerzel": "SK", "rolle": "Pflegeleitung"},
        {"name": "Aaron Quazi",   "kuerzel": "AQ", "rolle": "Pflegefachmann"},
        {"name": "Thomas Meier",  "kuerzel": "TM", "rolle": "Pflegehilfskraft"}
    ],
    "leistungsvorlagen": [
        {"id": "GKP", "name": "Ganzkörperpflege",            "zeiten": ["06:30"],                     "pflicht": True,  "intervall_h": None},
        {"id": "MP",  "name": "Mundpflege / Teilpflege",     "zeiten": ["06:30", "12:00", "20:00"],   "pflicht": True,  "intervall_h": None},
        {"id": "TK",  "name": "Trachealkanülenpflege",       "zeiten": ["07:15"],                     "pflicht": True,  "intervall_h": None},
        {"id": "ABS", "name": "Absaugung tracheal",          "zeiten": ["07:30"],                     "pflicht": False, "intervall_h": 4},
        {"id": "INH", "name": "Inhalation NaCl + Ambroxol", "zeiten": ["08:00", "14:00", "20:00"],   "pflicht": True,  "intervall_h": None},
        {"id": "VIT", "name": "Vitalzeichenkontrolle",       "zeiten": ["08:15", "14:00", "20:00"],   "pflicht": True,  "intervall_h": 2},
        {"id": "LAG", "name": "Lagerungswechsel",            "zeiten": [],                            "pflicht": True,  "intervall_h": 2},
        {"id": "MED", "name": "Medikamentengabe",            "zeiten": ["07:00", "13:00", "19:00", "22:00"], "pflicht": True, "intervall_h": None}
    ]
}


def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, encoding="utf-8") as f:
            return json.load(f)
    return DEMO_CONFIG


def save_config(cfg):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


def ensure_demo_patients():
    cfg = load_config()
    existing_ids = {p['id'] for p in cfg.get('patienten', [])}
    changed = False
    for dp in DEMO_CONFIG['patienten']:
        if dp['id'] not in existing_ids:
            cfg['patienten'].append(dp)
            changed = True
    if changed:
        save_config(cfg)


# ──────────────────────────────────────────
# SESSION HELPERS
# ──────────────────────────────────────────

def get_current_patient_id():
    return session.get('patient_id', 'P-2024-0042')


def get_current_patient():
    pid = get_current_patient_id()
    cfg = load_config()
    for p in cfg.get('patienten', []):
        if p['id'] == pid:
            demo = DEMO_PATIENTEN.get(pid, {})
            return {**demo, **p}
    return DEMO_PATIENTEN.get(pid, DEMO_PATIENTEN['P-2024-0042'])


def get_current_verordnung():
    return DEMO_BEATMUNGSVERORDNUNGEN.get(get_current_patient_id(),
           DEMO_BEATMUNGSVERORDNUNGEN['P-2024-0042'])

# ──────────────────────────────────────────
# DATEI-HELPERS
# ──────────────────────────────────────────

def get_kurve_data(patient_id=None, datum=None):
    if patient_id is None:
        patient_id = get_current_patient_id()
    if datum is None:
        datum = date.today().strftime("%Y-%m-%d")
    fname = os.path.join(DATA_DIR, f"kurve_{patient_id}_{datum}.json")
    if os.path.exists(fname):
        with open(fname, encoding="utf-8") as f:
            return json.load(f)
    return {}

def get_leistungen_signoffs(patient_id=None, datum=None):
    if patient_id is None:
        patient_id = get_current_patient_id()
    if datum is None:
        datum = date.today().strftime("%Y-%m-%d")
    fname = os.path.join(DATA_DIR, f"leistungen_{patient_id}_{datum}.json")
    if os.path.exists(fname):
        with open(fname, encoding="utf-8") as f:
            return json.load(f)
    return {}

def get_bemerkungen_data(patient_id=None, datum=None):
    if patient_id is None:
        patient_id = get_current_patient_id()
    if datum is None:
        datum = date.today().strftime("%Y-%m-%d")
    fname = os.path.join(DATA_DIR, f"bemerkungen_{patient_id}_{datum}.json")
    if os.path.exists(fname):
        with open(fname, encoding="utf-8") as f:
            return json.load(f)
    return []

def get_therapien_data(patient_id=None):
    if patient_id is None:
        patient_id = get_current_patient_id()
    fname = os.path.join(DATA_DIR, f"therapien_{patient_id}.json")
    if os.path.exists(fname):
        with open(fname, encoding="utf-8") as f:
            return json.load(f)
    return {"verordnungen": [], "eintraege": []}

def get_protokolle_data(patient_id=None):
    if patient_id is None:
        patient_id = get_current_patient_id()
    fname = os.path.join(DATA_DIR, f"protokolle_{patient_id}.json")
    if os.path.exists(fname):
        with open(fname, encoding="utf-8") as f:
            return json.load(f)
    return {"arztbriefe": [], "befunde": [], "ueberweisungen": [], "sonstiges": []}

def get_sis_data(patient_id=None):
    if patient_id is None:
        patient_id = get_current_patient_id()
    fname = os.path.join(DATA_DIR, f"sis_{patient_id}.json")
    if os.path.exists(fname):
        with open(fname, encoding="utf-8") as f:
            return json.load(f)
    return {"themenfelder": {}}

def get_pflegebericht_data(patient_id=None):
    if patient_id is None:
        patient_id = get_current_patient_id()
    fname = os.path.join(DATA_DIR, f"pflegebericht_{patient_id}.json")
    if os.path.exists(fname):
        with open(fname, encoding="utf-8") as f:
            return json.load(f)
    return []

def get_ereignisse_data(patient_id=None):
    if patient_id is None:
        patient_id = get_current_patient_id()
    fname = os.path.join(DATA_DIR, f"ereignisse_{patient_id}.json")
    if os.path.exists(fname):
        with open(fname, encoding="utf-8") as f:
            return json.load(f)
    return []

def get_wunden_data(patient_id=None):
    if patient_id is None:
        patient_id = get_current_patient_id()
    fname = os.path.join(DATA_DIR, f"wunden_{patient_id}.json")
    if os.path.exists(fname):
        with open(fname, encoding="utf-8") as f:
            return json.load(f)
    return []

def safe_num(val, default=None):
    try:
        return float(str(val).strip())
    except (ValueError, TypeError, AttributeError):
        return default

def get_kurve_letzt_werte(patient_id=None):
    kurve = get_kurve_data(patient_id)
    result = {}
    for key in ['spo2','hf','bd_sys','bd_dia','af','vt','leckage','ipap','epap']:
        group = kurve.get(key, {})
        last_val, last_h = None, -1
        for h_str, v in group.items():
            if v and str(v).strip():
                try:
                    h = int(h_str)
                    if h > last_h:
                        last_h, last_val = h, str(v).strip()
                except ValueError:
                    pass
        result[key] = last_val
        result[key + '_uhr'] = f"{last_h:02d}:00" if last_h >= 0 else None
    lag_group = kurve.get('lagerung', {})
    last_lag, last_lag_h = None, -1
    for h_str, v in lag_group.items():
        if v and str(v).strip():
            try:
                h = int(h_str)
                if h > last_lag_h:
                    last_lag_h, last_lag = h, str(v).strip()
            except ValueError:
                pass
    result['lagerung'] = last_lag
    result['lagerung_uhr'] = f"{last_lag_h:02d}:00" if last_lag_h >= 0 else None
    return result

# ──────────────────────────────────────────
# DEMO-DATEN-FUNKTIONEN
# ──────────────────────────────────────────

def get_demo_leistungen(patient_id=None):
    if patient_id is None:
        patient_id = get_current_patient_id()
    heute = date.today().strftime("%d.%m.%Y")
    base = [
        {"zeit": "06:30", "datum": heute, "leistung": "Ganzkörperpflege",                    "kuerzel": "GKP", "pflegekraft": "", "bestaetigt": False},
        {"zeit": "07:00", "datum": heute, "leistung": "Medikamentengabe (07:00)",             "kuerzel": "MED", "pflegekraft": "", "bestaetigt": False},
        {"zeit": "07:15", "datum": heute, "leistung": "Trachealkanülenpflege + Cuffdruck",    "kuerzel": "TK",  "pflegekraft": "", "bestaetigt": False},
        {"zeit": "07:30", "datum": heute, "leistung": "Absaugung tracheal",                   "kuerzel": "ABS", "pflegekraft": "", "bestaetigt": False},
        {"zeit": "08:00", "datum": heute, "leistung": "Inhalation NaCl + Ambroxol",           "kuerzel": "INH", "pflegekraft": "", "bestaetigt": False},
        {"zeit": "08:15", "datum": heute, "leistung": "Vitalzeichenkontrolle",                "kuerzel": "VIT", "pflegekraft": "", "bestaetigt": False},
        {"zeit": "10:00", "datum": heute, "leistung": "Lagerungswechsel (30°-Lagerung)",      "kuerzel": "LAG", "pflegekraft": "", "bestaetigt": False},
        {"zeit": "12:00", "datum": heute, "leistung": "Mittagspflege / Mundpflege",           "kuerzel": "MP",  "pflegekraft": "", "bestaetigt": False},
        {"zeit": "12:00", "datum": heute, "leistung": "Morphin 10mg s.c. — BTM-pflichtig",   "kuerzel": "MED", "pflegekraft": "", "bestaetigt": False, "btm": True},
        {"zeit": "13:00", "datum": heute, "leistung": "Medikamentengabe (13:00)",             "kuerzel": "MED", "pflegekraft": "", "bestaetigt": False},
        {"zeit": "14:00", "datum": heute, "leistung": "Vitalzeichenkontrolle",                "kuerzel": "VIT", "pflegekraft": "", "bestaetigt": False},
        {"zeit": "22:00", "datum": heute, "leistung": "Lorazepam 0,5 mg — BTM-pflichtig",    "kuerzel": "MED", "pflegekraft": "", "bestaetigt": False, "btm": True},
    ]
    signoffs = get_leistungen_signoffs(patient_id)
    for l in base:
        lid = f"{l['kuerzel']}_{l['zeit']}"
        if lid in signoffs:
            l['bestaetigt'] = True
            l['pflegekraft'] = signoffs[lid]['kuerzel']
    return base

def get_uebergabe_check(patient_id=None):
    if patient_id is None:
        patient_id = get_current_patient_id()
    leistungen = get_demo_leistungen(patient_id)
    offen = [l for l in leistungen if not l["bestaetigt"]]
    warnungen = []
    now_min = datetime.now().hour * 60 + datetime.now().minute
    truly_overdue = []
    for l in offen:
        try:
            h, m = l['zeit'].split(':')
            if now_min - (int(h) * 60 + int(m)) > 15:
                truly_overdue.append(l)
        except Exception:
            truly_overdue.append(l)
    if truly_overdue:
        warnungen.append(f"{len(truly_overdue)} Leistungen überfällig — vor Übergabe abzeichnen")
    kurve_werte = get_kurve_letzt_werte(patient_id)
    spo2_val = safe_num(kurve_werte.get('spo2'))
    if spo2_val is not None and spo2_val < 94:
        warnungen.append(f"SpO₂ zuletzt {kurve_werte['spo2']}% — beobachten")
    verordnung = DEMO_BEATMUNGSVERORDNUNGEN.get(patient_id, DEMO_BEATMUNGSVERORDNUNGEN['P-2024-0042'])
    tk_next = verordnung["trachealkanüle"].get("naechster_wechsel", "—")
    if tk_next and tk_next != "—":
        try:
            tk_wechsel = datetime.strptime(tk_next, "%Y-%m-%d")
            tage = (tk_wechsel - datetime.now()).days
            if tage <= 7:
                warnungen.append(f"TK-Wechsel in {tage} Tagen fällig")
        except ValueError:
            pass
    return {"offene_leistungen": offen, "warnungen": warnungen, "bereit": len(truly_overdue) == 0}

def get_demo_verlauf_14_tage(patient_id='P-2024-0042'):
    rng = random.Random(hash(patient_id) % 9999)
    today = date.today()
    if patient_id == 'P-2024-0043':
        base_spo2, base_hf, base_bd = 93, 86, 138
    else:
        base_spo2, base_hf, base_bd = 96, 72, 118
    verlauf = []
    for i in range(13, -1, -1):
        d = today - timedelta(days=i)
        sv = [max(85, base_spo2 + rng.randint(-3, 2)) for _ in range(8)]
        hv = [base_hf + rng.randint(-6, 6) for _ in range(8)]
        bv = [base_bd + rng.randint(-10, 10) for _ in range(8)]
        av = [15 + rng.randint(-2, 3) for _ in range(8)]
        verlauf.append({
            "datum": d.strftime("%d.%m."),
            "datum_iso": d.strftime("%Y-%m-%d"),
            "spo2_min": min(sv), "spo2_max": max(sv),
            "spo2_avg": round(sum(sv) / len(sv), 1),
            "hf_avg": round(sum(hv) / len(hv), 1),
            "hf_min": min(hv), "hf_max": max(hv),
            "bd_sys_avg": round(sum(bv) / len(bv)),
            "af_avg": round(sum(av) / len(av), 1),
        })
    return verlauf

# ──────────────────────────────────────────
# DEMO-DATEN INITIALISIERUNG
# ──────────────────────────────────────────

def init_demo_data():
    heute = date.today().strftime("%Y-%m-%d")
    cur_h = datetime.now().hour

    VITAL_HOURS   = [7, 9, 11, 13, 15]         # SpO2, HF, AF, Beatmung
    BD_TEMP_HOURS = [8, 12, 18]                 # Blutdruck + Temperatur
    LAGERUNG_PLAN = {7: "30° re", 9: "90° li", 11: "30° li", 13: "Rücken", 15: "30° re"}

    # ── Max Mustermann (P-2024-0042) ──
    pid = "P-2024-0042"
    kf  = os.path.join(DATA_DIR, f"kurve_{pid}_{heute}.json")
    # Always regenerate Kurve so time-based demo data stays current
    if True:
        k = {key: {} for key in ['spo2','hf','bd_sys','bd_dia','af','ipap','epap','vt','leckage','lagerung','temp','inhalation','cuffdruck','tk_pflege']}

        SPO2 = [96, 97, 95, 96, 97]
        HF   = [72, 70, 74, 68, 76]
        AF   = [15, 14, 16, 15, 17]
        VT   = [600, 595, 610, 590, 605]
        LK   = [8, 9, 7, 10, 8]
        BDS  = [118, 116, 122]
        BDD  = [76, 74, 78]
        TEMP = ["36.7", "38.7", "37.0"]

        for idx, h in enumerate(VITAL_HOURS):
            if h <= cur_h:
                k['spo2'][str(h)]    = str(SPO2[idx])
                k['hf'][str(h)]      = str(HF[idx])
                k['af'][str(h)]      = str(AF[idx])
                k['ipap'][str(h)]    = "22"
                k['epap'][str(h)]    = "6"
                k['vt'][str(h)]      = str(VT[idx])
                k['leckage'][str(h)] = str(LK[idx])

        for idx, h in enumerate(BD_TEMP_HOURS):
            if h <= cur_h:
                k['bd_sys'][str(h)] = str(BDS[idx])
                k['bd_dia'][str(h)] = str(BDD[idx])
                k['temp'][str(h)]   = TEMP[idx]

        for h, lage in LAGERUNG_PLAN.items():
            if h <= cur_h:
                k['lagerung'][str(h)] = lage

        if cur_h >= 8:
            k['inhalation']['8'] = "✓"

        k['cuffdruck']['7'] = "22"
        k['tk_pflege']['7'] = "✓"

        with open(kf, "w", encoding="utf-8") as f:
            json.dump(k, f, ensure_ascii=False, indent=2)

    lf = os.path.join(DATA_DIR, f"leistungen_{pid}_{heute}.json")
    if not os.path.exists(lf):
        with open(lf, "w", encoding="utf-8") as f:
            json.dump({"GKP_06:30":{"kuerzel":"AQ","zeitstempel":"06:32","begruendung":""},
                       "MED_07:00":{"kuerzel":"AQ","zeitstempel":"07:02","begruendung":""},
                       "TK_07:15": {"kuerzel":"AQ","zeitstempel":"07:18","begruendung":""},
                       "ABS_07:30":{"kuerzel":"AQ","zeitstempel":"07:33","begruendung":""},
                       "INH_08:00":{"kuerzel":"AQ","zeitstempel":"08:05","begruendung":""},
                       "VIT_08:15":{"kuerzel":"AQ","zeitstempel":"08:20","begruendung":""},
                       "LAG_10:00":{"kuerzel":"AQ","zeitstempel":"10:03","begruendung":""}},
                      f, ensure_ascii=False, indent=2)

    bf = os.path.join(DATA_DIR, f"bemerkungen_{pid}_{heute}.json")
    if not os.path.exists(bf):
        with open(bf, "w", encoding="utf-8") as f:
            json.dump([{"zeitstempel":"06:45","kuerzel":"AQ","schicht":"Frühdienst",
                "text":"Patient hat gut geschlafen. Beatmung lief regelgerecht über Nacht. "
                       "SpO₂ stabil zwischen 95–97%. Um 09:00 kurzer SpO₂-Abfall auf 94% "
                       "bei Lagerungswechsel, danach wieder normalisiert. "
                       "Sekret: weißlich, mäßig. Absaugung 2x durchgeführt."}],
                      f, ensure_ascii=False, indent=2)

    # ── Maria Musterfrau (P-2024-0043) ──
    pid2 = "P-2024-0043"
    kf2  = os.path.join(DATA_DIR, f"kurve_{pid2}_{heute}.json")
    if True:
        k2 = {key: {} for key in ['spo2','hf','bd_sys','bd_dia','af','ipap','epap','vt','leckage','lagerung','temp','inhalation']}

        SPO2_M = [93, 94, 92, 93, 91]
        HF_M   = [86, 88, 82, 92, 85]
        AF_M   = [20, 18, 22, 19, 21]
        VT_M   = [520, 535, 540, 525, 550]
        LK_M   = [10, 12, 8, 15, 9]
        BDS_M  = [138, 135, 142]
        BDD_M  = [88, 86, 90]
        TEMP_M = ["37.1", "37.0", "37.2"]

        for idx, h in enumerate(VITAL_HOURS):
            if h <= cur_h:
                k2['spo2'][str(h)]    = str(SPO2_M[idx])
                k2['hf'][str(h)]      = str(HF_M[idx])
                k2['af'][str(h)]      = str(AF_M[idx])
                k2['ipap'][str(h)]    = "18"
                k2['epap'][str(h)]    = "8"
                k2['vt'][str(h)]      = str(VT_M[idx])
                k2['leckage'][str(h)] = str(LK_M[idx])

        for idx, h in enumerate(BD_TEMP_HOURS):
            if h <= cur_h:
                k2['bd_sys'][str(h)] = str(BDS_M[idx])
                k2['bd_dia'][str(h)] = str(BDD_M[idx])
                k2['temp'][str(h)]   = TEMP_M[idx]

        for h, lage in LAGERUNG_PLAN.items():
            if h <= cur_h:
                k2['lagerung'][str(h)] = lage

        if cur_h >= 8:
            k2['inhalation']['8'] = "✓"

        with open(kf2, "w", encoding="utf-8") as f:
            json.dump(k2, f, ensure_ascii=False, indent=2)

    lf2 = os.path.join(DATA_DIR, f"leistungen_{pid2}_{heute}.json")
    if not os.path.exists(lf2):
        with open(lf2, "w", encoding="utf-8") as f:
            json.dump({"GKP_06:30":{"kuerzel":"SK","zeitstempel":"06:35","begruendung":""},
                       "MED_07:00":{"kuerzel":"SK","zeitstempel":"07:05","begruendung":""},
                       "INH_08:00":{"kuerzel":"SK","zeitstempel":"08:10","begruendung":""},
                       "VIT_08:15":{"kuerzel":"SK","zeitstempel":"08:22","begruendung":""},
                       "LAG_10:00":{"kuerzel":"SK","zeitstempel":"10:05","begruendung":""}},
                      f, ensure_ascii=False, indent=2)

    bf2 = os.path.join(DATA_DIR, f"bemerkungen_{pid2}_{heute}.json")
    if not os.path.exists(bf2):
        with open(bf2, "w", encoding="utf-8") as f:
            json.dump([{"zeitstempel":"07:00","kuerzel":"SK","schicht":"Frühdienst",
                "text":"Patientin schläft noch beim Dienstbeginn. Nachtbeatmung wurde um 07:30 abgenommen. "
                       "SpO₂ nach NIV-Abnahme stabil bei 91–94%. Leichte Dyspnoe bei Mobilisation. "
                       "Ödeme an Unterschenkeln bilateral unverändert. Nächste RZV-Kontrolle am Donnerstag."}],
                      f, ensure_ascii=False, indent=2)


def init_demo_therapien():
    pid = "P-2024-0042"
    fname = os.path.join(DATA_DIR, f"therapien_{pid}.json")
    if os.path.exists(fname):
        return
    today = date.today()
    data = {
        "verordnungen": [
            {"id": "t1", "typ": "Physiotherapie", "frequenz": "3x/Woche",  "therapeut": "T. Müller", "seit": "2024-01-15", "ziel": "Muskelerhalt und Atemtherapie"},
            {"id": "t2", "typ": "Ergotherapie",   "frequenz": "2x/Woche",  "therapeut": "S. Klein",  "seit": "2024-02-01", "ziel": "Kommunikation und Alltagsaktivitäten"},
            {"id": "t3", "typ": "Logopädie",      "frequenz": "1x/Woche",  "therapeut": "M. Bauer",  "seit": "2024-03-10", "ziel": "Schluck- und Kommunikationstherapie"},
        ],
        "eintraege": [
            {
                "id": "e1",
                "datum": (today - timedelta(days=1)).strftime("%Y-%m-%d"),
                "uhrzeit": "10:00",
                "typ": "Physiotherapie",
                "therapeut": "T. Müller",
                "bericht": "Atemübungen, passive Mobilisation beider Arme. Patient gut kooperativ. Keine Auffälligkeiten.",
                "kuerzel": "AQ"
            },
            {
                "id": "e2",
                "datum": (today - timedelta(days=3)).strftime("%Y-%m-%d"),
                "uhrzeit": "11:00",
                "typ": "Ergotherapie",
                "therapeut": "S. Klein",
                "bericht": "Kommunikationstraining mit Augensteuerung. Fortschritte beim Buchstabieren erkennbar. Patient motiviert.",
                "kuerzel": "AQ"
            },
            {
                "id": "e3",
                "datum": (today - timedelta(days=5)).strftime("%Y-%m-%d"),
                "uhrzeit": "10:00",
                "typ": "Physiotherapie",
                "therapeut": "T. Müller",
                "bericht": "Atemmuskeltraining und Vibrationstherapie. Patient toleriert Lagerung gut. SpO₂ stabil während gesamter Therapie.",
                "kuerzel": "SK"
            },
            {
                "id": "e4",
                "datum": (today - timedelta(days=8)).strftime("%Y-%m-%d"),
                "uhrzeit": "14:00",
                "typ": "Logopädie",
                "therapeut": "M. Bauer",
                "bericht": "Schlucktherapie. Reflextestung durchgeführt. Empfehlung: Speisen weiterhin püriert reichen. Flüssigkeiten angedickt.",
                "kuerzel": "AQ"
            },
        ]
    }
    with open(fname, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def init_demo_protokolle():
    pid = "P-2024-0042"
    fname = os.path.join(DATA_DIR, f"protokolle_{pid}.json")
    if os.path.exists(fname):
        return
    data = {
        "arztbriefe": [
            {
                "id": "ab1", "datum": "2026-05-15",
                "titel": "Entlassungsbrief",
                "quelle": "Lungenklinik Musterstadt",
                "zusammenfassung": "Stationärer Aufenthalt 10.–15.05.2026. Pneumonie behandelt, Beatmung optimiert.",
                "volltext": "Sehr geehrte Frau Dr. Hoffmann,\n\nwir berichten über den stationären Aufenthalt von Herrn Max Mustermann (geb. 14.03.1958) vom 10.05.2026 bis 15.05.2026.\n\nAufnahmegrund: Exazerbation mit Pneumonie bei bekannter ALS und Beatmungspflichtigkeit.\n\nTherapie: Antibiose mit Amoxicillin/Clavulansäure i.v. für 5 Tage, Optimierung der Beatmungseinstellungen (IPAP erhöht auf 22 mbar). Sekretmanagement intensiviert.\n\nEntlassung in gutem Allgemeinzustand. SpO₂ stabil 95–97% unter bestehender Beatmung.\n\nMit freundlichen kollegialen Grüßen,\nProf. Dr. M. Wagner, Lungenklinik Musterstadt"
            },
            {
                "id": "ab2", "datum": "2026-03-02",
                "titel": "Ambulanzbrief",
                "quelle": "Neurologische Ambulanz (ALS-Zentrum)",
                "zusammenfassung": "Quartalsuntersuchung. ALS-Progression moderat. Empfehlung: Ernährungsberatung.",
                "volltext": "Sehr geehrte Frau Dr. Hoffmann,\n\nwir berichten über die Vorstellung von Herrn Mustermann in unserer ALS-Ambulanz am 02.03.2026.\n\nNeurologischer Befund: Progredienter Verlauf. Deutliche Tetraparese, Dysarthrie zunehmend. Schluckfunktion eingeschränkt. Kommunikation via Augensteuerung.\n\nEmpfehlungen: Ernährungsberatung (PEG-Anlage erwägen), Intensivierung der Logopädie, Fortführung Riluzol 2×50 mg täglich.\n\nNächste Kontrolle in 3 Monaten.\n\nMit freundlichen Grüßen,\nDr. K. Bauer, ALS-Zentrum Musterstadt"
            },
            {
                "id": "ab3", "datum": "2026-01-10",
                "titel": "Beatmungskontrolle",
                "quelle": "Dr. Hoffmann",
                "zusammenfassung": "Beatmungsparameter überprüft. Gerät läuft regelgerecht. TK-Wechsel planmäßig.",
                "volltext": "Hausarztbericht — Beatmungskontrolle 10.01.2026\n\nPatient: Max Mustermann, P-2024-0042\n\nBeatmungsgerät Astral 150 technisch einwandfrei. Parameter wie verordnet. Auslesesoftware zeigt mittlere Nutzungsdauer 9,8 h/Nacht. Leckage im Normbereich.\n\nTrachealkanüle (Shiley 8.0) gewechselt. Nächster Wechsel: 10.02.2026.\n\nAllgemeinzustand stabil. Patient zufrieden mit Beatmungstoleranz.\n\nDr. Elisabeth Hoffmann"
            }
        ],
        "befunde": [
            {
                "id": "bf1", "datum": "2026-06-10",
                "titel": "Röntgen Thorax",
                "quelle": "Radiologie Musterstadt",
                "zusammenfassung": "Keine neuen Infiltrate. Zwerchfelltiefstand beidseits bekannt.",
                "volltext": "Röntgen Thorax a.p. vom 10.06.2026\n\nPatient: Max Mustermann, 68 J.\n\nBefund: Kein Nachweis frischer Infiltrate. Herz queroval, Herzgröße normal. Zwerchfelltiefstand beidseits bei bekanntem Emphysem. Hili unauffällig. TK in korrekter Position.\n\nBeurteilung: Kein Hinweis auf Pneumonie oder Pleuraerguss."
            },
            {
                "id": "bf2", "datum": "2026-04-15",
                "titel": "Blutbild + CRP",
                "quelle": "Labor Musterstadt",
                "zusammenfassung": "Leukozyten leicht erhöht (10,2 G/l). CRP 18 mg/l — Verlaufskontrolle empfohlen.",
                "volltext": "Laborbefund vom 15.04.2026\n\nHämatologie:\n- Leukozyten: 10,2 G/l (↑, Norm: 4,0–9,5)\n- Erythrozyten: 4,8 T/l\n- Hämoglobin: 14,2 g/dl\n- Thrombozyten: 238 G/l\n\nEntzündung:\n- CRP: 18 mg/l (↑, Norm: < 5)\n\nBeurteilung: Leichte Entzündungszeichen. Klinischer Kontext beachten. Verlaufskontrolle in 2 Wochen empfohlen."
            },
            {
                "id": "bf3", "datum": "2026-03-01",
                "titel": "Lungenfunktion",
                "quelle": "Lungenfunktionslabor",
                "zusammenfassung": "FVC 22%, FEV1 18% — schwer reduziert bei bekannter ALS.",
                "volltext": "Lungenfunktionsuntersuchung vom 01.03.2026\n\nFVC: 0,85 l (22 % Soll)\nFEV1: 0,70 l (18 % Soll)\nTiffeneau: 82 %\n\nBeurteilung: Schwere restriktive Ventilationsstörung bei bekannter ALS. Werte progredient verschlechtert im Vergleich zur Voruntersuchung. Beatmungstherapie indiziert und weiterhin erforderlich."
            }
        ],
        "ueberweisungen": [
            {
                "id": "uw1", "datum": "2026-06-20",
                "titel": "Überweisung Neurologie",
                "quelle": "Dr. Hoffmann",
                "zusammenfassung": "Überweisung zur ALS-Quartalsuntersuchung und Kommunikationshilfsmittelberatung.",
                "volltext": "Überweisung vom 20.06.2026\n\nAn: Neurologische Ambulanz, ALS-Zentrum\n\nDiagnose: G12.2 — Amyotrophe Lateralsklerose\n\nBitte um Quartalsuntersuchung. Schwerpunkt: Evaluation Kommunikationshilfsmittel (Augensteuerung), Prüfung PEG-Indikation.\n\nDr. Elisabeth Hoffmann"
            },
            {
                "id": "uw2", "datum": "2026-06-05",
                "titel": "Überweisung Pneumologie",
                "quelle": "Dr. Hoffmann",
                "zusammenfassung": "Beatmungskontrolle und Geräteauslese durch Pneumologen.",
                "volltext": "Überweisung vom 05.06.2026\n\nAn: Pneumologische Praxis Dr. Schmidt\n\nBitte um Auslese des Beatmungsgerätes (Astral 150) und Überprüfung der aktuellen Beatmungsparameter. Letzte Kontrolle vor 3 Monaten.\n\nDr. Elisabeth Hoffmann"
            }
        ],
        "sonstiges": [
            {
                "id": "s1", "datum": "2026-01-01",
                "titel": "Pflegeplanung 2026",
                "quelle": "Pflegeteam",
                "zusammenfassung": "Aktuelle Pflegeplanung und Ziele für 2026.",
                "volltext": "Pflegeplanung — Max Mustermann — Stand: 01.01.2026\n\nPflegeziele:\n1. Beatmungssicherheit gewährleisten\n2. Infektionsprophylaxe (Pneumonieprophylaxe)\n3. Dekubitusprophylaxe (2-stündliche Lagerung)\n4. Kommunikation erhalten (Augensteuerung)\n5. Wohlbefinden und Würde\n\nVerantwortlich: Sandra Krause, Pflegeleitung"
            },
            {
                "id": "s2", "datum": "2025-03-15",
                "titel": "Betreuungsverfügung",
                "quelle": "Max Mustermann / Notar",
                "zusammenfassung": "Patientenverfügung und Vorsorgevollmacht. Ehefrau Maria Mustermann bevollmächtigt.",
                "volltext": "DEMO — Betreuungsverfügung\n\nIn dieser Datei sind Informationen zur Patientenverfügung von Max Mustermann hinterlegt.\n\nBevollmächtigte Person: Maria Mustermann (Ehefrau)\nKontakt: 0151 12345678\n\nZu weiteren Informationen bitte Originaldokument aus der Patientenakte entnehmen.\n\nBeglaubigt: Notar Dr. B. Fischer, Musterstadt"
            }
        ]
    }
    with open(fname, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def init_demo_sis():
    pid = "P-2024-0042"
    fname = os.path.join(DATA_DIR, f"sis_{pid}.json")
    if os.path.exists(fname):
        return
    data = {
        "patient_id": pid,
        "letzte_aktualisierung": "2026-06-20",
        "themenfelder": {
            "kognition": {
                "selbstbeschreibung": "Ich verstehe alles, kann aber kaum sprechen. Ich nutze eine Augensteuerung zum Kommunizieren.",
                "fachliche_einschaetzung": "Patient ist kognitiv vollständig orientiert und wach. Kommunikation ausschließlich über Augensteuerungssystem (Tobii). Versteht komplexe Anweisungen. Gedächtnis und Orientierung intakt.",
                "massnahmen": "Augensteuerung täglich überprüfen und reinigen. Kommunikationstafel als Backup bereithalten. Beim Ansprechen immer Blickkontakt herstellen."
            },
            "mobilitaet": {
                "selbstbeschreibung": "Ich kann mich nicht mehr selbst bewegen. Ich bin vollständig auf Hilfe angewiesen.",
                "fachliche_einschaetzung": "Vollständige Immobilität bei ALS. Tetraparese. Lagerungswechsel alle 2 Stunden erforderlich zur Dekubitusprophylaxe. Anti-Dekubitus-Matratze vorhanden.",
                "massnahmen": "2-stündliche Lagerungswechsel nach Lagerungsplan. Passivbewegungen täglich. Lagerungsprotokoll führen."
            },
            "krankheit": {
                "selbstbeschreibung": "Ich weiß, dass meine Krankheit fortschreitet. Ich habe Angst vor Atemnot.",
                "fachliche_einschaetzung": "ALS mit progredienter Entwicklung. Vollständige Beatmungspflichtigkeit seit 11/2022. Schluckstörung mit pürierter Kost. Neurologische Kontrollen quartalsweise.",
                "massnahmen": "Regelmäßige psychologische Begleitung. Palliativversorgung eingebunden. Notfallplan für Atemnot liegt am Bett."
            },
            "selbstversorgung": {
                "selbstbeschreibung": "Ich brauche bei allem Hilfe — beim Essen, beim Waschen, beim Anziehen.",
                "fachliche_einschaetzung": "Vollpflegebedarf in allen Bereichen. Ganzkörperpflege täglich im Bett. Mundpflege 3x täglich. Ernährung püriert, ggf. PEG-Anlage evaluieren.",
                "massnahmen": "GKP täglich Frühdienst. Mundpflege 3x täglich. Pürierte Kost, angedickte Flüssigkeiten. Hautpflege täglich."
            },
            "soziales": {
                "selbstbeschreibung": "Meine Frau kommt jeden Tag. Das ist mir sehr wichtig.",
                "fachliche_einschaetzung": "Gut eingebundenes Sozialumfeld. Ehefrau täglich anwesend und aktiv in Pflege eingebunden. Sohn besucht regelmäßig.",
                "massnahmen": "Angehörigenbesuche fördern. Ehefrau in Pflegemaßnahmen einweisen. Kommunikation über Augensteuerung erklären."
            },
            "haushalt": {
                "selbstbeschreibung": "Ich lebe in einer Pflegeeinrichtung und muss mir darüber keine Gedanken machen.",
                "fachliche_einschaetzung": "Patient lebt in der Beatmungs-WG Musterstadt. Vollversorgung durch Einrichtung. Wohnumfeld ist behindertengerecht und auf Pflegebedarf angepasst.",
                "massnahmen": "Regelmäßige Überprüfung der Zimmerausstattung. Pflegebettfunktionen täglich kontrollieren. Beleuchtung und Temperatur nach Patientenwunsch."
            }
        }
    }
    with open(fname, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def init_demo_pflegebericht():
    pid = "P-2024-0042"
    fname = os.path.join(DATA_DIR, f"pflegebericht_{pid}.json")
    if os.path.exists(fname):
        return
    today = date.today()
    def d(days_ago):
        return (today - timedelta(days=days_ago)).strftime("%Y-%m-%d")
    data = [
        {"id":"pb1","datum":d(0),"uhrzeit":"08:15","kategorie":"Beatmung",
         "text":"Beatmung regelgerecht. Astral 150 läuft störungsfrei. Leckage 8 L/min, im Normbereich. SpO₂ stabil 95–97%. TK (Shiley 8.0) ohne Auffälligkeiten, Cuffdruck 22 cmH₂O.","kuerzel":"AQ"},
        {"id":"pb2","datum":d(0),"uhrzeit":"07:30","kategorie":"Pflege",
         "text":"GKP durchgeführt. Haut intakt, keine Rötungen oder Druckstellen. Mundpflege mit Chlorhexidin-Lösung. Lagerungswechsel 30° rechts um 07:00 Uhr.","kuerzel":"AQ"},
        {"id":"pb3","datum":d(1),"uhrzeit":"14:30","kategorie":"Besonderheit",
         "text":"SpO₂-Abfall auf 91% bei Lagerungswechsel um 14:00 Uhr. O₂-Gabe auf 3 L/min erhöht. SpO₂ nach 10 Min. wieder bei 95%. Absaugung: weißliches, zähes Sekret. Dr. Hoffmann informiert.","kuerzel":"AQ"},
        {"id":"pb4","datum":d(1),"uhrzeit":"10:00","kategorie":"Allgemein",
         "text":"Patient wach und aufmerksam. Kommuniziert über Augensteuerung. Stimmung ausgeglichen. Ehefrau Maria zu Besuch. Patient äußert, gut geschlafen zu haben.","kuerzel":"SK"},
        {"id":"pb5","datum":d(2),"uhrzeit":"09:00","kategorie":"Arzt informiert",
         "text":"Dr. Hoffmann über erhöhte Sekretmenge informiert. Empfehlung: Inhalation auf 4x täglich erhöhen, Vitalzeichen engmaschig kontrollieren. Laborentnahme für Montag angeordnet.","kuerzel":"AQ"},
        {"id":"pb6","datum":d(3),"uhrzeit":"08:00","kategorie":"Medikamente",
         "text":"Medikamentengabe 07:00 Uhr: Baclofen 10 mg, Riluzol 50 mg (nüchtern), Pantoprazol 40 mg durchgeführt. Einnahme via Löffel (püriert). Keine Schluckprobleme. Lorazepam 0,5 mg für 22:00 bereitgestellt.","kuerzel":"AQ"},
        {"id":"pb7","datum":d(4),"uhrzeit":"16:00","kategorie":"Pflege",
         "text":"TK-Pflege durchgeführt. TK-Kragen gewechselt. Stomabereich gereinigt, keine Rötung. Cuffdruck 22 cmH₂O. Nächster TK-Wechsel planmäßig 12.07.2026.","kuerzel":"SK"},
        {"id":"pb8","datum":d(6),"uhrzeit":"11:30","kategorie":"Allgemein",
         "text":"Physiotherapie durch T. Müller durchgeführt. Passive Mobilisation aller Extremitäten, Atemübungen. Patient toleriert Therapie gut. SpO₂ während der Therapie stabil.","kuerzel":"AQ"},
    ]
    with open(fname, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def init_demo_ereignisse():
    pid = "P-2024-0042"
    fname = os.path.join(DATA_DIR, f"ereignisse_{pid}.json")
    if os.path.exists(fname):
        return
    today = date.today()
    def d(days_ago):
        return (today - timedelta(days=days_ago)).strftime("%Y-%m-%d")
    data = [
        {
            "id": "er1",
            "typ": "Beatmungszwischenfall",
            "datum": d(2), "uhrzeit": "14:22", "ort": "Zimmer 3",
            "beschreibung": "Beatmungsalarm: Leckage plötzlich auf 38 L/min angestiegen. SpO₂-Abfall auf 88%. Patient unruhig, Beatmungsgerät zeigte Diskonnektions-Alarm.",
            "sofortmassnahmen": "Überprüfung aller Beatmungsschläuche. TK-Kragen war leicht verrutscht — Neupositionierung. O₂ auf 4 L/min erhöht. SpO₂ stieg innerhalb 3 Min. wieder auf 94%.",
            "arzt_informiert": True, "arzt_wer": "Dr. Hoffmann", "arzt_wann": "14:25",
            "angehoerige_informiert": False, "angehoerige_wer": "", "angehoerige_wann": "",
            "folgemassnahmen": "TK-Fixierung überprüft und Kragen neu angelegt. Beatmungsschläuche kontrolliert — einwandfrei. Engmaschige Vitalzeichen für 2 Stunden. Bericht an nächste Schicht.",
            "kuerzel": "AQ"
        },
        {
            "id": "er2",
            "typ": "Arzt informiert",
            "datum": d(1), "uhrzeit": "09:10", "ort": "Dienstzimmer",
            "beschreibung": "Telefonische Information an Dr. Hoffmann über zunehmende Sekretmenge seit 48 Stunden. Sekret weißlich-gelblich, zähe Konsistenz, 3–4x täglich absaugpflichtig.",
            "sofortmassnahmen": "Inhalation NaCl 0,9% auf 4x täglich erhöht. Erhöhte Flüssigkeitszufuhr sichergestellt.",
            "arzt_informiert": True, "arzt_wer": "Dr. Hoffmann", "arzt_wann": "09:10",
            "angehoerige_informiert": False, "angehoerige_wer": "", "angehoerige_wann": "",
            "folgemassnahmen": "Laborentnahme für Montag angeordnet. Vitalzeichen alle 2 Stunden. Bei Temperaturerhöhung oder SpO₂ < 92% sofort kontaktieren.",
            "kuerzel": "AQ"
        },
    ]
    with open(fname, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def init_demo_wunden():
    pid = "P-2024-0042"
    fname = os.path.join(DATA_DIR, f"wunden_{pid}.json")
    if os.path.exists(fname):
        return
    today = date.today()
    def d(days_ago):
        return (today - timedelta(days=days_ago)).strftime("%Y-%m-%d")
    data = [
        {
            "id": "w1",
            "typ": "Tracheostomawunde",
            "lokalisation": "Trachea anterior, zervikaler Bereich",
            "erstbefund": "2022-11-01",
            "aktueller_status": "gruen",
            "zusammenfassung": "Tracheostoma seit 11/2022. Reizlos, regelgerecht verheilt. Regelmäßige Pflege und Kontrolle.",
            "verlauf": [
                {"id":"wv1","datum":d(0),"groesse":"","wundgrund":"epithelialisiert","exsudat":"kein",
                 "umgebung":"reizlos","behandlung":"Stomareinigung NaCl 0,9%, sterile Kompressen, TK-Kragen gewechselt","status":"gruen","kuerzel":"AQ"},
                {"id":"wv2","datum":d(7),"groesse":"","wundgrund":"epithelialisiert","exsudat":"gering serös",
                 "umgebung":"leichte Rötung perifokal","behandlung":"Stomareinigung NaCl 0,9%, Betaisodona-Tupfer, TK-Kragen gewechselt. Dr. Hoffmann informiert.","status":"gelb","kuerzel":"SK"},
                {"id":"wv3","datum":d(14),"groesse":"","wundgrund":"epithelialisiert","exsudat":"kein",
                 "umgebung":"reizlos","behandlung":"Routinepflege","status":"gruen","kuerzel":"AQ"}
            ]
        }
    ]
    with open(fname, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def init_demo_maria():
    """Erstellt vollständige Demo-Daten für Maria Musterfrau (P-2024-0043)."""
    pid = "P-2024-0043"
    today = date.today()
    def d(days_ago): return (today - timedelta(days=days_ago)).strftime("%Y-%m-%d")

    # Pflegebericht
    pb_f = os.path.join(DATA_DIR, f"pflegebericht_{pid}.json")
    if not os.path.exists(pb_f):
        data = [
            {"id":"mpb1","datum":d(0),"uhrzeit":"07:15","kategorie":"Allgemein",
             "text":"Patientin hat gut geschlafen. COPD-bedingt erhöhte Atemfrequenz am Morgen (22/min), nach Inhalation gebessert auf 18/min. Allgemeinzustand stabil.",
             "kuerzel":"SK","schmerz":"","lokalisation":""},
            {"id":"mpb2","datum":d(1),"uhrzeit":"09:30","kategorie":"Beatmung",
             "text":"Sekret: zähflüssig, gelblich. Absaugung 3x durchgeführt. Arzt über Sekretbeschaffenheit informiert. Dr. Hoffmann empfiehlt Intensivierung der Inhalation.",
             "kuerzel":"SK","schmerz":"2","lokalisation":"Brust"},
            {"id":"mpb3","datum":d(2),"uhrzeit":"14:00","kategorie":"Pflege",
             "text":"Lagerungswechsel durchgeführt. Patientin kooperativ. SpO₂ stabil bei 92–93% unter Beatmung. Keine Druckstellen. Mobilisation im Bett nach Plan.",
             "kuerzel":"AQ","schmerz":"","lokalisation":""},
        ]
        with open(pb_f, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    # Therapien
    th_f = os.path.join(DATA_DIR, f"therapien_{pid}.json")
    if not os.path.exists(th_f):
        data = {
            "verordnungen": [
                {"id":"mt1","typ":"Atemphysiotherapie","frequenz":"3x/Woche","therapeut":"T. Müller","seit":"2024-04-01","ziel":"Sekretmobilisation und Atemmuskelkräftigung"},
                {"id":"mt2","typ":"Ergotherapie","frequenz":"1x/Woche","therapeut":"S. Klein","seit":"2024-05-15","ziel":"Selbstständigkeit im Alltag erhalten"},
            ],
            "eintraege": [
                {"id":"me1","datum":d(1),"uhrzeit":"10:00","typ":"Atemphysiotherapie","therapeut":"T. Müller",
                 "bericht":"Atemübungen durchgeführt. Vibrationsmassage zur Sekretlösung. Patientin toleriert Maßnahmen gut. Deutliche Sekretmobilisation.","kuerzel":"SK"},
                {"id":"me2","datum":d(4),"uhrzeit":"11:30","typ":"Ergotherapie","therapeut":"S. Klein",
                 "bericht":"Alltagstraining: Trinkbecher selbstständig halten. Feinmotorik leicht eingeschränkt. Übungen für die Hände durchgeführt.","kuerzel":"SK"},
                {"id":"me3","datum":d(5),"uhrzeit":"10:00","typ":"Atemphysiotherapie","therapeut":"T. Müller",
                 "bericht":"Husten- und Atemübungen. PEP-Atemtherapie mit Flutter-VRP1. Patientin sehr motiviert. SpO₂ während Therapie stabil 91-93%.","kuerzel":"AQ"},
            ]
        }
        with open(th_f, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    # Protokolle
    pr_f = os.path.join(DATA_DIR, f"protokolle_{pid}.json")
    if not os.path.exists(pr_f):
        data = {
            "arztbriefe": [
                {"id":"mab1","datum":"2026-05-20","titel":"Pneumologischer Befundbericht",
                 "quelle":"Pneumologische Praxis Dr. Schmidt",
                 "zusammenfassung":"Beatmungskontrolle: CPAP/BiPAP gut toleriert. FEV1 stabil bei 38%. Sauerstoffbedarf unverändert.",
                 "volltext":"Befundbericht vom 20.05.2026\n\nPatientin: Maria Musterfrau, P-2024-0043\n\nDiagnose: COPD Gold IV mit hyperkapnischer Insuffizienz\n\nBeatmungsauslese: Beatmungsgerät Lumis 150 läuft regelgerecht. Mittlere Nutzungsdauer 9,2 h/Nacht. Leckage im Normbereich (12 L/min im Mittel). AHI 2,8/h.\n\nBeatmungseinstellung: IPAP 18 mbar, EPAP 8 mbar, Backup AF 14/min — unverändert adäquat.\n\nEmpfehlung: Beatmungseinstellungen beibehalten. Nächste Kontrolle in 3 Monaten.\n\nDr. P. Schmidt, Pneumologe"},
                {"id":"mab2","datum":"2026-03-10","titel":"Hausarztbrief",
                 "quelle":"Dr. E. Hoffmann",
                 "zusammenfassung":"Quartalskontrolle. COPD stabil. Antibiose abgeschlossen. Ödeme rückläufig.",
                 "volltext":"Hausarzt-Verlaufsbericht 10.03.2026\n\nPatientin: Maria Musterfrau\n\nZustand: Allgemeinzustand gebessert nach Infekt im Februar. Antibiose (Amoxicillin 5 Tage) abgeschlossen. Ödeme an Unterschenkeln rückläufig unter Furosemid.\n\nAtemwerte: SpO₂ 92-94% unter NIV stabil.\n\nFortführung aktuelle Medikation. Nächste Kontrolle in 6 Wochen.\n\nDr. E. Hoffmann"},
            ],
            "befunde": [
                {"id":"mbf1","datum":"2026-04-08","titel":"Lungenfunktion + Blutgas",
                 "quelle":"Pneumologisches Labor",
                 "zusammenfassung":"FEV1 38% Soll. Hyperkapnie kompensiert. pH 7,38, pCO2 52 mmHg.",
                 "volltext":"Lungenfunktionsuntersuchung und Blutgasanalyse 08.04.2026\n\nPatientin: Maria Musterfrau, 80 J.\n\nLungenfunktion:\nFVC: 1,12 l (42 % Soll)\nFEV1: 0,98 l (38 % Soll)\nTiffeneau: 87 %\nBefund: Schwere obstruktive Ventilationsstörung\n\nBlutgas (kapillär):\npH: 7,38\npCO₂: 52 mmHg (mäßige Hyperkapnie, kompensiert)\npO₂: 58 mmHg\nHCO₃: 31 mmol/l\nSaO₂: 91 %\n\nBeurteilung: Bekannte COPD Gold IV mit kompensierter respiratorischer Azidose. NIV-Therapie effektiv."},
            ],
            "ueberweisungen": [
                {"id":"muw1","datum":"2026-06-15","titel":"Überweisung Pneumologie",
                 "quelle":"Dr. E. Hoffmann",
                 "zusammenfassung":"Beatmungskontrolle und Geräteauslese halbjährlich.",
                 "volltext":"Überweisung 15.06.2026\n\nAn: Pneumologische Praxis Dr. Schmidt\n\nDiagnose: J44.1 — COPD mit akuter Exazerbation (stabil)\n\nBitte um Beatmungsauslese Lumis 150 und Überprüfung der Beatmungsparameter (halbjährliche Kontrolle).\n\nDr. E. Hoffmann"},
            ],
            "sonstiges": [
                {"id":"ms1","datum":"2024-06-01","titel":"Pflegeplanung COPD",
                 "quelle":"Pflegeteam",
                 "zusammenfassung":"Pflegeziele und -maßnahmen bei COPD Gold IV.",
                 "volltext":"Pflegeplanung — Maria Musterfrau — Stand: 01.06.2024\n\nPflegeziele:\n1. Atemwegssicherheit und NIV-Compliance sicherstellen\n2. Sekretmanagement optimieren (Inhalation 3x täglich)\n3. Beweglichkeit erhalten (Atemphysiotherapie)\n4. Ödemprophylaxe (Lagerung, Kompression, Furosemid)\n5. Soziale Teilhabe fördern (Sohn besucht regelmäßig)\n\nVerantwortlich: Sandra Krause, Pflegeleitung"},
            ]
        }
        with open(pr_f, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


ensure_demo_patients()
init_demo_data()
init_demo_therapien()
init_demo_protokolle()
init_demo_sis()
init_demo_pflegebericht()
init_demo_ereignisse()
init_demo_wunden()
init_demo_maria()

# ──────────────────────────────────────────
# CONTEXT PROCESSOR
# ──────────────────────────────────────────

@app.context_processor
def inject_global():
    comp = DocumentationCompliance()
    pid  = session.get('patient_id', 'P-2024-0042')
    cfg  = load_config()

    all_p = []
    for p in cfg.get('patienten', []):
        demo = DEMO_PATIENTEN.get(p['id'], {})
        diag = p.get('diagnose', demo.get('diagnose', ''))
        diag_kurz = diag[:30] + ('…' if len(diag) > 30 else '')
        all_p.append({
            "id":          p['id'],
            "name":        p.get('name',    demo.get('name',    '?')),
            "zimmer":      p.get('zimmer',  demo.get('zimmer',  '—')),
            "station":     p.get('station', demo.get('station', '')),
            "diagnose_kurz": diag_kurz,
        })

    nav_patient = None
    for p in cfg.get('patienten', []):
        if p['id'] == pid:
            demo = DEMO_PATIENTEN.get(pid, {})
            nav_patient = {**demo, **p}
            break
    if nav_patient is None:
        nav_patient = DEMO_PATIENTEN.get(pid, DEMO_PATIENTEN['P-2024-0042'])

    return {
        "nav_compliance_status": comp.get_overall_status(),
        "nav_compliance_count":  comp.get_overdue_count(),
        "nav_patient":           nav_patient,
        "current_patient_id":    pid,
        "all_patienten":         all_p,
    }

# ──────────────────────────────────────────
# ROUTEN
# ──────────────────────────────────────────

@app.route("/ping")
def ping():
    return jsonify({"ok": True})

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/switch_patient/<patient_id>")
def switch_patient(patient_id):
    cfg = load_config()
    valid_ids = {p['id'] for p in cfg.get('patienten', [])}
    if patient_id in valid_ids:
        session['patient_id'] = patient_id
    return redirect(request.referrer or url_for('dashboard'))

@app.route("/dashboard")
def dashboard():
    patient = get_current_patient()
    pid = patient['id']
    kurve_werte = get_kurve_letzt_werte(pid)
    leistungen = get_demo_leistungen(pid)
    offen = sum(1 for l in leistungen if not l["bestaetigt"])
    uebergabe = get_uebergabe_check(pid)
    comp = DocumentationCompliance()
    letzter = {
        'spo2':        safe_num(kurve_werte.get('spo2'), 96),
        'puls':        int(safe_num(kurve_werte.get('hf'), 72)),
        'blutdruck':   f"{int(safe_num(kurve_werte.get('bd_sys'),118))}/{int(safe_num(kurve_werte.get('bd_dia'),76))}",
        'tidalvolumen':int(safe_num(kurve_werte.get('vt'), 600)),
        'leckage':     int(safe_num(kurve_werte.get('leckage'), 8)),
        'ipap':        int(safe_num(kurve_werte.get('ipap'), 22)),
    }
    return render_template("dashboard.html",
        patient=patient,
        letzter=letzter,
        leistungen_offen=offen,
        warnungen=uebergabe["warnungen"],
        compliance=comp.get_status(),
        compliance_status=comp.get_overall_status(),
        compliance_next=comp.get_next_due(),
        aktiv="dashboard"
    )

@app.route("/intensivkurve")
def intensivkurve():
    patient = get_current_patient()
    return render_template("intensivkurve.html",
        patient=patient,
        heute=date.today().strftime("%Y-%m-%d"),
        stunden=list(range(7, 23)),
        aktiv="intensivkurve"
    )

@app.route("/api/kurve/save", methods=["POST"])
def api_kurve_save():
    payload = request.get_json(force=True)
    pid   = get_current_patient_id()
    datum = payload.get("datum", date.today().strftime("%Y-%m-%d"))
    data  = payload.get("data", {})
    fname = os.path.join(DATA_DIR, f"kurve_{pid}_{datum}.json")
    with open(fname, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return jsonify({"ok": True})

@app.route("/api/kurve/load")
def api_kurve_load():
    pid   = get_current_patient_id()
    datum = request.args.get("datum", date.today().strftime("%Y-%m-%d"))
    fname = os.path.join(DATA_DIR, f"kurve_{pid}_{datum}.json")
    if os.path.exists(fname):
        with open(fname, encoding="utf-8") as f:
            return jsonify(json.load(f))
    return jsonify({})

@app.route("/leistungsnachweis")
def leistungsnachweis():
    patient = get_current_patient()
    pid = patient['id']
    leistungen = get_demo_leistungen(pid)
    bestaetigt = sum(1 for l in leistungen if l["bestaetigt"])
    return render_template("leistungsnachweis.html",
        patient=patient,
        leistungen=leistungen,
        bestaetigt=bestaetigt,
        gesamt=len(leistungen),
        heute_str=date.today().strftime("%d.%m.%Y"),
        aktiv="leistungsnachweis"
    )

@app.route("/api/naechste-aktionen")
def api_naechste_aktionen():
    pid = get_current_patient_id()
    leistungen = get_demo_leistungen(pid)
    signoffs = get_leistungen_signoffs(pid)
    now = datetime.now()
    now_min = now.hour * 60 + now.minute
    upcoming = []
    for l in leistungen:
        lid = f"{l['kuerzel']}_{l['zeit']}"
        if lid in signoffs:
            continue
        try:
            h, m = l['zeit'].split(':')
            due_min = int(h) * 60 + int(m)
        except Exception:
            continue
        minutes_to_due = due_min - now_min
        if -30 <= minutes_to_due <= 120:
            upcoming.append({
                "leistung": l['leistung'],
                "zeit": l['zeit'],
                "kuerzel": l['kuerzel'],
                "btm": l.get('btm', False),
                "minutes_to_due": minutes_to_due
            })
    upcoming.sort(key=lambda x: x['minutes_to_due'])
    return jsonify(upcoming[:4])

@app.route("/beatmungsverordnung")
def beatmungsverordnung():
    patient = get_current_patient()
    return render_template("beatmungsverordnung.html",
        patient=patient,
        verordnung=get_current_verordnung(),
        aktiv="beatmungsverordnung"
    )

@app.route("/medikamentenplan")
def medikamentenplan():
    patient = get_current_patient()
    return render_template("medikamentenplan.html",
        patient=patient,
        medikamente=DEMO_MEDIKAMENTENPLAN,
        heute_str=date.today().strftime("%d.%m.%Y"),
        aktiv="medikamentenplan"
    )

@app.route("/uebergabe")
def uebergabe():
    patient = get_current_patient()
    pid = patient['id']
    check       = get_uebergabe_check(pid)
    leistungen  = get_demo_leistungen(pid)
    kurve_letzt = get_kurve_letzt_werte(pid)
    bemerkungen = get_bemerkungen_data(pid)
    verordnung  = get_current_verordnung()
    comp        = DocumentationCompliance()
    vitalwerte  = [{"spo2": int(safe_num(kurve_letzt.get('spo2'), 96)),
                    "puls": int(safe_num(kurve_letzt.get('hf'), 72)),
                    "blutdruck": f"{int(safe_num(kurve_letzt.get('bd_sys'),118))}/{int(safe_num(kurve_letzt.get('bd_dia'),76))}",
                    "tidalvolumen": int(safe_num(kurve_letzt.get('vt'), 600)),
                    "leckage": int(safe_num(kurve_letzt.get('leckage'), 8)),
                    "zeit": kurve_letzt.get('spo2_uhr', '—') or '—'}]
    return render_template("uebergabe.html",
        patient=patient,
        check=check,
        leistungen=leistungen,
        vitalwerte=vitalwerte,
        kurve_letzt=kurve_letzt,
        bemerkungen=bemerkungen,
        verordnung=verordnung,
        medikamente=DEMO_MEDIKAMENTENPLAN,
        compliance=comp.get_status(),
        compliance_status=comp.get_overall_status(),
        compliance_count=comp.get_overdue_count(),
        aktiv="uebergabe"
    )

@app.route("/arztuebergabe")
def arztuebergabe():
    patient    = get_current_patient()
    pid        = patient['id']
    verordnung = get_current_verordnung()
    verlauf    = get_demo_verlauf_14_tage(pid)
    kurve_letzt = get_kurve_letzt_werte(pid)
    heute_str  = date.today().strftime("%d.%m.%Y")
    spo2_list  = [v['spo2_avg'] for v in verlauf]
    return render_template("arztuebergabe.html",
        patient=patient,
        verordnung=verordnung,
        medikamente=DEMO_MEDIKAMENTENPLAN,
        verlauf=verlauf,
        kurve_letzt=kurve_letzt,
        heute_str=heute_str,
        spo2_gesamt_avg=round(sum(spo2_list)/len(spo2_list), 1) if spo2_list else 96,
        spo2_gesamt_min=min(v['spo2_min'] for v in verlauf),
        spo2_gesamt_max=max(v['spo2_max'] for v in verlauf),
        hf_gesamt_avg=round(sum(v['hf_avg'] for v in verlauf)/len(verlauf), 1),
        hf_gesamt_min=min(v['hf_min'] for v in verlauf),
        hf_gesamt_max=max(v['hf_max'] for v in verlauf),
        aktiv="arztuebergabe"
    )

@app.route("/api/vitalwerte")
def api_vitalwerte():
    pid = get_current_patient_id()
    kurve = get_kurve_letzt_werte(pid)
    return jsonify([{
        "zeit": kurve.get('spo2_uhr','—') or '—',
        "spo2": int(safe_num(kurve.get('spo2'), 96)),
        "puls": int(safe_num(kurve.get('hf'), 72)),
        "blutdruck": f"{int(safe_num(kurve.get('bd_sys'),118))}/{int(safe_num(kurve.get('bd_dia'),76))}",
        "atemfrequenz": int(safe_num(kurve.get('af'), 15)),
        "tidalvolumen": int(safe_num(kurve.get('vt'), 600)),
        "leckage": int(safe_num(kurve.get('leckage'), 8)),
        "ipap": int(safe_num(kurve.get('ipap'), 22)),
    }])

# ──────────────────────────────────────────
# THERAPIEN
# ──────────────────────────────────────────

@app.route("/therapien")
def therapien():
    patient = get_current_patient()
    pid = patient['id']
    daten = get_therapien_data(pid)
    eintraege = sorted(daten.get('eintraege', []),
                       key=lambda x: (x.get('datum', ''), x.get('uhrzeit', '')),
                       reverse=True)
    return render_template("therapien.html",
        patient=patient,
        verordnungen=daten.get('verordnungen', []),
        eintraege=eintraege,
        aktiv="therapien"
    )

@app.route("/api/therapie/eintrag", methods=["POST"])
def api_therapie_eintrag():
    payload = request.get_json(force=True)
    pid = get_current_patient_id()
    fname = os.path.join(DATA_DIR, f"therapien_{pid}.json")
    daten = get_therapien_data(pid)
    eintraege = daten.get('eintraege', [])
    new_id = f"e{len(eintraege)+1}_{int(datetime.now().timestamp())}"
    eintrag = {
        "id": new_id,
        "datum":     payload.get("datum",     date.today().strftime("%Y-%m-%d")),
        "uhrzeit":   payload.get("uhrzeit",   datetime.now().strftime("%H:%M")),
        "typ":       payload.get("typ",       ""),
        "therapeut": payload.get("therapeut", ""),
        "bericht":   payload.get("bericht",   ""),
        "kuerzel":   payload.get("kuerzel",   "")
    }
    eintraege.append(eintrag)
    daten['eintraege'] = eintraege
    with open(fname, "w", encoding="utf-8") as f:
        json.dump(daten, f, ensure_ascii=False, indent=2)
    return jsonify({"ok": True, "eintrag": eintrag})

@app.route("/api/therapie/verordnung", methods=["POST"])
def api_therapie_verordnung():
    payload = request.get_json(force=True)
    pid = get_current_patient_id()
    fname = os.path.join(DATA_DIR, f"therapien_{pid}.json")
    daten = get_therapien_data(pid)
    verordnungen = daten.get('verordnungen', [])
    new_id = f"v{len(verordnungen)+1}_{int(datetime.now().timestamp())}"
    verordnung = {
        "id":        new_id,
        "typ":       payload.get("typ",       ""),
        "frequenz":  payload.get("frequenz",  ""),
        "therapeut": payload.get("therapeut", ""),
        "seit":      payload.get("seit",      ""),
        "ziel":      payload.get("ziel",      "")
    }
    verordnungen.append(verordnung)
    daten['verordnungen'] = verordnungen
    with open(fname, "w", encoding="utf-8") as f:
        json.dump(daten, f, ensure_ascii=False, indent=2)
    return jsonify({"ok": True, "verordnung": verordnung})

# ──────────────────────────────────────────
# PROTOKOLLE & DOKUMENTE
# ──────────────────────────────────────────

@app.route("/protokolle")
def protokolle():
    patient = get_current_patient()
    pid = patient['id']
    daten = get_protokolle_data(pid)
    # Flat lookup dict for client-side JS
    alle_docs = {}
    for kat, docs in daten.items():
        if isinstance(docs, list):
            for d in docs:
                alle_docs[d['id']] = d
    return render_template("protokolle.html",
        patient=patient,
        arztbriefe=daten.get('arztbriefe', []),
        befunde=daten.get('befunde', []),
        ueberweisungen=daten.get('ueberweisungen', []),
        sonstiges=daten.get('sonstiges', []),
        protokolle_json=json.dumps(alle_docs, ensure_ascii=False),
        aktiv="protokolle"
    )

@app.route("/api/protokoll/hinzufuegen", methods=["POST"])
def api_protokoll_hinzufuegen():
    payload = request.get_json(force=True)
    pid = get_current_patient_id()
    fname = os.path.join(DATA_DIR, f"protokolle_{pid}.json")
    daten = get_protokolle_data(pid)
    kategorie = payload.get("kategorie", "sonstiges")
    if kategorie not in ["arztbriefe", "befunde", "ueberweisungen", "sonstiges"]:
        kategorie = "sonstiges"
    liste = daten.get(kategorie, [])
    new_id = f"{kategorie[0]}{len(liste)+1}_{int(datetime.now().timestamp())}"
    doc = {
        "id":              new_id,
        "datum":           payload.get("datum",           date.today().strftime("%Y-%m-%d")),
        "titel":           payload.get("titel",           ""),
        "quelle":          payload.get("quelle",          ""),
        "zusammenfassung": payload.get("zusammenfassung", ""),
        "volltext":        payload.get("volltext",        "")
    }
    liste.append(doc)
    daten[kategorie] = liste
    with open(fname, "w", encoding="utf-8") as f:
        json.dump(daten, f, ensure_ascii=False, indent=2)
    return jsonify({"ok": True, "dokument": doc})

# ──────────────────────────────────────────
# LEISTUNGEN ABZEICHNEN
# ──────────────────────────────────────────

@app.route("/api/leistung/abzeichnen", methods=["POST"])
def api_leistung_abzeichnen():
    payload = request.get_json(force=True)
    pid     = get_current_patient_id()
    datum   = date.today().strftime("%Y-%m-%d")
    fname   = os.path.join(DATA_DIR, f"leistungen_{pid}_{datum}.json")
    signoffs = json.load(open(fname, encoding="utf-8")) if os.path.exists(fname) else {}
    zeitstempel = datetime.now().strftime("%H:%M")
    entry = {
        "kuerzel":     payload.get("kuerzel",     ""),
        "zeitstempel": zeitstempel,
        "begruendung": payload.get("begruendung", "")
    }
    if payload.get("kuerzel2"):
        entry["kuerzel2"]    = payload.get("kuerzel2")
        entry["restmenge_ok"] = bool(payload.get("restmenge_ok", False))
    signoffs[payload.get("id","")] = entry
    with open(fname, "w", encoding="utf-8") as f:
        json.dump(signoffs, f, ensure_ascii=False, indent=2)
    return jsonify({"ok": True, "zeitstempel": zeitstempel})

@app.route("/api/leistung/status")
def api_leistung_status():
    pid   = get_current_patient_id()
    datum = date.today().strftime("%Y-%m-%d")
    fname = os.path.join(DATA_DIR, f"leistungen_{pid}_{datum}.json")
    if os.path.exists(fname):
        with open(fname, encoding="utf-8") as f:
            return jsonify(json.load(f))
    return jsonify({})

# ──────────────────────────────────────────
# SCHICHTBEMERKUNGEN
# ──────────────────────────────────────────

@app.route("/api/bemerkung/speichern", methods=["POST"])
def api_bemerkung_speichern():
    payload = request.get_json(force=True)
    pid     = get_current_patient_id()
    datum   = date.today().strftime("%Y-%m-%d")
    fname   = os.path.join(DATA_DIR, f"bemerkungen_{pid}_{datum}.json")
    bm = json.load(open(fname, encoding="utf-8")) if os.path.exists(fname) else []
    eintrag = {"zeitstempel": datetime.now().strftime("%H:%M"),
               "kuerzel": payload.get("kuerzel",""),
               "schicht":  payload.get("schicht",""),
               "text":     payload.get("text","")}
    bm.append(eintrag)
    with open(fname, "w", encoding="utf-8") as f:
        json.dump(bm, f, ensure_ascii=False, indent=2)
    return jsonify({"ok": True, "eintrag": eintrag})

@app.route("/api/bemerkung/laden")
def api_bemerkung_laden():
    pid   = get_current_patient_id()
    datum = date.today().strftime("%Y-%m-%d")
    fname = os.path.join(DATA_DIR, f"bemerkungen_{pid}_{datum}.json")
    if os.path.exists(fname):
        with open(fname, encoding="utf-8") as f:
            return jsonify(json.load(f))
    return jsonify([])

# ──────────────────────────────────────────
# ADMIN / CONFIG
# ──────────────────────────────────────────

@app.route("/admin")
def admin():
    return render_template("admin.html", aktiv="admin")

@app.route("/api/config")
def api_config_get():
    return jsonify(load_config())

@app.route("/api/config/save", methods=["POST"])
def api_config_save():
    data = request.get_json(force=True)
    existing_cfg = load_config()
    existing_ids = {p['id'] for p in existing_cfg.get('patienten', [])}
    save_config(data)
    # Create data files for newly added patients
    heute = date.today().strftime("%Y-%m-%d")
    neue_ids = []
    for p in data.get('patienten', []):
        pid = p.get('id', '')
        if pid and pid not in existing_ids:
            neue_ids.append(pid)
            kf = os.path.join(DATA_DIR, f"kurve_{pid}_{heute}.json")
            if not os.path.exists(kf):
                k = {key: {} for key in ['spo2','hf','bd_sys','bd_dia','af','ipap','epap','vt','leckage','lagerung','temp','inhalation']}
                with open(kf, "w", encoding="utf-8") as f:
                    json.dump(k, f, ensure_ascii=False, indent=2)
            lf = os.path.join(DATA_DIR, f"leistungen_{pid}_{heute}.json")
            if not os.path.exists(lf):
                with open(lf, "w", encoding="utf-8") as f:
                    json.dump({}, f)
    return jsonify({"ok": True, "neue_patienten": neue_ids})

@app.route("/api/config/patient/<patient_id>/intervalle")
def api_patient_intervalle(patient_id):
    cfg = load_config()
    for p in cfg.get("patienten", []):
        if p.get("id") == patient_id:
            iv = p.get("intervalle", {})
            defaults = {"spo2":2,"hf":2,"bd_sys":4,"bd_dia":4,"af":2,"beatmung":2,"vt":2,"leckage":2,"lagerung":2}
            defaults.update(iv)
            return jsonify(defaults)
    return jsonify({"spo2":2,"hf":2,"bd_sys":4,"bd_dia":4,"af":2,"beatmung":2,"vt":2,"leckage":2,"lagerung":2})

@app.route("/api/patient/hinzufuegen", methods=["POST"])
def api_patient_hinzufuegen():
    payload = request.get_json(force=True)
    cfg = load_config()
    existing_ids = {p['id'] for p in cfg.get('patienten', [])}
    vorschlag_id = f"P-{date.today().year}-{(len(cfg.get('patienten', []))+1):04d}"
    neue_id = payload.get("id", vorschlag_id)
    if neue_id in existing_ids:
        return jsonify({"ok": False, "error": f"ID {neue_id} existiert bereits"}), 400
    neuer_patient = {
        "id":              neue_id,
        "name":            payload.get("name", ""),
        "geburtsdatum":    payload.get("geburtsdatum", ""),
        "zimmer":          payload.get("zimmer", ""),
        "diagnose":        payload.get("diagnose", ""),
        "beatmungsgeraet": payload.get("beatmungsgeraet", ""),
        "beatmungspflichtig": payload.get("beatmungspflichtig", False),
        "aktiv":           True,
        "station":         payload.get("station", ""),
        "arzt":            payload.get("arzt", ""),
        "intervalle": {"spo2":2,"hf":2,"bd_sys":4,"bd_dia":4,"af":2,"beatmung":2,"vt":2,"leckage":2,"lagerung":2}
    }
    cfg['patienten'].append(neuer_patient)
    save_config(cfg)
    # Leere Tagesdaten für neuen Patienten anlegen
    heute = date.today().strftime("%Y-%m-%d")
    kf = os.path.join(DATA_DIR, f"kurve_{neue_id}_{heute}.json")
    if not os.path.exists(kf):
        k = {key: {} for key in ['spo2','hf','bd_sys','bd_dia','af','ipap','epap','vt','leckage','lagerung','temp','inhalation']}
        with open(kf, "w", encoding="utf-8") as f:
            json.dump(k, f, ensure_ascii=False, indent=2)
    lf = os.path.join(DATA_DIR, f"leistungen_{neue_id}_{heute}.json")
    if not os.path.exists(lf):
        with open(lf, "w", encoding="utf-8") as f:
            json.dump({}, f)
    session['patient_id'] = neue_id
    return jsonify({"ok": True, "patient": neuer_patient, "patient_id": neue_id, "redirect": "/dashboard"})

@app.route("/api/patient/session", methods=["POST"])
def api_patient_session():
    payload = request.get_json(force=True)
    patient_id = payload.get("patient_id", "")
    cfg = load_config()
    valid_ids = {p['id'] for p in cfg.get('patienten', [])}
    if patient_id in valid_ids:
        session['patient_id'] = patient_id
        return jsonify({"ok": True})
    return jsonify({"ok": False}), 400

@app.route("/api/config/patienten")
def api_config_patienten():
    cfg = load_config()
    return jsonify(cfg.get("patienten", []))

# ──────────────────────────────────────────
# LÖSCHEN-ROUTEN
# ──────────────────────────────────────────

@app.route("/api/therapie/eintrag/<eintrag_id>", methods=["DELETE", "PUT"])
def api_therapie_eintrag_update(eintrag_id):
    pid = get_current_patient_id()
    fname = os.path.join(DATA_DIR, f"therapien_{pid}.json")
    daten = get_therapien_data(pid)
    if request.method == "DELETE":
        daten['eintraege'] = [e for e in daten.get('eintraege', []) if e.get('id') != eintrag_id]
        with open(fname, "w", encoding="utf-8") as f:
            json.dump(daten, f, ensure_ascii=False, indent=2)
        return jsonify({"ok": True})
    # PUT — update existing entry
    payload = request.get_json(force=True)
    for e in daten.get('eintraege', []):
        if e.get('id') == eintrag_id:
            e['datum']     = payload.get('datum', e.get('datum', ''))
            e['uhrzeit']   = payload.get('uhrzeit', e.get('uhrzeit', ''))
            e['typ']       = payload.get('typ', e.get('typ', ''))
            e['therapeut'] = payload.get('therapeut', e.get('therapeut', ''))
            e['bericht']   = payload.get('bericht', e.get('bericht', ''))
            e['kuerzel']   = payload.get('kuerzel', e.get('kuerzel', ''))
            break
    with open(fname, "w", encoding="utf-8") as f:
        json.dump(daten, f, ensure_ascii=False, indent=2)
    return jsonify({"ok": True})

@app.route("/api/therapie/verordnung/<verordnung_id>", methods=["DELETE", "PUT"])
def api_therapie_verordnung_update(verordnung_id):
    pid = get_current_patient_id()
    fname = os.path.join(DATA_DIR, f"therapien_{pid}.json")
    daten = get_therapien_data(pid)
    if request.method == "DELETE":
        daten['verordnungen'] = [v for v in daten.get('verordnungen', []) if v.get('id') != verordnung_id]
        with open(fname, "w", encoding="utf-8") as f:
            json.dump(daten, f, ensure_ascii=False, indent=2)
        return jsonify({"ok": True})
    # PUT — update existing verordnung
    payload = request.get_json(force=True)
    for v in daten.get('verordnungen', []):
        if v.get('id') == verordnung_id:
            v['typ']       = payload.get('typ', v.get('typ', ''))
            v['frequenz']  = payload.get('frequenz', v.get('frequenz', ''))
            v['therapeut'] = payload.get('therapeut', v.get('therapeut', ''))
            v['seit']      = payload.get('seit', v.get('seit', ''))
            v['ziel']      = payload.get('ziel', v.get('ziel', ''))
            break
    with open(fname, "w", encoding="utf-8") as f:
        json.dump(daten, f, ensure_ascii=False, indent=2)
    return jsonify({"ok": True})

@app.route("/api/protokoll/<kategorie>/<dok_id>", methods=["DELETE"])
def api_protokoll_loeschen(kategorie, dok_id):
    if kategorie not in ["arztbriefe", "befunde", "ueberweisungen", "sonstiges"]:
        return jsonify({"ok": False, "error": "Ungültige Kategorie"}), 400
    pid = get_current_patient_id()
    fname = os.path.join(DATA_DIR, f"protokolle_{pid}.json")
    daten = get_protokolle_data(pid)
    daten[kategorie] = [d for d in daten.get(kategorie, []) if d.get('id') != dok_id]
    with open(fname, "w", encoding="utf-8") as f:
        json.dump(daten, f, ensure_ascii=False, indent=2)
    return jsonify({"ok": True})

@app.route("/api/leistung/rueckgaengig", methods=["POST"])
def api_leistung_rueckgaengig():
    payload = request.get_json(force=True)
    leistung_id = payload.get("id", "")
    pid = get_current_patient_id()
    datum = date.today().strftime("%Y-%m-%d")
    fname = os.path.join(DATA_DIR, f"leistungen_{pid}_{datum}.json")
    signoffs = json.load(open(fname, encoding="utf-8")) if os.path.exists(fname) else {}
    if leistung_id not in signoffs:
        return jsonify({"ok": False, "error": "Eintrag nicht gefunden"}), 404
    zeitstempel = signoffs[leistung_id].get("zeitstempel", "")
    try:
        h, m = map(int, zeitstempel.split(":"))
        jetzt = datetime.now()
        sign_dt = jetzt.replace(hour=h, minute=m, second=0, microsecond=0)
        diff = (jetzt - sign_dt).total_seconds()
        if diff > 600:
            return jsonify({"ok": False, "error": "Rückgängig nur innerhalb von 10 Minuten möglich"}), 400
    except Exception:
        pass
    del signoffs[leistung_id]
    with open(fname, "w", encoding="utf-8") as f:
        json.dump(signoffs, f, ensure_ascii=False, indent=2)
    return jsonify({"ok": True})

@app.route("/api/kurve/zelle-loeschen", methods=["POST"])
def api_kurve_zelle_loeschen():
    payload = request.get_json(force=True)
    pid   = get_current_patient_id()
    datum = payload.get("datum", date.today().strftime("%Y-%m-%d"))
    key   = payload.get("key", "")
    stunde = str(payload.get("hour", payload.get("stunde", "")))
    fname = os.path.join(DATA_DIR, f"kurve_{pid}_{datum}.json")
    if os.path.exists(fname):
        with open(fname, encoding="utf-8") as f:
            kurve = json.load(f)
        if key in kurve and stunde in kurve[key]:
            del kurve[key][stunde]
        with open(fname, "w", encoding="utf-8") as f:
            json.dump(kurve, f, ensure_ascii=False, indent=2)
    return jsonify({"ok": True})

# ──────────────────────────────────────────
# PROJEKT-PRÄSENTATION
# ──────────────────────────────────────────

@app.route("/projekt")
def projekt():
    return render_template("projekt.html", aktiv="projekt")

# ──────────────────────────────────────────
# SIS
# ──────────────────────────────────────────

SIS_FELDER = [
    ("kognition",        "Kognition und Kommunikation"),
    ("mobilitaet",       "Mobilität und Beweglichkeit"),
    ("krankheit",        "Krankheitsbezogene Anforderungen"),
    ("selbstversorgung", "Selbstversorgung"),
    ("soziales",         "Soziale Kontakte"),
    ("haushalt",         "Haushaltsführung und Wohnen"),
]

@app.route("/sis")
def sis():
    patient = get_current_patient()
    pid = patient['id']
    sis_data = get_sis_data(pid)
    themenfelder = sis_data.get("themenfelder", {})
    ausgefuellt = sum(1 for key, _ in SIS_FELDER
                      if themenfelder.get(key, {}).get("fachliche_einschaetzung", "").strip())
    return render_template("sis.html",
        patient=patient,
        sis=themenfelder,
        sis_felder=SIS_FELDER,
        ausgefuellt=ausgefuellt,
        letzte_aktualisierung=sis_data.get("letzte_aktualisierung", ""),
        aktiv="sis"
    )

@app.route("/api/sis/speichern", methods=["POST"])
def api_sis_speichern():
    payload = request.get_json(force=True)
    pid = get_current_patient_id()
    fname = os.path.join(DATA_DIR, f"sis_{pid}.json")
    sis_data = get_sis_data(pid)
    themenfelder = sis_data.get("themenfelder", {})
    for key, val in payload.get("themenfelder", {}).items():
        if key not in themenfelder:
            themenfelder[key] = {}
        themenfelder[key].update(val)
    sis_data["themenfelder"] = themenfelder
    sis_data["letzte_aktualisierung"] = date.today().strftime("%Y-%m-%d")
    sis_data["patient_id"] = pid
    with open(fname, "w", encoding="utf-8") as f:
        json.dump(sis_data, f, ensure_ascii=False, indent=2)
    return jsonify({"ok": True})

# ──────────────────────────────────────────
# PFLEGEBERICHT
# ──────────────────────────────────────────

@app.route("/pflegebericht")
def pflegebericht():
    patient = get_current_patient()
    pid = patient['id']
    eintraege = get_pflegebericht_data(pid)
    eintraege_sorted = sorted(eintraege, key=lambda x: (x.get('datum',''), x.get('uhrzeit','')), reverse=True)
    return render_template("pflegebericht.html",
        patient=patient,
        eintraege=eintraege_sorted,
        aktiv="pflegebericht"
    )

@app.route("/api/pflegebericht/eintrag", methods=["POST"])
def api_pflegebericht_eintrag():
    payload = request.get_json(force=True)
    pid = get_current_patient_id()
    fname = os.path.join(DATA_DIR, f"pflegebericht_{pid}.json")
    eintraege = get_pflegebericht_data(pid)
    new_id = f"pb{len(eintraege)+1}_{int(datetime.now().timestamp())}"
    eintrag = {
        "id":          new_id,
        "datum":       payload.get("datum",       date.today().strftime("%Y-%m-%d")),
        "uhrzeit":     payload.get("uhrzeit",     datetime.now().strftime("%H:%M")),
        "kategorie":   payload.get("kategorie",   "Allgemein"),
        "text":        payload.get("text",        ""),
        "kuerzel":     payload.get("kuerzel",     ""),
        "schmerz":     payload.get("schmerz",     ""),
        "lokalisation": payload.get("lokalisation", "")
    }
    eintraege.append(eintrag)
    with open(fname, "w", encoding="utf-8") as f:
        json.dump(eintraege, f, ensure_ascii=False, indent=2)
    return jsonify({"ok": True, "eintrag": eintrag})

@app.route("/api/pflegebericht/eintrag/<eintrag_id>", methods=["PUT", "DELETE"])
def api_pflegebericht_eintrag_update(eintrag_id):
    pid = get_current_patient_id()
    fname = os.path.join(DATA_DIR, f"pflegebericht_{pid}.json")
    eintraege = get_pflegebericht_data(pid)
    if request.method == "DELETE":
        eintraege = [e for e in eintraege if e.get('id') != eintrag_id]
        with open(fname, "w", encoding="utf-8") as f:
            json.dump(eintraege, f, ensure_ascii=False, indent=2)
        return jsonify({"ok": True})
    payload = request.get_json(force=True)
    for e in eintraege:
        if e.get('id') == eintrag_id:
            e['datum']        = payload.get('datum',        e.get('datum', ''))
            e['uhrzeit']      = payload.get('uhrzeit',      e.get('uhrzeit', ''))
            e['kategorie']    = payload.get('kategorie',    e.get('kategorie', ''))
            e['text']         = payload.get('text',         e.get('text', ''))
            e['kuerzel']      = payload.get('kuerzel',      e.get('kuerzel', ''))
            e['schmerz']      = payload.get('schmerz',      e.get('schmerz', ''))
            e['lokalisation'] = payload.get('lokalisation', e.get('lokalisation', ''))
            break
    with open(fname, "w", encoding="utf-8") as f:
        json.dump(eintraege, f, ensure_ascii=False, indent=2)
    return jsonify({"ok": True})

# ──────────────────────────────────────────
# EREIGNISDOKUMENTATION
# ──────────────────────────────────────────

@app.route("/ereignisse")
def ereignisse():
    patient = get_current_patient()
    pid = patient['id']
    ereignisse_liste = get_ereignisse_data(pid)
    ereignisse_sorted = sorted(ereignisse_liste, key=lambda x: (x.get('datum',''), x.get('uhrzeit','')), reverse=True)
    return render_template("ereignisse.html",
        patient=patient,
        ereignisse=ereignisse_sorted,
        aktiv="ereignisse"
    )

@app.route("/api/ereignis/neu", methods=["POST"])
def api_ereignis_neu():
    payload = request.get_json(force=True)
    pid = get_current_patient_id()
    fname = os.path.join(DATA_DIR, f"ereignisse_{pid}.json")
    ereignisse_liste = get_ereignisse_data(pid)
    new_id = f"er{len(ereignisse_liste)+1}_{int(datetime.now().timestamp())}"
    ereignis = {
        "id":                     new_id,
        "typ":                    payload.get("typ", "Sonstiges"),
        "datum":                  payload.get("datum", date.today().strftime("%Y-%m-%d")),
        "uhrzeit":                payload.get("uhrzeit", datetime.now().strftime("%H:%M")),
        "ort":                    payload.get("ort", ""),
        "beschreibung":           payload.get("beschreibung", ""),
        "sofortmassnahmen":       payload.get("sofortmassnahmen", ""),
        "arzt_informiert":        payload.get("arzt_informiert", False),
        "arzt_wer":               payload.get("arzt_wer", ""),
        "arzt_wann":              payload.get("arzt_wann", ""),
        "angehoerige_informiert": payload.get("angehoerige_informiert", False),
        "angehoerige_wer":        payload.get("angehoerige_wer", ""),
        "angehoerige_wann":       payload.get("angehoerige_wann", ""),
        "folgemassnahmen":        payload.get("folgemassnahmen", ""),
        "kuerzel":                payload.get("kuerzel", "")
    }
    ereignisse_liste.append(ereignis)
    with open(fname, "w", encoding="utf-8") as f:
        json.dump(ereignisse_liste, f, ensure_ascii=False, indent=2)
    return jsonify({"ok": True, "ereignis": ereignis})

@app.route("/api/ereignis/<ereignis_id>", methods=["PUT", "DELETE"])
def api_ereignis_update(ereignis_id):
    pid = get_current_patient_id()
    fname = os.path.join(DATA_DIR, f"ereignisse_{pid}.json")
    ereignisse_liste = get_ereignisse_data(pid)
    if request.method == "DELETE":
        ereignisse_liste = [e for e in ereignisse_liste if e.get('id') != ereignis_id]
        with open(fname, "w", encoding="utf-8") as f:
            json.dump(ereignisse_liste, f, ensure_ascii=False, indent=2)
        return jsonify({"ok": True})
    payload = request.get_json(force=True)
    for e in ereignisse_liste:
        if e.get('id') == ereignis_id:
            for key in ["typ","datum","uhrzeit","ort","beschreibung","sofortmassnahmen",
                        "arzt_informiert","arzt_wer","arzt_wann","angehoerige_informiert",
                        "angehoerige_wer","angehoerige_wann","folgemassnahmen","kuerzel"]:
                if key in payload:
                    e[key] = payload[key]
            break
    with open(fname, "w", encoding="utf-8") as f:
        json.dump(ereignisse_liste, f, ensure_ascii=False, indent=2)
    return jsonify({"ok": True})

# ──────────────────────────────────────────
# WUNDDOKUMENTATION
# ──────────────────────────────────────────

@app.route("/wunden")
def wunden():
    patient = get_current_patient()
    pid = patient['id']
    wunden_liste = get_wunden_data(pid)
    return render_template("wunden.html",
        patient=patient,
        wunden=wunden_liste,
        aktiv="wunden"
    )

@app.route("/api/wunde/neu", methods=["POST"])
def api_wunde_neu():
    payload = request.get_json(force=True)
    pid = get_current_patient_id()
    fname = os.path.join(DATA_DIR, f"wunden_{pid}.json")
    wunden_liste = get_wunden_data(pid)
    new_id = f"w{len(wunden_liste)+1}_{int(datetime.now().timestamp())}"
    wunde = {
        "id":               new_id,
        "typ":              payload.get("typ", "Sonstige"),
        "lokalisation":     payload.get("lokalisation", ""),
        "erstbefund":       payload.get("erstbefund", date.today().strftime("%Y-%m-%d")),
        "aktueller_status": payload.get("aktueller_status", "gelb"),
        "zusammenfassung":  payload.get("zusammenfassung", ""),
        "verlauf": []
    }
    wunden_liste.append(wunde)
    with open(fname, "w", encoding="utf-8") as f:
        json.dump(wunden_liste, f, ensure_ascii=False, indent=2)
    return jsonify({"ok": True, "wunde": wunde})

@app.route("/api/wunde/<wunde_id>/verlauf", methods=["POST"])
def api_wunde_verlauf(wunde_id):
    payload = request.get_json(force=True)
    pid = get_current_patient_id()
    fname = os.path.join(DATA_DIR, f"wunden_{pid}.json")
    wunden_liste = get_wunden_data(pid)
    for w in wunden_liste:
        if w.get('id') == wunde_id:
            verlauf = w.get('verlauf', [])
            new_vid = f"wv{len(verlauf)+1}_{int(datetime.now().timestamp())}"
            eintrag = {
                "id":         new_vid,
                "datum":      payload.get("datum", date.today().strftime("%Y-%m-%d")),
                "groesse":    payload.get("groesse", ""),
                "wundgrund":  payload.get("wundgrund", ""),
                "exsudat":    payload.get("exsudat", ""),
                "umgebung":   payload.get("umgebung", ""),
                "behandlung": payload.get("behandlung", ""),
                "status":     payload.get("status", "gelb"),
                "kuerzel":    payload.get("kuerzel", "")
            }
            verlauf.append(eintrag)
            w['verlauf'] = verlauf
            w['aktueller_status'] = eintrag['status']
            break
    with open(fname, "w", encoding="utf-8") as f:
        json.dump(wunden_liste, f, ensure_ascii=False, indent=2)
    return jsonify({"ok": True})

@app.route("/api/wunde/<wunde_id>", methods=["PUT"])
def api_wunde_update(wunde_id):
    payload = request.get_json(force=True)
    pid = get_current_patient_id()
    fname = os.path.join(DATA_DIR, f"wunden_{pid}.json")
    wunden_liste = get_wunden_data(pid)
    for w in wunden_liste:
        if w.get('id') == wunde_id:
            for key in ["typ","lokalisation","erstbefund","aktueller_status","zusammenfassung"]:
                if key in payload:
                    w[key] = payload[key]
            break
    with open(fname, "w", encoding="utf-8") as f:
        json.dump(wunden_liste, f, ensure_ascii=False, indent=2)
    return jsonify({"ok": True})

# ──────────────────────────────────────────
# FHIR DEMO
# ──────────────────────────────────────────

def build_fhir_resources(patient, today):
    pid = patient['id']
    parts = patient['name'].split(' ', 1)
    family = parts[-1] if len(parts) > 1 else parts[0]
    given  = parts[0]  if len(parts) > 1 else ""
    gender = "male" if pid == "P-2024-0042" else "female"
    bdate  = patient.get('geburtsdatum_iso', patient.get('geburtsdatum', ''))
    return [
        {
            "resourceType": "Patient",
            "id": pid,
            "meta": {"profile": "http://hl7.org/fhir/StructureDefinition/Patient"},
            "identifier": [{"system": "https://carebridge-demo.onrender.com/patienten", "value": pid}],
            "name": [{"family": family, "given": [given]}],
            "birthDate": bdate,
            "gender": gender,
            "address": [{"text": f"{patient.get('station','')}, {patient.get('zimmer','')}"}]
        },
        {
            "resourceType": "Observation",
            "id": f"obs-spo2-{pid[-4:]}",
            "status": "final",
            "category": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/observation-category",
                                       "code": "vital-signs", "display": "Vital Signs"}]}],
            "code": {"coding": [{"system": "http://loinc.org", "code": "2708-6",
                                  "display": "Sauerstoffsättigung (SpO₂)"}]},
            "subject": {"reference": f"Patient/{pid}"},
            "effectiveDateTime": f"{today}T07:00:00+01:00",
            "valueQuantity": {"value": 96, "unit": "%",
                              "system": "http://unitsofmeasure.org", "code": "%"}
        },
        {
            "resourceType": "MedicationRequest",
            "id": f"med-riluzol-{pid[-4:]}",
            "status": "active",
            "intent": "order",
            "medicationCodeableConcept": {"coding": [{"system": "http://www.whocc.no/atc",
                                                       "code": "N07XX02",
                                                       "display": "Riluzol (Rilutek) 50mg"}]},
            "subject": {"reference": f"Patient/{pid}"},
            "dosageInstruction": [{
                "timing": {"repeat": {"frequency": 2, "period": 1, "periodUnit": "d",
                                      "timeOfDay": ["07:00", "19:00"]}},
                "doseAndRate": [{"doseQuantity": {"value": 50, "unit": "mg"}}]
            }]
        },
        {
            "resourceType": "CarePlan",
            "id": f"careplan-{pid}",
            "status": "active",
            "intent": "plan",
            "subject": {"reference": f"Patient/{pid}"},
            "period": {"start": "2026-01-01"},
            "activity": [
                {"detail": {"code": {"text": "Nächtliche Heimbeatmung"}, "status": "in-progress",
                             "scheduledTiming": {"repeat": {"timeOfDay": ["22:00"],
                                                            "duration": 10, "durationUnit": "h"}}}},
                {"detail": {"code": {"text": "Trachealkanülenpflege"}, "status": "in-progress",
                             "scheduledTiming": {"repeat": {"frequency": 1, "period": 1,
                                                            "periodUnit": "d"}}}}
            ]
        }
    ]

@app.route("/fhir")
def fhir():
    patient = get_current_patient()
    today   = date.today().strftime("%Y-%m-%d")
    resources = build_fhir_resources(patient, today)
    return render_template("fhir.html",
        patient=patient, today=today,
        resources=resources, aktiv="fhir")

@app.route("/api/fhir/export")
def api_fhir_export():
    patient   = get_current_patient()
    today     = date.today().strftime("%Y-%m-%d")
    resources = build_fhir_resources(patient, today)
    resp = jsonify(resources)
    resp.headers['Content-Disposition'] = \
        f'attachment; filename="fhir-{patient["id"]}-{today}.json"'
    return resp

# ──────────────────────────────────────────
# QUALITÄTSDASHBOARD
# ──────────────────────────────────────────

def get_qualitaets_kennzahlen():
    pid   = get_current_patient_id()
    today = date.today()
    tage  = ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So']
    labels = [tage[(today - timedelta(days=i)).weekday()] for i in range(6, -1, -1)]

    # ── Heutige Leistungen (echt) ──
    leistungen_heute = get_demo_leistungen(pid)
    gesamt_heute     = len(leistungen_heute)
    bestaetigt_heute = sum(1 for l in leistungen_heute if l['bestaetigt'])
    offen_heute      = gesamt_heute - bestaetigt_heute
    doku_heute       = round(bestaetigt_heute / gesamt_heute * 100) if gesamt_heute else 0

    # ── Alarmereignisse diese Woche (echt) ──
    woche_start  = (today - timedelta(days=today.weekday())).strftime('%Y-%m-%d')
    ereignisse   = get_ereignisse_data(pid)
    alarm_woche  = sum(1 for e in ereignisse if e.get('datum', '') >= woche_start)

    # ── Persönliche Statistik (Wochenbasis + heute echt) ──
    if pid == 'P-2024-0042':
        pb = {
            "AQ": {"leistungen": 35, "puenktlich": 33, "verspaetet": 2},
            "SK": {"leistungen": 30, "puenktlich": 27, "verspaetet": 3},
            "MB": {"leistungen": 25, "puenktlich": 22, "verspaetet": 3},
        }
    else:
        pb = {
            "SK": {"leistungen": 32, "puenktlich": 29, "verspaetet": 3},
            "TM": {"leistungen": 28, "puenktlich": 24, "verspaetet": 4},
            "AB": {"leistungen": 22, "puenktlich": 19, "verspaetet": 3},
        }

    signoffs = get_leistungen_signoffs(pid)
    for lid, so in signoffs.items():
        k = so.get('kuerzel', '')
        if not k:
            continue
        if k not in pb:
            pb[k] = {"leistungen": 0, "puenktlich": 0, "verspaetet": 0}
        pb[k]['leistungen'] += 1
        parts = lid.rsplit('_', 1)
        is_pünktlich = True
        if len(parts) == 2 and ':' in parts[1]:
            try:
                soll_min = int(parts[1][:2]) * 60 + int(parts[1][3:])
                ist_zeit = so.get('zeitstempel', '')
                ist_min  = int(ist_zeit[:2]) * 60 + int(ist_zeit[3:])
                if ist_min - soll_min > 15:
                    is_pünktlich = False
            except Exception:
                pass
        if is_pünktlich:
            pb[k]['puenktlich'] += 1
        else:
            pb[k]['verspaetet'] += 1

    personal = []
    for k, s in sorted(pb.items(), key=lambda x: -x[1]['leistungen']):
        total = s['leistungen']
        quote = round(s['puenktlich'] / total * 100, 1) if total else 0.0
        personal.append({"kuerzel": k, "leistungen": total,
                          "puenktlich": s['puenktlich'],
                          "verspaetet": s['verspaetet'], "quote": quote})

    # ── Patientenspez. Wochenhistorie (6 Vortage Demo + heute echt) ──
    if pid == 'P-2024-0042':
        doku_basis  = [91, 88, 95, 92, 89, 94]
        comp_basis  = [95, 92, 98, 94, 90, 96]
        alarm_typen = ["SpO₂-Abfall", "Beatmungsalarm", "Überf. Doku", "BTM-Warnung"]
        alarm_demo  = [3, 1, 5, 2]
        uq          = 87
    else:
        doku_basis  = [85, 82, 88, 84, 86, 83]
        comp_basis  = [88, 85, 91, 87, 83, 89]
        alarm_typen = ["SpO₂-Abfall", "Dyspnoe-Episode", "Überf. Doku", "Beatmungsalarm"]
        alarm_demo  = [5, 3, 4, 1]
        uq          = 81

    doku_werte       = doku_basis + [doku_heute]
    compliance_werte = comp_basis + [min(100, doku_heute + 3)]
    alarm_gesamt     = alarm_woche if alarm_woche > 0 else (1 if pid == 'P-2024-0042' else 3)

    doku_trend_val = doku_heute - doku_basis[-1]
    doku_trend = f"+{doku_trend_val}%" if doku_trend_val >= 0 else f"{doku_trend_val}%"

    return {
        "patient_id":          pid,
        "patient_name":        get_current_patient().get('name', ''),
        "doku_quote":          doku_heute,
        "doku_trend":          doku_trend,
        "offene_leistungen":   offen_heute,
        "offene_gesamt":       gesamt_heute,
        "alarm_ereignisse":    alarm_gesamt,
        "uebergabe_qualitaet": uq,
        "woche_labels":        labels,
        "doku_werte":          doku_werte,
        "compliance_werte":    compliance_werte,
        "alarm_typen":         alarm_typen,
        "alarm_werte":         alarm_demo,
        "personal":            personal,
    }

@app.route("/qualitaet")
def qualitaet():
    kn      = get_qualitaets_kennzahlen()
    patient = get_current_patient()
    return render_template("qualitaet.html", kn=kn, patient=patient, aktiv="qualitaet")


# ──────────────────────────────────────────
# KONTAKTE
# ──────────────────────────────────────────

KONTAKTE_FILE = os.path.join(DATA_DIR, "kontakte.json")

DEMO_KONTAKTE_MEDIZIN = [
    {"name": "Dr. Elisabeth Hoffmann", "rolle": "Hausärztin / Beatmungsmedizin",
     "tel": "0151 23 456 789", "tel_roh": "+4915123456789",
     "tel2": None, "tel2_label": None,
     "detail": "Erreichbar: Mo–Fr 08:00–18:00 · Notfall: 24 h Bereitschaft"},
    {"name": "Lungenklinik Musterstadt", "rolle": "Pneumologie / Beatmungszentrum",
     "tel": "0123 456-0", "tel_roh": "+491234560",
     "tel2": "0123 456-200", "tel2_label": "Station",
     "detail": "Sprechstunde: Di + Do 09:00–12:00 · Aufnahme 24 h"},
    {"name": "Neurologische Praxis Dr. Berger", "rolle": "Neurologie / ALS-Spezialambulanz",
     "tel": "0123 789-100", "tel_roh": "+4912378900",
     "tel2": None, "tel2_label": None,
     "detail": "Mo, Mi, Fr 08:00–13:00 · Termine nach Vereinbarung"},
    {"name": "Palliativnetz Musterstadt", "rolle": "Palliativmedizin / Krisenintervention",
     "tel": "0800 500 400 300", "tel_roh": "+49800500400300",
     "tel2": None, "tel2_label": None,
     "detail": "24 h erreichbar · Krisentelefon auch nachts"},
]

DEMO_KONTAKTE_TECHNIK = [
    {"name": "ResMed Geräte-Hotline", "rolle": "Astral 150 — technischer Support",
     "tel": "0800 7376 633", "tel_roh": "+498007376633",
     "detail": "24 h · 7 Tage · Kostenlos · Gerätenummer bereithalten"},
    {"name": "Linde Gas — Sauerstoffversorgung", "rolle": "O₂-Lieferung & Notfallversorgung",
     "tel": "0800 5463 463", "tel_roh": "+498005463463",
     "detail": "24 h Notfallservice · Kundennummer bereithalten"},
    {"name": "Sanitätshaus Musterstadt GmbH", "rolle": "Hilfsmittelversorgung & Zubehör",
     "tel": "0123 789-0", "tel_roh": "+491237890",
     "detail": "Mo–Fr 08:00–17:00 · Sa 09:00–13:00 · Lieferservice"},
    {"name": "Intensivpflege-Service Nord", "rolle": "Reparatur & Wartung Beatmungsgeräte",
     "tel": "040 1234 5678", "tel_roh": "+4940123456780",
     "detail": "Mo–Fr 07:00–18:00 · Bereitschaftsdienst wochends"},
]

DEMO_KONTAKTE_INTERN = [
    {"name": "Sandra Krause", "rolle": "Pflegeleitung · Examinierte Pflegefachfrau",
     "tel": "0152 98 765 432", "tel_roh": "+4915298765432",
     "detail": "Bereitschaft: 06:00–22:00 · Nachtbereitschaft nach Absprache"},
    {"name": "Aaron Quazi", "rolle": "Examinierter Pflegefachmann",
     "tel": "0151 11 223 344", "tel_roh": "+4915111223344",
     "detail": "Frühschicht 06:00–14:00 · Spätschicht 14:00–22:00"},
    {"name": "Michael Berger", "rolle": "Pflegefachmann",
     "tel": "0152 33 445 566", "tel_roh": "+4915233445566",
     "detail": "Nachtschicht 22:00–06:00 · Bereitschaft nach Dienstplan"},
]

def get_extra_kontakte():
    if os.path.exists(KONTAKTE_FILE):
        with open(KONTAKTE_FILE, encoding="utf-8") as f:
            return json.load(f)
    return []

@app.route("/kontakte")
def kontakte():
    extra = get_extra_kontakte()
    return render_template("kontakte.html",
        medizin=DEMO_KONTAKTE_MEDIZIN,
        technik=DEMO_KONTAKTE_TECHNIK,
        intern=DEMO_KONTAKTE_INTERN,
        extra=extra,
        aktiv="kontakte"
    )

@app.route("/api/kontakte/hinzufuegen", methods=["POST"])
def api_kontakte_hinzufuegen():
    payload = request.get_json(force=True)
    name = payload.get("name", "").strip()
    if not name:
        return jsonify({"ok": False}), 400
    extra = get_extra_kontakte()
    entry = {
        "name":         name,
        "funktion":     payload.get("funktion", ""),
        "telefon":      payload.get("telefon", ""),
        "erreichbarkeit": payload.get("erreichbarkeit", ""),
        "kategorie":    payload.get("kategorie", "intern"),
        "erstellt":     datetime.now().strftime("%Y-%m-%d %H:%M")
    }
    extra.append(entry)
    with open(KONTAKTE_FILE, "w", encoding="utf-8") as f:
        json.dump(extra, f, ensure_ascii=False, indent=2)
    return jsonify({"ok": True})

# ──────────────────────────────────────────
# EXPORT — PATIENTENAKTE
# ──────────────────────────────────────────

def get_kurve_zeilen_fuer_export(patient_id):
    kurve = get_kurve_data(patient_id)
    stunden = list(range(7, 23))
    zeilen = []
    for h in stunden:
        h_str = str(h)
        def v(key):
            return kurve.get(key, {}).get(h_str, "") or ""
        spo2 = v('spo2')
        hf   = v('hf')
        if not spo2 and not hf:
            continue
        zeilen.append({
            "uhrzeit":  f"{h:02d}:00",
            "spo2":     spo2,
            "hf":       hf,
            "bd_sys":   v('bd_sys'),
            "bd_dia":   v('bd_dia'),
            "af":       v('af'),
            "vt":       v('vt'),
            "leckage":  v('leckage'),
            "ipap":     v('ipap'),
            "epap":     v('epap'),
            "lagerung": v('lagerung'),
        })
    return zeilen

def get_pflegebericht_7tage(patient_id):
    alle = get_pflegebericht_data(patient_id)
    cutoff = (date.today() - timedelta(days=7)).strftime("%Y-%m-%d")
    result = []
    for e in alle:
        datum_iso = e.get("datum_iso") or e.get("datum", "")
        if len(datum_iso) == 10 and datum_iso >= cutoff:
            result.append(e)
        elif len(datum_iso) < 10:
            result.append(e)
    return sorted(result, key=lambda x: (x.get("datum", ""), x.get("uhrzeit", "")), reverse=True)

@app.route("/export/patientenakte")
def export_patientenakte():
    patient    = get_current_patient()
    pid        = patient['id']
    verordnung = get_current_verordnung()
    kurve_zeilen = get_kurve_zeilen_fuer_export(pid)
    pflegebericht = get_pflegebericht_7tage(pid)
    heute_str  = date.today().strftime("%d.%m.%Y")
    return render_template("export_akte.html",
        patient=patient,
        verordnung=verordnung,
        medikamente=DEMO_MEDIKAMENTENPLAN,
        kurve_zeilen=kurve_zeilen,
        pflegebericht=pflegebericht,
        heute_str=heute_str,
        aktiv="export_akte"
    )

# ──────────────────────────────────────────
# SCHICHTPLAN
# ──────────────────────────────────────────

SCHICHTPLAN_FILE = os.path.join(DATA_DIR, "schichtplan.json")

DEMO_SCHICHTPLAN_MUSTER = [
    {"frueh": "AQ", "spaet": "SK", "nacht": "MB"},
    {"frueh": "SK", "spaet": "AQ", "nacht": "MB"},
    {"frueh": "AQ", "spaet": "MB", "nacht": "SK"},
    {"frueh": "MB", "spaet": "SK", "nacht": "AQ"},
    {"frueh": "AQ", "spaet": "SK", "nacht": "MB"},
    {"frueh": "SK", "spaet": "AQ", "nacht": "MB"},
    {"frueh": "MB", "spaet": "AQ", "nacht": "SK"},
]

WOCHENTAGE_LANG  = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
WOCHENTAGE_KURZ  = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]

def get_schichtplan_daten():
    if os.path.exists(SCHICHTPLAN_FILE):
        with open(SCHICHTPLAN_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}

def get_aktive_schicht():
    h = datetime.now().hour
    if 6 <= h < 14:
        return "frueh"
    elif 14 <= h < 22:
        return "spaet"
    else:
        return "nacht"

SCHICHT_LABELS = {"frueh": "Frühschicht", "spaet": "Spätschicht", "nacht": "Nachtschicht"}
SCHICHT_ZEITEN = {"frueh": "06:00–14:00", "spaet": "14:00–22:00", "nacht": "22:00–06:00"}
SCHICHT_NEXT_AB = {"frueh": "14:00", "spaet": "22:00", "nacht": "06:00"}
PERSONAL_NAMEN = {"AQ": "Aaron Quazi", "SK": "Sandra Krause", "MB": "Michael Berger"}

@app.route("/schichtplan", methods=["GET", "POST"])
def schichtplan():
    heute = date.today()
    montag = heute - timedelta(days=heute.weekday())
    gespeichert = get_schichtplan_daten()

    woche = []
    for i in range(7):
        tag_datum = montag + timedelta(days=i)
        datum_str = tag_datum.strftime("%Y-%m-%d")
        ist_heute = (tag_datum == heute)
        muster = DEMO_SCHICHTPLAN_MUSTER[i]
        schichten = gespeichert.get(datum_str, muster)
        aktive = get_aktive_schicht() if ist_heute else None
        woche.append({
            "datum":          datum_str,
            "datum_kurz":     tag_datum.strftime("%d.%m."),
            "wochentag_kurz": WOCHENTAGE_KURZ[i],
            "wochentag_lang": WOCHENTAGE_LANG[i],
            "ist_heute":      ist_heute,
            "aktive_schicht": aktive,
            "schichten":      schichten,
        })

    heute_schicht_key = get_aktive_schicht()
    heute_eintrag     = woche[heute.weekday()]
    heute_kuerzel     = heute_eintrag["schichten"].get(heute_schicht_key, "AQ")
    next_key_map      = {"frueh": "spaet", "spaet": "nacht", "nacht": "frueh"}
    next_schicht_key  = next_key_map[heute_schicht_key]
    next_kuerzel      = heute_eintrag["schichten"].get(next_schicht_key, "SK")

    heute_dienst = {
        "name":         PERSONAL_NAMEN.get(heute_kuerzel, heute_kuerzel),
        "kuerzel":      heute_kuerzel,
        "schicht_label": SCHICHT_LABELS[heute_schicht_key],
        "zeiten":       SCHICHT_ZEITEN[heute_schicht_key],
    }
    naechste_dienst = {
        "name":         PERSONAL_NAMEN.get(next_kuerzel, next_kuerzel),
        "kuerzel":      next_kuerzel,
        "schicht_label": SCHICHT_LABELS[next_schicht_key],
        "ab":           SCHICHT_NEXT_AB[heute_schicht_key],
    }

    kw = heute.isocalendar()[1]
    woche_label = f"{montag.strftime('%d.%m.')} – {(montag + timedelta(days=6)).strftime('%d.%m.%Y')}"

    return render_template("schichtplan.html",
        woche=woche,
        heute_dienst=heute_dienst,
        naechste_dienst=naechste_dienst,
        kw=kw,
        woche_label=woche_label,
        aktiv="schichtplan"
    )

@app.route("/api/schichtplan/eintrag", methods=["POST"])
def api_schichtplan_eintrag():
    payload = request.get_json(force=True)
    datum   = payload.get("datum", "")
    schicht = payload.get("schicht", "")
    kuerzel = payload.get("kuerzel", "")
    if not datum or schicht not in ("frueh", "spaet", "nacht"):
        return jsonify({"ok": False, "fehler": "Ungültige Parameter"}), 400
    daten = get_schichtplan_daten()
    if datum not in daten:
        heute = date.today()
        montag = heute - timedelta(days=heute.weekday())
        for i in range(7):
            d = montag + timedelta(days=i)
            dstr = d.strftime("%Y-%m-%d")
            if dstr not in daten:
                daten[dstr] = dict(DEMO_SCHICHTPLAN_MUSTER[i])
    daten.setdefault(datum, {})
    daten[datum][schicht] = kuerzel
    with open(SCHICHTPLAN_FILE, "w", encoding="utf-8") as f:
        json.dump(daten, f, ensure_ascii=False, indent=2)
    return jsonify({"ok": True})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=False)
