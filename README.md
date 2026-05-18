# Deșertul de servicii, Banat

**Investiție, nu desființare.**

Hartă civică a accesului la servicii publice (școli, medici de familie, spitale de urgență) în cele 99 de UAT-uri ale județului Timiș. Scor compozit între 0 (rău) și 100 (bine), calculat pe baza distanței în linie dreaptă de la centrul UAT-ului la cel mai apropiat serviciu plus densitatea medicilor de familie raportată la populație.

Live: **https://vtemian.github.io/desertul-serviciilor-banat/** *(disponibil după lansarea publică pe 14 iulie 2026)*

Metodologie completă: [METHODOLOGY.md](METHODOLOGY.md).

## Ce arată

- 99 de poligoane UAT din OpenStreetMap (admin_level=8 pentru județul Timiș).
- 603 școli geocodate din SIIIR (rețeaua școlară 2016-2017 + dump-ul de coordonate GPS din 2017).
- 4 spitale de urgență din județ, geocodate manual: Spitalul Clinic Județean de Urgență Timișoara, Spitalul Clinic Municipal de Urgență Timișoara, Spitalul Municipal Lugoj, Spitalul Orășenesc Făget.
- Populația rezidentă pe UAT din Recensământul 2021 (datele finale RPL 2021 publicate de INS).
- 5 vignete cu cele mai prost servite UAT-uri (draft generat din date, redactat înainte de lansare).

Stratul medicilor de familie va fi adăugat în v0.1, după ce CAS Timiș răspunde la cererea de date publice.

## Cum se rulează local

```bash
make install       # creează .venv, instalează dependențele, descarcă Chromium pentru Playwright
make pipeline      # rulează tot pipeline-ul de date (~5 min cu cache-urile pline)
make serve         # servește web/ pe http://localhost:8080
make test          # rulează suita pytest
```

## Surse (ultima actualizare: 2026-05-18)

| Sursa | Format | Licență | Notă |
|---|---|---|---|
| OpenStreetMap Overpass | GeoJSON | ODbL | Poligoanele UAT (fallback de la ANCPI; ANCPI a fost down 500/502 la build). |
| data.gov.ro SIRUTA register | XLS | CC-BY 4.0 | Registrul codurilor SIRUTA. |
| recensamantromania.ro RPL 2021 | XLSX | INS | Populația rezidentă la 1 decembrie 2021, per UAT. |
| data.gov.ro SIIIR rețeaua școlară 2016-2017 | CSV (UTF-16 LE TSV) | CC-BY 4.0 | Registrul unităților de învățământ. |
| data.gov.ro SIIIR coordonate GPS școli 2017 | XLSX | CC-BY 4.0 | Lat/lng per cod SIIIR. |
| Hand-geocodate | constante | n/a | 4 spitale de urgență. |

## Atribuire

© OpenStreetMap contributors (ODbL). Date publice de la INS, Ministerul Educației, ANCPI și data.gov.ro.

Acest site este o inițiativă civică independentă, nu reprezintă o poziție oficială PNL. Nu propune desființarea localităților.
