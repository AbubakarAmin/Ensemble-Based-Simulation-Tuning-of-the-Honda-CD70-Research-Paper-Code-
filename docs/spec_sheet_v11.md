# CD70 Engine: Final Specification Sheet (v11, standard for research)

Finalised 11 October 2026. Supersedes v10 and all earlier versions. This is the version to attach to the research paper. Changes from v10: (1) top speed is now a calibration target (80-90 km/h real-world top speed of a stock CD70) instead of an unused literature range; (2) cranking compression is calibrated against an uncertain cranking speed instead of a fixed 1,000 rpm; (3) section 8 lists all 38 uncertain inputs and the calibration targets cal_1 to cal_4 actually used by the code; (4) section 9 states honestly that the study is simulation-only. All values from v10 sections 1-5, 7 and 10 are unchanged.

Read section 9 first if you only read one part. It says what this sheet can and cannot support.

---

## 1. Source hierarchy used

1. **O (Official):** Atlas Honda pages and PDFs for the CD70, current model. Highest weight.
2. **C (CD70-specific secondary):** dealers, listings, reference sites that name the CD70 with matching numbers.
3. **W (Workshop manual, older edition):** the CD70 workshop manual copy on Scribd. The user states it is an older version. Its values conflict with the official document on two points (section 5), so it is used only where nothing newer exists.
4. **S (Sibling model):** C70, CT70, XR70R, CB/CL 350/360 values. Never used as a CD70 value. Used only as a sanity check.
5. **L (Low):** forum posts, unlabelled data, aggregators that contradict official sources.

Tags used in every table: **OFFICIAL**, **MEDIUM**, **WSM** (older workshop manual, provisional), **DERIVED**, **PROXY** (sibling), **ASSUMED**, **LOW**, **OPEN**.

---

## 2. Engine and geometry

| Parameter | Value | Tag | Source(s) |
|---|---|---|---|
| Engine type | 4-stroke, OHC, air-cooled, single cylinder, carburettor | OFFICIAL | [Atlas CD70 product page](https://www.atlashonda.com.pk/cd70/) (checked 9 Oct 2026); [Atlas CD70 Specifications PDF](https://www.atlashonda.com.pk/wp-content/uploads/2025/08/CD70-Specifications.pdf) (checked 9 Oct 2026) |
| Displacement | 72 cm³ (71.84 cm³ calculated) | OFFICIAL | Atlas product page; Atlas Specifications PDF; [Wikipedia, Honda 70](https://en.wikipedia.org/wiki/Honda_70) (checked 9 Oct 2026) |
| Bore × stroke | 47.0 × 41.4 mm | OFFICIAL | Atlas product page; [Wikipedia, Honda 70](https://en.wikipedia.org/wiki/Honda_70); [BikeBD, CD70 Dream 2022 vs C70](https://bikebd.com/bike-compare/honda-cd70-dream-2022/vs/honda-c-70-1970) |
| **Compression ratio** | **9.3 : 1** | **OFFICIAL** | Atlas product page; [Atlas Specifications PDF](https://www.atlashonda.com.pk/wp-content/uploads/2025/08/CD70-Specifications.pdf) (shows 9.3:1); [Wikipedia, Honda 70](https://en.wikipedia.org/wiki/Honda_70); [Motorradundreisen, CD70 Dream 2022](https://www.motorradundreisen.de/motorraddatenbank/honda/cd70-dream-13124.html) (9,3:1); [Gari.pk, CD70 vs PH70 (2026)](https://www.gari.pk/bikes/compare/pak-hero-ph-70-10-vs-honda-cd-70-19) |
| Clearance volume | 8.66 cm³ | DERIVED | 71.84 / (9.3 − 1) |
| Cranking compression (workshop manual states 1,000 rpm) | 12.7 bar (13 kgf/cm²), ±10%. The cranking speed itself is treated as uncertain (300-1,000 rpm); a kick-start or motor does not reach 1,000 rpm. | WSM | W, workshop manual pp. 1-6, 3-6 ([Scribd copy](https://www.scribd.com/document/958566633/CD70-Workshop-Manual-URDU); not accessible 9 Oct 2026) |
| Connecting rod, centre-to-centre | 91 mm (90–92 sensitivity) | MEDIUM | [Con-Rods.com CD70 kit](https://www.con-rods.com/for-honda-cd70-036.html) (aftermarket, CD70 listed). No OEM value found. |
| Small-end ID / piston pin bore | 13.02 mm / 13.005 mm | WSM | W pp. 7-4 |
| Wrist pin diameter | ~13.0 mm | WSM-implied | Must fit the bores above. The 23.1 mm figure from the rod-kit listing is rejected. |
| Peak cylinder pressure limit | 60–70 bar | ASSUMED | No source |

---

## 3. Valve train

| Parameter | Value | Tag | Source(s) |
|---|---|---|---|
| Valve timing IO / IC / EO / EC | 0° BTDC / 20° ABDC / 20° BBDC / 0° ATDC | WSM | W pp. 1-6 (text layer). No official value found. |
| Intake and exhaust duration | 200° / 200° | DERIVED | 180 + IO + IC; 180 + EO + EC |
| Valve overlap | 0° | DERIVED | IO + EC |
| Cam lobe height IN / EX | 29.353 / 29.350 mm | WSM | W pp. 6-7 |
| Valve clearance, cold IN and EX | 0.08–0.10 mm (use 0.09) | WSM; MEDIUM at 0.10 | W pp. 3-4, 1-6; [MotoPartsPakistan CD70 page](https://quickreviewsandgui.wixsite.com/motopartspakistan/cd70-important-instructions-from-ow) (0.10 mm) |
| Valve stem OD IN / EX | 4.98 / 4.96 mm | WSM (cross-checked) | W pp. 6-0 |
| Valve guide ID | 5.006 mm (5.000–5.012) | WSM (cross-checked) | W pp. 6-0 |
| Guide clearance IN / EX | 0.010–0.037 / 0.030–0.057 mm | WSM | W pp. 6-9 |
| Valve seat width / angles | 1.0 mm; 45° / 32° / 60° | WSM | W pp. 6-11, 6-13 |
| Valve lift | 6.5 mm (6.0–7.0) | ASSUMED | No source. Lobe height alone does not give lift. |
| Head diameter IN / EX | 25 / 21.9 mm | PROXY | [K&L valve set, C70K/CT70 family](https://4into1.com/k-l-engine-valve-set-honda-s65-c-ct-sl-xl70/) |

---

## 4. Ignition, fuel and carburettor

| Parameter | Value | Tag | Source(s) |
|---|---|---|---|
| Ignition type | AC-CDI | OFFICIAL | Atlas Specifications PDF; [Wikipedia, Honda 70](https://en.wikipedia.org/wiki/Honda_70) (CDI) |
| Static timing (F mark, 1,500 rpm) | 20° BTDC | WSM | W pp. 1-6, 14-4. No other CD70 source found. |
| Advance at 4,000 rpm | 35° BTDC | WSM | W pp. 1-6, 14-4 |
| Advance above 4,000 rpm | Held at 35° | ASSUMED | — |
| Spark plug | C7HSA | OFFICIAL | Atlas Specifications PDF; W pp. 1-6 |
| Plug gap | 0.6–0.7 mm | OFFICIAL / MEDIUM | Atlas Specifications PDF; W; MotoPartsPakistan |
| Carburettor code | **PZ18** (fitment for CD70 1997–2004, PB12H/J/K) | MEDIUM− | [Oro2u PZ18 listing](https://www.oro2u.com/carburetor-assy-97-04-honda-cd-xr-crf-r-f-70-16-5mm-pb12h-pb12j-pb12k-16100-gcf-672). Current Euro II code not confirmed. Other codes seen: PB5PC (W), PZ16/PZI6 ([PakWheels forum](https://www.pakwheels.com/forums/t/cd70-carbourater-setting/261042)). |
| Venturi (carb bore) | **OPEN: 18 mm or 16.5 mm** | OPEN | Same [Oro2u PZ18 listing](https://www.oro2u.com/carburetor-assy-97-04-honda-cd-xr-crf-r-f-70-16-5mm-pb12h-pb12j-pb12k-16100-gcf-672) gives both. [Second Oro2u listing](https://www.oro2u.com/carburetor-assy-honda-xr-crf-r-f-70-16-5mm-pb12h-pb12j-pb12k-16100-gcf-672) gives 16.5 mm. |
| Main jet | **#78** (test #72) | MEDIUM | W pp. 4-0 (printed "78", UNCERTAIN); [Keihin main jet sizes #60–#78](https://www.randakks.com/main-jet-primary-keihin-99201-601-type-sizes-60-to-78.html) (general Keihin list, not CD70) |
| Slow / idle jet | **#38** (test #35) | PROXY / OPEN | [CMSNL CD70 parts list](https://www.cmsnl.com/honda-cd70_model50394/partslist/) (sizes 38/40/42); W printed "35"; [Vintage Honda twins forum](https://www.vintagehondatwins.com/forums/goto/post?id=39609) (#35 is a common Honda idle jet on other models) |
| Float level | 11.7 mm | WSM | W pp. 4-7. [C70 proxy 10.7 mm](https://lrio.com/news/motos/c70/c70-specifications) rejected for CD70. |
| Air screw | 2.125 turns out (owners 1.25–1.75) | WSM | W pp. 4-8; [PakWheels forum](https://www.pakwheels.com/forums/t/cd70-carbourater-setting/261042) (owner reports) |
| Throttle grip free play | 2–6 mm | OFFICIAL / WSM | [Atlas Operation Guide](https://www.atlashonda.com.pk/wp-content/uploads/2025/08/CD70-Operation-Guide.pdf) (2-6 mm); W pp. 3-5 |
| Fuel tank | 8.5 L (1.0 L reserve) | OFFICIAL | Atlas product page; Atlas Specifications PDF. [Motodealers 2021](https://motodealers.co.uk/bikes/atlas-honda/cd-70/2021/specs) lists 9.0 L and is rejected. |
| Engine oil | SAE 20W-40 (API SG / JASO MA) | OFFICIAL | Atlas Specifications PDF; Atlas Operation Guide; W pp. 2-2 |
| Oil capacity change / overhaul | 0.6 L / 0.8 L | OFFICIAL | Atlas Specifications PDF; W pp. 2-2 |
| Gear oil | SAE 80/90 | OFFICIAL | Atlas Specifications PDF |
| Idle speed | 1,500 ± 100 rpm | OFFICIAL | Atlas Specifications PDF (1,500 100 rpm); W pp. 3-5 |

---

## 5. Drivetrain, chassis and weights

| Parameter | Value | Tag | Source(s) |
|---|---|---|---|
| Transmission | 4-speed constant mesh | OFFICIAL | Atlas product page; Atlas Specifications PDF |
| Clutch | Multiplate wet | OFFICIAL | Atlas product page |
| Starting | Kick | OFFICIAL | Atlas product page |
| Chain | 420, 104 links | OFFICIAL | Atlas Specifications PDF |
| Chain slack | 20–30 mm | OFFICIAL | Atlas Specifications PDF. **W says 10–20 mm; the official value is used.** |
| Final drive | 14T / 41T = 2.93 | OFFICIAL | Atlas Specifications PDF |
| Primary reduction | 3.722 | WSM | W pp. 1-6 (text layer). Not in official document. |
| Gear 1 / 2 / 3 / 4 | 3.272 / 1.937 / 1.350 / 1.043 | WSM | W pp. 1-6 (text layer). Gear teeth not found. |
| Tyres front / rear | 2.25-17 (4PR) / 2.50-17 (4PR) | OFFICIAL | Atlas product page; Atlas Specifications PDF |
| Tyre pressure | Front 25 psi; rear 29–33 psi | OFFICIAL (partial labels) | [Atlas Operation Guide](https://www.atlashonda.com.pk/wp-content/uploads/2025/08/CD70-Operation-Guide.pdf); Atlas Specifications PDF |
| Dry weight | 82 kg | OFFICIAL | Atlas product page; Atlas Specifications PDF; [Wikipedia](https://en.wikipedia.org/wiki/Honda_70) |
| Weight, other figure | 110 kg | OPEN | Atlas Specifications PDF (label lost; probably kerb or gross weight) |
| Dimensions L × W × H | 1,897 × 751 × 1,014 mm | OFFICIAL | Atlas product page; Atlas Specifications PDF |
| Wheelbase | 1,206 mm | MEDIUM | [Wikipedia, Honda 70](https://en.wikipedia.org/wiki/Honda_70); [PakWheels CD70](https://www.pakwheels.com/bikes/honda/cd-70--3/) |
| Ground clearance | 136 mm | OFFICIAL | Atlas product page; Atlas Specifications PDF |
| Rolling radius (rear, estimate) | ~0.279 m | DERIVED, APPROX | 0.2159 + 0.0635 m (17 in rim + tyre height estimate) |

---

## 6. Performance (calibration and check values)

| Parameter | Value | Tag | Source(s) |
|---|---|---|---|
| Maximum power | 5.0–5.1 hp at 7,500 rpm (calibrate to 5.05) | MEDIUM | [Wikipedia, Honda 70](https://en.wikipedia.org/wiki/Honda_70) (5.0 hp @ 7,500); [PakWheels CD70](https://www.pakwheels.com/bikes/honda/cd-70--3/) (5.1 HP @ 7500); [Urdupoint CD70](https://www.urdupoint.com/bikes/detail/honda/4/cd-70.html) (5.1 HP); [Gari.pk 2026](https://www.gari.pk/bikes/compare/pak-hero-ph-70-10-vs-honda-cd-70-19) (5.1 HP @ 7500); [BikeBD](https://bikebd.com/bike-compare/honda-cd70-dream-2022/vs/honda-c-70-1970) (6.17 in one table, rejected) |
| Maximum torque | 5.0 Nm at 5,500 rpm (±10%) | MEDIUM | [PakWheels CD70](https://www.pakwheels.com/bikes/honda/cd-70--3/); [Urdupoint CD70](https://www.urdupoint.com/bikes/detail/honda/4/cd-70.html); [Gari.pk 2026](https://www.gari.pk/bikes/compare/pak-hero-ph-70-10-vs-honda-cd-70-19); [Wikipedia Honda CD70](https://en.wikipedia.org/wiki/Honda_CD70) (0.53 kgf·m @ 8,000 — rejected) |
| Top speed | **80–90 km/h real-world top speed of a stock CD70 (calibration target cal_4)**; literature 75–90 km/h (Wikipedia, LOW) and 100 km/h (Gari.pk, LOW, not used) | MEDIUM (project owner statement, consistent with Wikipedia; not an instrumented test) | [Wikipedia, Honda 70](https://en.wikipedia.org/wiki/Honda_70); [Gari.pk 2026](https://www.gari.pk/bikes/compare/pak-hero-ph-70-10-vs-honda-cd-70-19). Needs engine power extrapolated to 9,500 rpm (ASSUMED; no power data above 7,500 rpm exists). In 4th gear 7,500 rpm is only about 69 km/h, so 80–90 km/h implies the engine pulls past 7,500 rpm. |
| Idle | 1,500 ± 100 rpm | OFFICIAL | Atlas Specifications PDF |
| Rated speed limit | 7,500 rpm | MEDIUM | Power point above |

---

## 7. Conflict log (final decisions)

| # | Parameter | Conflicting values and sources | Decision | Why |
|---|---|---|---|---|
| C1 | Compression ratio | **9.3** — [Atlas product page](https://www.atlashonda.com.pk/cd70/), [Atlas Specifications PDF](https://www.atlashonda.com.pk/wp-content/uploads/2025/08/CD70-Specifications.pdf), [Wikipedia](https://en.wikipedia.org/wiki/Honda_70), [Motorradundreisen](https://www.motorradundreisen.de/motorraddatenbank/honda/cd70-dream-13124.html), [BikeBD CD70 Dream](https://bikebd.com/bike-compare/honda-cd70-dream-2022/vs/honda-c-70-1970). **8.8** — [W](https://www.scribd.com/document/958566633/CD70-Workshop-Manual-URDU), [Webbikeworld C70 Passport](https://www.webbikeworld.com/honda-cub-70/) (C70, sibling), [Motodealers 2021](https://motodealers.co.uk/bikes/atlas-honda/cd-70/2021/specs), [PakObserver 2026](https://pakobserver.net/honda-cd-70-2026-model-launched-in-pakistan-price-pictures-and-specs/), [Daily Pakistan 2023](https://en.dailypakistan.com.pk/02-Sep-2023/honda-cd-70-2024-latest-price-in-september), [StemedHub 2024](https://stemedhub.org/members/28175/blog/2024/05/price-honda-cd-70-2024-model-price-in-pakistan). **9.4** — [Alibaba](https://alibaba.com/showroom/honda-cd70-engine.html) (rejected). | **9.3 CONFIRMED** | Official Atlas, both Atlas documents agree. 8.8 matches the C70 Passport and the W, which is an older edition. |
| C2 | Chain slack | 20–30 mm (Atlas PDF); 10–20 mm (W) | **20–30 mm** | Official. Confirms W is a different edition. |
| C3 | Fuel tank | 8.5 L (Atlas); 9.0 L ([Motodealers](https://motodealers.co.uk/bikes/atlas-honda/cd-70/2021/specs)) | **8.5 L** | Official |
| C4 | Length | 1,897 mm (Atlas); 1,881 mm ([Motodealers](https://motodealers.co.uk/bikes/atlas-honda/cd-70/2021/specs)) | **1,897 mm** | Official |
| C5 | Carburettor code | PZ18 ([Oro2u](https://www.oro2u.com/carburetor-assy-97-04-honda-cd-xr-crf-r-f-70-16-5mm-pb12h-pb12j-pb12k-16100-gcf-672)); PB5PC (W); PZ16 / PZI6 ([PakWheels](https://www.pakwheels.com/forums/t/cd70-carbourater-setting/261042)); PZ19 / PZ22 (user-supplied, not found in any page checked) | **PZ18 working value, MEDIUM−** | Only sourced code with CD70 fitment. Current Euro II code still OPEN. |
| C6 | Venturi | 18 mm and 16.5 mm, both in one [Oro2u](https://www.oro2u.com/carburetor-assy-97-04-honda-cd-xr-crf-r-f-70-16-5mm-pb12h-pb12j-pb12k-16100-gcf-672) listing | **OPEN.** Use 18 mm base, 16.5 mm test. | Conflicting listing |
| C7 | Main jet | #78 (W printed; [Keihin list](https://www.randakks.com/main-jet-primary-keihin-99201-601-type-sizes-60-to-78.html)); #72 ([C70Z parts list](https://www.motorcyclespareparts.eu/en/honda-parts/1982-c70z-scooters/carburettor-2) sibling) | **#78** | CD70 workshop reading plus a retailer size list |
| C8 | Slow / idle jet | #38 ([CMSNL CD70 list](https://www.cmsnl.com/honda-cd70_model50394/partslist/)); #35 (W); #35 common Honda idle jet ([Vintage Honda twins](https://www.vintagehondatwins.com/forums/goto/post?id=39609)) | **#38, test #35** | Parts list is CD70-specific. Low impact on wide-open-throttle calibration. |
| C9 | Ignition timing | 20° BTDC (W); 10° (LOW, Facebook video); 15° and 25° (sibling, unverified) | **20° BTDC WSM, OPEN** | Only CD70-specific source is W. |
| C10 | Valve clearance | 0.08–0.10 (W); 0.10 ([MotoPartsPakistan](https://quickreviewsandgui.wixsite.com/motopartspakistan/cd70-important-instructions-from-ow)); 0.05 (CT70 / XR70R, [howtomotorcyclerepair](https://howtomotorcyclerepair.com/how-to-honda-50-70cc-valve-adjustment-xr70r/)) | **0.09 nominal, 0.08–0.10** | 0.05 is a different model and is rejected |
| C11 | Valve timing | W 0/20/20/0; C70/CT70 proxy 5/23/25/5 ([LRIO C70](https://lrio.com/news/motos/c70/c70-specifications)) | **W, OPEN** | No CD70 official value. Proxy rejected as CD70 value. |
| C12 | Connecting rod | 91 mm ([Con-Rods](https://www.con-rods.com/for-honda-cd70-036.html)); 95 mm (earlier assumption); W gives no length, and its 110 mm is a brake drum ID | **91 mm, MEDIUM** | Only CD70 listing |
| C13 | Wrist pin | 23.1 mm ([Con-Rods](https://www.con-rods.com/for-honda-cd70-036.html)); W bores imply 13 mm | **13.0 mm** | 23.1 mm cannot fit the 13 mm small end |
| C14 | Octane | RON 87 (older reports); RON 90 partial (2019–2020); RON 92 approved ([Carspirit ECC](https://carspiritpk.com/ron-92-petrol-approved-for-use-in-pakistan-by-ecc), [ProPakistani](https://propakistani.pk/?p=107513), [The News](https://www.thenews.com.pk/print/145758-Import-of-RON-92-standard-petrol-likely-to-start-in-November), [PakWheels agreement](https://www.pakwheels.com/blog/agreement-signed-higher-grade-petrol/amp)); 2026 price news does not state grade ([ARY, Aug 2026](https://www.arynews.tv/petrol-price-in-pakistan-for-august-13-2026)) | **Run both 87 and 92** | No 2026 grade confirmation |
| C15 | MMT limit | 40 mg/L (to Oct 2018); 24 mg/L (Nov 2018–Apr 2019). **Original source link not recorded in earlier versions.** | HISTORICAL. No current limit. | Needs a link before submission (section 8) |

---

## 8. Simulation input table (single source for code)

| Input | Value | Range | Tag |
|---|---|---|---|
| bore_mm | 47.0 | ±0.01 | OFFICIAL |
| stroke_mm | 41.4 | fixed | OFFICIAL |
| cr | 9.3 | 8.8 (one check run) | OFFICIAL |
| conrod_mm | 91 | 90–92 | MEDIUM |
| IO / IC / EO / EC (deg) | 0 / 20 / 20 / 0 | ±2 | WSM |
| valve_lift_max_mm | 6.5 | 6.0–7.0 | ASSUMED |
| valve_clearance_mm | 0.09 | 0.08–0.10 | WSM |
| stem OD IN / EX (mm) | 4.98 / 4.96 | ±0.01 | WSM |
| guide_ID (mm) | 5.006 | ±0.006 | WSM |
| head_dia IN / EX (mm) | 25.0 / 21.9 | ±10% | PROXY |
| ign_static (deg BTDC at 1,500) | 20 | 15–25 | WSM |
| ign_adv_4000 (deg BTDC) | 35 | ±2 | WSM |
| ign_adv_above_4000 | 35 flat | ±3 | ASSUMED |
| carb_code | PZ18 | — | MEDIUM− |
| venturi_mm | 18 | 16.5 | OPEN |
| main_jet | 78 | 72 | MEDIUM |
| slow_jet | 38 | 35 | PROXY / OPEN |
| float_mm | 11.7 | ±0.5 | WSM |
| air_screw_turns | 2.125 | 1.25–1.75 | WSM |
| primary | 3.722 | ±0.02 | WSM |
| gears 1–4 | 3.272 / 1.937 / 1.350 / 1.043 | ±0.02 | WSM |
| final_drive | 2.93 | fixed | OFFICIAL |
| rolling_radius_m | 0.279 | 0.26–0.28 | DERIVED, APPROX |
| fuel_RON | 87 and 92 | — | LOW |
| peak_pressure_limit_bar | 60–70 | — | ASSUMED |
| cal_1 | 5.05 hp at 7,500 rpm | ±5% | MEDIUM |
| cal_2 | 5.0 Nm at 5,500 rpm | ±10% | MEDIUM |
| cal_3 | 12.7 bar cranking compression, cranking speed uncertain 300–1,000 rpm, leak area 0.03–0.6 mm² | ±10% | WSM |
| cal_4 | True top speed 80–90 km/h | range | MEDIUM |
| cda_m2 (drag area, upright commuter rider) | 0.45 | 0.25–0.65 | ASSUMED |
| crr (rolling resistance) | 0.020 | 0.014–0.030 | ASSUMED |
| drive_eff (chain + gearbox) | 0.86 | 0.80–0.92 | ASSUMED |
| mass_kg (bike + rider) | 155 | 140–170 | ASSUMED |
| speedo_overread (reporting only, not calibrated) | 0.05 | 0–0.10 | ASSUMED |
| crank_rpm | 600 | 300–1,000 | WSM / ASSUMED |
| Other uncertain inputs (friction, heat transfer, Wiebe, blow-by, knock, flow coefficients, manifold, muffler, fuel) | see `config/priors.yaml` | see file | tag in file |
| Valve-timing reading A | 0 / 20 / 20 / 0 as printed (200° duration) | — | WSM |
| Valve-timing reading B (main case) | 20° added to each flank, 240° duration, 40° overlap | — | WSM, interpretation |
| Engine point used for top speed | WOT to 9,500 rpm, power extrapolated | — | ASSUMED |

Total: 38 uncertain inputs and 8 design variables (compression ratio, ignition at low and high rpm, main-jet number, intake and exhaust phasing, cam duration scale, intake valve size scale) in `config/priors.yaml`. Design variables change only within the design rules (head skim ≤0.8 mm, valve-piston gap ≥1.0 mm, valve acceleration ratio ≤1.15, overlap ≤70°, intake valve/bore ≤0.58, ignition 0–40° BTDC, WOT lambda 0.78–1.0) and plausibility limits (bsfc ≥230 g/kWh, VE ≤1.10, power ≤9 hp, torque 2–7.5 Nm, brake efficiency ≤0.75 × Otto).
| idle_rpm | 1,500 | ±100 | OFFICIAL |
| rated_rpm | 7,500 | — | MEDIUM |

---

## 9. What this output means

**What it is.** A specification sheet built from official Atlas Honda documents, CD70-specific secondary sources, and an older CD70 workshop manual. Every value carries a tag, so you can see where it came from and how far to trust it.

**What is solid.** The geometry (47.0 × 41.4 mm, 72 cm³, 9.3:1 compression), the drivetrain (4-speed, 14/41 final drive, 420 chain), the official ignition type (AC-CDI), the spark plug (C7HSA), oil grade, idle speed, and tyres are backed by official Atlas documents and agree with independent sources. A model built on these will be on firm ground.

**What is provisional.** The valve timing, valve train dimensions, ignition advance, float level, jets, and gear ratios come from the older workshop manual alone. The same manual disagreed with the official Atlas documents on compression and chain slack, so it is probably a different edition. These values are the most likely to be wrong, and they drive the breathing and ignition behaviour that the optimisation will tune. A results paper must name them as provisional until a current CD70 manual is checked.

**Validation.** The model is calibrated to two published numbers and the 80–90 km/h real-world top speed and checked against physics tests, design rules and plausibility limits. It has not been validated against measurements of a real CD70.

**What is not known.** Current Euro II carburettor code and venturi size, the slow jet, ignition timing on the current engine, valve lift, head diameters, gear teeth, the 2026 national petrol octane, and the MMT limit. These are sensitivity variables, not fixed inputs.

**What the simulation output will mean.** The model will show how much torque and fuel efficiency could change from tuning compression, ignition advance, jetting, and valve timing, within these bounds. Results are predictions for a model calibrated to two published CD70 numbers (5.0–5.1 hp at 7,500 rpm and 5.0 Nm at 5,500 rpm). They are not measurements of a real engine . The paper can claim modelled trends, their uncertainty (a calibrated ensemble of engines, not one engine) and their sensitivity to the provisional inputs. It cannot claim measured gains.

**What to say in the paper.** State the source hierarchy in section 1. List the provisional inputs and the test that would confirm each one. Report the RON 87 and RON 92 scenarios separately. Keep the compression value at 9.3 as the official figure.

**What to do before submission.**
1. Obtain a current Atlas Honda CD70 workshop or service manual, or a printed copy, and re-check every WSM value.
2. Read the Euro II carburettor tag and the jets on a running CD70, and confirm the venturi.
3. Time the ignition on a running CD70 at 1,500 and 4,000 rpm.
4. Find a source for the MMT limit and the 2026 national octane grade.
5. Measure or find a valve lift and head diameters.

---

## 10. Source register (every source used across all versions, with status)

### Official (Atlas Honda)
| # | Source | Link | What it gives | Status (9 Oct 2026) |
|---|---|---|---|---|
| O1 | Atlas Honda CD70 product page | https://www.atlashonda.com.pk/cd70/ | Dimensions, 72 cc, 47.0 × 41.4, CR 9.3, 8.5 L tank, clutch, transmission, tyres, 82 kg dry, 136 mm clearance | **Fetched 9 Oct 2026**; last updated 1 Oct 2026 |
| O2 | Atlas Honda CD70 Specifications PDF | https://www.atlashonda.com.pk/wp-content/uploads/2025/08/CD70-Specifications.pdf | CR 9.3, C7HSA, plug gap 0.6–0.7, idle 1,500 ±100, chain 420 / 104 links, slack 20–30 mm, final drive 14/41, oil 20W-40 and 0.6 / 0.8 L, gear oil SAE 80/90, tyre pressures; some labels lost in extraction | **Fetched 9 Oct 2026**; partial labels |
| O3 | Atlas Honda CD70 Operation Guide PDF | https://www.atlashonda.com.pk/wp-content/uploads/2025/08/CD70-Operation-Guide.pdf | Oil SAE 20W-40, free play 2–6 mm, tyre pressures 25 / 29–33 psi | **Fetched 9 Oct 2026**; partial |
| O4 | Atlas Honda CD70 Tool Kit Information PDF | https://www.atlashonda.com.pk/wp-content/uploads/2025/08/CD70-Tool-Kit-Information.pdf | No engine specs extracted | Fetched 9 Oct 2026; not used |
| O5 | Atlas Honda CD70 Motorcycle Safety PDF | https://www.atlashonda.com.pk/wp-content/uploads/2025/08/CD70-Motorcycle-Safety.pdf | Safety notes | Listed on O1; not fetched |
| O6 | Hondazone CD70 Euro II carburettor (Atlas-branded) | https://hondazone.pk/product/honda-70-carburetor-euro-ii/ | Part is genuine Atlas, Euro II, CD70. No code or jets given. | Fetched 9 Oct 2026 |

### Workshop manual (older edition, provisional)
| # | Source | Link | What it gives | Status |
|---|---|---|---|---|
| W1 | CD70 Workshop Manual (Urdu), Atlas Honda, 186 pp. (unofficial Scribd upload) | https://www.scribd.com/document/958566633/CD70-Workshop-Manual-URDU | Valve timing, valve train, ignition, gears, jets, float, air screw, cranking compression, clearance | **Not accessible 9 Oct 2026** (JS-gated). Earlier text-layer read. User states older edition. |

### CD70-specific secondary
| # | Source | Link | What it gives | Status |
|---|---|---|---|---|
| S1 | Wikipedia, Honda 70 | https://en.wikipedia.org/wiki/Honda_70 | CR 9.3, 47.0 × 41.4, 5.0 hp @ 7,500, CDI, wheelbase 1,206, dimensions, dry weight 82 kg | Fetched 9 Oct 2026 |
| S2 | Wikipedia, Honda CD70 | https://en.wikipedia.org/wiki/Honda_CD70 | CR and bore match; 6.41 hp @ 9,500 (uncited infobox) and 0.53 kgf·m @ 8,000 | Conflicting infobox; power and torque rejected |
| S3 | PakWheels, CD70 price and specs | https://www.pakwheels.com/bikes/honda/cd-70--3/ | 72 cc, 47.0 × 41.4, CR 9.3 (table) / 8.8 (prose), 5.1 hp @ 7,500, 5.0 Nm @ 5,500 | Verified 8 Oct 2026; mixed CR |
| S4 | Urdupoint, CD70 specs | https://www.urdupoint.com/bikes/detail/honda/4/cd-70.html | 72 cc, 47.0 × 41.4, CR 9.3, 5.1 hp, 5.0 Nm | Verified 8 Oct 2026 |
| S5 | BikeBD, CD70 Dream 2022 vs C70 | https://bikebd.com/bike-compare/honda-cd70-dream-2022/vs/honda-c-70-1970 | CR 9.3, 47.0 × 41.4, 2.50-17 rear, 6.17 power in one column (rejected) | Fetched 9 Oct 2026 |
| S6 | BikeBD, C70 vs CD70 | https://bikebd.com/bike-compare/honda-c-70-1970/vs/honda-cd70 | CD70 5.2 hp, 5 Nm, 47.0 × 41.4, 2.50-17 rear, 1,897 mm length; C70 CR 8.8 | Fetched 9 Oct 2026 |
| S7 | Motorradundreisen, CD70 Dream 2022 | https://www.motorradundreisen.de/motorraddatenbank/honda/cd70-dream-13124.html | CR 9.3, bore × stroke 47 × 41.5 (rounded), 130 mm drum | Fetched 9 Oct 2026 |
| S8 | Motorradundreisen, CD70 | https://www.motorradundreisen.de/motorraddatenbank/honda/cd70-13123.html | Euro-II in 2012, same dimensions | Fetched 9 Oct 2026 |
| S9 | Motodealers, 2021 Atlas CD 70 specs | https://motodealers.co.uk/bikes/atlas-honda/cd-70/2021/specs | CR 8.8, tank 9.0 L, length 1,881 mm | Fetched 9 Oct 2026. Rejected for CR, tank, length. |
| S10 | Gari.pk, CD70 vs Pak Hero PH70 (2026) | https://www.gari.pk/bikes/compare/pak-hero-ph-70-10-vs-honda-cd-70-19 | 5.1 hp @ 7,500, 5.0 Nm @ 5,500, CR 9.3 (table), dry 82 kg, wheelbase 1,206 | Fetched 9 Oct 2026 |
| S11 | Gari.pk, CD70 Dream vs PH70 | https://www.gari.pk/bikes/compare/pak-hero-ph-70-10-vs-honda-cd-70-dream-29/ | CR 9.3, 5.1 hp, 5.0 Nm | Fetched 9 Oct 2026 |
| S12 | PakObserver, CD70 2026 model | https://pakobserver.net/honda-cd-70-2026-model-launched-in-pakistan-price-pictures-and-specs/ | CR 8.8 in table | Fetched 9 Oct 2026. Secondary. Conflicts with Atlas. |
| S13 | Daily Pakistan, CD70 2024 price | https://en.dailypakistan.com.pk/02-Sep-2023/honda-cd-70-2024-latest-price-in-september | CR 8.8, price | Secondary. Conflicts with Atlas. |
| S14 | StemedHub blog, CD70 2024 price | https://stemedhub.org/members/28175/blog/2024/05/price-honda-cd-70-2024-model-price-in-pakistan | CR 8.8, price | Secondary. Conflicts with Atlas. |
| S15 | Alibaba, Honda CD70 engine | https://alibaba.com/showroom/honda-cd70-engine.html | CR 9.4 (rejected), valve clearance "check every 3000 km" (no value) | Not used |
| S16 | SBRC2017 Atlas CD70 article | https://sbrc2017.ufpa.br/trip/atlas-honda-cd70-motorcycle | CR "approximately 9.3:1" | Low-quality. Not used as primary. |
| S17 | Bikez, CD70 2022 | https://bikez.com/motorcycles/honda_cd70_2022.php | CR, bore, stroke, weight, tank | Not re-checked this session |
| S18 | Retailer, CD70 MotoPartsPakistan | https://quickreviewsandgui.wixsite.com/motopartspakistan/cd70-important-instructions-from-ow | Valve clearance 0.10 mm (IN and EX), plug gap, chain slack 20–30 mm, oil | Verified 8 Oct 2026. Values unlabelled. |
| S19 | CMSNL CD70 parts catalogue | https://www.cmsnl.com/honda-cd70_model50394/partslist/ | Part numbers; slow jet sizes #38 / #40 / #42 | Verified earlier; parts only |
| S20 | Oro2u, PZ18 carburettor (CD70 1997–2004 fitment) | https://www.oro2u.com/carburetor-assy-97-04-honda-cd-xr-crf-r-f-70-16-5mm-pb12h-pb12j-pb12k-16100-gcf-672 | PZ18 code, PB12H/J/K types, CD70 fitment, venturi 18 mm and 16.5 mm | Fetched 9 Oct 2026. Retailer. |
| S21 | Oro2u, second PZ18 listing | https://www.oro2u.com/carburetor-assy-honda-xr-crf-r-f-70-16-5mm-pb12h-pb12j-pb12k-16100-gcf-672 | Venturi 16.5 mm, PZ18 | Fetched 9 Oct 2026 |
| S22 | Randakks, Keihin main jet sizes #60–#78 | https://www.randakks.com/main-jet-primary-keihin-99201-601-type-sizes-60-to-78.html | Available Keihin main jet sizes | Fetched 9 Oct 2026. General, not CD70. |
| S23 | Vintage Honda twins forum, slow / pilot jets | https://www.vintagehondatwins.com/forums/goto/post?id=39609 | #35 slow / pilot on CB/CL 350 and 360 | Fetched 9 Oct 2026. Other models. |
| S24 | PakWheels forum, CD70 carburettor setting | https://www.pakwheels.com/forums/t/cd70-carbourater-setting/261042 | Air screw 1.25 / 1.75 turns; PZ16 / PZI6 code | Owner posts. LOW. |
| S25 | PakWheels forum, Honda CD 70 carburettor | https://www.pakwheels.com/forums/t/honda-cd-70-carborator/210022 | Owner carb discussion | Owner posts. LOW. |
| S26 | Motorcycle Spare Parts, C70Z carburettor parts | https://www.motorcyclespareparts.eu/en/honda-parts/1982-c70z-scooters/carburettor-2 | C70Z main #72, slow #38 | Sibling model. Not used for CD70. |
| S27 | LRIO, Honda C70 specifications | https://lrio.com/news/motos/c70/c70-specifications | C70 timing, clearance, float 10.7 mm | Sibling model. Not used for CD70. |
| S28 | Webbikeworld, Honda C70 Passport | https://www.webbikeworld.com/honda-cub-70/ | C70 CR 8.8:1 | Sibling model. Source of the 8.8 figure. |
| S29 | Honda ST / CH50–70 shop manual (scanned) | https://files.semestergas.se/Honda_4-takt/Shop_Manual_Honda_ST-_CH50-70_-_'69-'82.pdf | ST50 / ST70 / CT70 shop manual | Blocked (403). Not used. |
| S30 | Classic Honda 50 Australia, CT70 manual (scanned) | https://www.classichonda50saustralia.com.au/Tech%20Info/CT70%2069-82%20Manual%20-%2013.5MB.pdf | CT70 shop manual | Blocked (403). Not used. |
| S31 | Archive.org, Honda C70 shop manual | https://archive.org/details/C70ShopManual | C70 shop manual 1980–82 | Not checked |
| S32 | K&L valve set, C70K / CT70 family | https://4into1.com/k-l-engine-valve-set-honda-s65-c-ct-sl-xl70/ | Head diameters 25 / 21.9 mm | Family proxy |
| S33 | Con-Rods.com, CD70 kit | https://www.con-rods.com/for-honda-cd70-036.html | Rod 91 mm centre to centre; 23.1 mm pin (rejected) | Aftermarket, CD70 listed |
| S34 | Howtomotorcyclerepair, XR70R valve adjustment | https://howtomotorcyclerepair.com/how-to-honda-50-70cc-valve-adjustment-xr70r/ | XR70R 0.002 in ± 0.001 | Different model. Not used. |
| S35 | JE Pistons, valve clearance guide | https://info.jepistons.com/checking-and-adjusting-valve-clearance-on-your-motorcycle | Generic method | Not used |
| S36 | Business Recorder, OGRA fuel | https://www.brecorder.com/news/404758 | Fuel grade context (from v6) | Listed earlier; not re-checked |

### Octane and fuel news
| # | Source | Link | What it gives | Status |
|---|---|---|---|---|
| F1 | PakWheels blog, agreement to higher-grade petrol | https://www.pakwheels.com/blog/agreement-signed-higher-grade-petrol/amp | 87 → 92 RON plan; 90 RON partial rollout | Fetched 9 Oct 2026. Undated in the page. |
| F2 | PakWheels blog, RON 91 question | https://www.pakwheels.com/blog/?p=53259 | Same agreement text | Secondary |
| F3 | The News, RON 92 import | https://www.thenews.com.pk/print/145758-Import-of-RON-92-standard-petrol-likely-to-start-in-November | RON 92 import from November | Dated 2019–2020 |
| F4 | ProPakistani, RON 92 | https://propakistani.pk/?p=107513 | 92 RON stations | Dated 2019–2020 |
| F5 | Carspirit, RON 92 approved by ECC | https://carspiritpk.com/ron-92-petrol-approved-for-use-in-pakistan-by-ecc | ECC approval of RON 92; price gap Rs 2.74/L | Dated 2019–2020 |
| F6 | PakWheels, Shell premium fuel | https://www.pakwheels.com/blog/shell-prepared-satisfy-premium-fuel-demand-pakistan/amp | Premium fuel deregulation | Undated |
| F7 | ARY, petrol price Aug 2026 | https://www.arynews.tv/petrol-price-in-pakistan-for-august-13-2026 | Rs 324.98/L; no RON stated | 2026. Grade not confirmed. |
| F8 | ARY, petrol price Oct (older) | https://arynews.tv/?p=251963 | Rs 73.50/L in an earlier year | Historical |

### Research and validation references (from research plan)
| # | Source | Link | Use |
|---|---|---|---|
| R1 | Morrissey and Shedd, SAE 2008-32-0043 | https://doi.org/10.4271/2008-32-0043 | Validation case |
| R2 | Avelar et al., SAE 2019-36-0170 | https://doi.org/10.4271/2019-36-0170 | GT-Power calibration |
| R3 | Peñaranda et al., ITA, Honda GX-35 | https://amcaonline.org.ar/ojs/index.php/mc/article/download/3359/3278 | 1D calibration, Wiebe |
| R4 | Dresler and Richtář, MZ125 | https://pernerscontacts.upce.cz/index.php/perner/article/download/900/734/1569 | Wiebe single-cylinder model |
| R5 | Deb et al., NSGA-II | https://repository.ias.ac.in/9403 | Stage 6 optimiser |
| R6 | Akiba et al., Optuna | https://arxiv.org/pdf/1907.10902 | Stage 6 comparison |
| R7 | OpenWAM documentation | https://openwam.webs.upv.es/docs/ | Cross-check simulator |
| R8 | Heywood, *Internal Combustion Engine Fundamentals* (textbook, no link) | — | Submodels |

### Sources rejected (checked, not used for CD70 values)
| Source | Link | Reason |
|---|---|---|
| bike-parts.fr owner manuals (CRF250, TRX, XR and similar) | https://www.bike-parts.fr/thumbs/pdf_url/img/owner_manuals/owner_CRF250RJ_EN/2500_2500/0075.pdf (and related pages) | Other Honda models. Valve values do not apply to CD70. |
| Alibaba CD70 page | https://alibaba.com/showroom/honda-cd70-engine.html | Unsourced; CR 9.4 conflicts with Atlas |

### Project documents and owner data
| # | Source | Use |
|---|---|---|
| P1 | Project owner statement: real-world top speed of a stock CD70 is 80–90 km/h | cal_4 target |
| P2 | Project model documents `docs/MODEL_SPEC.md`, `docs/ANALYSIS_SPEC.md`, `docs/CLAIM_RULES.md`, `docs/LIMITATIONS.md` | method definitions |

### Sources in earlier versions with no recorded link
- **MMT limit (40 mg/L, then 24 mg/L):** the earlier sheets did not record a link. Find and add the 2018 directive before submission.
- **Carburettor codes PZ19 and PZ22 (from the user's message):** not found in any page checked. Add the source if one exists.
- **daraz, OLX, techmen carburettor pages (from the user's message):** not opened. Check and add if used.
