import os
import pandas as pd
import ee

# Constants
BASIN_ASSET_ID = "projects/ee-officialsatbir23/assets/Rhone-20250531T062224Z-1-001"
YEARS = [2021, 2022]
SCALE = 10  # in meters
PIXEL_AREA_M2 = 100  # For 10m resolution, each pixel = 100 m²
MAX_PIXELS = 2_000_000_000
OUTPUT_PATH = os.path.join("..", "outputs", "coverage_results.csv")

# Initialize Earth Engine
ee.Initialize(project="ee-officialsatbir23")


def compute_covered_area(img: ee.Image, geom: ee.Geometry, scale: int) -> ee.Number:
    """
    Fast approximation of covered area in hectares using valid pixel count.
    Each valid pixel is assumed to be 100 m² (for 10m resolution).
    """
    valid_pixel_mask = img.mask().gt(0)
    pixel_count = valid_pixel_mask.reduceRegion(
        reducer=ee.Reducer.count(),
        geometry=geom,
        scale=scale,
        maxPixels=MAX_PIXELS,
        tileScale=4
    ).values().get(0)

    return ee.Number(pixel_count).multiply(PIXEL_AREA_M2).divide(10_000)  # m² to hectares


def quantify_dw_coverage(basin_asset_id: str, years: list[int]) -> list[dict]:
    basin = ee.FeatureCollection(basin_asset_id).geometry()
    dw_col = ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1").select("label")

    print("Calculating total basin area in hectares (this may take a while)...")
    total_area_ha = compute_covered_area(ee.Image.constant(1).clip(basin), basin, SCALE).getInfo()

    rows = []
    for year in years:
        year_start = ee.Date(f"{year}-01-01")
        year_end = year_start.advance(1, 'year')
        year_img = dw_col.filterDate(year_start, year_end).mosaic().clip(basin)

        year_area_ha = compute_covered_area(year_img, basin, SCALE).getInfo()
        rows.append({
            "Period": f"{year}_total",
            "Coverage_hectares": round(year_area_ha, 2),
            "Coverage_percent": round(100 * year_area_ha / total_area_ha, 2)
        })

        for m in range(1, 13):
            start = ee.Date(f"{year}-{m:02d}-01")
            end = start.advance(1, 'month')
            month_img = dw_col.filterDate(start, end).mosaic().clip(basin)

            month_area_ha = compute_covered_area(month_img, basin, SCALE).getInfo()
            rows.append({
                "Period": f"{year}_{m:02d}",
                "Coverage_hectares": round(month_area_ha, 2),
                "Coverage_percent": round(100 * month_area_ha / total_area_ha, 2)
            })

    return rows


# Driver
if __name__ == "__main__":
    print("Processing Dynamic World coverage …")
    results = quantify_dw_coverage(BASIN_ASSET_ID, YEARS)

    # Save to CSV
    df = pd.DataFrame(results)
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8")
    print(f"Results written to {OUTPUT_PATH}")


# ######################
# import os
# import pandas as pd
# import ee

# BASIN_ASSET_ID   = "projects/ee-officialsatbir23/assets/Rhone-20250531T062224Z-1-001"
# YEARS            = [2021, 2022]                       
# SCALE            = 10                                 
# MAX_PIXELS       = 2_000_000_000                      
# OUTPUT_PATH      = os.path.join("..", "outputs", "coverage_results.csv")


# ee.Initialize(project="ee-officialsatbir23")

# def count_pixels(img: ee.Image, geom: ee.Geometry, scale: int) -> ee.ComputedObject:
#     """
#     Returns an ee.Number with the pixel count of `img` inside `geom`
#     at the given `scale` (metres).
#     """
#     return img.reduceRegion(
#         reducer   = ee.Reducer.count(),
#         geometry  = geom,
#         scale     = scale,
#         maxPixels = MAX_PIXELS,   
#         tileScale = 4             
#     ).values().get(0)             


# # 4. Core function -------------------------------------------------------------
# def quantify_dw_coverage(basin_asset_id: str, years: list[int]) -> list[dict]:
#     basin  = ee.FeatureCollection(basin_asset_id).geometry()
#     dw_col = ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1").select("label")

#     print("Calculating total basin area (this may take a while)...")
#     basin_area_pixels = count_pixels(ee.Image.constant(1), basin, SCALE).getInfo()

#     rows = []
#     for year in years:
#         # Year mosaic
#         year_start = ee.Date(f"{year}-01-01")
#         year_end   = year_start.advance(1, 'year')
#         year_img   = dw_col.filterDate(year_start, year_end).mosaic().clip(basin)

#         # Year coverage
#         year_cov_px = count_pixels(year_img.mask(), basin, SCALE).getInfo()
#         rows.append({
#             "Period"           : f"{year}_total",
#             "Coverage_pixels"  : year_cov_px,
#             "Coverage_percent" : round(100 * year_cov_px / basin_area_pixels, 2)
#         })

#         # Monthly coverage
#         for m in range(1, 13):
#             start = ee.Date(f"{year}-{m:02d}-01")
#             end   = start.advance(1, 'month')
#             month_img = dw_col.filterDate(start, end).mosaic().clip(basin)
#             month_cov_px = count_pixels(month_img.mask(), basin, SCALE).getInfo()

#             rows.append({
#                 "Period"           : f"{year}_{m:02d}",
#                 "Coverage_pixels"  : month_cov_px,
#                 "Coverage_percent" : round(100 * month_cov_px / basin_area_pixels, 2)
#             })

#     return rows


# # 5. Driver --------------------------------------------------------------------
# if __name__ == "__main__":
#     print("🛰️  Processing Dynamic World coverage …")
#     results = quantify_dw_coverage(BASIN_ASSET_ID, YEARS)

#     # Save to CSV
#     df = pd.DataFrame(results)
#     os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
#     df.to_csv(OUTPUT_PATH, index=False)
#     print(f"✅ Results written to {OUTPUT_PATH}")
