import importlib.util
import sys

# --- Dependency-Check ---
# Nur Third-Party-Packages hier eintragen (import-Name: pip-Paketname)
REQUIRED = {
    "webview": "pywebview",
}

missing = {imp: pkg for imp, pkg in REQUIRED.items()
           if importlib.util.find_spec(imp) is None}

if missing:
    print("Fehlende Module:", ", ".join(missing.keys()))
    print("Installation mit:")
    print(f"    pip install {' '.join(missing.values())}")
    sys.exit(1)

# --- Imports ---
import webview
import os
import json
import threading
import http.server
import socketserver

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PORT = 18432

# --- Tech-Stack Infotexte ---
TECH_INFO = {
    "symfony": {
        "title": "Symfony 7 / PHP",
        "body": """
            <p>Symfony bildet das Rückgrat von PVOC. Als Full-Stack-Framework übernimmt es Routing,
            Dependency Injection, ORM-Integration via Doctrine und die gesamte Controller-Schicht –
            von der Vocabulary-API bis zum Job-Queue-System für die ML-Pipelines.</p>
            <p>Die Entscheidung für Symfony 7 fiel aus mehreren Gründen: Das Komponentensystem erlaubt
            es, nur das einzubinden, was wirklich gebraucht wird. Der <strong>AssetMapper</strong>
            ersetzt einen kompletten Node.js-Build-Stack – JavaScript und CSS werden ohne Webpack
            oder Vite direkt ausgeliefert, was den Docker-Build erheblich schlanker hält.</p>
            <p>Besonders im Zusammenspiel mit <strong>Stimulus</strong> zeigt Symfony seine Stärke:
            Server-side Rendering mit gezielten JS-Controllern dort, wo Interaktivität gebraucht wird –
            kein unnötiges SPA-Overhead. Das <strong>Mercure-Protokoll</strong> für Server-Sent Events
            ist ebenfalls nahtlos in das Symfony-Ökosystem integriert und ermöglicht Echtzeit-Updates
            in der Gallery-Pipeline.</p>
        """
    },
    "stimulus": {
        "title": "Stimulus / AssetMapper",
        "body": """
            <p>Stimulus ist das JavaScript-Framework der Wahl in PVOC – nicht trotz seiner Bescheidenheit,
            sondern genau deswegen. Anstatt eine komplette SPA zu bauen, reichert Stimulus gezielt
            einzelne HTML-Elemente mit Verhalten an. Ein Controller pro Komponente, klare
            <code>data-controller</code>-Attribute im Markup, kein virtuelles DOM.</p>
            <p>In PVOC steuert Stimulus praktisch jede interaktive Komponente: die Gallery-Navigation,
            den GuteFrage-Scraping-Trigger, die Benutzerverwaltung mit Leaflet-Karte, den Vokabeltrainer
            und die Analyse-Pipeline im Testbed. Die Migration von jQuery und React zu Stimulus hat den
            Frontend-Code deutlich lesbarer und wartbarer gemacht – ohne Build-Step, ohne Transpiler.</p>
            <p>Der <strong>AssetMapper</strong> ergänzt das perfekt: JavaScript-Module werden direkt
            per ES-Module-Syntax im Browser geladen, Symfony mapped die Import-Pfade automatisch.
            Das spart einen kompletten Webpack- oder Vite-Stack im Docker-Image.</p>
        """
    },
    "bootstrap": {
        "title": "Bootstrap 5",
        "body": """
            <p>Bootstrap 5 liefert in PVOC das gesamte UI-Fundament: Grid-System, Cards, Badges,
            Buttons, Navbar und Modals – alles ohne eigene CSS-Architektur von Grund auf aufbauen
            zu müssen. Gerade für ein Projekt, das primär als technisches Portfolio dient, ist das
            der richtige Trade-off: solides, konsistentes Aussehen mit minimalem Aufwand.</p>
            <p>Bootstrap wird dabei konsequent ohne jQuery eingesetzt – die JavaScript-Komponenten
            laufen über das native Bootstrap-Bundle und fügen sich sauber neben Stimulus ein.
            Beide Frameworks konkurrieren nicht, sondern ergänzen sich: Bootstrap kümmert sich
            ums visuelle Gerüst, Stimulus um die applikationsspezifische Logik.</p>
            <p>Die Entscheidung gegen Tailwind fiel bewusst: Bootstrap-Klassen sind semantischer
            und machen das HTML lesbarer, wenn man wie hier serverseitig gerendertes Twig-Markup
            schreibt und nicht in einer Komponenten-Bibliothek lebt.</p>
        """
    },
    "docker": {
        "title": "Docker",
        "body": """
            <p>PVOC läuft vollständig in Docker – ein einzelner Container vereint PHP 8.2/Apache,
            Python 3 mit dem gesamten ML-Stack (PyTorch, MediaPipe, Ultralytics/YOLO, Real-ESRGAN),
            Chromium/ChromeDriver für Selenium sowie den Node.js/Express-Microservice für MongoDB.
            Das Image ist mit rund 7 GB bewusst groß – die Konsequenz einer All-in-one-Entscheidung,
            die dafür auf jedem Rechner sofort läuft.</p>
            <p>Der Vorteil: Die Entwicklungsumgebung ist reproduzierbar und portabel. Kein
            „funktioniert bei mir" – alle Abhängigkeiten, Pfade und Dienste sind im
            <code>Dockerfile</code> und <code>docker-compose.yml</code> festgeschrieben.
            Python-Skripte, die Symfony per <code>shell_exec</code> aufruft, finden ihre
            Bibliotheken immer unter denselben Pfaden.</p>
            <p>Für das Portfolio-Ziel ist Docker außerdem ein klares Signal: Das Projekt lässt
            sich ohne Einrichtungsaufwand klonen und starten – ein wichtiges Kriterium für
            die geplante Veröffentlichung auf GitHub.</p>
        """
    },
    "apache": {
        "title": "Apache",
        "body": """
            <p>Als Webserver innerhalb des Docker-Containers kommt Apache 2 zum Einsatz –
            in der klassischen Kombination mit <code>mod_php</code>, die Symfony out-of-the-box
            unterstützt. Die Konfiguration ist überschaubar: ein VirtualHost, der alle Requests
            auf <code>public/index.php</code> umleitet, dazu <code>mod_rewrite</code> für
            saubere URLs.</p>
            <p>Die Entscheidung für Apache statt Nginx fiel pragmatisch: Die
            <code>.htaccess</code>-basierte Konfiguration von Symfony funktioniert mit Apache
            ohne zusätzlichen Aufwand. Nginx würde eine separate FastCGI/PHP-FPM-Konfiguration
            erfordern – mehr Komplexität ohne nennenswerten Gewinn für ein Entwicklungsprojekt
            dieser Größe.</p>
            <p>Apache verwaltet dabei sowohl die Symfony-Routen als auch die statischen Assets
            des AssetMappers und die direkten Aufrufe der Python-Skripte über den
            Symfony-Controller – alles über einen einzigen Port nach außen.</p>
        """
    },
    "nodejs": {
        "title": "Node.js / Express",
        "body": """
            <p>Node.js kommt in PVOC als schlanker Microservice zum Einsatz, der die Kommunikation
            mit MongoDB übernimmt. Da der PHP-Container keinen nativen MongoDB-Treiber mitbringt,
            der für alle Anwendungsfälle ausreicht, wurde ein separater Express-Server eingeführt,
            der per HTTP-API angesprochen wird.</p>
            <p>Die Entscheidung für diesen Ansatz war bewusst pragmatisch: Node.js und MongoDB
            harmonieren von Haus aus hervorragend – beide arbeiten nativ mit JSON, der Mongoose-ODM
            ist ausgreift und die Async-Architektur von Node passt ideal zu den nicht-blockierenden
            Datenbankoperationen. Der Microservice läuft als eigener Prozess im Docker-Container
            und ist für den Symfony-Controller transparent über einen internen Port erreichbar.</p>
            <p>Das GuteFrage-Scraping-Modul und die Benutzerverwaltung nutzen diesen Service
            intensiv – für Zeitreihenspeicherung, Snapshot-Verwaltung und die geo-indexierten
            Benutzerabfragen mit Leaflet.</p>
        """
    },
    "mongodb": {
        "title": "MongoDB",
        "body": """
            <p>MongoDB ist die Datenbank der Wahl überall dort, wo in PVOC flexible, schemalose
            Strukturen gebraucht werden. Das betrifft zwei Module: das GuteFrage-Scraping, das
            Zeitreihen von Gruppenrankings speichert, und die Benutzerverwaltung mit
            geo-indexierten Standortdaten.</p>
            <p>Der entscheidende Vorteil gegenüber MySQL ist hier die Flexibilität des
            Dokument-Modells. Scraping-Ergebnisse variieren in ihrer Struktur je nach
            Datenlage – kein starres Schema, das bei jeder Änderung migriert werden muss.
            Für die Benutzerverwaltung ermöglichen MongoDB-GeoJSON-Indizes effiziente
            räumliche Abfragen, die mit MySQL deutlich aufwändiger wären.</p>
            <p>Der Zugriff läuft über den Node.js/Express-Microservice, der MongoDB
            als natürlichen Partner behandelt und die Ergebnisse als JSON direkt
            an den Symfony-Controller weiterreicht.</p>
        """
    },
    "mysql": {
        "title": "MySQL",
        "body": """
            <p>MySQL ist die relationale Datenbank für den PVOC-Kern – den Vokabeltrainer.
            Vokabeln, Lernhefte, Beispielsätze, Bilder und Lernfortschritte sind strukturierte,
            stark verknüpfte Daten, für die ein relationales Schema die richtige Wahl ist.
            Doctrine als ORM übernimmt die Abbildung auf PHP-Entities und macht Migrationen
            mit Symfony-Migrations komfortabel verwaltbar.</p>
            <p>Die Entscheidung MySQL vs. PostgreSQL fiel zugunsten von MySQL, weil die
            Anforderungen des Projekts keine PostgreSQL-spezifischen Features erfordern
            und MySQL in der PHP/Symfony-Welt das verbreitetere Setup ist – mit entsprechend
            breiter Tooling-Unterstützung und bewährten Docker-Images.</p>
        """
    },
    "python": {
        "title": "Python / MediaPipe",
        "body": """
            <p>Python ist die Sprache der gesamten ML-Pipeline in PVOC. Symfony ruft die
            Python-Skripte unter <code>/var/www/html/bin/python/</code> per
            <code>shell_exec</code> auf und kommuniziert über NDJSON-Streams –
            ein robustes, einfaches Protokoll, das strukturierte Zwischenergebnisse
            (Bounding Boxes, Base64-Crops) und das Endergebnis in einem einzigen
            Durchlauf liefert.</p>
            <p>MediaPipe übernimmt die Gesichtserkennung: Es liefert präzise Landmark-Daten
            und Bounding Boxes mit konfigurierbarem Padding, die als Grundlage für den
            anschließenden ESRGAN-Upscale und das OpenAI-Inpainting dienen. Die Wahl fiel
            auf MediaPipe wegen seiner Geschwindigkeit auf CPU – kein CUDA nötig –
            und der stabilen Python-API.</p>
            <p>Ergänzt wird MediaPipe durch <code>landmark.py</code> für detaillierte
            Körper-Landmarks und <code>upscale_preview.py</code> für schnelle
            Vorschaubilder – alle Skripte folgen demselben NDJSON-Ausgabeformat
            und sind damit austauschbar erweiterbar.</p>
        """
    },
    "yolo": {
        "title": "YOLO / Real-ESRGAN",
        "body": """
            <p>YOLOv8 (Ultralytics) übernimmt in der PVOC-Pipeline die Personenerkennung –
            schnell, treffsicher und auf CPU ohne Abstriche nutzbar. Die erkannten
            Bounding Boxes werden als JSON-Dateien gecacht, sodass wiederholte Analysen
            desselben Bildes keine erneute Inferenz erfordern. Das spart Rechenzeit
            erheblich, da YOLO mit dem 7-GB-Docker-Image zu den schwergewichtigsten
            Komponenten zählt.</p>
            <p>Real-ESRGAN ergänzt die Pipeline als Upscaler: Gesichts-Crops, die aus
            dem MediaPipe-Schritt stammen, werden vor dem OpenAI-Inpainting hochskaliert,
            um dem Modell mehr Bilddetail zu liefern und das Ergebnis der Reinsertierung
            in das Originalbild zu verbessern. Real-ESRGAN läuft ebenfalls rein auf CPU –
            für Einzelbilder akzeptabel, für Batch-Verarbeitung bewusst als
            Engpass akzeptiert.</p>
        """
    },
    "mercure": {
        "title": "Mercure",
        "body": """
            <p>Mercure ist das Echtzeit-Protokoll in PVOC und ermöglicht Server-Sent Events
            direkt aus dem Symfony-Ökosystem heraus. Konkret wird es in der NSFW-Gallery-Pipeline
            eingesetzt: Während ein Analyse-Job läuft – MediaPipe, YOLO, Real-ESRGAN –
            schickt der Symfony-Controller Fortschrittsupdates per Mercure an den Browser,
            ohne dass der Client pollen muss.</p>
            <p>Die Entscheidung für Mercure statt WebSockets war pragmatisch: Mercure ist
            als Symfony-Bundle nahtlos integriert, funktioniert über einfache
            HTTP-Verbindungen und braucht keine separate WebSocket-Infrastruktur.
            Für unidirektionale Server-zu-Client-Kommunikation – Fortschrittsbalken,
            Statusmeldungen – ist es die schlankere und besser ins Framework passende Lösung.</p>
        """
    },
    "selenium": {
        "title": "Selenium / ChromeDriver",
        "body": """
            <p>Selenium mit ChromeDriver ist das Werkzeug für das GuteFrage-Scraping-Modul.
            gutefrage.net rendert seine Gruppenrankings vollständig clientseitig per JavaScript –
            ein klassischer HTTP-Fetch würde leere Seiten liefern. Selenium steuert einen
            headless Chromium-Browser im Docker-Container und wartet auf das vollständige
            DOM-Rendering, bevor es Rang, Mitgliederzahl und Beitragsanzahl extrahiert.</p>
            <p>ChromeDriver läuft als fester Bestandteil des Docker-Images und ist auf die
            installierte Chromium-Version abgestimmt – ein Versionsmismatch, der in
            lokalen Setups häufig Probleme macht, ist damit ausgeschlossen. Der automatische
            Login, das Navigieren durch bis zu 100 Gruppen und die Fehlerbehandlung bei
            Timeouts sind in einem dedizierten Symfony-Controller gekapselt.</p>
        """
    },
    "chartjs": {
        "title": "Chart.js",
        "body": """
            <p>Chart.js liefert die interaktive Visualisierung im GuteFrage-Scraping-Modul.
            Die gespeicherten Zeitreihen – Rang, Mitglieder, Beiträge pro Gruppe über
            mehrere Snapshots – werden als Linien-Charts dargestellt, mit Delta-Anzeige
            zwischen zwei wählbaren Zeitpunkten und einer sortierbaren Ranglisten-Tabelle
            daneben.</p>
            <p>Die Wahl fiel auf Chart.js wegen seiner schlanken API, der guten
            Bootstrap-Kompatibilität und der Tatsache, dass keine Build-Pipeline
            nötig ist – ein CDN-Import reicht. Für die Datenmenge und den
            Interaktionsgrad des Moduls ist Chart.js mehr als ausreichend; eine
            schwergewichtigere Lösung wie D3.js wäre hier Overkill.</p>
        """
    }
}

# JSON beim Start schreiben
json_path = os.path.join(BASE_DIR, 'techinfo.json')
with open(json_path, 'w', encoding='utf-8') as f:
    json.dump(TECH_INFO, f, ensure_ascii=False, indent=2)

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=BASE_DIR, **kwargs)
    def log_message(self, format, *args):
        pass  # kein Output im Terminal

def start_server():
    with socketserver.TCPServer(('127.0.0.1', PORT), Handler) as httpd:
        httpd.serve_forever()

thread = threading.Thread(target=start_server, daemon=True)
thread.start()

class Api:
    def open_image(self, path):
        webview.create_window(
            'Bild',
            html=f'''<!DOCTYPE html>
<html>
<head>
<style>
  * {{ margin:0; padding:0; }}
  body {{ background:#000; display:flex; align-items:center;
          justify-content:center; height:100vh; overflow:hidden; }}
  img {{ max-width:100%; max-height:100vh; object-fit:contain; }}
</style>
</head>
<body>
  <img src="{path}">
</body>
</html>''',
            width=1400,
            height=900,
            resizable=True
        )

api = Api()

webview.create_window(
    'PVOC – Projektübersicht',
    f'http://127.0.0.1:{PORT}/projekte.html',
    width=1200,
    height=800,
    resizable=True,
    js_api=api
)

webview.start()
