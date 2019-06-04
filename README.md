# geotiffext

https://github.com/johan/world.geo.json/tree/master/countries

https://pcjericks.github.io/py-gdalogr-cookbook/vector_layers.html

https://gdal.org/python/

## Usage
Setting up `geotiffext` on Windows:

```batch
rem get the project
git clone https://github.com/msrocka/geotiffext.git
cd geotiffext

rem create a virtual environment and activate it
python -m venv env
.\env\Scripts\activate.bat

rem install numpy
pip install numpy

rem download the GDAL wheel from
rem https://www.lfd.uci.edu/~gohlke/pythonlibs/#gdal
rem and install it
pip install C:\...\GDAL-2.4.1-cp37-cp37m-win_amd64.whl

```