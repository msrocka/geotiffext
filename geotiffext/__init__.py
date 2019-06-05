import logging as log
import glob
import numbers

import numpy as np
from osgeo import gdal, ogr


def gextract(tif_path: str, data_folder: str):
    """
    We assume that all data use WGS 84 (= WGS 1984, = EPSG:4326) as reference
    coordinate system (which is the standard system for GeoJSON
    https://tools.ietf.org/html/rfc7946).
    """
    jdriver = ogr.GetDriverByName("GeoJSON")  # type: ogr.Driver
    tdriver = ogr.GetDriverByName("GTiff")  # type: ogr.Driver

    log.info("read raster data from %s", tif_path)
    data_raster = gdal.Open(tif_path)  # type: gdal.Dataset
    data_band = data_raster.GetRasterBand(1)  # type: gdal.Band
    data = data_band.ReadAsArray()

    # rows are the y-dimension: 90 <-> -90,
    # columns the x-dimension: -180 <-> 180
    ydim, xdim = data.shape

    for geo_json_path in glob.glob(data_folder + "/*.geo.json"):
        feature_raster = raster_from_geojson(geo_json_path, xdim, ydim)
        feature_band = feature_raster.GetRasterBand(1)  # type: gdal.Band
        val = compute_value(data, feature_band.ReadAsArray(), minval=0)
        print(val)


def raster_from_geojson(geojson_path: str, xdim: int, ydim: int) -> gdal.Dataset:
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


def compute_value(data_raster: np.ndarray, feature_raster: np.ndarray,
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


def extract(tif_path: str):
    data = gdal.Open(tif_path)  # type: gdal.Dataset
    band = data.GetRasterBand(1)  # type: gdal.Band
    print(band.GetMetadata())
    print(band.GetNoDataValue())
    print(band.GetMinimum(), " <= x <= ", band.GetMaximum())
    array = band.ReadAsArray()
    print(array.shape)


def rasterize():
    driver = ogr.GetDriverByName("GeoJSON")  # type: ogr.Driver
    data = driver.Open("./data/countries.geo.json")  # type: ogr.DataSource
    layer = data.GetLayer()  # type: ogr.Layer
    print(" found", layer.GetFeatureCount(), "features")

    tif_driver = gdal.GetDriverByName("GTiff")
    for feature in layer:  # type: ogr.Feature
        fid = feature.GetField("id")  # type: str
        if not isinstance(fid, str) or len(fid) == 0 or not fid[0].isalnum():
            continue
        tif_ds = tif_driver.Create("./data/" + fid + ".tif",
                                   4320, 2160, gdal.GDT_Byte)
        tif_ds.SetGeoTransform((-180, 0.083333, 0, 90, 0, -0.083333))
        print("  read feature ", feature.GetField("id"))
        band = tif_ds.GetRasterBand(1)
        band.SetNoDataValue(0)
        gdal.RasterizeLayer(tif_ds, [1], layer)
        break


if __name__ == "__main__":
    log.basicConfig(level=log.INFO)

    # extract("../data/Cropland2000_5m.tif")
    # rasterize()

    gextract("../data/Cropland2000_5m.tif", "../data")
