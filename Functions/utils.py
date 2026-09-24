# -*- coding: utf-8 -*-
"""
Created on Wed Sep  3 11:21:33 2025

@author: maakr@dtu.dk
"""


import glob
import rasterio 
import pandas as pd
import geopandas as gpd
import numpy as np
from pyproj import Transformer
import os.path
import xml.etree.ElementTree as ET
from datetime import datetime
from shapely.geometry import Point
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from collections import Counter
import xlsxwriter
import csv

# =============================================================================
# Custom function - gpxLoader
# =============================================================================

def gpxLoader(input_filename):
    '''Imports GPS Waypoints from .gpx files.
    
    Input parameters:
    
        input_filename - String containing the filepath to desied .gpx file
    '''
    
    # =========================================================================
    # Sanity check 1 - Ensure that the input file is either a.gpx or .csv file
    # =========================================================================
    
    # Define custom error class
    class InvalidFileType(Exception):
        pass
    
    # Define custom file validator function
    def validate_filetype(input_filename):
        
        # Extract file extension
        _, extension = os.path.splitext(input_filename)
        
        # Make check
        if not extension.lower() in ['.gpx']:
            raise InvalidFileType("ERROR - Input must be a .gpx file")
    
    # Try to validate the file type
    try:
        validate_filetype(input_filename)
    except InvalidFileType as e:
        print(e)
        return None

    # =========================================================================
    # Load in data
    # =========================================================================

    # Parse the GPX file
    tree = ET.parse(input_filename)
    root = tree.getroot()
    
    # Define the namespace for GPX 1.1
    namespace = {'gpx': 'http://www.topografix.com/GPX/1/1'}
    
    # List to store the extracted data
    data = []
    
    #Initialice count number
    counts = 1
    
    # =========================================================================
    # Waypoints
    # =========================================================================
    
    # Find all waypoints (wpt) in the GPX file
    waypoints = root.findall('.//gpx:wpt', namespace)
    
    # Iterate through each waypoint and extract the data
    for wpt in waypoints:
        
        # Gater dat
        lat = float(wpt.get('lat')) 
        lon = float(wpt.get('lon'))
        name = wpt.find('gpx:name', namespace).text if wpt.find('gpx:name', namespace) is not None else ('Point ' + str(counts))
        ele = float(wpt.find('gpx:ele', namespace).text) if wpt.find('gpx:ele', namespace) is not None else None
        time_str = wpt.find('gpx:time', namespace).text if wpt.find('gpx:time', namespace) is not None else None
        time = datetime.strptime(time_str, '%Y-%m-%dT%H:%M:%SZ') if time_str else None
    
        # Initialize a dictionary for the waypoint data
        waypoint_data = {
            'lat': lat,
            'lon': lon,
            'Name': name,
            'Timestamp': time,
            'Altitude_MSL': ele,
            'Altitude_Ellipsoid': None,
            'Accuracy': None}
    
        # Find the extensions element
        extensions = wpt.find('gpx:extensions', namespace)
    
        # If extensions exist, extract the relevant fields
        if extensions is not None:
            accuracy = extensions.find('gpx:accuracy', namespace)
            altitudehae = extensions.find('gpx:altitudehae', namespace)
    
            waypoint_data['Accuracy'] = float(accuracy.text) if accuracy is not None else None
            waypoint_data['Altitude_Ellipsoid'] = float(altitudehae.text) if altitudehae is not None else None
            
        else:
            accuracy, altitudehae = None, None
    
        # Append the data for each waypoint to the list
        data.append(waypoint_data)
        
        # Update counts vector
        counts = counts + 1

    # =========================================================================
    # Trackpoints
    # =========================================================================
    
    # Find all trackpoints (trk) in GPX file
    trackpoints = root.findall('.//gpx:trkpt', namespace)
    
    # Iterate through all trackpoints
    for trkpt in trackpoints:
        lat = float(trkpt.get('lat'))
        lon = float(trkpt.get('lon'))
        name = trkpt.find('gpx:name', namespace).text if trkpt.find('gpx:name', namespace) is not None else ('Point ' + str(counts))
        ele = float(trkpt.find('gpx:ele', namespace).text) if trkpt.find('gpx:ele', namespace) is not None else None
        time_str = trkpt.find('gpx:time', namespace).text if trkpt.find('gpx:time', namespace) is not None else None
        time = datetime.strptime(time_str, '%Y-%m-%dT%H:%M:%SZ') if time_str else None
    
        # Initialize a dictionary for the trackpoint data
        trackpoint_data = {
            'lat': lat,
            'lon': lon,
            'Name': name,
            'Timestamp': time,
            'Altitude_MSL': ele,
            'Altitude_Ellipsoid': None,
            'Accuracy': None}
    
        # Find the extensions element
        extensions = trkpt.find('gpx:extensions', namespace)
        
        # If extensions exist, extract the relevant fields
        if extensions is not None:
            
            accuracy = extensions.find('gpx:accuracy', namespace)
            altitudehae = extensions.find('gpx:altitudehae', namespace)
            
            trackpoint_data['Accuracy'] = float(accuracy.text) if accuracy is not None else None
            trackpoint_data['Altitude_Ellipsoid'] = float(altitudehae.text) if altitudehae is not None else None
            
        else:
            accuracy, altitudehae = None, None
        
        # Append the data for each waypoint to the list
        data.append(trackpoint_data)
        
        # Update counts vector
        counts = counts + 1

    # =========================================================================
    # Routepoints
    # =========================================================================

    # Extract route points (rtept)
    routepoints = root.findall('.//gpx:rtept', namespace)
    
    # Iterate through all trackpoints
    for rtepts in routepoints:
        lat = float(rtepts.get('lat'))
        lon = float(rtepts.get('lon'))
        name = rtepts.find('gpx:name', namespace).text if rtepts.find('gpx:name', namespace) is not None else ('Point ' + str(counts))
        ele = float(rtepts.find('gpx:ele', namespace).text) if rtepts.find('gpx:ele', namespace) is not None else None
        time_str = rtepts.find('gpx:time', namespace).text if rtepts.find('gpx:time', namespace) is not None else None
        time = datetime.strptime(time_str, '%Y-%m-%dT%H:%M:%SZ') if time_str else None
    
        # Initialize a dictionary for the trackpoint data
        routepoint_data = {
            'lat': lat,
            'lon': lon,
            'Name': name,
            'Timestamp': time,
            'Altitude_MSL': ele,
            'Altitude_Ellipsoid': None,
            'Accuracy': None}
    
        # Find the extensions element
        extensions = rtepts.find('gpx:extensions', namespace)
        
        # If extensions exist, extract the relevant fields
        if extensions is not None:
            
            accuracy = extensions.find('gpx:accuracy', namespace)
            altitudehae = extensions.find('gpx:altitudehae', namespace)
            
            routepoint_data['Accuracy'] = float(accuracy.text) if accuracy is not None else None
            routepoint_data['Altitude_Ellipsoid'] = float(altitudehae.text) if altitudehae is not None else None
            
        else:
            accuracy, altitudehae = None, None
        
        # Append the data for each waypoint to the list
        data.append(routepoint_data)
        
        # Update counts vector
        counts = counts + 1

    # Create a DataFrame
    df_raw = pd.DataFrame(data)
    
    # Extract all columns except 'lat' and 'lon'
    df_filtered = df_raw.drop(columns=['lat', 'lon'])
    
    # Create a geometry column from 'lat' and 'lon'
    df_filtered['geometry'] = df_raw.apply(lambda row: Point(row['lon'], row['lat']), axis=1)

    # Convert to GeoDataFrame
    gdf = gpd.GeoDataFrame(df_filtered, geometry='geometry')

    # Set the coordinate reference system to WGS84 (latitude/longitude)
    gdf.set_crs(epsg=4326, inplace=True)
    
    # If time column exist, then convert it to datetime format
    if 'Timestamp' in gdf.columns:
        
        gdf['Timestamp'] = pd.to_datetime(gdf['Timestamp'], errors='coerce')
        
        # Convert the datetime objects to the specified string format
        gdf['Timestamp']  = gdf['Timestamp'] .dt.strftime('%Y-%m-%dT%H:%M:%SZ')

    return gdf

# =============================================================================
# Custom function - csvLoader
# =============================================================================

def csvLoader(input_filename):
    '''Imports GPS Waypoints from .csv files.
    
    Input parameters:
    
        input_filename - String containing the filepath to desied .gpx file
    '''
    
    # =========================================================================
    # Sanity check 1 - Ensure that the input file is either a.gpx or .csv file
    # =========================================================================
    
    # Define custom error class
    class InvalidFileType(Exception):
        pass
    
    # Define custom file validator function
    def validate_filetype(input_filename):
        
        # Extract file extension
        _, extension = os.path.splitext(input_filename)
        
        # Make check
        if not extension.lower() in ['.csv']:
            raise InvalidFileType("ERROR - Input must be a .csv file")
    
    # Try to validate the file type
    try:
        validate_filetype(input_filename)
    except InvalidFileType as e:
        print(e)
        return None

    # =========================================================================
    # Load in data
    # =========================================================================

    # Specify possible variable names
    columns_to_extract = ['Name', 'name', 
                          'Timestamp', 'timestamp', 'time',
                          'Longitude', 'longitude', 'lon',
                          'Latitude', 'latitude', 'lat',
                          'Altitude_Ellipsoid','Altitude Ellipsoid(m)', 'Altitude Ellipsoid',
                          'altitude ellipsoid(m)', 'altitude ellipsoid',
                          'Altitudehae', 'altitudehae',
                          'Altitude_MSL','Altitude MSL(m)', 'Altitude MSL', 
                          'altitude MSL(m)', 'altitude MSL',
                          'altitude(m)', 'altitude',
                          'Altitude(m)', 'Altitude',
                          'Elevation', 'elevation','ele',
                          'Accuracy','Accuracy(m)', 'Accuracy', 'accuracy(m)','accuracy',
                          'Altitude_Reference_Surface', 'Altitude_Reference_Terrain'] 

    # Open the file and read the first line
    with open(input_filename, 'r', newline='', encoding='utf-8-sig') as file:
        first_line = file.readline().strip()
    
    if first_line.startswith('sep='):
        # Separator explicitly defined in file
        separator = first_line.split('=')[1]
        df = pd.read_csv(
            input_filename,
            skiprows=1,
            sep=separator,
            index_col=False,
            encoding='utf-8-sig'
        )
    else:
        # Auto-detect delimiter
        with open(input_filename, 'r', newline='', encoding='utf-8-sig') as file:
            sample = file.read(2048)
            try:
                dialect = csv.Sniffer().sniff(sample, delimiters=[',',';','\t'])
                separator = dialect.delimiter
            except csv.Error:
                separator = ','  # fallback default
        df = pd.read_csv(
            input_filename,
            sep=separator,
            index_col=False,
            encoding='utf-8-sig')
    
    # Check if the specified columns exist in the DataFrame
    filtered_columns = [col for col in df.columns if col in columns_to_extract]
    
    # If some of the coloumns exist in the data frame, then extract them 
    if filtered_columns:
        
        # Possible column names for latitude and longitude
        lat_columns = ['Latitude', 'latitude', 'lat']
        lon_columns = ['Longitude', 'longitude', 'lon']

        # Find the correct latitude column in the DataFrame
        lat_col = next((col for col in lat_columns if col in df.columns), None)
        lon_col = next((col for col in lon_columns if col in df.columns), None)
        
        # Create geometry points from latitude and longitude
        geometry = [Point(xy) for xy in zip(df[lon_col], df[lat_col])]
        
        # Possible column names for remeinder of variables - Name
        name_columns = ['Name', 'name']
        
        # Possible column names for remeinder of variables - Time
        time_columns = ['Timestamp', 'timestamp', 'time']
        
        # Possible column names for remeinder of variables - Altitude Elliposid 
        ellipsoid_columns = ['Altitude_Ellipsoid','Altitude Ellipsoid(m)', 'Altitude Ellipsoid',
                                      'altitude ellipsoid(m)', 'altitude ellipsoid',
                                      'Altitudehae', 'altitudehae']
        
        # Possible column names for remeinder of variables - Altitude MSL
        msl_columns = ['Altitude_MSL','Altitude MSL(m)', 'Altitude MSL', 
                        'altitude MSL(m)', 'altitude MSL',
                        'altitude(m)', 'altitude',
                        'Altitude(m)', 'Altitude',
                        'Elevation', 'elevation','ele']
        
        # Possible column names for remeinder of variables - Accuracy
        accuracy_columns = ['Accuracy(m)', 'Accuracy', 'accuracy(m)','accuracy']
        
        # Possible column names for variables - Reference Surface Altitude
        reference_surface_columns = ['Altitude_Reference_Surface']
        
        # Possible column names for variables - Reference Terrain Altitude
        reference_terrain_columns = ['Altitude_Reference_Terrain']
    
        # Find the correct variable columns in the DataFrame
        name_col = next((col for col in name_columns if col in df.columns), None)
        time_col = next((col for col in time_columns if col in df.columns), None)
        ellipsoid_col = next((col for col in ellipsoid_columns if col in df.columns), None)
        msl_col = next((col for col in msl_columns if col in df.columns), None)
        accuracy_col = next((col for col in accuracy_columns if col in df.columns), None)
        reference_surface_col = next((col for col in reference_surface_columns if col in df.columns), None)
        reference_terrain_col = next((col for col in reference_terrain_columns if col in df.columns), None)
        
        # Create list with column names
        variable_list = [name_col,time_col,ellipsoid_col,msl_col,accuracy_col,reference_surface_col,reference_terrain_col]
        
        # Sort out all None entries in the variable list
        filtered_variable_list = [s for s in variable_list if s is not None]
        
        # Extract the filtered out variables
        new_df = df[filtered_variable_list].copy()

        # Convert to GeoDataFrame
        gdf = gpd.GeoDataFrame(new_df, geometry=geometry)

        # Set the coordinate reference system to WGS84 (latitude/longitude)
        gdf.set_crs(epsg=4326, inplace=True)
        
        # If time column exist, then convert it to datetime format
        if time_col is not None:
            
            gdf[time_col] = pd.to_datetime(gdf[time_col], errors='coerce')
            
            # Convert the datetime objects to the specified string format
            gdf[time_col]  = gdf[time_col] .dt.strftime('%Y-%m-%dT%H:%M:%SZ')
        
        
        # Rename column variables to their standard name
        if name_col is not None:
            gdf.rename(columns = {name_col:'Name'}, inplace = True)
            
        if ellipsoid_col is not None:
            gdf.rename(columns = {ellipsoid_col:'Altitude_Ellipsoid'}, inplace = True)
            
        if msl_col is not None:
            gdf.rename(columns = {msl_col:'Altitude_MSL'}, inplace = True)
            
        if accuracy_col is not None:
            gdf.rename(columns = {accuracy_col:'Accuracy'}, inplace = True)
            
        if  reference_surface_col is not None:
            gdf.rename(columns = { reference_surface_col:'Altitude_Reference_Surface'}, inplace = True)
            
        if  reference_terrain_col is not None:
            gdf.rename(columns = { reference_terrain_col:'Altitude_Reference_Terrain'}, inplace = True)
        
        # Return geopandas data frame with extracted data
        return gdf
        
    else:
        
        print(f"\nERROR - The CSV file does not contain any data coloumns with one or more of the expected headers: '{columns_to_extract}'")
        return None
    
# =============================================================================
# Custom function - pdMerger
# =============================================================================

def pdMerger(df_list):
    '''Merges geopanda data frames into a single data frame. Only keeps variables
    of the same type that are shared between all individual data frames. 
    
    Input parameters:
    
        df_list - list containing each individual data frame
    '''
    # Define the lists of possible column names
    column_lists = {
    'Name': ['Name', 'name'],
    'Timestamp': ['Timestamp', 'timestamp', 'time'],
    'Altitude_MSL': ['Altitude_MSL','Altitude MSL(m)', 'Altitude MSL', 'altitude MSL(m)', 'altitude MSL', 'altitude(m)', 'altitude', 'Altitude(m)', 'Altitude', 'Elevation', 'elevation', 'ele'],
    'Altitude_Ellipsoid': ['Altitude_Ellipsoid','Altitude Ellipsoid(m)', 'Altitude Ellipsoid', 'altitude ellipsoid(m)', 'altitude ellipsoid', 'Altitudehae', 'altitudehae'],
    'Altitude_Reference_Surface': ['Altitude_Reference_Surface'],
    'Altitude_Reference_Terrain': ['Altitude_Reference_Terrain'],
    'Accuracy': ['Accuracy','Accuracy(m)', 'accuracy(m)', 'accuracy'],
    'geometry': ['geometry']
    }
    
    # Initialize an empty dictionary to hold the collected columns
    collected_data = {key: [] for key in column_lists}
    
    # Iterate over each DataFrame
    for df in df_list:
        for key, possible_columns in column_lists.items():
            # Find the first column that matches any of the possible column names for this variable type
            for col in possible_columns:
                if col in df.columns:
                    collected_data[key].append(df[col].rename(key))
                    break
            else:
                # If no column matches, append None to keep the structure
                collected_data[key].append(pd.Series([None]*len(df)))
    
    # Concatenate the columns, aligning them by index
    combined_df = pd.concat([pd.concat(col_list, axis=0).reset_index(drop=True) for col_list in collected_data.values()], axis=1)
    
    # Rename columns to standardized names
    combined_df.columns = collected_data.keys()
    
    # Select columns that contain at least one non-None value (non-NaN)
    non_none_columns = [col for col in combined_df.columns if combined_df[col].notna().any()]
    
    # Convert to GeoDataFrame, making sure the 'geometry' column is set as the geometry
    if 'geometry' in non_none_columns:
        # Convert the DataFrame to a GeoDataFrame, using the 'geometry' column
        pd_final = gpd.GeoDataFrame(combined_df[non_none_columns], geometry='geometry')
        
        # Set the coordinate reference system to WGS84 (latitude/longitude)
        pd_final.set_crs(epsg=4326, inplace=True)
        
    else:
        # Return a regular DataFrame if no geometry column is present
        pd_final = pd.DataFrame(combined_df[non_none_columns])

    return pd_final

# =============================================================================
# Custom function - getReferenceHeight
# =============================================================================

def getReferenceHeight(dataframe):
    '''Extracts reference height values for GPS Waypoints.
    
    Input parameters:
    
        input_filename - Pandas DataFrame containing the GPS waypoints
    '''

    # =========================================================================
    # Sanity check 1 - Ensure that the input is a geopandas dataframe
    # =========================================================================
    
    # Define custom error class
    class InvalidDataTypeError(Exception):
        pass
    
    # Define custom file validator function
    def validate_datatype(dataframe):
        if not isinstance(dataframe, pd.DataFrame):
            raise InvalidDataTypeError("ERROR - Input must be a GeoPandas DataFrame")
    
    # Try to validate the file type
    try:
        validate_datatype(dataframe)
    except InvalidDataTypeError as e:
        print(e)
        return None
    
    # =========================================================================
    # Sanity check 2 - Check if there are any .tif files in the Data/Surfacemap folder
    # =========================================================================
    
    # Define custom error class
    class NoSurfaceMapstError(Exception):
        pass
    
    # Define custom file validator function
    def validate_dataexistence(filelist):
        if len(filelist) == 0:
            raise NoSurfaceMapstError("ERROR - No reference surface heightmaps were found in the Data/Surfacemap folder")
    
    # Try to validate the file type
    try:
        validate_dataexistence(glob.glob("Data/Surfacemap/**/*.tif",recursive=True))
    except NoSurfaceMapstError as e:
        print(e)
        return None
    
    # =========================================================================
    # Sanity check 3 - Check if there are any .tif files in the Data/Surfacemap folder
    # =========================================================================
    
    # Define custom error class
    class NoTerrainMapstError(Exception):
        pass
    
    # Define custom file validator function
    def validate_dataexistence(filelist):
        if len(filelist) == 0:
            raise NoTerrainMapstError("ERROR - No reference terrain heightmaps were found in the Data/Terrainmap folder")
    
    # Try to validate the file type
    try:
        validate_dataexistence(glob.glob("Data/Terrainmap/**/*.tif",recursive=True))
    except NoTerrainMapstError as e:
        print(e)
        return None
    
    # =========================================================================
    # Load in data files
    # =========================================================================
    
    # Extract list of files containing surface height .tif files
    filelist_surface = glob.glob("Data/Surfacemap/**/*.tif",recursive=True)
    
    # Extract list of files containing surface terrain .tif files
    filelist_terrain = glob.glob("Data/Terrainmap/**/*.tif",recursive=True)
    
    # =========================================================================
    # Transform GPS points to reference height map geometry
    # =========================================================================
    
    # Save a local copy of the data frame
    df_new = dataframe.copy()
    
    df_new = df_new.to_crs("EPSG:25832")
    
    # Find the corresponding file index name for each coordinate
    coord_files = [str(df_new.geometry.y[s])[:4] + "_" + str(df_new.geometry.x[s])[:3] for s in np.arange(0,len(df_new.geometry.x))]
    
    # Find index for each unique name 
    id_unique = [coord_files.index(x) for x in sorted(set(coord_files))]
    
    # =========================================================================
    # Pre-allocate arrays to input data to
    # =========================================================================
    
    # Create a numpy array with the desired output dimensions - Surface height
    surface_height = np.zeros(len(df_new.geometry.x))
    
    # Create a numpy array with the desired output dimensions - Terrain height
    terrain_height = np.zeros(len(df_new.geometry.x))
    
    # Create filetracker vector to monitor what GPS points have reference maps avavible - Surface
    file_tracker_surface = np.array([True]*len(df_new.geometry.x))
    
    # Create filetracker vector to monitor what GPS points have reference maps avavible - Terrain
    file_tracker_terrain = np.array([True]*len(df_new.geometry.y))
    
    # =========================================================================
    # Loop through all GPS points
    # =========================================================================
    
    # Loop through all the bounding list elements
    for ii in np.arange(0,len(id_unique)):
    
        # =========================================================================
        # Surface
        # =========================================================================    
    
        # Find name of unique data file
        file_id_surface = [s for s in filelist_surface if coord_files[id_unique[ii]] in s]
        
        # Find index values of all files relevant for the given coordinates
        idx_files_surface = np.array(np.array(coord_files) == coord_files[id_unique[ii]])
        
        # Check if the file_id exists for the current datapoints
        if len(file_id_surface) == 0:
            
            # Insert NaN values if no reference height data exists
            surface_height[idx_files_surface] = np.nan
            
            # Update filetracker vector
            file_tracker_surface[idx_files_surface] = False 
        
        # If reference height map exists, then continue 
        else: 
    
            # Load in .tif file
            img = rasterio.open(file_id_surface[0])

            # Create list of sampling coordinates
            coord_list = [(x, y) for x, y in zip(df_new.geometry.x[idx_files_surface], df_new.geometry.y[idx_files_surface])]
        
            # Extract coordinate values 
            vals_tmp = [x for x in img.sample(coord_list)]
        
            # Flatten output coordinate list
            surface_height[idx_files_surface] = np.concatenate(vals_tmp).ravel()
            
        # =========================================================================
        # Terrain
        # =========================================================================    
    
        # Find name of unique data file
        file_id_terrain = [s for s in filelist_terrain if coord_files[id_unique[ii]] in s]
        
        # Find index values of all files relevant for the given coordinates
        idx_files_terrain = np.array(np.array(coord_files) == coord_files[id_unique[ii]])
        
        # Check if the file_id exists for the current datapoints
        if len(file_id_terrain) == 0:
            
            # Insert NaN values if no reference height data exists
            terrain_height[idx_files_terrain] = np.nan
            
            # Update filetracker vector
            file_tracker_terrain[idx_files_terrain] = False 
        
        # If reference height map exists, then continue 
        else: 
    
            # Load in .tif file
            img = rasterio.open(file_id_terrain[0])
    
            # Create list of sampling coordinates
            coord_list = [(x, y) for x, y in zip(df_new.geometry.x[idx_files_terrain], df_new.geometry.y[idx_files_terrain])]
        
            # Extract coordinate values 
            vals_tmp = [x for x in img.sample(coord_list)]
        
            # Flatten output coordinate list
            terrain_height[idx_files_terrain] = np.concatenate(vals_tmp).ravel()

    # If there are data points with no relevant height maps, then print a warning message stating that filler values has been inserted
    if not all(file_tracker_surface):
        print('WARNING - No relevant surface height map exists for GPS Waypoint(s) ' + np.array2string((np.arange(0,len(df_new.geometry.x))+1)[np.where(file_tracker_surface == False)], separator=',') + ', inserting filler value(s)')
    
    # If there are data points with no relevant height maps, then print a warning message stating that filler values has been inserted
    if not all(file_tracker_terrain):
        print('WARNING - No relevant terrain height map exists for GPS Waypoint(s) ' + np.array2string((np.arange(0,len(df_new.geometry.x))+1)[np.where(file_tracker_terrain == False)], separator=',') + ', inserting filler value(s)')
    
    # Append reference height data to the new data frame
    df_new['Altitude_Reference_Surface'] = surface_height
    
    # Append reference height data to the new data frame
    df_new['Altitude_Reference_Terrain'] = terrain_height
    
    # Return the new data frame
    return df_new

# =========================================================================
# Custom function - getMapsList
# =========================================================================

def getMapsList(dataframe):
    '''Extracts a lis with relevant reference height maps.
    
    Input parameters:
    
        input_filename - Pandas DataFrame containing the GPS waypoints
    '''

    # =========================================================================
    # Sanity check 1 - Ensure that the input is a geopandas dataframe
    # =========================================================================
    
    # Define custom error class
    class InvalidDataTypeError(Exception):
        pass
    
    # Define custom file validator function
    def validate_datatype(dataframe):
        if not isinstance(dataframe, pd.DataFrame):
            raise InvalidDataTypeError("ERROR - Input must be a GeoPandas DataFrame")
    
    # Try to validate the file type
    try:
        validate_datatype(dataframe)
    except InvalidDataTypeError as e:
        print(e)
        return None
    
    # =========================================================================
    # Load in data files
    # =========================================================================
    
    # Save a local copy of the data frame
    df = dataframe.copy()
    
    df = df.to_crs("EPSG:25832")
    
    # Find the corresponding .zip files - Surface
    zip_files_surface = list(set(["DSM_" + str(df.geometry.y[s])[:3] + "_" + str(df.geometry.x[s])[:2] + "_TIF_UTM32-ETRS89.zip" for s in np.arange(0,len(df.geometry.x))]))
    
    # Find the corresponding file index name for each coordinate - Surface
    coord_files_surface = ["DSM_1km_" + str(df.geometry.y[s])[:4] + "_" + str(df.geometry.x[s])[:3] + ".tif" for s in np.arange(0,len(df.geometry.x))]
    
    # Create list of unique map names - Surface
    # surface_map_list = list(set(coord_files_surface))
    
    # Find the name of the map that contains the highest number of GPS points - Surface
    counts = Counter(coord_files_surface)
    max_count = max(counts.values())
    for s in coord_files_surface:  # preserve first occurrence order
        if counts[s] == max_count:
            surface_map_dense = s
    
    # Find the corresponding .zip files - Surface
    zip_files_terrain = list(set(["DTM_" + str(df.geometry.y[s])[:3] + "_" + str(df.geometry.x[s])[:2] + "_TIF_UTM32-ETRS89.zip" for s in np.arange(0,len(df.geometry.x))]))
    
    # Find the corresponding file index name for each coordinate - Terrain
    coord_files_terrain = ["DTM_1km_" + str(df.geometry.y[s])[:4] + "_" + str(df.geometry.x[s])[:3] + ".tif" for s in np.arange(0,len(df.geometry.x))]
    
    # Create list of unique map names - Terrain
    # terrain_map_list = list(set(coord_files_terrain))
    
    # Find the name of the map that contains the highest number of GPS points - Terrain
    counts = Counter(coord_files_terrain)
    max_count = max(counts.values())
    for s in coord_files_terrain:  # preserve first occurrence order
        if counts[s] == max_count:
            terrain_map_dense = s

    # Print fillisterne for de forskellige typer referencekort
    print('Vi skal bruge disse .zip filer med overfladehøjdekort: ' + str(zip_files_surface) + '\n')
    # print('Vi skal bruge disse overfladehøjdekort: ' + str(surface_map_list) + '\n')
    print('Vi har flest GPS-punkter som ligger i overfladehøjdekortet: ' + str(surface_map_dense) + '\n')
    
    print('Vi skal bruge disse .zip filer med terrænhøjdekort: ' + str(zip_files_terrain) + '\n')
    # print('Vi skal bruge disse terrænhøjdekort: ' + str(terrain_map_list) + '\n')
    print('Vi har flest GPS-punkter som ligger i terrænhøjdekortet: ' + str(terrain_map_dense))


    return 

# =========================================================================
# Custom function - pdExport
# =========================================================================

def pdExport(dataframe, output_filename=None, coloumn_seperator=None, decimal_seperator=None):
    '''Extracts subset of data from a GeoPandas DataFrame file and exports it to a .txt , .csv  or .xlsx file.
    
    Input parameters:
    
        input_filename - string specifying the name of the input Pandas DataFrame file.
    
        output_filename - string specifying the desired name of the output 
        .csv or .txt file. If no argument is provided, the output file will 
        be assigned the name GPSWpts.csv and saved in the Results folder
        
        coloumn_seperator - character specifying the delimiter that seperates data in the 
        output .csv or .txt file. For computers with the ENG system languae, this
        delimeter is ',' but for DK system language computers, this should be 
        changed to a ';' Standard is ';' for .csv files and ',' for .txt files
        
        decimal_seperator - character specifying the delimiter that indicates
        decimal places within numbers in the output .csv or .txt file. 
        For computers with the ENG system languae, this delimeter is '.' but 
        for DK system language computers, this should be changed to a ','
        Standard is '.' for all file types
    '''
    
    # =========================================================================
    # Sanity check 1 - Ensure that the input is a geopandas dataframe
    # =========================================================================
    
    # Define custom error class
    class InvalidDataTypeError(Exception):
        pass
    
    # Define custom file validator function
    def validate_datatype(dataframe):
        if not isinstance(dataframe, pd.DataFrame):
            raise InvalidDataTypeError("ERROR - Input must be a GeoPandas DataFrame")
    
    # Try to validate the file type
    try:
        validate_datatype(dataframe)
    except InvalidDataTypeError as e:
        print(e)
        return None
    
    # =========================================================================
    # Check if an output filename has been specified, and if so, is it correct
    # =========================================================================
    
    # No output filename has been specified
    if output_filename == None:
        
        # Designate the standard name of the 
        output_filename = "Results/GPSWpts.csv"
        
        # Defining filetype string
        ftype = '.csv'
        
        #Print output statement
        print("\nWarning - No output filename was specified, falling back to standard name: GPSWpts.csv")
    
    # Output filename has been specified, but no file extension has been given
    elif (output_filename != None) & (os.path.splitext(output_filename)[1] == ''):
        
        # Append correct file extension
        output_filename = output_filename + ".csv"
        
        # Defining filetype string
        ftype = '.csv'
        
        #Print output statement
        print("\nWarning - No output file format was specified, falling back to standard filetype: .csv")
        
    # Output filename has been specified, but wrong file extension has been given
    elif (output_filename != None) & ((not output_filename.lower().endswith('.txt')) & (not output_filename.lower().endswith('.csv')) & (not output_filename.lower().endswith('.xlsx'))):
           
        # Print message stating the file type has been changed to .txt
        print(f"\nWarning - Incorrect filetype '{os.path.splitext(output_filename)[1]}' specified for the output file, changing to .csv format")
        
        # Extract basename of the output file and append the correct extension
        output_filename = os.path.splitext(os.path.basename(output_filename))[0] + ".csv"
        
        # Defining filetype string
        ftype = '.csv'
        
    # If a filename and correct filetype has been specified, the extract this file extension
    else: 
        
        # Defining filetype string
        ftype = os.path.splitext(output_filename)[1]
        
    # =========================================================================
    # Check if an optional coloumn seperator character has been specified
    # =========================================================================
    
    # No coloumn_seperator has been specified
    if coloumn_seperator == None:
        
        # For .csv files
        if ftype == '.csv':
            
            coloumn_seperator = ','
            
        # For .xlsm files
        elif ftype == '.xlsx':
            
            coloumn_seperator = ','
        
        # For .txt files
        else:
            
            coloumn_seperator = ','
    
    # If coloumn_seperator has been specified 
    else:
        
        # If coloumn_seperator is not in aproved list
        if coloumn_seperator in [',', ';', '\t']:
            
            coloumn_seperator = coloumn_seperator
        
        # If coloumn_seperator not in aproved list
        else:
            
            # For .csv files
            if ftype == '.csv':
                
                coloumn_seperator = ','
            
                print(f"\nWarning - Incorrect coloumn seperator '{coloumn_seperator}' specified for the output file, changing to comma")
                
            # For .xlsm files
            elif ftype == '.xlsx':
                
                coloumn_seperator = ','
            
                print(f"\nWarning - Incorrect coloumn seperator '{coloumn_seperator}' specified for the output file, changing to comma")
            
            # For .txt files
            else:
                
                coloumn_seperator = ','
                
                print(f"\nWarning - Incorrect coloumn seperator '{coloumn_seperator}' specified for the output file, changing to comma")
            
    # =========================================================================
    # Check if an optional decimal seperator character has been specified
    # =========================================================================
    
    # No decimal_seperator has been specified
    if decimal_seperator == None:
        
        # For .csv files
        if ftype == '.csv':
            
            decimal_seperator = '.'
            
        # For .xlsm files
        elif ftype == '.xlsx':
            
            decimal_seperator = ','        
        
        # For .txt files
        else:
            
            decimal_seperator = '.'
    
    # If decimal_seperator has been specified 
    else:
        
        # If decimal_seperator is not in aproved list
        if decimal_seperator in [',', '.']:
            
            decimal_seperator = decimal_seperator
        
        # If decimal_seperator not in aproved list
        else:
            
            # For .csv files
            if ftype == '.csv':
                
                decimal_seperator = '.'
            
                print(f"\nWarning - Incorrect decimal character '{decimal_seperator}' specified for the output file, changing to dot")
                
                
            # For .xlsm files
            elif ftype == '.xlsx':
                
                decimal_seperator = ','   
                
                print(f"\nWarning - Incorrect decimal character '{decimal_seperator}' specified for the output file, changing to comma")
            
            # For .txt files
            else:
                
                decimal_seperator = '.'
                
                print(f"\nWarning - Incorrect decimal character '{decimal_seperator}' specified for the output file, changing to dot")
    
    # =========================================================================
    # Check what attributes are included in the data file
    # =========================================================================
    
    # Possible column names for variables - Name
    name_columns = ['Name', 'name']
    
    # Possible column names for variables - Time
    time_columns = ['Timestamp', 'timestamp', 'time']
    
    # Possible column names for variables - Altitude Elliposid 
    ellipsoid_columns = ['Altitude_Ellipsoid','Altitude Ellipsoid(m)', 'Altitude Ellipsoid',
                                  'altitude ellipsoid(m)', 'altitude ellipsoid',
                                  'Altitudehae', 'altitudehae']
    
    # Possible column names for variables - Altitude MSL
    msl_columns = ['Altitude_MSL','Altitude MSL(m)', 'Altitude MSL', 
                    'altitude MSL(m)', 'altitude MSL',
                    'altitude(m)', 'altitude',
                    'Altitude(m)', 'Altitude',
                    'Elevation', 'elevation','ele']
    
    # Possible column names for variables - Accuracy
    accuracy_columns = ['Accuracy(m)', 'Accuracy', 'accuracy(m)','accuracy']
    
    # Possible column names for variables - Reference Surface Altitude
    reference_surface_columns = ['Altitude_Reference_Surface']
    
    # Possible column names for variables - Reference Terrain Altitude
    reference_terrain_columns = ['Altitude_Reference_Terrain']

    # Find the correct variable columns in the DataFrame
    name_col = next((col for col in name_columns if col in dataframe.columns), None)
    time_col = next((col for col in time_columns if col in dataframe.columns), None)
    ellipsoid_col = next((col for col in ellipsoid_columns if col in dataframe.columns), None)
    msl_col = next((col for col in msl_columns if col in dataframe.columns), None)
    accuracy_col = next((col for col in accuracy_columns if col in dataframe.columns), None)
    reference_surface_col = next((col for col in reference_surface_columns if col in dataframe.columns), None)
    reference_terrain_col = next((col for col in reference_terrain_columns if col in dataframe.columns), None)
    
    # Create list with column names
    variable_list = [name_col,time_col,ellipsoid_col,msl_col,accuracy_col,reference_surface_col,reference_terrain_col]
    
    # Sort out all None entries in the variable list
    filtered_variable_list = [s for s in variable_list if s is not None]
    
    # Extract the filtered out variables
    df_new = dataframe[filtered_variable_list].copy()
    
    # Append Longitude and Latitude coordinates as variables
    df_new['Longitude'] = dataframe.geometry.x
    df_new['Latitude'] = dataframe.geometry.y
    
    # If the filetype is .csv
    if ftype == '.csv':
        
        # Export new data frame
        df_new.to_csv(output_filename, header=True, index=False, sep=coloumn_seperator, decimal=decimal_seperator, encoding='utf-8-sig')
    
    # If filetype is .xlsm
    elif ftype == '.xlsx':
        
        # Export new data frame
        df_new.to_excel(output_filename,sheet_name='GPS_Data', header=True, index=False, engine='xlsxwriter')
        
    # If the filetype is .txt
    else:
    
        # Export new data frame
        df_new.to_csv(output_filename, header=True, index=False, sep=coloumn_seperator, decimal=decimal_seperator)


# =========================================================================
# Middleman function 1
# =========================================================================

def calculateMapBounds(tif_filepaths):
    overall_extent = None  # To hold the overall spatial extent
    overall_min_height = np.inf  # To track the minimum height across all rasters
    overall_max_height = -np.inf  # To track the maximum height across all rasters

    for filepath in tif_filepaths:
        
        if not os.path.isfile(filepath):
            continue
        
        try:
            # Step 1: Open the .tif raster file
            with rasterio.open(filepath) as src:
                # Get raster bounds (spatial extent)
                raster_bounds = src.bounds

                # Read the first band of raster data
                raster_data = src.read(1)

                # Step 2: Calculate min and max height for this raster
                min_height = np.nanmin(raster_data)  # Min height in this raster
                max_height = np.nanmax(raster_data)  # Max height in this raster

                # Step 3: Update the overall min and max heights
                overall_min_height = min(overall_min_height, min_height)
                overall_max_height = max(overall_max_height, max_height)

                # Step 4: Update the overall spatial extent
                if overall_extent is None:
                    overall_extent = raster_bounds
                else:
                    # Merge current raster bounds with the overall extent
                    overall_extent = rasterio.coords.BoundingBox(
                        left=min(overall_extent.left, raster_bounds.left),
                        bottom=min(overall_extent.bottom, raster_bounds.bottom),
                        right=max(overall_extent.right, raster_bounds.right),
                        top=max(overall_extent.top, raster_bounds.top)
                    )

        except Exception as e:
            print(f"Error processing file {filepath}: {e}")

    return overall_extent, overall_min_height, overall_max_height

# =========================================================================
# Middleman function 2
# =========================================================================

def parse_filename_to_bbox(filename, grid_size=1000):
    """
    Extract grid coordinates from the filename and calculate the bounding box.
    
    Parameters:
    - filename (str): The .tif filename, e.g., 'DTM_1km_6170_720.tif'.
    - grid_size (int): The size of each grid cell in meters (1 km = 1000 meters).
    
    Returns:
    - Tuple of bounding box coordinates (min_x, min_y, max_x, max_y).
    """
    # Split the filename to extract the grid indices (easting and northing)
    parts = filename.split('_')
    easting_index = int(parts[2])  # Extract easting index (6170)
    northing_index = int(parts[3].split('.')[0])  # Extract northing index (720)

    # Convert grid indices to geographic coordinates assuming grid_size x grid_size grid cells
    min_x = easting_index * grid_size
    min_y = northing_index * grid_size
    max_x = min_x + grid_size
    max_y = min_y + grid_size

    return (min_x, min_y, max_x, max_y)

# =========================================================================
# Middleman function 3
# =========================================================================

def bbox_overlap(bbox1, bbox2):
    """
    Check if two bounding boxes overlap (partially or fully).
    
    Parameters:
    - bbox1 (tuple): Bounding box (min_x, min_y, max_x, max_y).
    - bbox2 (tuple): Bounding box (min_x, min_y, max_x, max_y).
    
    Returns:
    - True if the bounding boxes overlap, False otherwise.
    """
    min_y1, min_x1, max_y1, max_x1 = bbox1
    min_x2, min_y2, max_x2, max_y2 = bbox2

    # Check if the bounding boxes overlap (partially or fully)
    return not (max_x1 < min_x2 or min_x1 > max_x2 or max_y1 < min_y2 or min_y1 > max_y2)

# =========================================================================
# Middleman function 4
# =========================================================================

def find_tif_files_in_bbox(directory, gdf, grid_size=1000):
    """
    Find all .tif files in the directory whose bounding box partially or fully overlaps
    with the GeoDataFrame's bounding box, using the naming convention of the .tif files.

    Parameters:
    - directory (str): The path to the directory containing .tif files.
    - gdf (GeoDataFrame): The GeoDataFrame whose bounding box will be used for comparison.
    - grid_size (int): The size of each grid cell in meters (default is 1 km = 1000 meters).
    
    Returns:
    - List of file paths that overlap with the bounding box of the GeoDataFrame.
    """
    # Get the bounding box of the GeoDataFrame
    gdf_bbox = gdf.total_bounds
    found_files = []

    # Loop through all .tif files in the directory
    for filename in os.listdir(directory):
        
        if filename.endswith('.tif'):
            # Parse the filename to get the bounding box of the .tif file
            file_bbox = parse_filename_to_bbox(filename, grid_size)
            
            # Check if the .tif bounding box overlaps with the GeoDataFrame bounding box
            if bbox_overlap(file_bbox, gdf_bbox):
                found_files.append(os.path.join(directory, filename))

    return found_files

# =========================================================================
# Custom function - plotDKMap
# =========================================================================

def plotDKMap(dataframe, output_file_name = None, zoom = False, name = False, height = False):
    
    # =========================================================================
    # Sanity check 1 - Ensure that the output file is in accpeted format
    # =========================================================================
    
    # Define custom error class
    class InvalidFileType(Exception):
        pass
    
    # Define custom file validator function
    def validate_filetype(output_file_name):
        
        # Extract file extension
        _, extension = os.path.splitext(output_file_name)
        
        # Make check
        if not extension.lower() in ['.png', '.jpg', '.pdf']:
            raise InvalidFileType("ERROR - Output file must be in either format: .png or .jpg or .pdf")
    
    
    if output_file_name != None:
        # Try to validate the file type
        try:
            validate_filetype(output_file_name)
        except InvalidFileType as e:
            print(e)
            return None
    

    # Find minimum og maksimum koordinaterne for GPS punkterne
    minx, miny, maxx, maxy = dataframe.total_bounds
    
    # Udregn distancen i Latitude og Longitude retningen mellem disse koordinater
    xdist = maxx-minx
    ydist = maxy-miny
    
    # Indhent en "SHaPefile" fil med polygoner i form af Danmark
    shp = gpd.read_file("Data/Landmap/dk_polygons.shp")
    
    # Specificer at vi plotter en figur kaldt fig med akserne ax, og at figuren skal være 8x8 tommer (ca 15x15cm) storm med opløsning 200 (standard 100)
    fig, ax = plt.subplots(figsize=(6,6), dpi=200, constrained_layout=True) 
    
    # Plot polygonerne med hvid fyldfarve og sorte kantstreger langs figurens akser 
    shp.plot(ax=ax,color="white", edgecolor='black') 
    
    # Tjek om GPS-punkterne skal farvekodes 
    if height == False:
        
        # Hvis nej
        
        # Plot de forskellige GPS punkter i rød langs figurens akser
        dataframe.plot(ax=ax,color='red',label='GPS punkter')   
    
        # Tilføj en legende (forklaring på hvad punkterne betyder) inde i figuren, specificer at den skal være i skriftstørrelse 8
        plt.legend(fontsize=8)
    
    else:
        
        # Hvis ja
        
        # Plot de forskellige GPS punkter men nu også farvekodet efter deres højde over middel havniveau
        dataframe.plot(column='Altitude_MSL', # Definer hvilken variabel punkterne skal farvekodes efter
                     ax = ax,     # Definer hvilke akser de skal plottes langs
                     cmap = 'viridis', # Definer hvilket farvetema punkterne skal farvekodes efter 
                     legend = True,      # Specificer at vi gerne vil have et navn for hvert punkt printet over dem
                     legend_kwds = {"location":"right","shrink":.5},) # Specificer hvor vi gerne vil have deres tilhørende colorbar stående i plottet, og at den skal skrumpes til 50% størrelse
        
        # Indhent akse-nummeret på plottets colorbar
        colorbar_ax = ax.get_figure().axes[-1]    
        
        # Definer hvad der skal stå ved siden af plottets colorbar, skrifttørrelse 8 og paddet med en linje af skriftstørrelse 15
        colorbar_ax.set_ylabel("Højde over middel havniveau [m]", size=8, labelpad = 10) 
        
        # Definer skriftstørrelsen på colorbarens inddelinger
        colorbar_ax.tick_params(labelsize=8)   
    
    # Tjek om punkterne skal have et navn sat på 
    if name == True:
        
        # Plot navnet på de individuelle GPS punkterne ved siden af dem og giv dem navnet ud fra variablen "name"
        for x, y, label in zip(dataframe.geometry.x, dataframe.geometry.y, dataframe.Name):
            ax.annotate(label, xy=(x, y), xytext=(3, 3), textcoords="offset points", fontsize=8)
    
    # Definer titlen på plottet, specificer at det skal være i skriftstørrelse 14, og at der skal indsættes 15 "punkter"'s mellemrum mellem titlen og figuren
    plt.title('Kort over Danmark med GPS-punkter',fontsize=14, pad=10)     
    
    # Definer navnet på x-aksen, specificer at det skal være i skriftstørrelse 8, og at der skal indsættes 15 "punkter"'s mellemrum mellem navnet på x-aksen og og figuren
    plt.xlabel('Længdegrad [decimalgrader]',fontsize=8, labelpad=10) 
    
    # Definer navnet på y-aksen, specificer at det skal være i skriftstørrelse 8, og at der skal indsættes 15 "punkter"'s mellemrum mellem navnet på y-aksen og og figuren
    plt.ylabel('Breddegrad [decimalgrader]',fontsize=8, labelpad=10) 
    
    # Definer størrelsen på teksten der står ved de store inddelinger på både x-aksen og y-aksen, specificer at det skal være i skriftstørrelse 8
    ax.tick_params(axis='both', which='major', labelsize=8)
    
    # Tjek om figuren skal være zoomet ind
    if zoom == True:
        
        # Definer grænserne på x-aksen og y-aksen som værende mellem de forskellige minimum/maksimum-koordinater +- 20 procent af distancen mellem dem
        plt.axis([minx-xdist*0.2, maxx+xdist*0.2, miny-ydist*0.2, maxy+ydist*0.2]) 
        
        # Roter Longitude koordinaterne så de står skråt ned af siden (gjort for at gøre dem lettere at læse)
        fig.figure.autofmt_xdate()

    # Specificer at vi ikke vil have videnskabelig notation på koordinaterne der står langs akserne
    ax.ticklabel_format(useOffset=False)
    
    # Tving figuren til at være en firkant med pæne dimensioner i begge retninger 
    ax.set_aspect(1.0/ax.get_data_ratio(), adjustable='box') 
    
    if output_file_name != None:
        
        # Definer output string
        output_string = "Results/" + output_file_name
        
        # Gem figuren som en .pdf fil, specificer at vi gerne vil fjerne unødvendigt hvid rum omkring figuren
        # Filtypen på den gemte figur kan ændres til .jpg .png eller lignende ved at ændre filtypen i slutningen af navnet
        fig.savefig(output_string, bbox_inches='tight')
    
# =============================================================================
# Custom function - plotHeightMap
# ============================================================================= 

def plotHeightMap(mapfile, dataframe = None, output_file_name = None, ptitle = 'Højdekort', name = False, zoom = True):

    # =========================================================================
    # Sanity check 1 - Ensure that the output file is in accpeted format
    # =========================================================================

    # Define custom error class
    class InvalidFileType(Exception):
        pass
    
    # Define custom file validator function
    def validate_filetype(output_file_name):
        
        # Extract file extension
        _, extension = os.path.splitext(output_file_name)
        
        # Make check
        if not extension.lower() in ['.png', '.jpg', '.pdf']:
            raise InvalidFileType("ERROR - Output file must be in either format: .png or .jpg or .pdf")
    
    
    if output_file_name != None:
        # Try to validate the file type
        try:
            validate_filetype(output_file_name)
        except InvalidFileType as e:
            print(e)
            return None    


    # Åben vores .tif fil
    r1 = rasterio.open(mapfile)
    
    # Læs vores .tif fil
    ra1 = r1.read()
    
    # Omdan højdeværdierne i vores .tif fil til en matrix der er lettere at arbejde med
    ras1 = np.reshape(ra1, (ra1.shape[0]*ra1.shape[1], ra1.shape[2]))
    
    # Få original transform og CRS
    transform_r = r1.transform
    crs_r = r1.crs
    
    # Lav koordinater for hjørnerne
    height, width = ras1.shape
    cols, rows = np.meshgrid(np.arange(width), np.arange(height))
    xs, ys = rasterio.transform.xy(transform_r, rows, cols)
    xs = np.array(xs)
    ys = np.array(ys)
    
    # Transformér koordinater fra original CRS til WGS84
    transformer = Transformer.from_crs(crs_r, "EPSG:4326", always_xy=True)
    lons, lats = transformer.transform(xs, ys)
    
    # Plot raster med WGS84-aksen
    f4, ax4 = plt.subplots(figsize=(6, 6), dpi=200, constrained_layout=True)
    base1 = ax4.imshow(ras1, extent=[lons.min(), lons.max(), lats.min(), lats.max()],
                       origin='upper', cmap='viridis')
    

        
    # Define the normalization for consistent color scaling
    min_height1 = ras1.min()  # Get the min height from the raster data
    max_height1 = ras1.max()  # Get the max height from the raster data
    norm1 = Normalize(vmin=min_height1, vmax=max_height1)
    
    if isinstance(dataframe, gpd.GeoDataFrame):
        # Plot the GeoDataFrame on top of the raster
        dataframe.plot(column='Altitude_MSL', # Definer hvilken variabel punkterne skal farvekodes efter
                     ax = ax4,     # Definer hvilke akser de skal plottes langs
                     cmap = 'viridis',# Definer hvilket farvetema vores GPS punkter skal have
                     edgecolor = 'black',# Definer hvilken farve kanten af vores GPS punkter skal have
                     norm=norm1)   
    
    if (name == True) & (isinstance(dataframe, gpd.GeoDataFrame)):
        
        # Create annotations
        for x, y, label in zip(dataframe.geometry.x, dataframe.geometry.y, dataframe.Name):
            ax4.annotate(label, xy=(x, y), xytext=(3, 3), textcoords="offset points", fontsize=8)
    
    # Colorbar
    cbar = f4.colorbar(base1, ax=ax4, shrink=0.5)
    cbar.set_label("Højde over middel havniveau [m]", size=8, labelpad=10)
    cbar.ax.tick_params(labelsize=8)
    
    # Titler og akse-labels
    plt.title(ptitle, fontsize=14, pad=10)
    plt.xlabel('Længdegrad [decimalgrader]', fontsize=8, labelpad=10)
    plt.ylabel('Breddegrad [decimalgrader]', fontsize=8, labelpad=10)
    
    # Definer størrelsen på teksten der står ved de store inddelinger på både x-aksen og y-aksen, specificer at det skal være i skriftstørrelse 8
    ax4.tick_params(axis='both', which='major', labelsize=8)
    
    # Sørg for kvadratisk forhold
    ax4.set_aspect(1.0 / ax4.get_data_ratio(), adjustable='box')
    
    if zoom == True: 
        ax4.set_xlim([lons.min(), lons.max()])
        ax4.set_ylim([lats.min(), lats.max()])
    
    # Roter 
    f4.figure.autofmt_xdate()
    plt.show()
    
    if output_file_name != None:
        
        # Definer output string
        output_string = "Results/" + output_file_name
        
        # Gem figuren som en .pdf fil, specificer at vi gerne vil fjerne unødvendigt hvid rum omkring figuren
        # Filtypen på den gemte figur kan ændres til .jpg .png eller lignende ved at ændre filtypen i slutningen af navnet
        f4.savefig(output_string, bbox_inches='tight')