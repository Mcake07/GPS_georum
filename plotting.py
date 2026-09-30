# -*- coding: utf-8 -*-
"""
plotting.py - Sammenligning af GPS-højder med terrænkort (DTM) og overfladekort (DSM)

Scriptet laver følgende figurer:
    1. GPS-højde og terrænhøjde som funktion af waypointnummer (+ diskrepans) - alle punkter
    2. Samme som 1, men uden outliers
    3. 3D: GPS-spor og terrænoverflade (DTM)
    4. 3D: diskrepans (GPS - terræn) for alle punkter
    5. 3D: diskrepans uden outliers
    6. 3D: diskrepans (uden outliers) sammen med objekthøjde (DSM - DTM), altså træer/bygninger
    7. 3D: diskrepans som farve oven på overfladekortet (DSM) - alle punkter
    8. 3D: som 7, men uden outliers
    9. Scatterplot: objekthøjde vs. diskrepans, samt korrelationskoefficient

Nøgleordet i det hele er DISKREPANS = GPS-højde - terrænhøjde.
Vi målte 1 m over jorden (pind + snor), så diskrepansen skal ligge omkring 1 m.
"""

# =============================================================================
# 1. IMPORTS (alt samlet her)
# =============================================================================

import os                               # arbejdsmappe og filstier
import glob                             # find filer med wildcards (fx *.tif)

import matplotlib
matplotlib.use("QtAgg")                 # Giver et selvstændigt vindue, man kan zoome/dreje i.
                                        # Skal stå FØR pyplot importeres. Virker Qt ikke, så skift til "TkAgg".
import matplotlib.pyplot as plt         # plotning
from matplotlib.colors import TwoSlopeNorm   # farveskala med midtpunkt (bruges til 1 m-referencen)

import numpy as np                      # arrays og matematik
import rasterio                         # læsning af .tif-højdekort
from rasterio.windows import from_bounds     # udsnit ("vindue") af et .tif-kort

from Functions.utils import csvLoader, getReferenceHeight   # egne funktioner fra utils.py


# =============================================================================
# 2. INDSTILLINGER (alt der kan skrues på står her)
# =============================================================================

# Sæt arbejdsmappen til den mappe scriptet ligger i, så relative stier
# (fx "Data/...") virker uanset hvorfra scriptet startes.
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Filer
CSV_STI  = "Data/GPS_Waypoints/GPS_waypoints_waypointLite.csv"
DTM_STI  = "Data/Terrainmap/**/DTM_1km_6188_724.tif"    # terrænkort (bar jord)
DSM_STI  = "Data/Surfacemap/**/DSM_1km_6188_724.tif"    # overfladekort (inkl. træer/bygninger)

# Outlier-kriterie: en måling regnes for rigtig, hvis diskrepansen ligger mellem disse grænser [m]
FORVENTET   = 1.0     # den højde vi målte i over jorden [m]
GRAENSE_LAV = 0.0     # under 0 m ville betyde at GPS'en er under jorden -> urealistisk
GRAENSE_HOJ = 2.0     # over 2 m er umuligt, da vi målte i 1 m højde

# Kortudsnit
MARGIN = 30           # ekstra plads omkring ruten på 3D-kortene [m]
GRID_N = 100          # antal gitterpunkter pr. akse i DSM/DTM-overfladerne (højere = finere, men langsommere)


# =============================================================================
# 3. INDLÆS DATA OG BEREGN DISKREPANS
# =============================================================================

# Læs waypoints fra csv-filen. Resultatet er en GeoDataFrame med koordinater i lon/lat (WGS84)
waypoints = csvLoader(CSV_STI)

# Slå terrænhøjde (DTM) og overfladehøjde (DSM) op for hvert waypoint.
# Funktionen omregner også koordinaterne til UTM (EPSG:25832), altså meter.
wp = getReferenceHeight(waypoints)
if wp is None:
    raise SystemExit("getReferenceHeight fejlede - se beskeden ovenfor")

# Waypointnummer 1, 2, 3, ... (samme nummerering som i advarslerne fra getReferenceHeight)
nr = np.arange(1, len(wp) + 1)

# Hent højderne som almindelige float-arrays
gps     = wp['Altitude_MSL'].to_numpy(dtype=float)                   # GPS-højde over havet
terraen = wp['Altitude_Reference_Terrain'].to_numpy(dtype=float)     # terrænhøjde (DTM) ved waypointet
dsm_wp  = wp['Altitude_Reference_Surface'].to_numpy(dtype=float)     # overfladehøjde (DSM) ved waypointet

# Nodata-værdier (fx -9999) omdannes til NaN, ellers ødelægger de akserne
terraen = np.where(terraen < -1000, np.nan, terraen)
dsm_wp  = np.where(np.abs(dsm_wp) > 1000, np.nan, dsm_wp)

# DISKREPANS: hvor meget GPS-højden ligger over terrænet. Forventet: ca. 1 m
diff = gps - terraen

# Objekthøjde ved waypointet (DSM - DTM): højden af træer/bygninger over jorden
obj = dsm_wp - terraen

# GPS-usikkerhed [m], hvis den findes i filen
acc = wp['Accuracy'].to_numpy(dtype=float) if 'Accuracy' in wp.columns else None

# Koordinater i meter (UTM), og relativt til det sydvestligste punkt så akserne starter ved 0
x_all = wp.geometry.x.to_numpy()
y_all = wp.geometry.y.to_numpy()
x0, y0 = np.nanmin(x_all), np.nanmin(y_all)
X_all = x_all - x0
Y_all = y_all - y0
omraade = (X_all.min(), X_all.max(), Y_all.min(), Y_all.max())   # udstrækning af ruten (bruges til plader i 3D)

# --- Outlier-masker (defineres ÉT sted og bruges i alle plots) ---
gyldig = ~np.isnan(diff)                                         # punkter hvor diskrepansen kan beregnes
ok = gyldig & (diff <= GRAENSE_HOJ) & (diff >= GRAENSE_LAV)      # punkter der er gyldige OG inden for grænserne

fjernet = nr[gyldig & ~ok]
print(f"Fjernede {len(fjernet)} punkt(er) uden for [{GRAENSE_LAV}, {GRAENSE_HOJ}] m: {fjernet}")
print(f"Middel diskrepans uden outliers: {np.mean(diff[ok]):.2f} m (forventet {FORVENTET:.1f} m)")


# =============================================================================
# 4. HJÆLPEFUNKTIONER
# =============================================================================

def find_fil(moenster):
    """Finder den første fil, der matcher et mønster (fx 'Data/**/DTM_*.tif')."""
    filer = glob.glob(moenster, recursive=True)
    if not filer:
        raise FileNotFoundError(f"Ingen filer fundet for mønsteret: {moenster}")
    return filer[0]


def laes_grid(tif, pts, form):
    """Aflæser et .tif-kort i en liste af punkter (pts, UTM-meter) og returnerer et 2D-array med
    formen 'form'. Nodata bliver til NaN."""
    with rasterio.open(tif) as src:
        z = np.array([v[0] for v in src.sample(pts)], dtype=float)   # sample() giver højden i hvert punkt
        z[z < -1000] = np.nan
        if src.nodata is not None:
            z[z == src.nodata] = np.nan
    return z.reshape(form)


def laes_dtm_vindue(tif, margin):
    """Læser den del af DTM-kortet, der ligger omkring ruten (+ margin), som et gitter.
    Returnerer x- og y-koordinater (relativt til x0, y0) og højderne Zr."""
    with rasterio.open(tif) as src:
        # Vindue omkring ruten i rasterets pixelkoordinater
        vindue = from_bounds(x_all.min() - margin, y_all.min() - margin,
                             x_all.max() + margin, y_all.max() + margin, src.transform)
        Zr = src.read(1, window=vindue).astype(float)
        tr = src.window_transform(vindue)          # transformation fra pixel til UTM for dette vindue
        if src.nodata is not None:
            Zr[Zr == src.nodata] = np.nan
    rows, cols = Zr.shape
    # Pixel-midtpunkternes UTM-koordinater (tr.c/tr.f = hjørne, tr.a/tr.e = pixelstørrelse)
    xs = tr.c + tr.a * (np.arange(cols) + 0.5) - x0
    ys = tr.f + tr.e * (np.arange(rows) + 0.5) - y0
    XR, YR = np.meshgrid(xs, ys)
    return XR, YR, Zr


def plot_hojder_vs_waypoint(nr, gps, terraen, diff, acc=None, titel=None, vis_middel=False):
    """Øverst: GPS- og terrænhøjde mod waypointnummer. Nederst: diskrepansen."""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 7), sharex=True)

    ax1.plot(nr, gps, 'o-', label='GPS-højde (MSL)')
    ax1.plot(nr, terraen, 's-', label='Terrænhøjde (DTM)')
    ax1.set_ylabel('Højde over havet [m]')
    if titel:
        ax1.set_title(titel)
    ax1.legend()
    ax1.grid(True)

    ax2.plot(nr, diff, 'o-', color='k', label='GPS − terræn')
    if acc is not None:                      # skygge = GPS-usikkerhed omkring diskrepansen
        ax2.fill_between(nr, diff - acc, diff + acc, alpha=0.25, label='GPS-usikkerhed')
    if vis_middel:                           # stiplet linje ved gennemsnittet
        ax2.axhline(np.nanmean(diff), color='r', ls='--',
                    label=f'Middel = {np.nanmean(diff):.2f} m')
    ax2.axhline(0, color='gray', lw=0.8)
    ax2.set_xlabel('Waypointnummer')
    ax2.set_ylabel('Diskrepans [m]')
    ax2.legend()
    ax2.grid(True)

    plt.tight_layout()


def plot_3d_gps_og_terraen(X, Y, Zg, Zt, XR, YR, Zr, exag=5):
    """3D: DTM-overflade (gennemsigtig) med GPS-sporet, terrænhøjden under waypoints og
    lodrette streger, der viser diskrepansen."""
    fig = plt.figure(figsize=(11, 8))
    ax = fig.add_subplot(111, projection='3d')

    # Terrænoverfladen. Vi tager kun hver 'step'-te pixel, så plottet ikke bliver tungt
    step = max(1, Zr.shape[0] // 80)
    ax.plot_surface(XR[::step, ::step], YR[::step, ::step], Zr[::step, ::step],
                    cmap='terrain', alpha=0.5, linewidth=0, antialiased=True)

    ax.plot(X, Y, Zg, 'o-', color='tab:red', label='GPS-højde (MSL)')
    ax.plot(X, Y, Zt, 's-', color='tab:blue', label='Terrænhøjde (DTM)')

    # Lodret streg fra terræn til GPS ved hvert waypoint = diskrepansen
    for xi, yi, zg, zt in zip(X, Y, Zg, Zt):
        ax.plot([xi, xi], [yi, yi], [zt, zg], color='gray', lw=0.8)

    ax.set_xlabel('Øst [m]')
    ax.set_ylabel('Nord [m]')
    ax.set_zlabel('Højde over havet [m]')
    ax.set_title('GPS-spor og terræn i 3D')

    # Forholdet mellem akserne. z ganges med 'exag' (lodret overdrivelse), ellers ser alt fladt ud
    zhojde = np.nanmax(Zr) - np.nanmin(Zr) + 1e-6
    ax.set_box_aspect((np.ptp(XR), np.ptp(YR), zhojde * exag))
    ax.legend()
    plt.tight_layout()


def plot_diskrepans_3d(X, Y, d, titel, omraade, nr_labels=None, exag=5):
    """3D: diskrepansen som z-akse. Grøn plade = forventet højde (1 m)."""
    xmin, xmax, ymin, ymax = omraade
    fig = plt.figure(figsize=(11, 8))
    ax = fig.add_subplot(111, projection='3d')

    # Gennemsigtig plade ved den forventede højde
    gx, gy = np.meshgrid([xmin, xmax], [ymin, ymax])
    ax.plot_surface(gx, gy, np.full_like(gx, FORVENTET), color='green', alpha=0.15)

    # Grå linje mellem punkterne, lodrette streger fra 0, og farvekodede punkter
    ax.plot(X, Y, d, '-', color='gray', lw=0.8)
    for xi, yi, di in zip(X, Y, d):
        ax.plot([xi, xi], [yi, yi], [0, di], color='lightgray', lw=0.8)
    sc = ax.scatter(X, Y, d, c=d, cmap='coolwarm', s=40, edgecolor='k')
    fig.colorbar(sc, ax=ax, shrink=0.6, pad=0.1, label='GPS − terræn [m]')

    if nr_labels is not None:                # skriv waypointnummer ved punktet
        for xi, yi, di, k in zip(X, Y, d, nr_labels):
            ax.text(xi, yi, di, str(k), fontsize=7)

    ax.set_xlabel('Øst [m]')
    ax.set_ylabel('Nord [m]')
    ax.set_zlabel('Diskrepans [m]')
    ax.set_title(titel)
    ax.set_box_aspect((xmax - xmin, ymax - ymin, max(np.ptp(d), 1) * exag))
    plt.tight_layout()


def plot_diskrepans_ndsm_3d(X, Y, d, titel, GXr, GYr, ndsm, nr_labels=None, exag=3):
    """3D: diskrepans-punkter oven på en overflade der viser objekthøjden (DSM - DTM),
    altså træer og bygninger over jorden. Blå plade = forventet højde (1 m)."""
    fig = plt.figure(figsize=(11, 8))
    ax = fig.add_subplot(111, projection='3d')

    surf = ax.plot_surface(GXr, GYr, ndsm, cmap='Greens', alpha=0.45,
                           linewidth=0, antialiased=True)
    fig.colorbar(surf, ax=ax, shrink=0.5, pad=0.02, location='left',
                 label='Objekthøjde DSM − DTM [m]')

    px, py = np.meshgrid([GXr.min(), GXr.max()], [GYr.min(), GYr.max()])
    ax.plot_surface(px, py, np.full_like(px, FORVENTET), color='blue', alpha=0.12)

    ax.plot(X, Y, d, '-', color='gray', lw=0.8)
    for xi, yi, di in zip(X, Y, d):
        ax.plot([xi, xi], [yi, yi], [0, di], color='lightgray', lw=0.8)
    sc = ax.scatter(X, Y, d, c=d, cmap='coolwarm', s=40, edgecolor='k', depthshade=False)
    fig.colorbar(sc, ax=ax, shrink=0.5, pad=0.1, label='GPS − terræn [m]')

    if nr_labels is not None:
        for xi, yi, di, k in zip(X, Y, d, nr_labels):
            ax.text(xi, yi, di, str(k), fontsize=7)

    ax.set_xlabel('Øst [m]')
    ax.set_ylabel('Nord [m]')
    ax.set_zlabel('Højde over jorden [m]')
    ax.set_title(titel)
    zmax = np.nanmax([np.nanmax(ndsm), np.nanmax(d), 1])
    ax.set_box_aspect((np.ptp(GXr), np.ptp(GYr), zmax * exag))
    plt.tight_layout()


def plot_diskrepans_dsm_3d(X, Y, Z, d, titel, GXr, GYr, dsm, nr_labels=None, exag=3):
    """3D: overfladekortet (DSM) i absolut højde over havet. Punkterne placeres på overfladen
    ved hvert waypoint og farvekodes efter diskrepansen (hvid/lys = 1 m, som forventet)."""
    fig = plt.figure(figsize=(11, 8))
    ax = fig.add_subplot(111, projection='3d')

    surf = ax.plot_surface(GXr, GYr, dsm, cmap='terrain', alpha=0.5,
                           linewidth=0, antialiased=True)
    fig.colorbar(surf, ax=ax, shrink=0.5, pad=0.02, location='left',
                 label='Overfladehøjde DSM [m over havet]')

    # Farveskala med midtpunkt ved FORVENTET, så over/under 1 m får hver sin farve
    norm = TwoSlopeNorm(vcenter=FORVENTET,
                        vmin=min(np.nanmin(d), FORVENTET - 0.1),
                        vmax=max(np.nanmax(d), FORVENTET + 0.1))
    sc = ax.scatter(X, Y, Z, c=d, cmap='coolwarm', norm=norm, s=60,
                    edgecolor='k', depthshade=False)
    fig.colorbar(sc, ax=ax, shrink=0.5, pad=0.1, label='Diskrepans GPS − terræn [m]')

    if nr_labels is not None:
        for xi, yi, zi, k in zip(X, Y, Z, nr_labels):
            ax.text(xi, yi, zi + 0.3, str(k), fontsize=7)

    ax.set_xlabel('Øst [m]')
    ax.set_ylabel('Nord [m]')
    ax.set_zlabel('Højde over havet [m]')
    ax.set_title(titel)
    ax.set_box_aspect((np.ptp(GXr), np.ptp(GYr), max(np.nanmax(dsm) - np.nanmin(dsm), 1) * exag))
    plt.tight_layout()


# =============================================================================
# 5. PLOTS
# =============================================================================

# --- Plot 1: højder og diskrepans mod waypointnummer, alle punkter ---
plot_hojder_vs_waypoint(nr, gps, terraen, diff, acc)

# --- Plot 2: som plot 1, men uden outliers (nu med middel-linje) ---
plot_hojder_vs_waypoint(nr[ok], gps[ok], terraen[ok], diff[ok],
                        acc[ok] if acc is not None else None,
                        titel='Uden outliers', vis_middel=True)

# --- Plot 3: 3D af GPS-spor og DTM-terræn (uden outliers) ---
tif_dtm = find_fil(DTM_STI)
tif_dsm = find_fil(DSM_STI)
XR, YR, Zr = laes_dtm_vindue(tif_dtm, MARGIN)
plot_3d_gps_og_terraen(X_all[ok], Y_all[ok], gps[ok], terraen[ok], XR, YR, Zr, exag=5)

# --- Plot 4 og 5: 3D af diskrepansen, alle punkter og uden outliers ---
plot_diskrepans_3d(X_all[gyldig], Y_all[gyldig], diff[gyldig],
                   'Diskrepans GPS − terræn (alle punkter)', omraade, nr[gyldig])
plot_diskrepans_3d(X_all[ok], Y_all[ok], diff[ok],
                   f'Diskrepans uden outliers ({GRAENSE_LAV:g}–{GRAENSE_HOJ:g} m over jorden)',
                   omraade, nr[ok])

# --- Fælles gitter til DSM/DTM-overfladerne (bruges i plot 6-8) ---
gx_utm = np.linspace(x_all.min() - MARGIN, x_all.max() + MARGIN, GRID_N)
gy_utm = np.linspace(y_all.min() - MARGIN, y_all.max() + MARGIN, GRID_N)
GX, GY = np.meshgrid(gx_utm, gy_utm)
pts = list(zip(GX.ravel(), GY.ravel()))          # liste af (x, y)-punkter som kortene aflæses i
GXr, GYr = GX - x0, GY - y0                      # samme koordinater relativt til startpunktet

dsm  = laes_grid(tif_dsm, pts, GX.shape)         # overfladehøjde (med træer/bygninger)
dtm  = laes_grid(tif_dtm, pts, GX.shape)         # terrænhøjde (bar jord)
ndsm = dsm - dtm                                 # objekthøjde: træer/bygninger over jorden [m]

# --- Plot 6: diskrepans (uden outliers) oven på objekthøjde-overfladen ---
plot_diskrepans_ndsm_3d(X_all[ok], Y_all[ok], diff[ok],
                        'Diskrepans uden outliers og objekthøjde', GXr, GYr, ndsm, nr[ok])

# --- Plot 7 og 8: diskrepans (farve) på overfladekortet DSM ---
g  = gyldig & ~np.isnan(dsm_wp)       # alle punkter der har både diskrepans og DSM-værdi
g2 = ok & ~np.isnan(dsm_wp)           # samme, men uden outliers
plot_diskrepans_dsm_3d(X_all[g], Y_all[g], dsm_wp[g], diff[g],
                       'Diskrepans (farve) oven på overfladekortet - alle punkter',
                       GXr, GYr, dsm, nr[g])
plot_diskrepans_dsm_3d(X_all[g2], Y_all[g2], dsm_wp[g2], diff[g2],
                       'Diskrepans (farve) oven på overfladekortet - uden outliers',
                       GXr, GYr, dsm, nr[g2])

# --- Plot 9: korrelation mellem objekthøjde og diskrepans ---
mask = ok & ~np.isnan(obj)
if mask.sum() >= 3:
    r = np.corrcoef(obj[mask], diff[mask])[0, 1]     # Pearson-korrelation: +1 = stiger sammen, 0 = ingen sammenhæng
    print(f"Korrelation mellem objekthøjde (DSM−DTM) og diskrepans: r = {r:.2f} (n = {mask.sum()})")

    plt.figure(figsize=(6, 5))
    plt.scatter(obj[mask], diff[mask], edgecolor='k')
    plt.xlabel('Objekthøjde ved waypoint, DSM − DTM [m]')
    plt.ylabel('Diskrepans GPS − terræn [m]')
    plt.title(f'Diskrepans vs. bevoksning (r = {r:.2f})')
    plt.grid(True)
else:
    print("For få punkter til at beregne korrelation")

# Vis alle figurer på én gang, hver i sit eget vindue
plt.show()