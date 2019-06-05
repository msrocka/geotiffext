# geotiffext
`geotiffext` extracts and averages data from a
[GeoTIFF](https://en.wikipedia.org/wiki/GeoTIFF) file for a set of regions
defined in [GeoJSON](https://en.wikipedia.org/wiki/GeoJSON) files. For this, it
takes a GeoTIFF file and a folder of GeoJSON files (with a `*.geo.json` file
extension) as input and produces a CSV file that contains the average data
for the respective regions.

Each GeoJSON file is handled as a single region. The feature layer of this
region is then mapped to a raster (producing a GeoTIFF file next to the
GeoJSON file; using the [GDAL API](https://gdal.org/python/)) and the
intersecting data are averaged. The file name (without the `*.geo.json`
extension) is used as location name in the resulting CSV file.

You can find a Github repository with
[GeoJSON files for countries here](https://github.com/johan/world.geo.json).
Also [this tool is great](https://geojson-maps.ash.ms/) to produce GeoJSON files
for custom regions.


## Usage
Assuming you have Python >= 3.6 installed, you can install `geotiffext`
in a Python virtual environment with the following steps (for Windows):

```batch
rem get the project via git (or just download it)
git clone https://github.com/msrocka/geotiffext.git
cd geotiffext

rem create a virtual environment and activate it
python -m venv env
.\env\Scripts\activate.bat

rem install numpy
pip install numpy

rem download the GDAL wheel from
rem https://www.lfd.uci.edu/~gohlke/pythonlibs/#gdal
rem and install it (check that you select the version
rem that matches your Python interpreter
pip install C:\...\GDAL-2.4.1-cp37-cp37m-win_amd64.whl

rem finally, install geotiffext
pip install -e .

rem and start the Python interpreter
py
```

`geotiffext` writes its logs to the standard logger. To see more details you
can set the level to info:

```python
import logging
logging.basicConfig(level=logging.INFO)
```

Finally, you call the `geotiffext.doit` function with a path to a GeoTiff file
and a filder with GeoJSON files:

```python
import geotiffext
geotiffext.doit("path/to/data_file.tif", 
                "path/to/folder/with/.geo.json/files",
                minval=0.0)
```

It is highly recommended to pass the minimum value of the expected value range
into the function to avoid the inclusion of no-data values from the data file.
 