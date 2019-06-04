from osgeo import gdal, ogr


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
    extract("./data/Cropland2000_5m.tif")
    # rasterize()
