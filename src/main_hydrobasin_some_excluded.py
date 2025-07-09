import ee
import random

# Constants
AREA_ASSET = "projects/ee-officialsatbir23/assets/China"
YEARS = list(range(2021, 2022)) 
SCALE = 10
PIXEL_AREA_M2 = 100
MAX_PIXELS = 1e13

# Read HYBAS_IDs to exclude from file
with open("hybas_ids.txt") as f:
    EXCLUDE_HYBAS_IDS = [line.strip() for line in f if line.strip()]

ee.Initialize(project="ee-officialsatbir23")

def compute_coverage_area(count_img: ee.Image, geom: ee.Geometry, scale: int) -> ee.Number:
    """Compute area of covered pixels using count thresholding"""

    count_img = ee.Image(
        ee.Algorithms.If(
            count_img.bandNames().size().gt(0),
            count_img,
            ee.Image.constant(0).rename('coverage')
        )
    )
    result = count_img.gt(0).reduceRegion(
        reducer=ee.Reducer.sum(),
        geometry=geom,
        scale=scale,
        maxPixels=MAX_PIXELS,
        tileScale=16
    )
    return ee.Number(result.values().get(0)).multiply(PIXEL_AREA_M2).divide(10_000)

def process_year_count_based(basin, year):
    """Process a single year for a given basin"""
    year = ee.Number(year)
    basin_geom = basin.geometry()
    
    # Filter collection for this basin and year
    dw_col = ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1").filterBounds(basin_geom).filterDate(ee.Date.fromYMD(year, 1, 1), 
                   ee.Date.fromYMD(year.add(1), 1, 1)).select("label")
    
    # Calculate total area once
    total_area_ha = compute_coverage_area(
        ee.Image.constant(1).rename('coverage').clip(basin_geom),basin_geom,SCALE
    )
    
    def create_monthly_feature(month):
        """Create feature for a single month"""
        month = ee.Number(month)
        start = ee.Date.fromYMD(year, month, 1)
        end = start.advance(1, 'month')
        
        monthly_count = dw_col.filterDate(start, end).select('label').count().rename('coverage')
        
        area_ha = compute_coverage_area(monthly_count, basin_geom, SCALE)
        
        return ee.Feature(None, {
            'HYBAS_ID': basin.get('HYBAS_ID'),
            'Period': ee.String(year.format()).cat('_').cat(month.format('%02d')),
            'Coverage_hectares': area_ha,
            'Coverage_percent': area_ha.divide(total_area_ha).multiply(100),
            'total_area': total_area_ha
        })
    
    # Process monthly data
    months = ee.List.sequence(1, 12)
    monthly_features = ee.FeatureCollection(months.map(create_monthly_feature))
    
    # Process yearly data
    yearly_count = dw_col.select('label').count().rename('coverage')
    year_area_ha = compute_coverage_area(yearly_count, basin_geom, SCALE)
    
    year_feature = ee.Feature(None, {
        'HYBAS_ID': basin.get('HYBAS_ID'),
        'Period': ee.String(year.format()).cat('_total'),
        'Coverage_hectares': year_area_ha,
        'Coverage_percent': year_area_ha.divide(total_area_ha).multiply(100),
        'total_area': total_area_ha
    })
    
    return ee.FeatureCollection([year_feature]).merge(monthly_features)

def analyze_basin(basin):
    """Analyze all years for a single basin"""
    return ee.FeatureCollection(
        ee.List(YEARS).map(lambda y: process_year_count_based(basin, y))
    ).flatten()

def start_export(basin):
    """Configure and start export for a single basin using pure server-side operations"""
    basin_results = analyze_basin(basin)
    hybas_id = basin.get('HYBAS_ID').getInfo()  

    task = ee.batch.Export.table.toDrive(
        collection=basin_results,
        description=f'DW_coverage_HYBAS_{hybas_id}',  
        fileFormat='CSV',
        folder='DynamicWorldExports_china_all',
        fileNamePrefix=f'coverage_HYBAS_{hybas_id}'   
    )
    
    return task

if __name__ == "__main__":
    hydrobasins = ee.FeatureCollection("WWF/HydroSHEDS/v1/Basins/hybas_5")
    china_geom = ee.FeatureCollection(AREA_ASSET).geometry()
    fr_basins = hydrobasins.filterBounds(china_geom)

    exclude_ids_num = [int(i) for i in EXCLUDE_HYBAS_IDS]
    filtered_basins = fr_basins.filter(
        ee.Filter.inList('HYBAS_ID', exclude_ids_num).Not()
    )
    
    # Get list of remaining basins and shuffle for randomness
    basin_list = filtered_basins.toList(filtered_basins.size())
    n_basins = basin_list.size().getInfo()
    n_select = n_basins // 2 if n_basins > 1 else 1

    # Get random indices
    indices = list(range(n_basins))
    random.shuffle(indices)
    selected_indices = indices[:n_select]

    # Process only the randomly selected basins
    for idx in selected_indices:
        basin = ee.Feature(basin_list.get(idx))
        hybas_id = basin.get('HYBAS_ID').getInfo()
        print(f"Started export task for HYBAS_ID: {hybas_id}")
        task = start_export(basin)
        task.start()
    print("All export tasks started for randomly selected basins. Check the Earth Engine Tasks tab for progress.")
    