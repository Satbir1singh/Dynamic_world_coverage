import ee

# Constants
HYBAS_ID = "2050022150"  
ASSET_PATH = "WWF/HydroSHEDS/v1/Basins/hybas_5" 
YEARS = list(range(2021, 2022))
SCALE = 10
PIXEL_AREA_M2 = 100
MAX_PIXELS = 1e13

ee.Initialize(project="ee-officialsatbir23")

def compute_coverage_area(count_img: ee.Image, geom: ee.Geometry, scale: int) -> ee.Number:
    """Compute area of covered pixels in hectares"""
    result = count_img.gt(0).reduceRegion(
        reducer=ee.Reducer.sum(),
        geometry=geom,
        scale=scale,
        maxPixels=MAX_PIXELS,
        tileScale=16
    )
    # print(result.values())  # Debugging output
    return ee.Number(result.values().get(0)).multiply(PIXEL_AREA_M2).divide(10000)

def process_year_count_based(year):
    """Process a year using optimized count-based approach"""
    year = ee.Number(year)
    
    def create_monthly_feature(month):
        """Create feature for a single month"""
        month = ee.Number(month)
        start = ee.Date.fromYMD(year, month, 1)
        end = start.advance(1, 'month')
        
        monthly_count = dw_col.filterDate(start, end)\
            .select('label')\
            .count()\
            .rename('coverage')
        
        area_ha = compute_coverage_area(monthly_count, basin_geom, SCALE)
        
        return ee.Feature(None, {
            'HYBAS_ID': HYBAS_ID,
            'Period': ee.String(year.format()).cat('_').cat(month.format('%02d')),
            'Coverage_hectares': area_ha,
            'Coverage_percent': area_ha.divide(total_area_ha).multiply(100),
            'total_area': total_area_ha
        })
    
    # Process monthly features
    months = ee.List.sequence(1, 12)
    monthly_features = ee.FeatureCollection(months.map(create_monthly_feature))
    
    # Process yearly data
    yearly_count = dw_col.filterDate(
        ee.Date.fromYMD(year, 1, 1),
        ee.Date.fromYMD(year, 1, 1).advance(1, 'year')
    ).select('label').count().rename('coverage')
    
    year_area_ha = compute_coverage_area(yearly_count, basin_geom, SCALE)
    year_feature = ee.Feature(None, {
        'HYBAS_ID': HYBAS_ID,
        'Period': ee.String(year.format()).cat('_total'),
        'Coverage_hectares': year_area_ha,
        'Coverage_percent': year_area_ha.divide(total_area_ha).multiply(100),
        'total_area': total_area_ha
    })
    
    return ee.FeatureCollection([year_feature]).merge(monthly_features)

def get_single_basin(hybas_id: str) -> ee.Feature:
    """Extract a single basin by its HYBAS_ID with error handling"""
    hydrobasins = ee.FeatureCollection(ASSET_PATH)
    basin_collection = hydrobasins.filter(ee.Filter.eq('HYBAS_ID', ee.Number.parse(hybas_id)))
    
    # Check if basin exists
    basin = basin_collection.first()
    return basin

def analyze_basin_coverage(basin_feature: ee.Feature, years: list[int]) -> ee.FeatureCollection:
    """Process coverage analysis for a single basin"""
    global basin_geom, dw_col, total_area_ha
    
    # Initialize variables
    basin_geom = basin_feature.geometry()
    
    # Filter Dynamic World collection
    start_date = ee.Date.fromYMD(min(years), 1, 1)
    end_date = ee.Date.fromYMD(max(years) + 1, 1, 1)
    
    dw_col = ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1")\
        .filterBounds(basin_geom)\
        .filterDate(start_date, end_date)\
        .select("label")
    
    # Calculate total area
    total_area_ha = compute_coverage_area(
        ee.Image.constant(1).rename('coverage').clip(basin_geom),
        basin_geom,
        SCALE
    )
    
    # Process all years
    features = ee.List(years).map(process_year_count_based)
    return ee.FeatureCollection(features).flatten()

if __name__ == "__main__":
    print(f"Extracting basin with HYBAS_ID: {HYBAS_ID}")
    basin = get_single_basin(HYBAS_ID)
    
    print("Processing Dynamic World coverage analysis...")
    fc = analyze_basin_coverage(basin, YEARS)
    
    task = ee.batch.Export.table.toDrive(
        collection=fc,
        description=f'DW_coverage_HYBAS_{HYBAS_ID}',
        fileFormat='CSV',
        folder='DynamicWorldExports_france_all',
        fileNamePrefix=f'coverage_HYBAS_{HYBAS_ID}'
    )
    task.start()
    
    print("Export task started. Check the Earth Engine Tasks tab for progress.")