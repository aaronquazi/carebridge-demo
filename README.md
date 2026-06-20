# CareBridge Demo

**Digitale Dokumentations- und Übergabeunterstützung für die außerklinische Beatmungspflege**

> ⚠ Demo-Projekt — Alle Daten sind fiktiv. Kein Medizinprodukt.

---

## Lokal starten

```bash
pip install flask
python app.py
# Öffne: http://localhost:5001
```

## Auf Render.com deployen

1. GitHub-Repo erstellen und Code pushen
2. render.com → "New Web Service"
3. Repo verbinden
4. Build Command: `pip install -r requirements.txt`
5. Start Command: `gunicorn app:app`
6. Deploy → URL kopieren

## Module

| Modul | Beschreibung |
|-------|-------------|
| Dashboard | Patientenübersicht, Vitalstatus, offene Aufgaben |
| Intensivkurve | Vitalwerte-Dokumentation mit Chart |
| Leistungsnachweis | Pflegeleistungen mit Bestätigung |
| Beatmungsverordnung | Ärztliche Parameter + Alarmgrenzen |
| Medikamentenplan | Medikamente + Einnahmezeiten |
| Übergabe | SBAR-Übergabeprotokoll + Vollständigkeitsprüfung |

---
*Projekt von: Pflegefachmann mit Interesse an Healthcare IT & Digitalisierung*
