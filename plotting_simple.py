import os
import pandas as pd
import matplotlib
matplotlib.use('QtAgg') #Giver zoombart vindue
import matplotlib.pyplot as plt

# Sørger for at vi altid starter i den mappe hvor scriptet ligger, så vi kan bruge relative stier til vores data.
os.chdir(os.path.dirname(os.path.abspath(__file__)))

df = pd.read_csv('Results/test_GPS_points_with_reference_heights.csv')
df['Diskrepans'] = df['Altitude_MSL'] - df['Altitude_Reference_Terrain']

real_mål = df[(df['Diskrepans'] > 0) & (df['Diskrepans'] <= 2)]

for data, titel in [(df, "Alle punkter"), (real_mål, "Uden outliers")]:
    nr = data.index + 1    

    middel = data['Diskrepans'].mean()
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 7), sharex=True)

    ax1.plot(nr, data['Altitude_MSL'], 'o-', label='GPS-Højde (DVR90)')
    ax1.plot(nr, data['Altitude_Reference_Terrain'], 's-', label='Terræn-Højde (DTM)')

    ax1.set_ylabel('Højde (m)')
    ax1.set_title(titel)
    ax1.legend()
    ax1.grid(True)

    ax2.plot(nr, data['Diskrepans'], 'o-', label='Diskrepans')
    ax2.fill_between(nr, data['Diskrepans'] - data['Accuracy'], data['Diskrepans'] + data['Accuracy'],alpha=0.25, label='GPS-usikkerhed')
    ax2.axhline(middel,linestyle='--', label=f'Middel = {middel:.2f} m')
    ax2.set_ylabel('GPS - Terræn (m)')
    ax2.set_xlabel('Waypoint nr.')
    ax2.legend()
    ax2.grid(True)

    plt.tight_layout()
    


plt.show()