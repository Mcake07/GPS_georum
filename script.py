# Importer vores funktion
from Functions.utils import csvLoader
from Functions.utils import plotHeightMap
from Functions.utils import pdExport
from Functions.utils import getReferenceHeight

# Indhent vores .csv fil
df = csvLoader('C:/Users/Mariu/Desktop/DTU/30101 Intro til GeoRum1/GPS_ting/GPS_praecs/Data/GPS_Waypoints/GPS_waypoints_waypointLite.csv')

# # # Plot et overfladehøjdekort hvor vi selv definerer titlen på kortet
#
# Navn på kortet vi vil tegne           = "Data/Surfacemap/DSM_1km_6187_720.tif"
# Navn på GPS-data vi vil plotte ovenpå =  df
# Navn på billedet vi gerne vil gemme   =  'Figur3.pdf'
# Titlen på figuren vi tegner           = "Overfladehøjdekort - DTU Space og omegn"
# Vis navnene på GPS-punkterne?         = False
# Zoom ind på højdekortet               = True
#
plotHeightMap(mapfile           = "Data/Surfacemap/DSM_1km_6188_724.tif", 
              dataframe         = df,
              output_file_name  = 'Figur3.pdf', 
              ptitle            = "OVerfladehøjdekort - dyrehaven SV hjørne",
              name              = False,
              zoom              = True)

# # # Plot et overfladehøjdekort hvor vi selv definerer titlen på kortet
#
# Navn på kortet vi vil tegne           = "Data/Terrainmap/DTM_1km_6187_720.tif"
# Navn på GPS-data vi vil plotte ovenpå =  df
# Navn på billedet vi gerne vil gemme   =  'Figur4.pdf'
# Titlen på figuren vi tegner           = "Terrænhøjdekort - DTU Space og omegn"
# Vis navnene på GPS-punkterne?         = False
# Zoom ind på højdekortet               = True
#
plotHeightMap(mapfile           = "Data/Terrainmap/DTM_1km_6188_724.tif", 
              dataframe         = df,
              output_file_name  = 'Figur4.pdf', 
              ptitle            = "Terrænhøjdekort - dyrehaven SV hjørne",
              name              = False,
              zoom              = True)


df_new = getReferenceHeight(df)

# Brug funktionen til at eksportere vores data - vi definerer at vi gerne vil have at output filen skal være i .csv format ved at angive det i navnet på den. 
pdExport(df_new, "Results/test_GPS_points_with_reference_heights.csv")