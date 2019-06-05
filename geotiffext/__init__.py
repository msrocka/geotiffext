import csv
import glob
import logging as log
import numbers
import os

import numpy as np
from osgeo import gdal, ogr


def doit(tif_path: str, data_folder: str):
    """
    We assume that all data use WGS 84 (= WGS 1984, = EPSG:4326) as reference
    coordinate system (which is the standard system for GeoJSON
    https://tools.ietf.org/html/rfc7946).
    """
    log.info("read raster data from %s", tif_path)
    data_raster = gdal.Open(tif_path)  # type: gdal.Dataset
    data_band = data_raster.GetRasterBand(1)  # type: gdal.Band
    data = data_band.ReadAsArray()

    # rows are the y-dimension: 90 <-> -90,
    # columns the x-dimension: -180 <-> 180
    ydim, xdim = data.shape

    results = []
    for geo_json_path in glob.glob(data_folder + "/*.geo.json"):
        code = os.path.basename(geo_json_path)[:-9]
        log.info("next location %s", code)
        feature_raster = _map_geojson(geo_json_path, xdim, ydim)
        feature_band = feature_raster.GetRasterBand(1)  # type: gdal.Band
        val = _compute_value(data, feature_band.ReadAsArray(), minval=0)
        results.append((code, val))

    csv_path = data_folder + "/geotiffext_" + os.path.basename(tif_path) + ".csv"
    log.info("write extracted results to %s", csv_path)
    with open(csv_path, "w", encoding="utf-8", newline="\n") as f:
        writer = csv.writer(f)
        writer.writerow(["Location", "Value"])
        writer.writerows(results)


def _map_geojson(geojson_path: str, xdim: int, ydim: int) -> gdal.Dataset:
    log.info("rasterize GeoJSON file %s", geojson_path)

    # read the JSON layer
    jdriver = ogr.GetDriverByName("GeoJSON")  # type: ogr.Driver
    data = jdriver.Open(geojson_path)  # type: ogr.DataSource
    layer = data.GetLayer()  # type: ogr.Layer
    log.info("found layer with %i features", layer.GetFeatureCount())

    # create the raster
    tdriver = gdal.GetDriverByName("GTiff")
    raster = tdriver.Create(geojson_path + ".tif",
                            xdim, ydim, gdal.GDT_Byte)

    # describe the mapping of the polygon to the raster
    # https://gis.stackexchange.com/a/165966
    raster.SetGeoTransform((-180, 360 / xdim, 0, 90, 0, -180 / ydim))

    # finally, rasterize the layer
    band = raster.GetRasterBand(1)
    band.SetNoDataValue(0)
    gdal.RasterizeLayer(raster, [1], layer)
    return raster


def _compute_value(data_raster: np.ndarray, feature_raster: np.ndarray,
                   minval=None, maxval=None) -> float:
    # define the overlapping matrix
    xdim_d, ydim_d = data_raster.shape
    xdim_f, ydim_f = feature_raster.shape
    if xdim_d != xdim_f or ydim_d != ydim_f:
        log.warning("the matrices have different dimensions: %i*%i vs %i*%i",
                    xdim_d, ydim_d, xdim_f, ydim_f)
    xdim = min(xdim_d, xdim_f)
    ydim = min(ydim_d, ydim_f)

    total = 0.0
    pixels = 0
    for x in range(0, xdim):
        for y in range(0, ydim):
            if feature_raster[x, y] == 0:
                continue
            val = data_raster[x, y]
            if not isinstance(val, numbers.Number):
                continue
            if minval is not None and val < minval:
                continue
            if maxval is not None and val > maxval:
                continue
            total += val
            pixels += 1

    if pixels == 0:
        log.warning("found no pixels with values")
        return 0

    result = total / pixels
    log.info("calculated an average value of %f from %i pixels", result, pixels)
    return result


if __name__ == "__main__":
    log.basicConfig(level=log.INFO)

    # extract("../data/Cropland2000_5m.tif")
    # rasterize()

    doit("../data/Cropland2000_5m.tif", "../data")
