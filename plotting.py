import matplotlib.pyplot as plt
from Functions.utils import getReferenceHeight
from Functions.utils import csvLoader
from Functions.utils import getMapsList


waypoints = csvLoader('C:/Users/Mariu/Desktop/DTU/30101 Intro til GeoRum1/GPS_ting/GPS_praecs/Data/GPS_Waypoints/GPS_waypoints_waypointLite.csv')

waypoints_height = getReferenceHeight(waypoints)

terrain_height = getMapsList('Data/Terrainmap/DTM_1km_6188_724')

plt.plot(waypoints_height, terrain_height)
plt.show()


#   Plot GPS_datapunkterne samt hvad det er per DTM. Plot i samme graf og lav evt sammenligning med usikkerhed og
#   diskrepans mellem de to

#   Konverter datatype til en acceptabel for plt.plot. List?? Check plotingfunktionerne i utils.py

#   plt.plot(reference_height)
#   plt.show()