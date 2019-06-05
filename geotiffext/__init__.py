import logging as log
import glob

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
