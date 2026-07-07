<#
.SYNOPSIS
    pvoc Setup-Assistent (Windows PowerShell)

.DESCRIPTION
    Interaktives Setup-Programm fuer das pvoc-Projekt.
    Fuehrt den Anwender durch die Auswahl der benoetigten Module,
    erzeugt eine passende .env Datei und startet den Docker-Compose-Stack
    nur mit den ausgewaehlten Profilen.

    Zielgruppe: auch Personen ohne tiefes Docker/Symfony-Wissen sollen
    das Skript ohne Vorwissen bedienen koennen.
#>

# ----------------------------------------------------------------------------
# Konfiguration: Module <-> Compose-Profile <-> Beschreibung
# ----------------------------------------------------------------------------

$Modules = @(
    [PSCustomObject]@{
        Key         = "vocab"
        Profile     = "vocab"
        Name        = "Vokabeltrainer (Kernmodul)"
        Description = "MySQL + Symfony-Webserver. Wird immer benoetigt."
        Required    = $true
    },
    [PSCustomObject]@{
        Key         = "geo"
        Profile     = "geo"
        Name        = "Geo-Nutzerverwaltung"
        Description = "MongoDB + Leaflet-Kartenansicht"
        Required    = $false
    },
    [PSCustomObject]@{
        Key         = "scraping"
        Profile     = "scraping"
        Name        = "GF-Scraping-Modul"
        Description = "Node.js/Express + Selenium/Chromium (laedt zusaetzliche Container)"
        Required    = $false
    },
    [PSCustomObject]@{
        Key         = "ml"
        Profile     = "ml-pipeline"
        Name        = "KI-Bildverarbeitung"
        Description = "Python/Torch/MediaPipe/YOLO/Real-ESRGAN (~7 GB, laengere Downloadzeit)"
        Required    = $false
    }
)

$EnvExamplePath = ".env.example"
$EnvPath        = ".env"

# ----------------------------------------------------------------------------
# Hilfsfunktionen
# ----------------------------------------------------------------------------

function Write-Header {
    param([string]$Text)
    Write-Host ""
    Write-Host "==============================================" -ForegroundColor Cyan
    Write-Host " $Text" -ForegroundColor Cyan
    Write-Host "==============================================" -ForegroundColor Cyan
}

function Test-DockerAvailable {
    $docker = Get-Command docker -ErrorAction SilentlyContinue
    if (-not $docker) {
        Write-Host "FEHLER: Docker wurde nicht gefunden." -ForegroundColor Red
        Write-Host "Bitte zuerst Docker Desktop installieren und starten: https://www.docker.com/products/docker-desktop/"
        return $false
    }

    try {
        docker info *> $null
    } catch {
        Write-Host "FEHLER: Docker Desktop scheint nicht zu laufen." -ForegroundColor Red
        Write-Host "Bitte Docker Desktop manuell starten und dieses Skript erneut ausfuehren."
        return $false
    }

    return $true
}

function Select-Modules {
    Write-Header "Modulauswahl"
    Write-Host "pvoc besteht aus mehreren unabhaengigen Modulen."
    Write-Host "Waehle aus, welche du installieren moechtest (Kernmodul ist immer aktiv)."
    Write-Host ""

    $selected = @()

    foreach ($module in $Modules) {
        if ($module.Required) {
            Write-Host "[x] $($module.Name)  - $($module.Description)  (Pflicht)" -ForegroundColor DarkGray
            $selected += $module
            continue
        }

        do {
            $answer = Read-Host "Modul '$($module.Name)' installieren? ($($module.Description)) [j/n]"
            $answer = $answer.Trim().ToLower()
        } while ($answer -ne "j" -and $answer -ne "n")

        if ($answer -eq "j") {
            $selected += $module
        }
    }

    return $selected
}

function New-EnvFile {
    param([array]$SelectedModules)

    if (-not (Test-Path $EnvExamplePath)) {
        Write-Host "WARNUNG: $EnvExamplePath nicht gefunden, erstelle leere .env" -ForegroundColor Yellow
        New-Item -Path $EnvPath -ItemType File -Force | Out-Null
    } else {
        Copy-Item -Path $EnvExamplePath -Destination $EnvPath -Force
    }

    $profiles = ($SelectedModules | ForEach-Object { $_.Profile }) -join ","

    # COMPOSE_PROFILES Zeile ersetzen oder anhaengen
    $envContent = Get-Content $EnvPath -ErrorAction SilentlyContinue
    $found = $false

    $newContent = $envContent | ForEach-Object {
        if ($_ -match "^COMPOSE_PROFILES=") {
            $found = $true
            "COMPOSE_PROFILES=$profiles"
        } else {
            $_
        }
    }

    if (-not $found) {
        $newContent += "COMPOSE_PROFILES=$profiles"
    }

    Set-Content -Path $EnvPath -Value $newContent

    Write-Host ""
    Write-Host "Erzeugte .env mit COMPOSE_PROFILES=$profiles" -ForegroundColor Green
}

function Start-Stack {
    param([array]$SelectedModules)

    Write-Header "Docker-Stack wird gestartet"

    $profileArgs = @()
    foreach ($module in $SelectedModules) {
        $profileArgs += "--profile"
        $profileArgs += $module.Profile
    }

    Write-Host "Fuehre aus: docker compose $($profileArgs -join ' ') up -d --build"
    Write-Host "(Das kann beim ersten Mal je nach Modulauswahl mehrere Minuten dauern.)"
    Write-Host ""

    & docker compose @profileArgs up -d --build

    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "FEHLER: docker compose ist fehlgeschlagen (Exit Code $LASTEXITCODE)." -ForegroundColor Red
        Write-Host "Bitte die Ausgabe oben pruefen."
        return $false
    }

    return $true
}

function Invoke-PostSetup {
    Write-Header "Nachbereitung"

    Write-Host "Fuehre Symfony-Setup-Kommando im Webserver-Container aus..."
    docker exec -it pvoc-webserver-1 bash -c "php bin/console app:setup --no-interaction"

    if ($LASTEXITCODE -ne 0) {
        Write-Host "WARNUNG: app:setup meldete einen Fehler. Bitte manuell pruefen." -ForegroundColor Yellow
    } else {
        Write-Host "Setup abgeschlossen." -ForegroundColor Green
    }
}

# ----------------------------------------------------------------------------
# Hauptablauf
# ----------------------------------------------------------------------------

Write-Header "pvoc Setup-Assistent"

if (-not (Test-DockerAvailable)) {
    exit 1
}

$selectedModules = Select-Modules

Write-Header "Zusammenfassung"
Write-Host "Folgende Module werden installiert:"
foreach ($module in $selectedModules) {
    Write-Host " - $($module.Name)"
}

$confirm = Read-Host "`nFortfahren? [j/n]"
if ($confirm.Trim().ToLower() -ne "j") {
    Write-Host "Abgebrochen."
    exit 0
}

New-EnvFile -SelectedModules $selectedModules

$stackStarted = Start-Stack -SelectedModules $selectedModules

if ($stackStarted) {
    Invoke-PostSetup
    Write-Header "Fertig"
    Write-Host "pvoc sollte nun erreichbar sein unter: http://localhost" -ForegroundColor Green
}
