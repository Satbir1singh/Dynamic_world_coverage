import ee
import random
# find country code for country of interest from 
COUNTRY_ADM0_CODE = 204
YEARS = list(range(2021, 2022))
SCALE = 10
PIXEL_AREA_M2 = 100
MAX_PIXELS = 1e13

# Read HYBAS_IDs to exclude from file
with open("hybas_ids.txt") as f:
    EXCLUDE_HYBAS_IDS = [line.strip() for line in f if line.strip()]

ee.Initialize(project="ee-officialsatbir23")

def compute_coverage_area(count_img: ee.Image, geom: ee.Geometry, scale: int) -> ee.Number:
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
    year = ee.Number(year)
    basin_geom = basin.geometry()
    dw_col = ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1").filterBounds(basin_geom).filterDate(
        ee.Date.fromYMD(year, 1, 1), ee.Date.fromYMD(year.add(1), 1, 1)).select("label")
    total_area_ha = compute_coverage_area(
        ee.Image.constant(1).rename('coverage').clip(basin_geom), basin_geom, SCALE
    )
    def create_monthly_feature(month):
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
    months = ee.List.sequence(1, 12)
    monthly_features = ee.FeatureCollection(months.map(create_monthly_feature))
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
    return ee.FeatureCollection(
        ee.List(YEARS).map(lambda y: process_year_count_based(basin, y))
    ).flatten()

def start_export(basin):
    basin_results = analyze_basin(basin)
    hybas_id = basin.get('HYBAS_ID').getInfo()
    task = ee.batch.Export.table.toDrive(
        collection=basin_results,
        description=f'DW_coverage_HYBAS_{hybas_id}',
        fileFormat='CSV',
        folder='DynamicWorldExports_country',
        fileNamePrefix=f'coverage_HYBAS_{hybas_id}'
    )
    return task

if __name__ == "__main__":
    # Load GAUL countries and filter by ADM0_CODE
    countries = ee.FeatureCollection("FAO/GAUL/2015/level0")
    country = countries.filter(ee.Filter.eq('ADM0_CODE', COUNTRY_ADM0_CODE))
    country_geom = country.geometry()

    # Filter HydroBASINS to country
    hydrobasins = ee.FeatureCollection("WWF/HydroSHEDS/v1/Basins/hybas_5")
    country_basins = hydrobasins.filterBounds(country_geom)

    # Exclude basins by HYBAS_ID
    exclude_ids_num = [int(i) for i in EXCLUDE_HYBAS_IDS]
    filtered_basins = country_basins.filter(
        ee.Filter.inList('HYBAS_ID', exclude_ids_num).Not()
    )

    # Get list of remaining basins and randomly select 20%
    basin_list = filtered_basins.toList(filtered_basins.size())
    n_basins = basin_list.size().getInfo()
    n_select = max(1, int(n_basins * 0.2))

    indices = list(range(n_basins))
    random.shuffle(indices)
    selected_indices = indices[:n_select]

    for idx in selected_indices:
        basin = ee.Feature(basin_list.get(idx))
        hybas_id = basin.get('HYBAS_ID').getInfo()
        print(f"Started export task for HYBAS_ID: {hybas_id}")
        task = start_export(basin)
        task.start()
    print("All export tasks started for randomly selected basins. Check the Earth Engine Tasks tab for progress.")