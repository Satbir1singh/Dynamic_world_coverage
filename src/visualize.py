import ee

ee.Initialize(project="ee-officialsatbir23")

roi = ee.FeatureCollection("projects/ee-officialsatbir23/assets/Rhone-20250531T062224Z-1-001").geometry()

start_date = '2021-01-01'
end_date = '2021-02-01'

# Dynamic World: Use mosaic to get best land cover coverage
dw = (
    ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1")
    .filterDate(start_date, end_date)
    .filterBounds(roi)
    .select("label")
)

dw_mosaic = dw.mosaic().clip(roi)

# Visualization parameters
dw_vis_params = {
    "min": 0,
    "max": 8,
    "palette": [
        "#419BDF",  # Water
        "#397D49",  # Trees
        "#88B053",  # Grass
        "#7A87C6",  # Flooded vegetation
        "#E49635",  # Crops
        "#DFC35A",  # Shrub and scrub
        "#C4281B",  # Built
        "#A59B8F",  # Bare
        "#B39FE1"   # Snow and ice
    ]
}

# Results function
def get_results():
    return {
        "ROI" : roi, 
        "classification": dw_mosaic.visualize(**dw_vis_params)
    }
