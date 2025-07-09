import ee
import datetime

ee.Initialize(project="ee-officialsatbir23")

CONSENSUS_SHP = "projects/ee-officialsatbir23/assets/dw_validation_tile-20250705T134654Z-1-001" 
CONSENSUS_TIF = "projects/ee-officialsatbir23/assets/dw_7p0867379523_4p8051119857_20181226_consensus" 

CONSENSUS_DATE = "2018-12-26"

DW_CLASSES = [
    "Water", "Trees", "Grass", "Flooded_vegetation", "Crops",
    "Shrub_and_scrub", "Built", "Bare", "Snow_and_ice"
]

consensus_fc = ee.FeatureCollection(CONSENSUS_SHP)
tile_geom = consensus_fc.geometry()

date_ee = ee.Date(CONSENSUS_DATE)
periods = {
    "month": date_ee.advance(-1, "month"),
    "6months": date_ee.advance(-6, "month"),
    "year": date_ee.advance(-1, "year")
}

def max_band_and_index(img):
    """Returns an image with two bands: max value and index of max band."""
    bands = img.bandNames()
    n = bands.size()
    # Stack band values into an array
    arr = img.toArray()
    # Find max value and its index
    maxval = arr.arrayReduce(ee.Reducer.max(), [0]).arrayGet([0])
    maxidx = arr.arrayArgmax().arrayGet([0])
    return img.expression(
        'float(idx)', {'idx': maxidx}
    ).rename('max_idx').addBands(
        img.expression('float(val)', {'val': maxval}).rename('max_val')
    )

def reduce_dw_collection(start, end, geom):
    dw = ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1") \
        .filterBounds(geom) \
        .filterDate(start, end) \
        .map(lambda img: img.clip(geom))
    prob_bands = [
        "water", "trees", "grass", "flooded_vegetation", "crops",
        "shrub_and_scrub", "built", "bare", "snow_and_ice"
    ]
    mean_img = dw.select(prob_bands).mean()
    median_img = dw.select(prob_bands).median()
    # Get max prob and index for mean and median
    mean_max = max_band_and_index(mean_img)
    median_max = max_band_and_index(median_img)
    # Mode of label band (most frequent class)
    mode_label = dw.select("label").reduce(ee.Reducer.mode()).toFloat()
    # Count of images per pixel
    count_img = dw.select("label").count().toFloat()
    result = mean_max.select('max_idx').rename('mean_max_idx').toFloat() \
        .addBands(mean_max.select('max_val').rename('mean_max_prob').toFloat()) \
        .addBands(median_max.select('max_idx').rename('median_max_idx').toFloat()) \
        .addBands(median_max.select('max_val').rename('median_max_prob').toFloat()) \
        .addBands(mode_label.rename("mode_label")) \
        .addBands(count_img.rename("count"))
    return result

results = {}
for period, start in periods.items():
    img = reduce_dw_collection(start, date_ee, tile_geom)
    results[period] = img

# --- EXPORT IMAGES TO DRIVE ---
for period, img in results.items():
    export_img = img.clip(tile_geom)
    task = ee.batch.Export.image.toDrive(
        image=export_img,
        description=f"DW_{period}_summary",
        folder="DW_validation_exports",
        fileNamePrefix=f"DW_{period}_summary",
        region=tile_geom,
        scale=10,
        maxPixels=1e13,
        crs='EPSG:32632'  # <-- Set the output projection here
    )
    task.start()
    print(f"Export started for {period} summary image.")