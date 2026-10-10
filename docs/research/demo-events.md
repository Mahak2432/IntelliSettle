# Demo claim scenarios: real Bihar events + one fake

Research date: 2026-10-10. All four scenarios are in **Bihar**: two districts, Darbhanga and Araria.
Every rainfall number below was fetched live from the Open-Meteo historical archive (`archive-api.open-meteo.com`, default `best_match` model, `timezone=Asia/Kolkata`).
Every Sentinel-1 date comes from the Copernicus Data Space OData catalogue (IW GRD products).
Radar backscatter values were sampled from Microsoft Planetary Computer's free `sentinel-1-rtc` collection, which uses the same S1 scenes after terrain correction. Each value is the mean of a 3x3 sample, about 60 m across, around the plot.
A drop in VV to below about -15 dB is treated as open water.

## Summary

| ID | Kind | Peril | Crop / season | Place (district > block > village) | Plot lat, lon | Event date | Max 1-day rain (Open-Meteo) | Sentinel-1 before / after | News | Overall |
|---|---|---|---|---|---|---|---|---|---|---|
| A | real | flood (Kosi embankment breach) | Paddy, Kharif 2024 | Darbhanga > Kiratpur > Bhobhaul (Bhubhaul) | 25.97100, 86.36300 | 2024-09-29/30 (night) | 50.3 mm (26 Sep); **0.7 mm on breach day** | Sep 24, Sep 27 / **Oct 6, Oct 9** (VV -5.5 dB -> -17.2 dB) | 4 sources incl. Lok Sabha question | **Strong** (radar + news). Rain was moderate, and the flood came on a dry day |
| B | real | excess_rain | Paddy, Kharif 2021 (harvest stage) | Araria > Sikti > Thengapur Pipra (next to Kauakoh) | 26.34800, 87.47500 | 2021-10-19 | **211.7 mm** (19 Oct) | Oct 8, Oct 17 / **Oct 20** (14 h after the rain), Oct 25 | DTE + 2 IMD press releases (Forbesganj gauge 26 cm) | **Strong** (rain + news). Radar shows brief ponding |
| C | real | hailstorm | Maize, Rabi 2025-26 (wheat also hit) | Araria > Forbesganj > Bhadesar | 26.33750, 87.25550 | 2026-03-20 (evening/night) | 47.5 mm (20 Mar), after 5 dry days | Mar 9, Mar 16 / **Mar 21** (8 h after), Mar 25, Mar 28 | 4 items: Patna Press x3, IANS; state paid input subsidy Jun 2026 (Araria on list) | **Medium-strong** (news + rain spike). Hail itself is not measurable from rain/radar |
| D | **fake** | flood (claimed) | Paddy, Kharif 2023 | Darbhanga > Kiratpur > Bhobhaul (same plot as A) | 25.97100, 86.36300 | claimed 2023-10-25 | **0.4 mm** (whole +-5 day window: 0.4 mm) | Oct 15, Oct 24 / Oct 27, Nov 5: all dry (VV -5 to -6 dB) | none found | **Contradicted by every source** |

Recommended demo set: **A + B + C (real) and D (fake)**.

---

## A. Riverine flood: Kosi western-embankment breach at Bhobhaul, Kiratpur block, Darbhanga (29-30 Sep 2024)

**What happened.** Very heavy rain fell in Nepal. On 28 Sep 2024, Birpur barrage released about 6.61 lakh cusecs from the Kosi, the highest release since 1968.
At about 01:00 IST on the night of 29/30 Sep, the **western Kosi embankment breached near Bhobhaul village** (also spelled Bhubhaul or Bhubhol; Census 2011 code 227790, Narkatia Bhandara panchayat). The breach was about 80 ft wide.
It flooded villages in **Kiratpur and Ghanshyampur blocks** (and Gaura Bauram), and standing **paddy** was destroyed.

**Location used**
- Village centroid (GeoNames, "Bhobhaul, Darbhanga > Kiratpur"): 25.97258, 86.36734.
- **Demo farm plot: 25.97100, 86.36300.** These are paddy fields about 450 m WSW of the village, on the country side, just west of the embankment. Radar confirms they flooded (see below).

**News / government sources**

| Publisher | Date | Fact (paraphrased) | URL |
|---|---|---|---|
| Down To Earth | 2024-09-30 | Kosi breached its western embankment near Bhubhol (Darbhanga) late on 29 Sep. Dozens of villages in five panchayats were inundated, 15-16 brick houses were wrecked, and standing paddy was destroyed. (It names the block "Kartarpur", an evident typo for Kiratpur.) | https://www.downtoearth.org.in/amp/story/natural-disasters/swollen-kosi-bagmati-gandak-breach-embankments-wreak-havoc-in-flood-hit-bihar |
| DD News (Prasar Bharati) | 2024-09-30 | The embankment near Bhubhaul (Kiratpur block) gave way at about 1 am after a night-long effort to save it. Water spread into Kiratpur and Ghanshyampur blocks. | https://ddnews.gov.in/nearly-16-lakh-population-affected-by-flood-in-north-bihar-06-people-died-due-to-drowning-in-kosi-seemanchal-1/ |
| IANS (via Morung Express) | 2024-09-30 | The Kiratpur-block embankment failed under the Kosi current and about 25 villages in Kiratpur and Ghanshyampur blocks went under. Farmers lost paddy, maize and sugarcane. (It spells the village "Badaul".) | https://morungexpress.com/devastating-floods-turn-villages-into-islands-in-north-bihar |
| Lok Sabha, Unstarred Q. 3061 | 2025-08-07 | The Darbhanga MP asked about the devastation in Kiratpur, Gaura Bauram and Ghanshyampur caused by the western Kosi embankment breach near Bhubhaul in the last week of Sep 2024. | https://eparlib.sansad.in/bitstream/123456789/2994807/2/AU3061_dBhtwm_hindi.pdf |

**Rainfall (Open-Meteo, grid cell 25.975, 86.361)**

| Date | 09-24 | 09-25 | 09-26 | 09-27 | 09-28 | **09-29** | **09-30** | 10-01 | 10-02 | 10-03 | 10-04 | 10-05 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| mm | 14.4 | 5.4 | 50.3 | 44.9 | 45.5 | **0.7** | **0.8** | 0.6 | 0.2 | 15.5 | 7.4 | 0.3 |

Max 1-day: **50.3 mm (26 Sep)**. The breach and inundation came on **dry days** (under 1 mm on 29 Sep to 2 Oct).
Caveat: local rain was not trivial. The same monsoon low dropped about 140 mm over 26-28 Sep. But the Sep 27 radar pass, taken after the first ~95 mm, shows **no** ponding at the plot. The water only appears after the breach.
Demo point: the flood came from the river, not from local rain.

**Sentinel-1 (Copernicus catalogue, 10 Sep to 15 Oct 2024; S1A only)**
2024-09-12, 09-15, 09-24, 09-27 (before) | **2024-10-06, 10-09** (after) | also 10-18, 10-21 (recession).
There was no pass between 27 Sep and 6 Oct (12-day S1A revisit), so the first post-event look is 6-7 days after the breach.

Backscatter at the plot (VV, dB):

| 09-03 | 09-15 | 09-24 | 09-27 | **10-06** | **10-09** | 10-18 | 10-21 |
|---|---|---|---|---|---|---|---|
| -7.3 | -5.5 | -7.5 | -5.5 | **-17.2** | **-16.2** | -11.6 | -11.6 |

A second flooded field, 3.5 km south (25.94000, 86.36100), reads -5.4 dB on 27 Sep and **-18.5 / -18.6 dB** on 6 / 9 Oct.
Change detection over a 7 x 9 km box around Bhobhaul shows about 5 km² of new open water on 6 Oct and about 3.7 km² on 9 Oct. The control pair (15 vs 27 Sep) shows essentially none.

**Verdict.** Radar: **strong**, with an ~10-12 dB drop and a clean before/after on two independent orbits. News: **strong**, with 4 sources naming the village or block and paddy loss. Rain: **weak to moderate**, which is the intended contrast because the flood was riverine.
Caveats:
- The first post-event pass is 6 days late, so peak extent is not imaged.
- Village spelling varies (Bhobhaul / Bhubhaul / Bhubhol / Badaul).
- Use the plot coordinate, not the village centroid. The settlement itself never reads as water.

---

## B. Excess rainfall: 18-19 Oct 2021 unseasonal deluge, Sikti block, Araria

**What happened.** A low-pressure area over Bihar dumped extreme rain on harvest-stage paddy in Seemanchal on 18-19 Oct 2021, after the monsoon had withdrawn.
IMD's 24-h report ending 08:30 IST on 20 Oct listed **Forbesganj 26 cm**, the highest in Bihar.
Down To Earth reported harvested and standing paddy damaged in Araria. It quoted a farmer from a village under **Sikti block** and another from near Forbesganj, whose standing paddy was submerged.

**Location used.** Thengapur Pipra, Sikti block (GeoNames village centroid 26.35024, 87.47328). Kauakoh (26.34868, 87.46522) is the next village west.
**Demo plot: 26.34800, 87.47500**, a low paddy field about 300 m SE of the village centroid.

**News / government sources**

| Publisher | Date | Fact (paraphrased) | URL |
|---|---|---|---|
| Down To Earth | 2021-10-20 | Unexpected heavy rain on 18-19 Oct damaged harvested and standing paddy in Araria (KVK Araria scientist). A Sikti-block farmer described paddy drying in fields and flowering paddy being hit. A Forbesganj-area farmer said submerged paddy would not recover. District officials ordered block-level surveys. | https://www.downtoearth.org.in/news/agriculture/heavy-rains-damage-paddy-crop-in-bihar-s-seemanchal-and-kosi-regions-79779 |
| IMD press release No. 1298 | 2021-10-20 | Past-24-h heavy rainfall for Bihar: Forbesganj 26 cm, Supaul 11 cm, Purnea 7 cm. | https://internal.imd.gov.in/press_release/20211020_pr_1298.pdf |
| IMD press release No. 1297 | 2021-10-19 | A low-pressure area over Bihar was expected to bring isolated very heavy falls over Bihar on 19 Oct. | https://internal.imd.gov.in/press_release/20211019_pr_1297.pdf |

**Rainfall (Open-Meteo, grid cell 26.327, 87.429)**

| Date | 10-14 | 10-15 | 10-16 | 10-17 | 10-18 | **10-19** | 10-20 | 10-21 | 10-22 | 10-23 | 10-24 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| mm | 0.0 | 0.0 | 5.7 | 2.3 | 19.5 | **211.7** | 19.3 | 2.0 | 0.0 | 1.4 | 0.0 |

Max 1-day: **211.7 mm (19 Oct)**. Hourly data shows the burst ran 08:00-16:00 IST on 19 Oct, peaking at 28.8 mm/h at 11:00. The highest rolling 24-h total is 220.5 mm (18 Oct 18:00 to 19 Oct 17:00).
For comparison, Open-Meteo at the Forbesganj gauge gives 158.2 mm, against IMD's 260 mm observed.

**Sentinel-1 (Copernicus catalogue, 29 Sep to 3 Nov 2021; S1A only)**
2021-10-01, 10-05, 10-08, 10-13, 10-17 (before) | **2021-10-20** (05:33 IST, about 14 h after the rain stopped), 10-25, 10-29, 11-01.

Backscatter at the plot (VV, dB):

| 10-01 | 10-05 | 10-08 | 10-13 | 10-17 | **10-20** | 10-25 | 10-29 |
|---|---|---|---|---|---|---|---|
| -9.8 | -10.9 | -10.7 | -11.9 | -11.8 | **-15.9** | -7.4 | -9.8 |

The plot shows short-lived ponding on 20 Oct, a 5 dB drop on the same orbit as 8 Oct, and it had drained by 25 Oct. Across the wider 40 x 20 km area, most fields **brightened** (wet soil and canopy) rather than flooding. Open water appeared only along streams and low fields around Kauakoh and Pipra.

**Verdict.** Rain: **very strong** (211.7 mm modelled; an IMD gauge 22 km away logged 260 mm). News: **strong** (national outlet naming the block and crop, plus IMD). Radar: **supporting**, with an ideally timed pass showing brief waterlogging, though excess-rain damage does not need standing water.
Caveats:
- Only one non-government news article names the block.
- The IMD gauge is in Forbesganj block, not Sikti.
- Bihar ran no PMFBY in 2021 (it uses its own state scheme). That doesn't matter for a demo.

---

## C. Hailstorm: 20 Mar 2026 hail and squall, Forbesganj block, Araria

**What happened.** On the night of Friday 20 Mar 2026, a nor'wester-type storm with hail swept north-east Bihar.
- Patna Press reported **hail falling for about half an hour in Forbesganj**. It said the Patna Met Centre listed Araria, Katihar and Vaishali as hail-hit areas.
- IANS reported heavy damage to **maize and wheat** from wind, rain and hail. It also reported two children killed in a wall collapse in Araria.
- The state later found **over 33% crop damage in 13 districts, including Araria**, from the third and fourth weeks of March. On 22 Jun 2026 it paid over Rs 200 crore input subsidy to about 3.96 lakh farmers.

**Location used.** Bhadesar, Forbesganj block (GeoNames village centroid 26.33449, 87.24941; about 3.5 km north of Forbesganj town).
**Demo plot: 26.33750, 87.25550**, fields about 700 m ENE of the village. Rabi maize is the main standing crop here in March, and wheat was near harvest.

**News / government sources**

| Publisher | Date | Fact (paraphrased) | URL |
|---|---|---|---|
| Patna Press | 2026-03-20 | Storms, rain and hail on Friday 20 Mar. Hail fell for about 30 min in Forbesganj (Araria). The Patna Met Centre named Araria, Katihar and Vaishali as hail areas. Red alert in 15 districts. | https://patnapress.com/bihar-weather-storms-rain-hail-two-dead-red-alert-15-districts/ |
| IANS (via Morung Express) | 2026-03-21 | Storm, rain, hail and lightning from Friday into Saturday heavily damaged maize and wheat. 6 deaths, including 2 children in Araria (wall collapse). | https://morungexpress.com/bihar-lightning-kills-6-injures-10-others |
| Patna Press | 2026-03-22 | Standing wheat, mustard, gram and maize flattened across the Kosi-Seemanchal belt just before harvest. DMs ordered to survey, with losses over 33% sent to the disaster department. | https://patnapress.com/?p=66430 |
| Patna Press (also UNI, same day) | 2026-06-22 | CM Samrat Choudhary paid over Rs 200 crore input subsidy to 3.96 lakh farmers for storm, untimely rain and **hail** in the 3rd and 4th weeks of March 2026. Over 33% damage was confirmed in 13 districts, **Araria among them**. | https://patnapress.com/?p=80378 |

**Rainfall (Open-Meteo, grid cell 26.327, 87.231)**

| Date | 03-15 | 03-16 | 03-17 | 03-18 | 03-19 | **03-20** | 03-21 | 03-22 | 03-23 | 03-24 | 03-25 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| mm | 0.0 | 0.2 | 0.1 | 0.0 | 0.0 | **47.5** | 12.0 | 0.0 | 0.0 | 3.8 | 0.0 |

Max 1-day: **47.5 mm (20 Mar)**. Hourly data shows convective rain from 17:00 to 23:00 IST, peaking at 14.7 mm/h at 21:00. Temperature fell from 30.8 °C at noon to about 20.5 °C by 21:00, and the daily maximum dropped from 31.2 °C to 22.5 °C the next day.
Both are classic signatures of a hail-bearing thunderstorm, but **ERA5 cannot detect hail**. The archive's `weather_code` only reaches 65 (heavy rain), never 96/99. ERA5 gusts (max 35 km/h) understate convective squalls.

**Sentinel-1 (Copernicus catalogue, 28 Feb to 5 Apr 2026; S1A only at this point)**
2026-03-01, 03-04, 03-09, 03-13, 03-16 (before) | **2026-03-21** (05:41 IST, about 8 h after the storm), 03-25, 03-28.

Backscatter at the plot (VV, dB):

| 03-01 | 03-04 | 03-09 | 03-13 | 03-16 | **03-21** | 03-25 | 03-28 |
|---|---|---|---|---|---|---|---|
| -11.4 | -13.7 | -11.7 | -12.3 | -11.6 | **-8.1** | -5.8 | -8.0 |

The plot brightened by about 3.6 dB on the same orbit (9 vs 21 Mar, and 16 vs 28 Mar), and it stayed bright for a week. That is consistent with canopy change (lodging) and/or wet soil. It is **not diagnostic of hail**.

**Verdict.** News: **good**. The hail is placed in Forbesganj block by name, and the official compensation list includes Araria. Rain: **supporting**, with a sharp storm-day spike after a dry week and a temperature crash. Radar: **neutral or supporting only**.
Caveats:
- Three of the four items come from one regional outlet (Patna Press). IANS and UNI corroborate, but without naming the block.
- No village-level hail report was found, so the village is chosen inside the named block.
- Hail cannot be proven from ERA5 or SAR. Present it as "news-led" in the demo.

---

## D. FAKE: flood claimed at Bhobhaul (same plot as A) on 25 Oct 2023

**Claim to stage.** "River flood submerged my standing paddy on 25 Oct 2023", at plot 25.97100, 86.36300, Kiratpur block, Darbhanga.

**Rainfall (Open-Meteo, grid cell 25.975, 86.361)**

| Date | 10-20 | 10-21 | 10-22 | 10-23 | 10-24 | **10-25** | 10-26 | 10-27 | 10-28 | 10-29 | 10-30 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| mm | 0.0 | 0.0 | 0.0 | 0.0 | 0.4 | **0.0** | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |

The +-5 day total is **0.4 mm**, and the max 1-day is 0.4 mm. The last rain was 5.3 mm on 17 Oct.

**Sentinel-1 (Copernicus catalogue, 5 Oct to 9 Nov 2023):** 2023-10-12, 10-15, 10-24 | 10-27, 11-05, 11-08.

| 10-03 | 10-12 | 10-15 | 10-24 | 10-27 | 11-05 | 11-08 |
|---|---|---|---|---|---|---|
| -6.1 | -8.0 | -5.5 | -5.9 | -6.0 | -5.1 | -3.8 |

These read as dry vegetated fields throughout, with no water signature. Compare A's -17 dB on the same plot.

**News:** a search found no flood, breach or heavy-rain reports for Kiratpur or Darbhanga in Oct 2023.

**Why this date.** It is the same village as real event A, so the contrast is clean. Paddy is still standing in late October, so the claim is plausible on its face.
Dates to **avoid** for the fake, because real events happened nearby:
- 29 Sep to ~20 Oct 2024: the A flood and its recession.
- ~15 Jan 2025: a Genhua-river flash flood damaged rabi crops in Kiratpur (Down To Earth).
- 3-5 Oct 2025: about 100 mm of rain in the region, and Darbhanga is on the state's Oct/Nov 2025 crop-compensation list.
- A fully dry alternative: 10-25 Oct 2025 has 0.0 mm. But it falls just 1-3 weeks after the 4-5 Oct 2025 heavy rain, so a news check might get confused. 25 Oct 2023 is cleaner.

---

## Candidates checked and not chosen (for transparency)

- **Bagmati breach at Madhkaul, Belsand block, Sitamarhi (29 Sep 2024).** There is a better-timed S1 pair (20 Sep / **2 Oct**), and new water is visible SE of Belsand. But sources disagree on whether it breached or seeped, and village coordinates are not in open gazetteers. This is a good backup for A.
- **Late Sep 2019 Patna/Darbhanga rains.** Open-Meteo gives 260 mm/day near Benipur (Darbhanga), but the Bihar WRD gauge logged only 92.4 mm, so the model overstates. Rejected for B.
- **4 Oct 2025 extreme rain.** IMD logged Maharajganj (Siwan) 32 cm and Kesariya (E. Champaran) 25 cm; Open-Meteo gives 162 mm and 124 mm. The rain is strong, but no block-level crop-loss reporting was found. Backup for B (East Champaran is on the state's compensation list).
- **9-10 Apr 2025 Bihar storms (Nalanda etc.).** Widely reported deaths and wheat damage, but no block-level hail location, and wheat was largely being harvested. Rejected in favour of C.
- **Cyclone Montha remnants (30-31 Oct 2025).** At most about 145 mm/day, and only on the Nepal border. Weaker than B.

## Reproduce

- Rain: `https://archive-api.open-meteo.com/v1/archive?latitude=LAT&longitude=LON&start_date=...&end_date=...&daily=precipitation_sum,rain_sum&timezone=Asia%2FKolkata` (add `&hourly=precipitation,temperature_2m` for event-day detail). Values may shift slightly if Open-Meteo re-processes; these were fetched on 2026-10-10.
- S1 catalogue: `https://catalogue.dataspace.copernicus.eu/odata/v1/Products?$filter=Collection/Name eq 'SENTINEL-1' and OData.CSC.Intersects(area=geography'SRID=4326;POINT(LON LAT)') and ContentDate/Start gt ... and contains(Name,'GRD')&$orderby=ContentDate/Start&$top=100` (ignore `_COG` duplicates).
- Backscatter: `https://planetarycomputer.microsoft.com/api/data/v1/item/point/LON,LAT?collection=sentinel-1-rtc&item=<S1 product id>_rtc&assets=vv&assets=vh` (linear gamma0; dB = 10*log10).
- Only Sentinel-1A products covered these points in these windows. S1C products exist over Bihar (e.g. 2025-10-09), but none over these plots in the chosen windows.

```json
[
  {
    "id": "A-flood-bhobhaul-2024",
    "kind": "real",
    "peril": "flood",
    "crop": "paddy",
    "season": "Kharif 2024",
    "state": "Bihar",
    "district": "Darbhanga",
    "block": "Kiratpur",
    "village": "Bhobhaul (also spelled Bhubhaul / Bhubhol)",
    "lat": 25.97100,
    "lon": 86.36300,
    "event_start": "2024-09-29",
    "event_end": "2024-10-09",
    "rainfall_daily_mm": {
      "2024-09-24": 14.4, "2024-09-25": 5.4, "2024-09-26": 50.3, "2024-09-27": 44.9,
      "2024-09-28": 45.5, "2024-09-29": 0.7, "2024-09-30": 0.8, "2024-10-01": 0.6,
      "2024-10-02": 0.2, "2024-10-03": 15.5, "2024-10-04": 7.4, "2024-10-05": 0.3
    },
    "max_1day_rain_mm": 50.3,
    "s1_acquisitions": ["2024-09-12", "2024-09-15", "2024-09-24", "2024-09-27", "2024-10-06", "2024-10-09"],
    "news": [
      {"url": "https://www.downtoearth.org.in/amp/story/natural-disasters/swollen-kosi-bagmati-gandak-breach-embankments-wreak-havoc-in-flood-hit-bihar", "publisher": "Down To Earth", "date": "2024-09-30", "fact": "Kosi western embankment breached near Bhubhol (Darbhanga) late on 29 Sep; dozens of villages in five panchayats flooded and standing paddy destroyed."},
      {"url": "https://ddnews.gov.in/nearly-16-lakh-population-affected-by-flood-in-north-bihar-06-people-died-due-to-drowning-in-kosi-seemanchal-1/", "publisher": "DD News (Prasar Bharati)", "date": "2024-09-30", "fact": "Embankment near Bhubhaul, Kiratpur block, gave way around 1 am; floodwater spread into Kiratpur and Ghanshyampur blocks."},
      {"url": "https://morungexpress.com/devastating-floods-turn-villages-into-islands-in-north-bihar", "publisher": "IANS via Morung Express", "date": "2024-09-30", "fact": "Kiratpur-block embankment failed; about 25 villages in Kiratpur and Ghanshyampur blocks submerged; paddy, maize and sugarcane lost."},
      {"url": "https://eparlib.sansad.in/bitstream/123456789/2994807/2/AU3061_dBhtwm_hindi.pdf", "publisher": "Lok Sabha (Unstarred Question 3061)", "date": "2025-08-07", "fact": "MP raised the devastation in Kiratpur, Gaura Bauram and Ghanshyampur from the Kosi western embankment breach near Bhubhaul in late Sep 2024."}
    ],
    "notes": "Riverine flood from record Kosi barrage release (6.61 lakh cusecs, 28 Sep). Breach ~01:00 IST on 30 Sep (night of 29/30). Local rain ~140 mm over 26-28 Sep but <1 mm on breach day; S1 on 27 Sep (after ~95 mm) shows no ponding. Plot VV: -5.5 dB (27 Sep) -> -17.2 dB (6 Oct) and -16.2 dB (9 Oct), -11.6 dB by 18 Oct. ~5 km2 new open water within 7x9 km of the village on 6 Oct. No S1 pass between 27 Sep and 6 Oct, so peak not imaged. Village centroid (GeoNames) 25.97258, 86.36734; plot is ~450 m WSW in flooded fields."
  },
  {
    "id": "B-excess-rain-sikti-2021",
    "kind": "real",
    "peril": "excess_rain",
    "crop": "paddy",
    "season": "Kharif 2021",
    "state": "Bihar",
    "district": "Araria",
    "block": "Sikti",
    "village": "Thengapur Pipra (adjacent to Kauakoh)",
    "lat": 26.34800,
    "lon": 87.47500,
    "event_start": "2021-10-18",
    "event_end": "2021-10-20",
    "rainfall_daily_mm": {
      "2021-10-14": 0.0, "2021-10-15": 0.0, "2021-10-16": 5.7, "2021-10-17": 2.3,
      "2021-10-18": 19.5, "2021-10-19": 211.7, "2021-10-20": 19.3, "2021-10-21": 2.0,
      "2021-10-22": 0.0, "2021-10-23": 1.4, "2021-10-24": 0.0
    },
    "max_1day_rain_mm": 211.7,
    "s1_acquisitions": ["2021-10-01", "2021-10-05", "2021-10-08", "2021-10-13", "2021-10-17", "2021-10-20", "2021-10-25", "2021-10-29", "2021-11-01"],
    "news": [
      {"url": "https://www.downtoearth.org.in/news/agriculture/heavy-rains-damage-paddy-crop-in-bihar-s-seemanchal-and-kosi-regions-79779", "publisher": "Down To Earth", "date": "2021-10-20", "fact": "Unexpected heavy rain on 18-19 Oct damaged harvested and standing paddy in Araria; farmers from Sikti block and near Forbesganj describe losses; block-level surveys ordered."},
      {"url": "https://internal.imd.gov.in/press_release/20211020_pr_1298.pdf", "publisher": "India Meteorological Department (press release 1298)", "date": "2021-10-20", "fact": "24-h heavy rainfall in Bihar to 08:30 IST 20 Oct: Forbesganj 26 cm, Supaul 11 cm, Purnea 7 cm."},
      {"url": "https://internal.imd.gov.in/press_release/20211019_pr_1297.pdf", "publisher": "India Meteorological Department (press release 1297)", "date": "2021-10-19", "fact": "Low-pressure area over Bihar; isolated very heavy rainfall expected over Bihar on 19 Oct."}
    ],
    "notes": "Post-monsoon deluge on harvest-stage paddy. Hourly burst 08:00-16:00 IST 19 Oct (peak 28.8 mm/h); max rolling 24 h 220.5 mm. Open-Meteo underestimates the Forbesganj gauge (158 vs 260 mm) but still >200 mm here. S1 on 20 Oct (05:33 IST, ~14 h after rain): plot VV -10.7 dB (8 Oct, same orbit) -> -15.9 dB (brief ponding), -7.4 dB on 25 Oct (drained). Area-wide response is mostly brightening (wet soil/canopy) rather than flooding. Village centroid (GeoNames) 26.35024, 87.47328."
  },
  {
    "id": "C-hail-forbesganj-2026",
    "kind": "real",
    "peril": "hailstorm",
    "crop": "maize",
    "season": "Rabi 2025-26",
    "state": "Bihar",
    "district": "Araria",
    "block": "Forbesganj",
    "village": "Bhadesar",
    "lat": 26.33750,
    "lon": 87.25550,
    "event_start": "2026-03-20",
    "event_end": "2026-03-21",
    "rainfall_daily_mm": {
      "2026-03-15": 0.0, "2026-03-16": 0.2, "2026-03-17": 0.1, "2026-03-18": 0.0,
      "2026-03-19": 0.0, "2026-03-20": 47.5, "2026-03-21": 12.0, "2026-03-22": 0.0,
      "2026-03-23": 0.0, "2026-03-24": 3.8, "2026-03-25": 0.0
    },
    "max_1day_rain_mm": 47.5,
    "s1_acquisitions": ["2026-03-01", "2026-03-04", "2026-03-09", "2026-03-13", "2026-03-16", "2026-03-21", "2026-03-25", "2026-03-28"],
    "news": [
      {"url": "https://patnapress.com/bihar-weather-storms-rain-hail-two-dead-red-alert-15-districts/", "publisher": "Patna Press", "date": "2026-03-20", "fact": "Hail fell for about 30 minutes in Forbesganj (Araria) on Friday night; Patna Met Centre listed Araria, Katihar and Vaishali as hail-hit."},
      {"url": "https://morungexpress.com/bihar-lightning-kills-6-injures-10-others", "publisher": "IANS via Morung Express", "date": "2026-03-21", "fact": "Storms, rain and hail from Friday into Saturday heavily damaged maize and wheat; two children killed in a wall collapse in Araria."},
      {"url": "https://patnapress.com/?p=66430", "publisher": "Patna Press", "date": "2026-03-22", "fact": "Standing wheat, mustard, gram and maize flattened across Kosi-Seemanchal just before harvest; DMs ordered crop-loss surveys."},
      {"url": "https://patnapress.com/?p=80378", "publisher": "Patna Press (also reported by UNI)", "date": "2026-06-22", "fact": "State paid over Rs 200 crore input subsidy to 3.96 lakh farmers for storm/untimely rain/hail in the 3rd-4th week of March 2026; over 33% damage confirmed in 13 districts including Araria."}
    ],
    "notes": "Evening convective storm: rain 17:00-23:00 IST 20 Mar (peak 14.7 mm/h at 21:00), temperature fell ~10 C, after 5 dry days. ERA5 cannot show hail (weather_code tops out at 65) and underestimates squall gusts (35 km/h). S1 on 21 Mar (~8 h after storm): plot VV -11.7 -> -8.1 dB (same orbit), stays elevated through 28 Mar; consistent with lodging/wet soil but not hail-diagnostic. Hail location is block-level (Forbesganj); no village-level report found. Wheat also plausible as the crop. Village centroid (GeoNames) 26.33449, 87.24941."
  },
  {
    "id": "D-fake-flood-bhobhaul-2023",
    "kind": "fake",
    "peril": "flood",
    "crop": "paddy",
    "season": "Kharif 2023",
    "state": "Bihar",
    "district": "Darbhanga",
    "block": "Kiratpur",
    "village": "Bhobhaul (also spelled Bhubhaul / Bhubhol)",
    "lat": 25.97100,
    "lon": 86.36300,
    "event_start": "2023-10-25",
    "event_end": "2023-10-25",
    "rainfall_daily_mm": {
      "2023-10-20": 0.0, "2023-10-21": 0.0, "2023-10-22": 0.0, "2023-10-23": 0.0,
      "2023-10-24": 0.4, "2023-10-25": 0.0, "2023-10-26": 0.0, "2023-10-27": 0.0,
      "2023-10-28": 0.0, "2023-10-29": 0.0, "2023-10-30": 0.0
    },
    "max_1day_rain_mm": 0.4,
    "s1_acquisitions": ["2023-10-12", "2023-10-15", "2023-10-24", "2023-10-27", "2023-11-05", "2023-11-08"],
    "news": [],
    "notes": "Same plot as real event A. 11-day total 0.4 mm. Plot VV -5.5 to -6.0 dB on 15, 24 and 27 Oct and -5.1 dB on 5 Nov: dry vegetated field, no water (compare -17 dB during event A). No flood/breach/heavy-rain reports found for Kiratpur in Oct 2023. Avoid fake dates near 29 Sep-20 Oct 2024 (event A), ~15 Jan 2025 (Genhua river flash flood in Kiratpur) and 3-5 Oct 2025 (regional heavy rain)."
  }
]
```
