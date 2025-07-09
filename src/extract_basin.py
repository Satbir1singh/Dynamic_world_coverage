import ee

# Constants
HYBAS_IDS = ["4050886350","4050838850","4050769470","4050786650","4051065250","4050607420","4050911950","4050769230","4050709990","4050607260","4050786190","4050709980","4050028550","4050051120","4050053490","4050031740","4050031750","4050026830","4050028560","4050900680"]  # <-- Add your list of HYBAS_IDs here
ASSET_PATH = "WWF/HydroSHEDS/v1/Basins/hybas_5"
YEARS = list(range(2021, 2022))
SCALE = 10
PIXEL_AREA_M2 = 100
MAX_PIXELS = 1e13

ee.Initialize(project="ee-officialsatbir23")

def compute_coverage_area(count_img: ee.Image, geom: ee.Geometry, scale: int) -> ee.Number:
    """Compute area of covered pixels in hectares, robust to empty images."""
    count_img = ee.Image(
        ee.Algorithms.If(
            count_img.bandNames().size().gt(0),
            count_img,
            ee.Image.constant(0).rename('coverage')
        )
    )
    # binary_mask = count_img.gt(0)
    # area_image = binary_mask.multiply(ee.Image.pixelArea())
    # result = area_image.reduceRegion(
    #     reducer=ee.Reducer.sum(),
    #     geometry=geom,
    #     scale=scale,
    #     maxPixels=MAX_PIXELS,
    #     tileScale=16
    # )
    # area_m2 = ee.Number(result.values().get(0))
    # return area_m2.divide(10_000)
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
    year = ee.Number(year)
    def create_monthly_feature(month):
        month = ee.Number(month)
        start = ee.Date.fromYMD(year, month, 1)
        end = start.advance(1, 'month')
        monthly_count = dw_col.filterDate(start, end).select('label').count().rename('coverage')
        area_ha = compute_coverage_area(monthly_count, basin_geom, SCALE)
        return ee.Feature(None, {
            'HYBAS_ID': current_hybas_id,
            'Period': ee.String(year.format()).cat('_').cat(month.format('%02d')),
            'Coverage_hectares': area_ha,
            'Coverage_percent': area_ha.divide(total_area_ha).multiply(100),
            'total_area': total_area_ha
        })
    months = ee.List.sequence(1, 12)
    monthly_features = ee.FeatureCollection(months.map(create_monthly_feature))
    yearly_count = dw_col.filterDate(
        ee.Date.fromYMD(year, 1, 1),
        ee.Date.fromYMD(year, 1, 1).advance(1, 'year')
    ).select('label').count().rename('coverage')
    year_area_ha = compute_coverage_area(yearly_count, basin_geom, SCALE)
    year_feature = ee.Feature(None, {
        'HYBAS_ID': current_hybas_id,
        'Period': ee.String(year.format()).cat('_total'),
        'Coverage_hectares': year_area_ha,
        'Coverage_percent': year_area_ha.divide(total_area_ha).multiply(100),
        'total_area': total_area_ha
    })
    return ee.FeatureCollection([year_feature]).merge(monthly_features)

def get_single_basin(hybas_id: str) -> ee.Feature:
    hydrobasins = ee.FeatureCollection(ASSET_PATH)
    basin_collection = hydrobasins.filter(ee.Filter.eq('HYBAS_ID', ee.Number.parse(hybas_id)))
    basin = basin_collection.first()
    return basin

def analyze_basin_coverage(basin_feature: ee.Feature, years: list[int], hybas_id: str) -> ee.FeatureCollection:
    global basin_geom, dw_col, total_area_ha, current_hybas_id
    current_hybas_id = hybas_id  # Set global for use in features
    basin_geom = basin_feature.geometry()
    start_date = ee.Date.fromYMD(min(years), 1, 1)
    end_date = ee.Date.fromYMD(max(years) + 1, 1, 1)
    dw_col = ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1")\
        .filterBounds(basin_geom)\
        .filterDate(start_date, end_date)\
        .select("label")
    total_area_ha = compute_coverage_area(
        ee.Image.constant(1).rename('coverage').clip(basin_geom),
        basin_geom,
        SCALE
    )
    features = ee.List(years).map(process_year_count_based)
    return ee.FeatureCollection(features).flatten()

if __name__ == "__main__":
    for hybas_id in HYBAS_IDS:
        print(f"Extracting basin with HYBAS_ID: {hybas_id}")
        basin = get_single_basin(hybas_id)
        if basin.getInfo() is None:
            print(f"Warning: No basin found with HYBAS_ID: {hybas_id}")
            continue
        print("Processing Dynamic World coverage analysis...")
        fc = analyze_basin_coverage(basin, YEARS, hybas_id)
        task = ee.batch.Export.table.toDrive(
            collection=fc,
            description=f'DW_coverage_HYBAS_{hybas_id}',
            fileFormat='CSV',
            folder='DynamicWorldExports_france_all',
            fileNamePrefix=f'coverage_HYBAS_{hybas_id}'
        )
        task.start()
        print(f"Export task started for HYBAS_ID: {hybas_id}. Check the Earth Engine Tasks tab for progress.")

