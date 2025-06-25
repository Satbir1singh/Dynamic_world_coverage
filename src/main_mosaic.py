
import ee

# Constants
BASIN_ASSET_ID = "projects/ee-officialsatbir23/assets/Area"
YEARS = list(range(2021, 2022))
SCALE = 10
PIXEL_AREA_M2 = 100
MAX_PIXELS = 1e13

ee.Initialize(project="ee-officialsatbir23")

def compute_covered_area(img: ee.Image, geom: ee.Geometry, scale: int) -> ee.Number:
    """Compute area of valid pixels in hectares"""
    result = img.reduceRegion(
        reducer=ee.Reducer.count(),
        geometry=geom,
        scale=scale,
        maxPixels=MAX_PIXELS,
        tileScale=16
    )
    values = result.values()
    pixel_count = ee.Algorithms.If(
        values.size().gt(0),
        values.get(0),
        ee.Number(0)
    )
    return ee.Number(pixel_count).multiply(PIXEL_AREA_M2).divide(10_000)

def process_year_optimized(year):
    """Process a year using monthly mosaics efficiently"""
    year = ee.Number(year)
    
    def create_monthly_mosaic(month):
        """Create mosaic for a single month"""
        month = ee.Number(month)
        start = ee.Date.fromYMD(year, month, 1)
        end = start.advance(1, 'month')
        
        return dw_col.filterDate(start, end).mosaic().selfMask().clip(basin)\
            .set('month', month).set('year', year)\
            .set('period', ee.String(year.format()).cat('_').cat(month.format('%02d')))

    # Create all monthly mosaics
    months = ee.List.sequence(1, 12)
    monthly_mosaics = ee.ImageCollection(months.map(create_monthly_mosaic))
    
    # Process monthly features
    def create_feature(img):
        area_ha = compute_covered_area(img, basin, SCALE)
        return ee.Feature(None, {
            'Period': img.get('period'),
            'Coverage_hectares': area_ha,
            'Coverage_percent': area_ha.divide(total_area_ha).multiply(100),
            'total_area': total_area_ha,
            'has_data': ee.Number(1)
        })
    
    monthly_features = monthly_mosaics.map(create_feature)
    
    # Create yearly mosaic and feature
    year_img = monthly_mosaics.mosaic()
    year_area_ha = compute_covered_area(year_img, basin, SCALE)
    year_feature = ee.Feature(None, {
        'Period': ee.String(year.format()).cat('_total'),
        'Coverage_hectares': year_area_ha,
        'Coverage_percent': year_area_ha.divide(total_area_ha).multiply(100),
        'total_area': total_area_ha,
        'has_data': monthly_mosaics.size().gt(0)
    })
    
    # Combine features using FeatureCollection operations
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
    
    dw_col = ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1").filterBounds(basin).filterDate(start_date, end_date).select("label")
    
    # Calculate total area once
    total_area_ha = compute_covered_area(
        ee.Image.constant(1).clip(basin),
        basin,
        SCALE
    )
    
    # Process all years using server-side map
    years_list = ee.List(years)
    features = years_list.map(process_year_optimized)
    
    return ee.FeatureCollection(features).flatten()

if __name__ == "__main__":
    print("Processing Dynamic World coverage for all years and months...")
    fc = quantify_dw_coverage_fc(BASIN_ASSET_ID, YEARS)
    
    task = ee.batch.Export.table.toDrive(
        collection=fc,
        description='dynamic_world_coverage_EECU_6',
        fileFormat='CSV',
        folder='DynamicWorldExports',
        fileNamePrefix='Varuna_coverage_EECU_6'
    )
    task.start()
    print("Export task started. Check the Earth Engine Tasks tab for progress.")

#----------------> used monthly mosaics to create yearly collection but its optimised a little > EECU :  60698.2695 >> 4 minutes