
# ############################################################
# import ee

# BASIN_ASSET_ID = "projects/ee-officialsatbir23/assets/Area"
# YEARS = list(range(2021, 2022))
# SCALE = 10
# PIXEL_AREA_M2 = 100
# MAX_PIXELS = 2_000_000_000

# ee.Initialize(project="ee-officialsatbir23")

# def compute_covered_area(img: ee.Image, geom: ee.Geometry, scale: int) -> ee.Number:
#     pixel_count = img.reduceRegion(
#         reducer=ee.Reducer.count(),
#         geometry=geom,
#         scale=scale,
#         maxPixels=MAX_PIXELS,
#         tileScale=16
#     ).values().get(0)
#     return ee.Number(pixel_count).multiply(PIXEL_AREA_M2).divide(10_000)  # m² to hectares

# def quantify_dw_coverage_fc(basin_asset_id: str, years: list[int]) -> ee.FeatureCollection:
#     basin = ee.FeatureCollection(basin_asset_id).geometry()
#     dw_col = ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1").select("label")
#     total_area_ha = compute_covered_area(ee.Image.constant(1).clip(basin), basin, SCALE)

#     features = []
#     for year in years:
#         year_start = ee.Date(f"{year}-01-01")
#         year_end = year_start.advance(1, 'year')
#         year_img = dw_col.filterDate(year_start, year_end).mosaic().selfMask().clip(basin)
#         year_area_ha = compute_covered_area(year_img, basin, SCALE)
#         coverage_percent = year_area_ha.divide(total_area_ha).multiply(100)

#         feat = ee.Feature(None, {
#             "Period": f"{year}_total",
#             "Coverage_hectares": year_area_ha,
#             "Coverage_percent": coverage_percent,
#             "total_area": total_area_ha
#         })
#         features.append(feat)

#         # Monthly breakdown
#         for m in range(1, 13):
#             start = ee.Date(f"{year}-{m:02d}-01")
#             end = start.advance(1, 'month')
#             month_img = dw_col.filterDate(start, end).mosaic().selfMask().clip(basin)
#             month_area_ha = compute_covered_area(month_img, basin, SCALE)
#             month_coverage_percent = month_area_ha.divide(total_area_ha).multiply(100)

#             month_feat = ee.Feature(None, {
#                 "Period": f"{year}_{m:02d}",
#                 "Coverage_hectares": month_area_ha,
#                 "Coverage_percent": month_coverage_percent,
#                 "total_area": total_area_ha
#             })
#             features.append(month_feat)
#     return ee.FeatureCollection(features)

# if __name__ == "__main__":
#     print("Exporting Dynamic World coverage results to Google Drive ...")
#     fc = quantify_dw_coverage_fc(BASIN_ASSET_ID, YEARS)
#     task = ee.batch.Export.table.toDrive(
#         collection=fc,
#         description='dynamic_world_coverage_EECU_1',
#         fileFormat='CSV',
#         folder='DynamicWorldExports',
#         fileNamePrefix='Varuna_coverage_EECU_1'
#     )
#     task.start()
#     print("Export task started. Check the Earth Engine Tasks tab or your Google Drive after completion.")
# --------------------------->> for loop used > EECU : more then 30 minutes >> i cut it off there : : 14740.8760 

########################################################################################################

# import ee

# BASIN_ASSET_ID = "projects/ee-officialsatbir23/assets/Area"
# YEARS = list(range(2021, 2022))
# SCALE = 10
# PIXEL_AREA_M2 = 100
# MAX_PIXELS = 2_000_000_000

# ee.Initialize(project="ee-officialsatbir23")

# def compute_covered_area(img: ee.Image, geom: ee.Geometry, scale: int) -> ee.Number:
#     pixel_count = img.reduceRegion(
#         reducer=ee.Reducer.count(),
#         geometry=geom,
#         scale=scale,
#         maxPixels=MAX_PIXELS,
#         tileScale=16
#     ).values().get(0)
#     return ee.Number(pixel_count).multiply(PIXEL_AREA_M2).divide(10_000)  # m² to hectares

# def quantify_dw_coverage_fc(basin_asset_id: str, years: list[int]) -> ee.FeatureCollection:
#     basin = ee.FeatureCollection(basin_asset_id).geometry()
#     dw_col = ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1").filterBounds(basin).select("label")    
#     total_area_ha = compute_covered_area(ee.Image.constant(1).clip(basin), basin, SCALE)

#     def year_feature(year):
#         year = ee.Number(year)
#         year_start = ee.Date(ee.String(year.format()).cat('-01-01'))
#         year_end = year_start.advance(1, 'year')
#         year_img = dw_col.filterDate(year_start, year_end).mosaic().selfMask().clip(basin)
#         year_area_ha = compute_covered_area(year_img, basin, SCALE)
#         coverage_percent = year_area_ha.divide(total_area_ha).multiply(100)

#         # Yearly feature
#         year_feat = ee.Feature(None, {
#             "Period": year.format().cat('_total'),
#             "Coverage_hectares": year_area_ha,
#             "Coverage_percent": coverage_percent,
#             "total_area": total_area_ha
#         })

#         # Monthly features
#         def month_feature(m):
#             m = ee.Number(m)
#             start = ee.Date(ee.String(year.format()).cat('-').cat(m.format('%02d')).cat('-01'))
#             end = start.advance(1, 'month')
#             month_img = dw_col.filterDate(start, end).mosaic().selfMask().clip(basin)
#             month_area_ha = compute_covered_area(month_img, basin, SCALE)
#             month_coverage_percent = month_area_ha.divide(total_area_ha).multiply(100)
#             return ee.Feature(None, {
#                 "Period": year.format().cat('_').cat(m.format('%02d')),
#                 "Coverage_hectares": month_area_ha,
#                 "Coverage_percent": month_coverage_percent,
#                 "total_area": total_area_ha
#             })

#         months = ee.List.sequence(1, 12)
#         month_feats = months.map(month_feature)
#         return ee.List([year_feat]).cat(month_feats)

#     years_list = ee.List(years)
#     all_feats = years_list.map(year_feature).flatten()
#     return ee.FeatureCollection(all_feats)

# if __name__ == "__main__":
#     print("Exporting Dynamic World coverage results to Google Drive ...")
#     fc = quantify_dw_coverage_fc(BASIN_ASSET_ID, YEARS)
#     task = ee.batch.Export.table.toDrive(
#         collection=fc,
#         description='dynamic_world_coverage_EECU_2',
#         fileFormat='CSV',
#         folder='DynamicWorldExports',
#         fileNamePrefix='Varuna_coverage_EECU_2'
#     )
#     task.start()
#     print("Export task started. Check the Earth Engine Tasks tab or your Google Drive after completion.")

    # ----------> EECU : 15 minutes >> i stopped it : 6728.6543 could be more


#################################################################################################

#complete

# import ee

# # Constants
# BASIN_ASSET_ID = "projects/ee-officialsatbir23/assets/Area"
# YEARS = list(range(2021, 2022))
# SCALE = 10
# PIXEL_AREA_M2 = 100
# MAX_PIXELS = 1e13

# ee.Initialize(project="ee-officialsatbir23")

# def compute_covered_area(img: ee.Image, geom: ee.Geometry, scale: int) -> ee.Number:
#     """Compute area of valid pixels in hectares"""
#     result = img.reduceRegion(
#         reducer=ee.Reducer.count(),
#         geometry=geom,
#         scale=scale,
#         maxPixels=MAX_PIXELS,
#         tileScale=16
#     )
#     values = result.values()
#     pixel_count = ee.Algorithms.If(
#         values.size().gt(0),
#         values.get(0),
#         ee.Number(0)
#     )
#     return ee.Number(pixel_count).multiply(PIXEL_AREA_M2).divide(10_000)

# def process_period(year, month=None):
#     """Process a specific time period (year or month)"""
#     year = ee.Number(year)
    
#     if month is None:
#         # Process year
#         start = ee.Date.fromYMD(year, 1, 1)
#         end = start.advance(1, 'year')
#         name = ee.String(year.format()).cat('_total')
#     else:
#         # Process month
#         month = ee.Number(month)
#         start = ee.Date.fromYMD(year, month, 1)
#         end = start.advance(1, 'month')
#         name = ee.String(year.format()).cat('_').cat(month.format('%02d'))
    
#     img = dw_col.filterDate(start, end).mosaic().selfMask().clip(basin)
    
#     area_ha = compute_covered_area(img, basin, SCALE)
    
#     return ee.Feature(None, {
#         'Period': name,
#         'Coverage_hectares': area_ha,
#         'Coverage_percent': area_ha.divide(total_area_ha).multiply(100),
#         'total_area': total_area_ha,
#         'has_data': dw_col.filterDate(start, end).size().gt(0)
#     })

# def process_year(year):
#     """Process a complete year including monthly data"""
#     # Get yearly feature
#     year_feature = process_period(year)
    
#     # Get monthly features using map()
#     months = ee.List.sequence(1, 12)
#     month_features = months.map(lambda m: process_period(year, m))
    
#     # Combine yearly and monthly features
#     return ee.List([year_feature]).cat(month_features)

# def quantify_dw_coverage_fc(basin_asset_id: str, years: list[int]) -> ee.FeatureCollection:
#     """Main function to process coverage analysis"""
#     global basin, dw_col, total_area_ha
    
#     # Initialize global variables
#     basin = ee.FeatureCollection(basin_asset_id).geometry().simplify(100)
#     dw_col = ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1").filterBounds(basin).select("label")
    
#     # Calculate total area once
#     total_area_ha = compute_covered_area(
#         ee.Image.constant(1).clip(basin),basin,SCALE
#     )
    
#     # Process all years using map()
#     years_list = ee.List(years)
#     features = years_list.map(process_year).flatten()
    
#     # Convert to FeatureCollection
#     return ee.FeatureCollection(features)

# if __name__ == "__main__":
#     print("Processing Dynamic World coverage for all years and months...")
#     fc = quantify_dw_coverage_fc(BASIN_ASSET_ID, YEARS)
    
#     task = ee.batch.Export.table.toDrive(
#         collection=fc,
#         description='dynamic_world_coverage_EECU_3',
#         fileFormat='CSV',
#         folder='DynamicWorldExports',
#         fileNamePrefix='varuna_coverage_EECU_3'
#     )
#     task.start()
#     print("Export task started. Check the Earth Engine Tasks tab for progress.")


#-------------------> map used instead of for loop > EECU :  26053.7910 6 minutes

#################################################################


# worked
# import ee

# # Constants
# BASIN_ASSET_ID = "projects/ee-officialsatbir23/assets/Area"
# YEARS = list(range(2021, 2022))
# SCALE = 10
# PIXEL_AREA_M2 = 100
# MAX_PIXELS = 1e13

# ee.Initialize(project="ee-officialsatbir23")

# def compute_covered_area(img: ee.Image, geom: ee.Geometry, scale: int) -> ee.Number:
#     """Compute area of valid pixels in hectares"""
#     result = img.reduceRegion(
#         reducer=ee.Reducer.count(),
#         geometry=geom,
#         scale=scale,
#         maxPixels=MAX_PIXELS,
#         tileScale=16
#     )
#     values = result.values()
#     pixel_count = ee.Algorithms.If(
#         values.size().gt(0),
#         values.get(0),
#         ee.Number(0)
#     )
#     return ee.Number(pixel_count).multiply(PIXEL_AREA_M2).divide(10_000)

# def process_year(year):
#     """Process a single year using server-side operations"""
#     year = ee.Number(year)
#     start = ee.Date.fromYMD(year, 1, 1)
#     end = start.advance(1, 'year')
    
#     img = dw_col.filterDate(start, end).mosaic().selfMask().clip(basin)
    
#     area_ha = compute_covered_area(img, basin, SCALE)
    
#     return ee.Feature(None, {
#         'Period': ee.String(year.format()).cat('_total'),
#         'Coverage_hectares': area_ha,
#         'Coverage_percent': area_ha.divide(total_area_ha).multiply(100),
#         'total_area': total_area_ha,
#         'has_data': dw_col.filterDate(start, end).size().gt(0)
#     })

# def quantify_dw_coverage_fc(basin_asset_id: str, years: list[int]) -> ee.FeatureCollection:
#     """Main function to process yearly coverage analysis"""
#     global basin, dw_col, total_area_ha
    
#     # Initialize global variables
#     basin = ee.FeatureCollection(basin_asset_id).geometry().simplify(100)
#     dw_col = ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1")\
#         .filterBounds(basin).select("label")
    
#     # Calculate total area once
#     total_area_ha = compute_covered_area(
#         ee.Image.constant(1).clip(basin),basin,SCALE
#     )
    
#     # Process years using server-side map()
#     years_list = ee.List(years)
#     features = years_list.map(process_year)
    
#     return ee.FeatureCollection(features)

# if __name__ == "__main__":
#     print("Processing Dynamic World yearly coverage...")
#     fc = quantify_dw_coverage_fc(BASIN_ASSET_ID, YEARS)
    
#     task = ee.batch.Export.table.toDrive(
#         collection=fc,
#         description='dynamic_world_coverage_EECU_4',
#         fileFormat='CSV',
#         folder='DynamicWorldExports',
#         fileNamePrefix='Varuna_coverage_EECU_4'
#     )
#     task.start()
#     print("Export task started. Check the Earth Engine Tasks tab for progress.")

#------------------> this is  for year only.

#############################################################################


# monthly mosaics as yearly collection

# import ee

# # Constants
# BASIN_ASSET_ID = "projects/ee-officialsatbir23/assets/Area"
# YEARS = list(range(2021, 2022))
# SCALE = 10
# PIXEL_AREA_M2 = 100
# MAX_PIXELS = 1e13

# ee.Initialize(project="ee-officialsatbir23")

# def compute_covered_area(img: ee.Image, geom: ee.Geometry, scale: int) -> ee.Number:
#     """Compute area of valid pixels in hectares"""
#     result = img.reduceRegion(
#         reducer=ee.Reducer.count(),
#         geometry=geom,
#         scale=scale,
#         maxPixels=MAX_PIXELS,
#         tileScale=16
#     )
#     values = result.values()
#     pixel_count = ee.Algorithms.If(
#         values.size().gt(0),
#         values.get(0),
#         ee.Number(0)
#     )
#     return ee.Number(pixel_count).multiply(PIXEL_AREA_M2).divide(10_000)

# def process_year_optimized(year):
#     """Process a year by first creating monthly mosaics and reusing them"""
#     year = ee.Number(year)
    
#     def process_month(month):
#         """Create monthly mosaic and feature"""
#         month = ee.Number(month)
#         start = ee.Date.fromYMD(year, month, 1)
#         end = start.advance(1, 'month')
        
#         # Create monthly mosaic
#         month_img = dw_col.filterDate(start, end).mosaic().selfMask().clip(basin).set('month', month).set('year', year)
        
#         # Calculate monthly stats
#         area_ha = compute_covered_area(month_img, basin, SCALE)
        
#         # Create monthly feature
#         month_feature = ee.Feature(None, {
#             'Period': ee.String(year.format()).cat('_').cat(month.format('%02d')),
#             'Coverage_hectares': area_ha,
#             'Coverage_percent': area_ha.divide(total_area_ha).multiply(100),
#             'total_area': total_area_ha,
#             'has_data': dw_col.filterDate(start, end).size().gt(0)
#         })
        
#         return {'image': month_img, 'feature': month_feature}
    
#     # Process all months and collect results
#     months = ee.List.sequence(1, 12)
#     month_results = months.map(process_month)
#     # Create collection from monthly mosaics
    
#     monthly_mosaics = ee.ImageCollection(month_results.map(lambda x: ee.Dictionary(x).get('image')))
#     monthly_features = ee.List(month_results.map(lambda x: ee.Dictionary(x).get('feature')))
    
#     # Create yearly mosaic from monthly mosaics
#     year_img = monthly_mosaics.mosaic().selfMask().clip(basin)
#     year_area_ha = compute_covered_area(year_img, basin, SCALE)
    
#     # Create yearly feature
#     year_feature = ee.Feature(None, {
#         'Period': ee.String(year.format()).cat('_total'),
#         'Coverage_hectares': year_area_ha,
#         'Coverage_percent': year_area_ha.divide(total_area_ha).multiply(100),
#         'total_area': total_area_ha,
#         'has_data': monthly_mosaics.size().gt(0)
#     })
    
#     # Combine yearly and monthly features
#     return ee.List([year_feature]).cat(monthly_features)

# def quantify_dw_coverage_fc(basin_asset_id: str, years: list[int]) -> ee.FeatureCollection:
#     """Main function to process coverage analysis"""
#     global basin, dw_col, total_area_ha
    
#     # Initialize global variables
#     basin = ee.FeatureCollection(basin_asset_id).geometry().simplify(100)

#     start_year = ee.Number(min(years))
#     end_year = ee.Number(max(years) + 1)
#     start_date = ee.Date.fromYMD(start_year, 1, 1)
#     end_date = ee.Date.fromYMD(end_year, 1, 1)
#     dw_col = ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1").filterBounds(basin).filterDate(start_date, end_date).select("label")
    
#     # Calculate total area once
#     total_area_ha = compute_covered_area(
#         ee.Image.constant(1).clip(basin),
#         basin,
#         SCALE
#     )
    
#     # Process all years using optimized method
#     years_list = ee.List(years)
#     features = years_list.map(process_year_optimized).flatten()
    
#     return ee.FeatureCollection(features)

# if __name__ == "__main__":
#     print("Processing Dynamic World coverage for all years and months...")
#     fc = quantify_dw_coverage_fc(BASIN_ASSET_ID, YEARS)
    
#     task = ee.batch.Export.table.toDrive(
#         collection=fc,
#         description='dynamic_world_coverage_EECU_5',
#         fileFormat='CSV',
#         folder='DynamicWorldExports',
#         fileNamePrefix='Varuna_coverage_EECU_5'
#     )
#     task.start()
#     print("Export task started. Check the Earth Engine Tasks tab for progress.")

#----------------> used monthly mosaics to create yearly collection > EECU : 72714.0078 >> 5 minutes

#############################################################################

####################################################################################

# import ee

# # Constants
# BASIN_ASSET_ID = "projects/ee-officialsatbir23/assets/Area"
# YEARS = list(range(2021, 2022))
# SCALE = 10
# PIXEL_AREA_M2 = 100
# MAX_PIXELS = 1e13

# ee.Initialize(project="ee-officialsatbir23")

# def compute_coverage_area(count_img: ee.Image, geom: ee.Geometry, scale: int) -> ee.Number:
#     """Compute area of covered pixels in hectares"""
#     result = count_img.gt(0).reduceRegion(
#         reducer=ee.Reducer.sum(),
#         geometry=geom,
#         scale=scale,
#         maxPixels=MAX_PIXELS,
#         tileScale=16
#     )
#     return ee.Number(result.values().get(0)).multiply(PIXEL_AREA_M2).divide(10_000)

# def process_year_count_based(year):
#     """Process a year using optimized count-based approach"""
#     year = ee.Number(year)
    
#     def create_monthly_feature_and_binary(month):
#         """Create feature and binary image in single pass"""
#         month = ee.Number(month)
#         start = ee.Date.fromYMD(year, month, 1)
#         end = start.advance(1, 'month')
        
#         # Create count and binary image once
#         monthly_count = dw_col.filterDate(start, end).select('label').count().rename('coverage')
            
#         area_ha = compute_coverage_area(monthly_count, basin, SCALE)
        
#         return ee.Feature(None, {
#             'Period': ee.String(year.format()).cat('_').cat(month.format('%02d')),
#             'Coverage_hectares': area_ha,
#             'Coverage_percent': area_ha.divide(total_area_ha).multiply(100),
#             'total_area': total_area_ha,
#             'binary_image': monthly_count.gt(0)  # Store binary image in feature properties
#         })
    
#     # Process monthly data
#     months = ee.List.sequence(1, 12)
#     monthly_features = ee.FeatureCollection(months.map(create_monthly_feature_and_binary))
    
#     # Create yearly feature using stored binary images
#     year_start = ee.Date.fromYMD(year, 1, 1)
#     year_end = year_start.advance(1, 'year')
#     yearly_count = dw_col.filterDate(year_start, year_end)\
#         .select('label')\
#         .count()\
#         .rename('coverage')
    
#     year_area_ha = compute_coverage_area(yearly_count, basin, SCALE)
#     year_feature = ee.Feature(None, {
#         'Period': ee.String(year.format()).cat('_total'),
#         'Coverage_hectares': year_area_ha,
#         'Coverage_percent': year_area_ha.divide(total_area_ha).multiply(100),
#         'total_area': total_area_ha
#     })
    
#     return ee.FeatureCollection([year_feature]).merge(monthly_features)

# def quantify_dw_coverage_fc(basin_asset_id: str, years: list[int]) -> ee.FeatureCollection:
#     """Process coverage analysis using server-side operations"""
#     global basin, dw_col, total_area_ha
    
#     basin = ee.FeatureCollection(basin_asset_id).geometry().simplify(100)
    
#     # Filter collection once
#     start_year = ee.Number(min(years))
#     end_year = ee.Number(max(years) + 1)
#     start_date = ee.Date.fromYMD(start_year, 1, 1)
#     end_date = ee.Date.fromYMD(end_year, 1, 1)
    
#     dw_col = ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1")\
#         .filterBounds(basin)\
#         .filterDate(start_date, end_date)\
#         .select("label")
    
#     total_area_ha = compute_coverage_area(
#         ee.Image.constant(1).rename('coverage').clip(basin),
#         basin,
#         SCALE
#     )
    
#     years_list = ee.List(years)
#     features = years_list.map(process_year_count_based)
    
#     return ee.FeatureCollection(features).flatten()

# if __name__ == "__main__":
#     print("Processing Dynamic World coverage analysis...")
#     fc = quantify_dw_coverage_fc(BASIN_ASSET_ID, YEARS)
    
#     task = ee.batch.Export.table.toDrive(
#         collection=fc,
#         description='dynamic_world_coverage_EECU_9',
#         fileFormat='CSV',
#         folder='DynamicWorldExports',
#         fileNamePrefix='coverage_results_optimized_varuna_EECU_9'
#     )
#     task.start()
#     print("Export task started. Check the Earth Engine Tasks tab for progress.")

    #------------------> count method with using monthly binary images as collection  > EECU : 25261.3613 in 9 minutes

# import ee

# # Constants
# BASIN_ASSET_ID = "projects/ee-officialsatbir23/assets/Area"
# YEARS = list(range(2021, 2022))
# SCALE = 10
# PIXEL_AREA_M2 = 100
# MAX_PIXELS = 1e13

# ee.Initialize(project="ee-officialsatbir23")

# def compute_coverage_area(count_img: ee.Image, geom: ee.Geometry, scale: int) -> ee.Number:
#     """Compute area of covered pixels using count thresholding with empty handling"""
#     # Add default band name for consistent processing
#     count_img = count_img.rename('coverage')
    
#     result = count_img.gt(0).reduceRegion(
#         reducer=ee.Reducer.sum(),
#         geometry=geom,
#         scale=scale,
#         maxPixels=MAX_PIXELS,
#         tileScale=16
#     )
    
#     return ee.Number(result.get('coverage', 0)).multiply(PIXEL_AREA_M2).divide(10_000)

# def process_year_count_based(year):
#     """Process a year using optimized count-based approach"""
#     year = ee.Number(year)
    
#     def create_monthly_feature(month):
#         """Create feature for a single month with empty collection handling"""
#         month = ee.Number(month)
#         start = ee.Date.fromYMD(year, month, 1)
#         end = start.advance(1, 'month')
        
#         # Get filtered collection
#         filtered = dw_col.filterDate(start, end)
        
#         # Create count image with empty check
#         monthly_count = ee.Image(
#             ee.Algorithms.If(
#                 filtered.size().gt(0),
#                 filtered.select('label').count(),
#                 ee.Image.constant(0)
#             )
#         )
        
#         area_ha = compute_coverage_area(monthly_count, basin, SCALE)
        
#         return ee.Feature(None, {
#             'Period': ee.String(year.format()).cat('_').cat(month.format('%02d')),
#             'Coverage_hectares': area_ha,
#             'Coverage_percent': area_ha.divide(total_area_ha).multiply(100),
#             'total_area': total_area_ha
#         })
    
#     # Process monthly data using server-side map
#     months = ee.List.sequence(1, 12)
#     monthly_features = ee.FeatureCollection(months.map(create_monthly_feature))
    
#     # Process yearly data
#     yearly_count = dw_col.filterDate(
#         ee.Date.fromYMD(year, 1, 1),
#         ee.Date.fromYMD(year, 1, 1).advance(1, 'year')
#     ).select('label').count().rename('coverage')
    
#     year_area_ha = compute_coverage_area(yearly_count, basin, SCALE)
#     year_feature = ee.Feature(None, {
#         'Period': ee.String(year.format()).cat('_total'),
#         'Coverage_hectares': year_area_ha,
#         'Coverage_percent': year_area_ha.divide(total_area_ha).multiply(100),
#         'total_area': total_area_ha
#     })
    
#     return ee.FeatureCollection([year_feature]).merge(monthly_features)

# def quantify_dw_coverage_fc(basin_asset_id: str, years: list[int]) -> ee.FeatureCollection:
#     """Process coverage analysis using optimized server-side operations"""
#     global basin, dw_col, total_area_ha
    
#     # Initialize and filter collection once
#     basin = ee.FeatureCollection(basin_asset_id).geometry().simplify(100)
#     start_date = ee.Date.fromYMD(min(years), 1, 1)
#     end_date = ee.Date.fromYMD(max(years) + 1, 1, 1)
    
#     dw_col = ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1").filterBounds(basin).filterDate(start_date, end_date).select("label")
    
#     total_area_ha = compute_coverage_area(
#         ee.Image.constant(1).clip(basin),
#         basin,
#         SCALE
#     )
    
#     # Process all years using server-side operations
#     features = ee.FeatureCollection(ee.List(years).map(process_year_count_based)).flatten()
#     return features

# if __name__ == "__main__":
#     print("Processing Dynamic World coverage using optimized count-based approach...")
#     fc = quantify_dw_coverage_fc(BASIN_ASSET_ID, YEARS)
    
#     task = ee.batch.Export.table.toDrive(
#         collection=fc,
#         description='dynamic_world_coverage_count_EECU_7',
#         fileFormat='CSV',
#         folder='DynamicWorldExports',
#         fileNamePrefix='coverage_results_count_EECU_7',
#     )
#     task.start()
#     print("Export task started. Check the Earth Engine Tasks tab for progress.")

    #------------------> count method instead of mosaic method> EECU : 20214.6680 in 6 minutes
#################################################################################################
