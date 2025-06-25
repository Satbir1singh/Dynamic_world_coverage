
import ee

# Constants
BASIN_ASSET_ID = "projects/ee-officialsatbir23/assets/Rhone-20250531T062224Z-1-001"
YEARS = list(range(2021, 2023))
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
    return ee.Number(result.values().get(0)).multiply(PIXEL_AREA_M2).divide(10_000)

def process_year_count_based(year):
    """Process a year using optimized count-based approach"""
    year = ee.Number(year)
    
    def create_monthly_feature(month):
        """Create feature for a single month"""
        month = ee.Number(month)
        start = ee.Date.fromYMD(year, month, 1)
        end = start.advance(1, 'month')
        
        monthly_count = dw_col.filterDate(start, end).select('label').count().rename('coverage')
        
        area_ha = compute_coverage_area(monthly_count, basin, SCALE)
        
        return ee.Feature(None, {
            'Period': ee.String(year.format()).cat('_').cat(month.format('%02d')),
            'Coverage_hectares': area_ha,
            'Coverage_percent': area_ha.divide(total_area_ha).multiply(100),
            'total_area': total_area_ha
        })
    
    # Process yearly data
    year_start = ee.Date.fromYMD(year, 1, 1)
    year_end = year_start.advance(1, 'year')
    
    yearly_count = dw_col.filterDate(year_start, year_end).select('label').count().rename('coverage')
    
    year_area_ha = compute_coverage_area(yearly_count, basin, SCALE)
    
    year_feature = ee.Feature(None, {
        'Period': ee.String(year.format()).cat('_total'),
        'Coverage_hectares': year_area_ha,
        'Coverage_percent': year_area_ha.divide(total_area_ha).multiply(100),
        'total_area': total_area_ha
    })
    
    # Process monthly features
    months = ee.List.sequence(1, 12)
    monthly_features = ee.FeatureCollection(months.map(create_monthly_feature))
    
    # Combine yearly and monthly features
    return ee.FeatureCollection([year_feature]).merge(monthly_features)

def quantify_dw_coverage_fc(basin_asset_id: str, years: list[int]) -> ee.FeatureCollection:
    """Process coverage analysis using server-side operations"""
    global basin, dw_col, total_area_ha
    
    # Initialize global variables
    basin = ee.FeatureCollection(basin_asset_id).geometry().simplify(100)
    
    # Filter collection by date range
    start_year = ee.Number(min(years))
    end_year = ee.Number(max(years) + 1)
    start_date = ee.Date.fromYMD(start_year, 1, 1)
    end_date = ee.Date.fromYMD(end_year, 1, 1)
    
    dw_col = ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1").filterBounds(basin)\
        .filterDate(start_date, end_date).select("label")
    
    # Calculate total area once
    total_area_ha = compute_coverage_area(
        ee.Image.constant(1).rename('coverage').clip(basin),basin,SCALE
    )
    
    # Process all years
    years_list = ee.List(years)
    features = years_list.map(process_year_count_based)
    
    return ee.FeatureCollection(features).flatten()

if __name__ == "__main__":
    print("Processing Dynamic World coverage analysis...")
    fc = quantify_dw_coverage_fc(BASIN_ASSET_ID, YEARS)
    
    task = ee.batch.Export.table.toDrive(
        collection=fc,
        description='dynamic_world_coverage_Rhone',
        fileFormat='CSV',
        folder='DynamicWorldExports',
        fileNamePrefix='coverage_results_Rhone'
    )
    task.start()
    print("Export task started. Check the Earth Engine Tasks tab for progress.")

#------------------> count : EECU : 5.2169 in 1 minute best till now 

