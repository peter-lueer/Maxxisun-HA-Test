# REST Example – Home Assistant Integration

Dies ist eine einfache **Beispielintegration für Home Assistant**, die demonstriert:

- Wie man Daten über **REST-API (GET)** abruft.
- Wie man Daten über **POST** an eine API sendet.
- Wie man **Integer-Sensoren** mit Typisierung implementiert.
- Wie man eine **Config Flow UI** für Integrationserstellung nutzt.

---

## 📦 Installation

1. Lege diesen Ordner in dein Home Assistant `config`-Verzeichnis:
    config/custom_components/rest_example/
2. Home Assistant neu starten
3. Integration über UI hinzufügen: **Einstellungen → Geräte & Dienste → Integration hinzufügen → REST Example**
4. Username und Password eingeben

---

## Komponenten

| Datei | Beschreibung |
|-------|---------------|
| `sensor.py` | Textsensor via REST GET |
| `sensor_int.py` | Integer-Sensor via REST GET |
| `button.py` | POST-Button via REST |
| `config_flow.py` | UI-basiertes Setup für Username/Password |
| `const.py` | Konstanten (API_BASE_URL, DOMAIN) |
| `manifest.json` | Metadaten für Home Assistant |

---

## Lizenz

Public Domain – frei kopierbar, anpassbar und verbreitbar.
