## Tagline

### RO

**Investiție, nu desființare.**

### EN

**Investment, not closure.**

## Ce arată harta / What the map shows

### RO

Harta acoperă cele 99 de UAT-uri din județul Timiș și calculează, pentru fiecare, un scor compozit de acces la trei servicii publice de bază: educație preuniversitară, asistență medicală primară (medic de familie) și asistență medicală de urgență (spital cu camera de gardă). Scorul fiecărei dimensiuni este normalizat pe intervalul 0–100, unde 100 înseamnă acces foarte bun, iar 0 acces practic absent. Compozitul standard ponderează școala cu 0.4, medicul de familie cu 0.4 și spitalul cu 0.2, pentru că primele două servicii sunt folosite zilnic, în timp ce spitalul intervine ocazional, dar critic.

Pentru v0, dimensiunea „medic de familie” lipsește, fiindcă scraper-ul pentru contractele CAS Timiș este încă în lucru. În absența acestei dimensiuni, formula compozitului renormalizează automat ponderile rămase la 0.667 pentru școală și 0.333 pentru spital. Stratul cu medici de familie va fi integrat în v0.1, imediat ce datele CAS sunt colectate, validate și hash-uite la nivel de UAT.

Obiectivul hărții este să arate clar unde statul român s-a retras din mediul rural și unde sunt necesare investiții suplimentare. Nu este un instrument de ranking competitiv între localități, ci un diagnostic care evidențiază lipsurile structurale și prioritățile de intervenție.

### EN

The map covers all 99 administrative units (UAT) in Timiș county and computes, for each one, a composite access score for three core public services: pre-university education, primary healthcare (family doctor) and emergency hospital care. Each dimension is normalised to a 0–100 range, where 100 represents very good access and 0 represents effectively no access. The default composite weights school at 0.4, family doctor at 0.4 and hospital at 0.2, because the first two services are used daily, while hospital care is occasional but critical.

For v0, the family-doctor dimension is missing because the CAS Timiș scraper is still under construction. When this dimension is absent, the composite formula automatically renormalises the remaining weights to 0.667 for school and 0.333 for hospital. The family-doctor layer will land in v0.1, once the CAS data is collected, validated and aggregated at the UAT level.

The goal of the map is to make visible where the Romanian state has withdrawn from rural areas and where additional investment is required. It is not a competitive ranking between localities; it is a diagnostic that highlights structural gaps and intervention priorities.

## Surse de date / Data sources

### RO

Toate sursele au fost ultima dată descărcate pe 2026-05-18.

- OSM Overpass, `admin_level=8` (poligoane UAT, 99 features, licență ODbL).
- data.gov.ro, registrul SIRUTA (fișier xls, 3228 de rânduri).
- recensamantromania.ro, RPL 2021, populație rezidentă (xlsx, 3186 de UAT-uri).
- data.gov.ro, SIIIR `reteascolara` 2016-2017 (registrul unităților școlare).
- data.gov.ro, SIIIR `coordonategps-scoli` 2017 (coordonate lat/lng pentru școli).
- Geocodare manuală pentru cele 4 spitale cu camera de gardă din județ: SCJU Timișoara, SCM Urgență Timișoara, Spitalul Municipal Lugoj, Spitalul Orășenesc Făget.

ANCPI fusese sursa planificată inițial pentru poligoanele UAT, dar serviciul a returnat erori 500/502 în perioada în care a fost construit v0. OSM Overpass este alternativa documentată în BRIEFING.md, iar migrarea la ANCPI este programată pentru v1.

### EN

All sources were last fetched on 2026-05-18.

- OSM Overpass, `admin_level=8` (UAT polygons, 99 features, ODbL license).
- data.gov.ro, SIRUTA register (xls file, 3228 rows).
- recensamantromania.ro, RPL 2021 resident population (xlsx, 3186 UATs).
- data.gov.ro, SIIIR `reteascolara` 2016-2017 (school registry).
- data.gov.ro, SIIIR `coordonategps-scoli` 2017 (school lat/lng coordinates).
- Hand-geocoded entries for the 4 emergency-room hospitals in the county: SCJU Timișoara, SCM Urgență Timișoara, Spitalul Municipal Lugoj, Spitalul Orășenesc Făget.

ANCPI was the originally-planned source for UAT polygons, but the service returned 500/502 errors during the v0 build window. OSM Overpass is the fallback documented in BRIEFING.md, and migration to ANCPI is scheduled for v1.

## Formulă / Formula

### RO

Toate distanțele sunt în metri, convertite la kilometri pentru claritate. Funcția `clamp(0, 100, x)` limitează rezultatul la intervalul închis [0, 100].

- `school_score(d_m) = clamp(0, 100, 100 * (8 - d_km) / 7)`. Scor 100 la cel mult 1 km de cea mai apropiată școală, scor 0 la 8 km sau mai mult.
- `gp_score(pop, count) = clamp(0, 100, 100 * (4000 - pop/count) / 2500)`. Scor 100 la cel mult 1500 de locuitori per medic, scor 0 la 4000 sau mai mult. Valoarea este NaN când numărul medicilor contractați este necunoscut (date lipsă).
- `hospital_score(d_m) = clamp(0, 100, 100 * (50 - d_km) / 40)`. Scor 100 la cel mult 10 km de cel mai apropiat spital cu camera de gardă, scor 0 la 50 km sau mai mult.
- `composite(s, g, h)` este media ponderată a dimensiunilor disponibile, cu ponderile renormalizate pe valorile NaN. Dacă una dintre dimensiuni este NaN, ponderea ei este eliminată, iar ponderile rămase sunt scalate proporțional ca să însumeze 1.

### EN

All distances are in metres, converted to kilometres for readability. The function `clamp(0, 100, x)` constrains the result to the closed interval [0, 100].

- `school_score(d_m) = clamp(0, 100, 100 * (8 - d_km) / 7)`. Score 100 at up to 1 km from the nearest school, score 0 at 8 km or more.
- `gp_score(pop, count) = clamp(0, 100, 100 * (4000 - pop/count) / 2500)`. Score 100 at up to 1500 residents per GP, score 0 at 4000 or more. The value is NaN when the number of contracted GPs is unknown (missing data).
- `hospital_score(d_m) = clamp(0, 100, 100 * (50 - d_km) / 40)`. Score 100 at up to 10 km from the nearest emergency-room hospital, score 0 at 50 km or more.
- `composite(s, g, h)` is the weighted average of the available dimensions, with weights renormalised on NaN values. If a dimension is NaN, its weight is removed and the remaining weights are scaled proportionally to sum to 1.

## Despre distanțe / About distances

### RO

Distanțele sunt măsurate în linie dreaptă. Valorile reale de drum pot fi mai mari. Versiunea v2 va folosi timp de condus real.

### EN

Distances are measured as the crow flies. Actual road values can be higher. Version v2 will use real driving time.

## Confidențialitate / Privacy

### RO

Pentru a respecta intimitatea medicilor, sunt afișate doar numere agregate per UAT, niciodată numărul de pacienți contractați per medic.

### EN

To protect the privacy of doctors, only aggregate numbers per UAT are shown, never the number of contracted patients per doctor.

## Dimensiuni lipsă și roadmap / Missing dimensions and roadmap

### RO

Versiunea v0 este o schiță minimă, conștientă de propriile limite. Următoarele etape sunt deja planificate:

- v0.1: integrarea stratului „medic de familie” cu datele CAS Timiș și activarea ponderii de 0.4 pentru dimensiunea GP.
- v1: includerea transportului școlar (rute, frecvențe, puncte de îmbarcare) și migrarea poligoanelor UAT de la OSM la ANCPI.
- v2: înlocuirea distanțelor în linie dreaptă cu timp real de condus, calculat prin OpenRouteService, plus un strat pentru rețeaua de transport public (CTP, microbuze interurbane, tren regional).

### EN

Version v0 is a minimal sketch, fully aware of its own limitations. The following stages are already planned:

- v0.1: integrate the family-doctor layer using CAS Timiș data and activate the 0.4 weight for the GP dimension.
- v1: include school transport (routes, frequencies, boarding points) and migrate UAT polygons from OSM to ANCPI.
- v2: replace straight-line distances with real driving time, computed via OpenRouteService, and add a layer for the public-transport network (CTP, intercity minibuses, regional rail).

## Investiție, nu desființare / Investment, not closure

### RO

Această hartă cere investiție rurală: minimum de servicii garantate, stimulente pentru medici și profesori în mediul rural, transport școlar asigurat. Nu propune comasarea sau desființarea niciunei localități.

### EN

This map calls for rural investment: a guaranteed minimum of services, incentives for doctors and teachers working in rural areas, and reliable school transport. It does not propose the merging or closure of any locality.

## Disclaimer

### RO

Acest site este o inițiativă civică independentă, nu reprezintă o poziție oficială PNL. Nu propune desființarea localităților.

### EN

This site is an independent civic initiative, it does not represent an official PNL position. It does not propose the closure of any locality.
