import sys
import random
#from hyper_resource_py import settings
import os

try:
    import mapnik
except:
    print ('***************************************************************************************************************************')
    print ('** The mapnik library and python bindings must have been compiled and \
installed successfully before running this script. **')
    print('** So it is not possible generate images                                                                                 **')
    print('** From image_generator>img_generator.py                                                                                 **')
    print ('***************************************************************************************************************************')
    #sys.exit(1)

STYLE_XML = 'image_generator/style.xml'

class IBuilderImage:
    spatialReference = {
        4326: "+init=epsg:4326",
        4674: "+proj=longlat +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +no_defs ",
        4618: "+proj=longlat +ellps=aust_SA +towgs84=-67.35,3.88,-38.22,0,0,0,0 +no_defs",
        9999: "+proj=lcc +ellps=GRS80 +lat_0=49 +lon_0=-95 +lat+1=49 +lat_2=77 +datum=NAD83 +units=m +no_defs"
    }

    def __init__(self, layer, bbox=0, srs=4326, width=800, height=600, length_name=16):
        #self.geometry = layer['geometry']
        #self.geojsonfile = layer['geojson']
        #self.table_name = layer['table_name']
        self.wkt = layer['wkt']
        if 'style' in layer:
            self.style = layer['style']
        else:
            self.style = STYLE_XML


        if 'type' in layer:
            self.geom_type = self._transform_to_basic_geom_type(layer['type'])
        else:
            self.geom_type = "polygon"

        self.deleteStyle = False
        if "deleteStyle" in layer:
            self.deleteStyle = layer['deleteStyle']

        self.bbox = bbox
        self.srs = srs
        self.width = width
        self.height = height
        self.imgType = None
        self.mapnikObj = mapnik.Map(width, height)
        self.mapnikImg = mapnik.Image(width, height)
        self.image_name = ''.join([random.choice('0123456789ABCDEF') for i in range(length_name)])

    def _transform_to_basic_geom_type(self, geom_type):
        basic_geom_type = "polygon"
        basic_geom_types = ['point', 'line', 'polygon']
        for b in basic_geom_types:
            if b.lower() in geom_type.lower():
                basic_geom_type = b
                break
        return basic_geom_type

    def generate(self):
        pass

#builderPNG, builderJpeg, builderTiff

class BuilderPNG(IBuilderImage):
    def __init__(self, layer, bbox=0, srs=4326, width=800, height=600):
        IBuilderImage.__init__(self, layer)
        self.imgType = "png"

    def generate(self):
        mapnik.load_map(self.mapnikObj, self.style)
        self.layer = mapnik.Layer('Provinces')
        self.layer.srs =self.spatialReference[self.srs]
        #sym = mapnik.PointSymbolizer("imgs/marker-icon.png", "png", 16, 16)
        self.layer.datasource = mapnik.CSV(inline='wkt\n"'+self.wkt+'"', filesize_max=500)

        # to use other datasources. The GeoJSON as datasource doesn't generate the image and we don't know why.
        #self.layer.datasource = mapnik.PostGIS(
        #    host=settings.DATABASES['default']['HOST'],
        #    user=settings.DATABASES['default']['USER'],
        #    password=settings.DATABASES['default']['PASSWORD'],
        #    dbname=settings.DATABASES['default']['NAME'],
        #    table=self.table_name)

        #self.layer.datasource = mapnik.GeoJSON(file=self.geojsonfile)
        #self.layer.datasource = mapnik.Shapefile(file=self.geometry, encoding='latin1')

        self.layer.styles.append(self.geom_type)
        self.mapnikObj.layers.append(self.layer)

        if self.bbox == 0:
            self.mapnikObj.zoom_all()

        # Render map
        mapnik.render(self.mapnikObj, self.mapnikImg)

        # Save image to files
        image_complete_name = self.image_name+'.'+self.imgType
        self.mapnikImg.save(image_complete_name, self.imgType)  # true-colour RGBA
        image_file = open(image_complete_name, 'rb')
        image_out = image_file.read()
        image_file.close()

        os.remove(image_complete_name)
        if self.deleteStyle:
            os.remove(self.style)

        return image_out