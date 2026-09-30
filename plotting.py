import numpy as np
import matplotlib.pyplot as plt
from Functions.utils import csvLoader, getReferenceHeight
import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))

waypoints = csvLoader('C:/Users/Mariu/Desktop/DTU/30101 Intro til GeoRum1/GPS_ting/GPS_praecs/Data/GPS_Waypoints/GPS_waypoints_waypointLite.csv')
wp = getReferenceHeight(waypoints)
if wp is None:
    raise SystemExit("getReferenceHeight fejlede - se beskeden ovenfor")

# Waypointnummer (starter ved 1, som i advarslerne i getReferenceHeight)
nr = np.arange(1, len(wp) + 1)

# Hent kolonnerne som almindelige float-arrays
gps     = wp['Altitude_MSL'].to_numpy(dtype=float)
terraen = wp['Altitude_Reference_Terrain'].to_numpy(dtype=float)

# Nodata-værdier (fx -9999) skal væk, ellers ødelægger de y-aksen
terraen = np.where(terraen < -1000, np.nan, terraen)

diff = gps - terraen
high_limit = 2.0
low_limit = 0.0

gyldig = ~np.isnan(diff)
ok = gyldig & (diff <= high_limit) & (diff >= low_limit)

fjernet = nr[gyldig & ~ok]
print(F'Fjernede {len(fjernet)} punkt(er) uden for [{low_limit}, {high_limit}] m: {fjernet}')

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 7), sharex=True)

ax1.plot(nr, gps, 'o-', label='GPS-højde (MSL)')
ax1.plot(nr, terraen, 's-', label='Terrænhøjde (DTM)')
ax1.set_ylabel('Højde over havet [m]')
ax1.legend()
ax1.grid(True)

ax2.plot(nr, diff, 'o-', color='k', label='GPS − terræn')
if 'Accuracy' in wp.columns:
    acc = wp['Accuracy'].to_numpy(dtype=float)
    ax2.fill_between(nr, diff - acc, diff + acc, alpha=0.25, label='GPS-usikkerhed')
ax2.axhline(0, color='gray', lw=0.8)
ax2.set_xlabel('Waypointnummer')
ax2.set_ylabel('Diskrepans [m]')
ax2.legend()
ax2.grid(True)

plt.tight_layout()
plt.show()



nr_c, gps_c, ter_c, diff_c = nr[ok], gps[ok], terraen[ok], diff[ok]

# --- Plot uden outliers ---
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 7), sharex=True)

ax1.plot(nr_c, gps_c, 'o-', label='GPS-højde (MSL)')
ax1.plot(nr_c, ter_c, 's-', label='Terrænhøjde (DTM)')
ax1.set_ylabel('Højde over havet [m]')
ax1.set_title('Uden outliers')
ax1.legend()
ax1.grid(True)

ax2.plot(nr_c, diff_c, 'o-', color='k', label='GPS − terræn')
ax2.axhline(np.mean(diff_c), color='r', ls='--',
            label=f'Middel = {np.mean(diff_c):.2f} m')
ax2.axhline(0, color='gray', lw=0.8)
ax2.set_xlabel('Waypointnummer')
ax2.set_ylabel('Diskrepans [m]')
ax2.legend()
ax2.grid(True)

plt.tight_layout()
plt.show()


import glob
import rasterio
from rasterio.windows import from_bounds

# --- Koordinater i meter, relativt til startpunktet ---
x_all = wp.geometry.x.to_numpy()
y_all = wp.geometry.y.to_numpy()
x0, y0 = np.nanmin(x_all), np.nanmin(y_all)

# Brug de rensede punkter (uden outliers). Skift 'ok' ud med en kolonne af True for at bruge alle.
X = x_all[ok] - x0
Y = y_all[ok] - y0
Zg = gps[ok]
Zt = terraen[ok]

fig = plt.figure(figsize=(11, 8))
ax = fig.add_subplot(111, projection='3d')

# --- Terrænoverflade fra DTM-kortet (valgfri) ---
tif = glob.glob("Data/Terrainmap/**/DTM_1km_6188_724.tif", recursive=True)[0]
m = 30  # margin omkring ruten [m]
with rasterio.open(tif) as src:
    win = from_bounds(x_all.min()-m, y_all.min()-m, x_all.max()+m, y_all.max()+m, src.transform)
    Zr = src.read(1, window=win).astype(float)
    tr = src.window_transform(win)
    if src.nodata is not None:
        Zr[Zr == src.nodata] = np.nan
rows, cols = Zr.shape
xs = tr.c + tr.a * (np.arange(cols) + 0.5) - x0
ys = tr.f + tr.e * (np.arange(rows) + 0.5) - y0
XR, YR = np.meshgrid(xs, ys)
step = max(1, rows // 80)   # nedsampling så plottet ikke bliver tungt
ax.plot_surface(XR[::step, ::step], YR[::step, ::step], Zr[::step, ::step],
                cmap='terrain', alpha=0.5, linewidth=0, antialiased=True)

# --- GPS-sporet og terrænhøjden under waypoints ---
ax.plot(X, Y, Zg, 'o-', color='tab:red', label='GPS-højde (MSL)')
ax.plot(X, Y, Zt, 's-', color='tab:blue', label='Terrænhøjde (DTM)')

# Lodrette streger der viser diskrepansen ved hvert waypoint
for xi, yi, zg, zt in zip(X, Y, Zg, Zt):
    ax.plot([xi, xi], [yi, yi], [zt, zg], color='gray', lw=0.8)

ax.set_xlabel('Øst [m]')
ax.set_ylabel('Nord [m]')
ax.set_zlabel('Højde over havet [m]')
ax.set_title('GPS-spor og terræn i 3D')

# Lodret overdrivelse, ellers ser højdeforskellene flade ud
exag = 5
ax.set_box_aspect((np.ptp(XR), np.ptp(YR), np.nanmax(Zr) - np.nanmin(Zr) + 1e-6) * np.array([1, 1, exag]) / 1)
ax.legend()
plt.tight_layout()
plt.show()


# --- Grundlag: alle punkter, diskrepans i meter ---
X_all = x_all - np.nanmin(x_all)
Y_all = y_all - np.nanmin(y_all)
forventet = 1.0        # målt 1 m over jorden (pind + snor)
graense_hoj = 2.0      # over 2 m over jorden = outlier
graense_lav = 0.0      # under 0 m (under jorden) er også urealistisk

def plot_diskrepans_3d(X, Y, d, titel, nr_labels=None):
    fig = plt.figure(figsize=(11, 8))
    ax = fig.add_subplot(111, projection='3d')

    # Gennemsigtig plade ved den forventede højde (1 m)
    gx, gy = np.meshgrid(np.linspace(np.nanmin(X_all), np.nanmax(X_all), 2),
                         np.linspace(np.nanmin(Y_all), np.nanmax(Y_all), 2))
    ax.plot_surface(gx, gy, np.full_like(gx, forventet), color='green', alpha=0.15)

    # Spor, lodrette streger fra 0 og farvekodede punkter
    ax.plot(X, Y, d, '-', color='gray', lw=0.8)
    for xi, yi, di in zip(X, Y, d):
        ax.plot([xi, xi], [yi, yi], [0, di], color='lightgray', lw=0.8)
    sc = ax.scatter(X, Y, d, c=d, cmap='coolwarm', s=40, edgecolor='k')
    fig.colorbar(sc, ax=ax, shrink=0.6, pad=0.1, label='GPS − terræn [m]')

    if nr_labels is not None:
        for xi, yi, di, n in zip(X, Y, d, nr_labels):
            ax.text(xi, yi, di, str(n), fontsize=7)

    ax.set_xlabel('Øst [m]')
    ax.set_ylabel('Nord [m]')
    ax.set_zlabel('Diskrepans [m]')
    ax.set_title(titel)
    ax.set_box_aspect((np.ptp(X_all), np.ptp(Y_all), max(np.ptp(d), 1) * 5))
    plt.tight_layout()
    plt.show()

# --- Plot 1: diskrepans, alle punkter ---
plot_diskrepans_3d(X_all[gyldig], Y_all[gyldig], diff[gyldig],
                   'Diskrepans GPS − terræn (alle punkter)', nr[gyldig])

# --- Plot 2: diskrepans uden outliers ---
print(f"Fjernede {len(fjernet)} punkt(er) uden for [{graense_lav}, {graense_hoj}] m: {fjernet}")
print(f"Middel diskrepans uden outliers: {np.mean(diff[ok]):.2f} m "
      f"(forventet {forventet:.1f} m)")

plot_diskrepans_3d(X_all[ok], Y_all[ok], diff[ok],
                   f'Diskrepans uden outliers (0–{graense_hoj:.0f} m over jorden)', nr[ok])


import glob
import rasterio

# --- Objekthøjde-grid (DSM − DTM) omkring ruten ---
tif_dtm = glob.glob("Data/Terrainmap/**/DTM_1km_6188_724.tif", recursive=True)[0]
tif_dsm = glob.glob("Data/Surfacemap/**/DSM_1km_6188_724.tif", recursive=True)[0]

m, n = 30, 100   # margin [m] og antal gitterpunkter pr. akse
gx_utm = np.linspace(x_all.min() - m, x_all.max() + m, n)
gy_utm = np.linspace(y_all.min() - m, y_all.max() + m, n)
GX, GY = np.meshgrid(gx_utm, gy_utm)
pts = list(zip(GX.ravel(), GY.ravel()))

def laes_grid(tif):
    with rasterio.open(tif) as src:
        z = np.array([v[0] for v in src.sample(pts)], dtype=float)
        z[z < -1000] = np.nan                      # nodata
        if src.nodata is not None:
            z[z == src.nodata] = np.nan
    return z.reshape(GX.shape)

ndsm = laes_grid(tif_dsm) - laes_grid(tif_dtm)     # træer/bygninger over jorden [m]
GXr = GX - x_all.min()
GYr = GY - y_all.min()

# --- Plotfunktion: diskrepans-punkter oven på objekthøjde-overfladen ---
def plot_diskrepans_3d(X, Y, d, titel, nr_labels=None):
    fig = plt.figure(figsize=(11, 8))
    ax = fig.add_subplot(111, projection='3d')

    # Objekthøjde (DSM − DTM) som overflade
    surf = ax.plot_surface(GXr, GYr, ndsm, cmap='Greens', alpha=0.45,
                           linewidth=0, antialiased=True)
    fig.colorbar(surf, ax=ax, shrink=0.5, pad=0.02, location='left',
                 label='Objekthøjde DSM − DTM [m]')

    # Plade ved forventet målehøjde (1 m)
    px, py = np.meshgrid([GXr.min(), GXr.max()], [GYr.min(), GYr.max()])
    ax.plot_surface(px, py, np.full_like(px, forventet), color='blue', alpha=0.12)

    # Diskrepans-punkter
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
    ax.set_box_aspect((np.ptp(GXr), np.ptp(GYr), zmax * 3))
    plt.tight_layout()
    plt.show()

# --- Plot 1: alle punkter ---
plot_diskrepans_3d(X_all[gyldig], Y_all[gyldig], diff[gyldig],
                   'Diskrepans GPS − terræn (alle) og objekthøjde', nr[gyldig])

# --- Plot 2: uden outliers ---
plot_diskrepans_3d(X_all[ok], Y_all[ok], diff[ok],
                   'Diskrepans uden outliers og objekthøjde', nr[ok])

# --- Tal på sammenhængen: objekthøjde ved hvert waypoint vs. diskrepans ---
obj = (wp['Altitude_Reference_Surface'] - wp['Altitude_Reference_Terrain']).to_numpy(dtype=float)
obj = np.where(np.abs(obj) > 1000, np.nan, obj)
mask = ok & ~np.isnan(obj)
r = np.corrcoef(obj[mask], diff[mask])[0, 1]
print(f"Korrelation mellem objekthøjde (DSM−DTM) og diskrepans: r = {r:.2f} (n = {mask.sum()})")

plt.figure(figsize=(6, 5))
plt.scatter(obj[mask], diff[mask], edgecolor='k')
plt.xlabel('Objekthøjde ved waypoint, DSM − DTM [m]')
plt.ylabel('Diskrepans GPS − terræn [m]')
plt.title(f'Diskrepans vs. bevoksning (r = {r:.2f})')
plt.grid(True)
plt.show()


from matplotlib.colors import TwoSlopeNorm

# --- DSM (overfladekort) som grid, absolut højde over havet ---
dsm = laes_grid(tif_dsm)

# DSM-højden ved hvert waypoint (bruges som punkternes z-placering)
dsm_wp = wp['Altitude_Reference_Surface'].to_numpy(dtype=float)
dsm_wp = np.where(np.abs(dsm_wp) > 1000, np.nan, dsm_wp)

def plot_diskrepans_dsm_3d(X, Y, Z, d, titel, nr_labels=None):
    fig = plt.figure(figsize=(11, 8))
    ax = fig.add_subplot(111, projection='3d')

    # Overfladekortet (DSM)
    surf = ax.plot_surface(GXr, GYr, dsm, cmap='terrain', alpha=0.5,
                           linewidth=0, antialiased=True)
    fig.colorbar(surf, ax=ax, shrink=0.5, pad=0.02, location='left',
                 label='Overfladehøjde DSM [m over havet]')

    # Punkter på overfladen, farvet efter diskrepans (centreret på forventet 1 m)
    lo, hi = np.nanmin(d), np.nanmax(d)
    norm = TwoSlopeNorm(vcenter=forventet, vmin=min(lo, forventet - 0.1),
                        vmax=max(hi, forventet + 0.1))
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
    ax.set_box_aspect((np.ptp(GXr), np.ptp(GYr), max(np.nanmax(dsm) - np.nanmin(dsm), 1) * 3))
    plt.tight_layout()
    plt.show()

# --- Plot 1: alle punkter ---
g = gyldig & ~np.isnan(dsm_wp)
plot_diskrepans_dsm_3d(X_all[g], Y_all[g], dsm_wp[g], diff[g],
                       'Diskrepans (farve) oven på overfladekortet - alle punkter', nr[g])

# --- Plot 2: uden outliers ---
g2 = ok & ~np.isnan(dsm_wp)
plot_diskrepans_dsm_3d(X_all[g2], Y_all[g2], dsm_wp[g2], diff[g2],
                       'Diskrepans (farve) oven på overfladekortet - uden outliers', nr[g2])
