# Palermo – Osud (PWA, Brython) – v1.4

Jedno‑mobilová offline‑friendly PWA appka, ktorá nahrádza „Osud“ (moderátora) pri hre **Mestečko Palermo / Mafia**.
Hráči si počas noci **podávajú mobil** – každý má rovnakú štruktúru krokov (PIN → akcia → výsledok → skryť), takže sa roly neprezrádzajú podľa rýchlosti.

## Funkcie (v1)
- 5–12 hráčov
- Roly: **Mafia**, **Občan**, **Komisár Katányi (Corrado Cattani)**, voliteľne **Lekár**
- Mafia: každý mafián volí tajne; default **prísna zhoda** (obeť zomrie len pri 100 % zhode), alternatíva „mafiánske hlasovanie“
- Katányi: zistí iba **MAFIA / OBČAN**
- Deň: hlasovanie prebieha mimo appky, v appke sa ručne vyberie odsúdený (alebo „nikto“)
- Odhaľovanie po odsúdení (prepínač): nič / mafia‑občan / plná rola (default: mafia‑občan)
- Bezpečnosť: **spoločný 4‑miestny PIN** + **podržanie (press&hold)** na odomknutie
- Maskovanie: voliteľná „Maskovacia akcia“ pre civilov + mikro‑obsah (fakty o seriáli *La piovra / Chobotnica*) – default: len pre civilov a bez spoilerov

## Spustenie lokálne
Najjednoduchšie je použiť ľubovoľný statický server:

```bash
# v koreňovom priečinku repa
python -m http.server 8000
```

Potom otvor:
- `http://localhost:8000/`

## Nasadenie na GitHub Pages
1. Nahraj repo na GitHub.
2. V `Settings → Pages` nastav:
   - Source: **Deploy from a branch**
   - Branch: `main` / folder `/ (root)`
3. Otvor URL z GitHub Pages a **prvýkrát načítaj online**.
4. Potom môžeš v mobile zvoliť:
   - Android Chrome: **Add to Home screen**
   - iOS Safari: **Share → Add to Home Screen**

PWA sa cache‑uje cez Service Worker (`sw.js`). Pre Brython sa používajú CDN skripty – po prvom načítaní sa uložia do cache, takže appka funguje aj offline.

## Súbory
- `index.html` – UI shell + registrácia service worker + Brython boot
- `app.py` – logika aplikácie (Brython)
- `facts_chobotnica.json` – mikro‑obsah (fakty)
- `manifest.json` – PWA manifest
- `sw.js` – service worker (cache‑first)
- `assets/` – ikony, logo

## Licencia
MIT – viď `LICENSE`.


## Troubleshooting

- Ak sa ti po update na GitHub Pages stále zobrazuje stará verzia, vymaž cache / odinštaluj PWA alebo v Chrome: **Settings → Site settings → Storage → Clear** pre danú stránku. (Service Worker si cacheuje súbory.)


## Poznámka k menám hráčov
- Appka zachová poradie hráčov presne podľa zoznamu v nastavení.
- Ak zadáš rovnaké meno viackrát (aj s inou veľkosťou písmen), appka ho automaticky odlíši pridaním „ (2)“, „ (3)“…
