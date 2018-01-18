import base64
import importlib
import inspect
import json
from datetime import date, datetime, time

import jwt
import requests
import sys
from django.contrib.gis.db import models
from django.contrib.gis.db.models import Q
# Create your models here.
from django.contrib.gis.db.models import GeometryField
from django.contrib.gis.gdal import OGRGeometry
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.geos import GeometryCollection
from django.contrib.gis.geos import LineString
from django.contrib.gis.geos import MultiLineString
from django.contrib.gis.geos import MultiPoint
from django.contrib.gis.geos import MultiPolygon
from django.contrib.gis.geos import Point
from django.contrib.gis.geos import Polygon
from django.contrib.gis.geos.prepared import PreparedGeometry

from django.contrib.gis.db.models import GeometryField
from django.contrib.gis.db.models import LineStringField
from django.contrib.gis.db.models import MultiLineStringField
from django.contrib.gis.db.models import MultiPointField
from django.contrib.gis.db.models import MultiPolygonField
from django.contrib.gis.db.models import PointField
from django.contrib.gis.db.models import PolygonField
from django.contrib.gis.db.models import ForeignKey
from requests import ConnectionError
from requests import HTTPError

#from university.settings import DEFAULT_CACHE_VALID_TIME, init_cache
#init_cache()

import sys
if sys.version_info > (3,):
    buffer = memoryview

def dict_map_geo_field_geometry():
    """
    Retorna um dicionário onde cada chave é um
    tipo geométrico e seu respectivo valor é um
    modelo geométrico
    :return:
    """
    dic = {}
    dic[GeometryField] = GEOSGeometry
    dic[LineStringField] = LineString
    dic[MultiLineStringField] = MultiLineString
    dic[MultiPointField] = MultiPoint
    dic[MultiPolygonField] = MultiPolygon
    dic[PointField] = Point
    dic[PolygonField] = Polygon
    return dic

class Type_Called():
    """
    Type_Called é uma definição de tipo que contém nome
    (name), uma lista de parâmetros (parameters) e um
    tipo de resposta (answer)
    """
    def __init__(self, a_name='', params=[], answer=None):
        self.name = a_name
        self.parameters = params
        self.return_type = answer

class ConverterType():

    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(ConverterType, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def value_has_url(self, value_str):
        return (value_str.find('http:') > -1) or (value_str.find('https:') > -1) or (value_str.find('www.') > -1)

    def make_geometrycollection_from_featurecollection(self, feature_collection):
        geoms = []
        #features = json.loads(feature_collection)
        gc = GeometryCollection()
        for feature in feature_collection['features']:
            feature_geom = json.dumps(feature['geometry'])
            geos_geom = (GEOSGeometry(feature_geom))
            gc.append(geos_geom)
        return gc


    def get_geos_geometry_from_request(self, url_as_str):
        resp = requests.get(url_as_str)
        if 400 <= resp.status_code <= 599:
            raise HTTPError({resp.status_code: resp.reason})
        if resp.headers['content-type'] == 'application/octet-stream':
            return GEOSGeometry(buffer(resp.content))

        elif resp.headers['content-type'] in ['application/json', 'application/geojson', 'application/vnd.geo+json']:
            js = resp.json()
            if (js.get("type") and js["type"].lower()=='feature'):
                return GEOSGeometry(json.dumps(js["geometry"]))

            elif  (js.get("type") and js["type"].lower()=='featurecollection'):
                return self.make_geometrycollection_from_featurecollection(js)

            else:
                return GEOSGeometry(json.dumps(js))

        return GEOSGeometry(resp.content)
    def convert_to_string(self, value_as_str):
        """
        Recebe um valor e retorna sua representação em string
        :param value_as_str:
        :return:
        """
        return str(value_as_str)

    def convert_to_int(self, value_as_str):
        """
        Recebe um valor e retorna sua representação em int
        :param value_as_str:
        :return:
        """
        return int(value_as_str)

    def convert_to_float(self, value_as_str):
        """
        Recebe um valor e retorna sua representação em float
        :param value_as_str:
        :return:
        """
        return float(value_as_str)

    def convert_to_date(self, value_as_str):
        """
        Recebe um valor e retorna sua representação em date
        :param value_as_str:
        :return:
        """
        return datetime.strptime(value_as_str, "%Y-%m-%d").date()

    def convert_to_datetime(self, value_as_str):
        """
        Recebe um valor e retorna sua representação em datetime
        :param value_as_str:
        :return:
        """
        return datetime.strptime(value_as_str, "%Y-%m-%d %H:%M:%S")

    def convert_to_time(self, value_as_str):
        """
        Recebe um valor e retorna sua representação em time
        :param value_as_str:
        :return:
        """
        return datetime.time.strptime(value_as_str, "%Y-%m-%d %H:%M:%S")

    def convert_to_geometry(self, value_as_str):
        try:
            if self.value_has_url(value_as_str):
               return self.get_geos_geometry_from_request(value_as_str)

            return GEOSGeometry(value_as_str)
        except (ValueError, ConnectionError, HTTPError) as err:
            print('Error: '.format(err))


    def operation_to_convert_value(self, a_type):
        """
        Retorna um dos dicionário listados abaixo
        de acordo com o tipo 'a_type' passado como
        parâmetro. Cada índice deste dicionário
        corresponde a uma função
        :param a_type:
        :return:
        """
        d = {}
        d[str] = self.convert_to_string
        d[int] = self.convert_to_int
        d[float] = self.convert_to_float
        d[date] = self.convert_to_date
        d[datetime] = self.convert_to_datetime
        d[time] = self.convert_to_time
        d[models.CharField] = self.convert_to_string
        d[models.TextField] = self.convert_to_string
        d[models.IntegerField] = self.convert_to_int
        d[models.AutoField] = self.convert_to_int
        d[models.FloatField] = self.convert_to_float
        d[models.TimeField] = self.convert_to_time
        d[models.DateTimeField] = self.convert_to_datetime
        d[models.DateField] = self.convert_to_date
        d[GeometryField] = self.convert_to_geometry
        d[PolygonField] = self.convert_to_geometry
        d[LineStringField] = self.convert_to_geometry
        d[PointField] = self.convert_to_geometry
        d[MultiPolygonField] = self.convert_to_geometry
        d[MultiLineString] = self.convert_to_geometry
        d[MultiPointField] = self.convert_to_geometry
        d[ForeignKey] = self.convert_to_int


        return d[a_type]

    def value_converted(self, a_type, value):
        """
        Paga o valor (value) recebido como argumento
        e submete a função do dicionário de funções
        correspondente a uma determinada classe (a_type).
        Depois da submissão, o valor resultante é retornado
        :param a_type:
        :param value:
        :return:
        """
        # ConverterType.operation_to_convert_value() retorna um dicionário
        # correspondente ao tipo passado como parâmetro
        # cada índice deste dicionário contém uma função
        # logo, object_method é uma função de 'a_type'
        object_method = self.operation_to_convert_value(a_type)
        return object_method(value)

    def convert_parameters(self, a_type, attribute_or_function_name, parameters):
        """
        Retorna uma lista de valores oriundos da lista de parâmetros
        representadas por 'parameters' submetida à função representada
        por 'attribute_or_function_name' do conjunto de funções referentes
        a classe 'a_type'. Caso 'a_type' não esteja no conjunto de operações
        espaciais ou primitivas, apenas retornamos a lista de parâmetros
        recebida como argumento
        :param a_type:
        :param attribute_or_function_name:
        :param parameters:
        :return:
        """
        # se o tipo do objeto enviado é algum dos índices
        # do dicionário de operações espaciais ou primitivas .
        if a_type in OperationController().dict_all_operation_dict():
            # ... recuperamos apenas o dicionário que contém as operações para este tipo
            operation_dict = OperationController().dict_all_operation_dict()[a_type]

            # se o nome do atributo ou da função esta
            # entre o conjunto de operações para este tipo ...
            if attribute_or_function_name in operation_dict:
                # ... recuperamos apenas a operação (Type_Called) específica cujo
                # 'attribute_or_function_name' é índice
                type_called = operation_dict[attribute_or_function_name]
                # IMPORTANTE: 'param' será cada item da lista do Type_Called retornado acima,
                # paramters[i] é a lista de parâmetros recebida por esta função
                # logo, a cada iteração, estamos enviando um parâmetro do Type_Called
                # (na verdade, seu valor) e um parâmetro da lista recebida correspondente
                # para a função ConverterType.value_converted()
                # RESUMINDO: o comando abaixo retorna uma lista de valores
                # resultantes do acionamento da função especificada por 'param'
                # enviando como parâmetro da função acionada o valor 'parameters[i]'
                return [ConverterType().value_converted(param, parameters[i]) for i, param in enumerate(type_called.parameters) ]

        # se o tipo de objeto não corresponder a algum dos índices
        # do dicionário de operações espaciais ou primeitivas, retornamos
        # apenas a lista de parametros
        return parameters

class QObjectFactory:

    def __init__(self, model_class, attribute_name, operation_or_operator, raw_value_as_str):
        self.model_class = model_class
        self.attribute_name = attribute_name
        self.operation_or_operator = operation_or_operator
        self.raw_value_as_str = raw_value_as_str

    def fields(self):
        return self.model_class._meta.fields

    def field_type(self):
        for field in self.fields():
            if field.name == self.attribute_name:
                return type(field)
        return None

    def convert_value_for(self, a_value):
        converter = ConverterType()
        field_type = self.field_type()
        if field_type is None:
            return None
        if isinstance(a_value, bool):
            return a_value
        if (a_value.lower() == 'false' or a_value.lower() == 'true') and self.operation_or_operator == 'isnull':
            return  False if a_value.lower() == 'false' else True

        return converter.value_converted(self.field_type(), a_value)


    def q_object_base_range(self, oper_operation):
        dc = {}
        arr_value = self.raw_value_as_str.split('&')
        arr_value_converted = [ self.convert_value_for(a_value) for a_value in arr_value]
        dc[self.attribute_name + '__' + oper_operation] = arr_value_converted
        return Q(**dc)

    def q_object_for_in(self):
        return self.q_object_base_range('in')

    def q_object_for_between(self):
        return self.q_object_base_range('range')

    def q_object_for_eq(self):
        dc = {}
        dc[self.attribute_name] = self.convert_value_for(self.raw_value_as_str)
        return Q(**dc)

    def q_object_for_neq(self):
        dc = {}
        dc[self.attribute_name] = self.convert_value_for(self.raw_value_as_str)
        return ~Q(**dc)

    def q_object_for_spatial_operation(self):
        dc = {}
        value_conveted = self.convert_value_for(self.raw_value_as_str)
        dc[self.attribute_name + '__' + self.operation_or_operator] = value_conveted
        return Q(**dc)

    def q_object_operation_or_operator_in_dict(self):
        d = {}
        d['in'] = self.q_object_for_in
        d['eq'] = self.q_object_for_eq
        d['neq'] = self.q_object_for_neq
        d['between'] = self.q_object_for_between
        d['*in'] = self.q_object_for_in
        d['*eq'] = self.q_object_for_eq
        d['*neq'] = self.q_object_for_neq
        d['*between'] = self.q_object_for_between

        return d.get(self.operation_or_operator, self.q_object_for_spatial_operation)

    def q_object(self):
        object_method = self.q_object_operation_or_operator_in_dict()
        return object_method()

class FactoryComplexQuery:
    _instance = None
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(FactoryComplexQuery, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def fields(self, model_class):
        return model_class._meta.fields

    def field_names(self, mode_class):
        return [field.name for field in self.fields(mode_class)]

    def base_operators(self):
        return ['neq', 'eq','lt','lte','gt','gte','between','isnull','isnotnull', 'like','notlike','in','notin',
        '*neq', '*eq','*lt','*lte','*gt','*gte','*between','*isnull','isnotnull','*like','*notlike','*in','*notin']

    def logical_operators(self):
        return ['or', 'and', '*or', '*and']

    def is_attribute(self, att_name, model_class):
        return att_name in self.field_names(model_class)

    def is_logical_operator(self, op):
       return op.lower() in self.logical_operators()


    def q_object_with_logical_operator(self, q_object_expression_or_none, q_object, logical_operator_str):
        if q_object_expression_or_none is None:
            return q_object
        exp = (q_object_expression_or_none & q_object) if logical_operator_str.lower() in ['and', '*and'] else (q_object_expression_or_none | q_object)
        return exp

    def q_object_for_filter_expression(self, q_object_or_none, model_class, expression_as_array):
        #'sigla/in/rj,es,go/and/data/between/2017-02-01,2017-06-30/' = ['sigla','in','rj,es,go','and','data', 'between','2017-02-01,2017-06-30']
        if '' in expression_as_array:
            expression_as_array.remove('')

        if len(expression_as_array)  == 2 and expression_as_array[1].lower() in ['isnull', 'isnotnull']:
            boolean = expression_as_array[1].lower() == 'isnull'
            expression_as_array[1] = 'isnull'
            expression_as_array.append(boolean)

        if len(expression_as_array)  < 3:
            return q_object_or_none
        oper = expression_as_array[0]
        if self.is_logical_operator(oper):
           expression_as_array = expression_as_array[1:]

        if self.is_attribute(expression_as_array[0], model_class):
            qof = QObjectFactory(model_class, expression_as_array[0], expression_as_array[1], expression_as_array[2])
            #oper = qof.operation_or_operator
        else:
            if len(expression_as_array) > 3:
                qof = QObjectFactory(model_class, expression_as_array[1], expression_as_array[2], expression_as_array[3])
            else:
                qof = QObjectFactory(model_class, expression_as_array[0], expression_as_array[1],
                                     expression_as_array[2])
            oper = expression_as_array[0]

        q_object_expression = self.q_object_with_logical_operator(q_object_or_none, qof.q_object(), oper)

        return self.q_object_for_filter_expression(q_object_expression, model_class, expression_as_array[3:])

    def q_object_for_spatial_expression(self, q_object_or_none, model_class, expression_as_array):
        #'geom/within/Polygon(10,10, 30, 30, 40, 40 , 10 10)/and/data/between/2017-02-01,2017-06-30/' = ['sigla','in','rj,es,go','and','data', 'between','2017-02-01,2017-06-30']
        if len(expression_as_array)  < 3:
            return q_object_or_none

        if self.is_attribute(expression_as_array[0], model_class):
            qof = QObjectFactory(model_class, expression_as_array[0], expression_as_array[1], expression_as_array[2])
            oper = qof.operation_or_operator
        else:
            qof = QObjectFactory(model_class, expression_as_array[1], expression_as_array[2], expression_as_array[3])
            oper = expression_as_array[0]

        q_object_expression = self.q_object_with_logical_operator(q_object_or_none, qof.q_object(), oper)

        return self.q_object_for_filter_expression(q_object_expression, model_class, expression_as_array[3:])

class OperationController:

    _instance = None
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(OperationController, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def geometry_operations_dict(self):
        # - 'dic' será um dicionário com todas as operações geoespaciais
        # - cada índice de 'dic' é uma referência para um Type_Called
        # - cada Type_Called recebe um nome uma lista de parâmetros e um tipo de retorno
        dic = {}
        if len(dic) == 0:
            dic['area'] = Type_Called('area', [], float)
            dic['boundary'] = Type_Called('boundary', [], float)
            dic['buffer'] = Type_Called('buffer', [float], GEOSGeometry)
            dic['centroid'] = Type_Called('centroid', [], Point)
            dic['contains'] = Type_Called('contains', [GEOSGeometry], bool)
            dic['convex_hull'] = Type_Called('convex_hull', [], Polygon)
            dic['coord_seq'] = Type_Called('coord_seq', [], tuple)
            dic['coords'] = Type_Called('coords', [], tuple)
            dic['count'] = Type_Called('count', [], int)
            dic['crosses'] = Type_Called('crosses', [GEOSGeometry], bool)
            from django.contrib.gis.gdal import SpatialReference

            dic['crs'] = Type_Called('crs', [], SpatialReference)
            dic['difference'] = Type_Called('difference', [GEOSGeometry], GEOSGeometry)
            dic['dims'] = Type_Called('dims', [], int)
            dic['disjoint'] = Type_Called('disjoint', [GEOSGeometry], bool)
            dic['distance'] = Type_Called('distance', [GEOSGeometry], float)
            dic['empty'] = Type_Called('empty', [], bool)
            dic['envelope'] = Type_Called('envelope', [], GEOSGeometry)
            dic['equals'] = Type_Called('equals', [GEOSGeometry], bool)
            dic['equals_exact'] = Type_Called('equals_exact', [GEOSGeometry, float], bool)
            dic['ewkb'] = Type_Called('ewkb', [], str)
            dic['ewkt'] = Type_Called('ewkt', [], str)
            dic['extend'] = Type_Called('extend', [], tuple)
            dic['extent'] = Type_Called('extent', [], tuple)
            dic['geojson'] = Type_Called('geojson', [], str)
            dic['geom_type'] = Type_Called('geom_type', [], str)
            dic['geom_typeid'] = Type_Called('geom_typeid', [], int)
            dic['get_coords'] = Type_Called('get_coords', [], tuple)
            dic['get_srid'] = Type_Called('get_srid', [], str)
            dic['get_x'] = Type_Called('get_x', [], str)
            dic['get_y'] = Type_Called('get_y', [], str)
            dic['get_z'] = Type_Called('get_z', [], str)
            dic['has_cs'] = Type_Called('has_cs', [], bool)
            dic['hasz'] = Type_Called('hasz', [], bool)
            dic['hex'] = Type_Called('hex', [], str)
            dic['hexewkb'] = Type_Called('hexewkb', [], str)
            dic['index'] = Type_Called('index', [], int)
            dic['intersection'] = Type_Called('intersection', [GEOSGeometry], GEOSGeometry)
            dic['intersects'] = Type_Called('intersects', [GEOSGeometry], bool)
            dic['interpolate'] = Type_Called('interpolate', [float], Point)
            dic['json'] = Type_Called('json', [], str)
            dic['kml'] = Type_Called('kml', [], str)
            dic['length'] = Type_Called('length', [], float)
            dic['normalize'] = Type_Called('normalize', [float], Point)
            dic['num_coords'] = Type_Called('num_coords', [], int)
            dic['num_geom'] = Type_Called('num_geom', [], int)
            dic['num_points'] = Type_Called('num_points', [], int)
            dic['ogr'] = Type_Called('ogr', [], OGRGeometry)
            dic['overlaps'] = Type_Called('overlaps', [GEOSGeometry], bool)
            dic['point_on_surface'] = Type_Called('point_on_surface', [], Point)
            # dic['pop'] = Type_Called('pop', [], tuple)
            # dic['prepared'] = Type_Called('prepared', [], PreparedGeometry)
            dic['relate'] = Type_Called('relate', [GEOSGeometry], str)
            dic['relate_pattern'] = Type_Called('relate_pattern', [GEOSGeometry, str], str)
            dic['ring'] = Type_Called('ring', [], bool)
            dic['set_coords'] = Type_Called('set_coords', [tuple], None)
            dic['set_srid'] = Type_Called('set_srid', [str], None)
            dic['set_x'] = Type_Called('set_x', [float], None)
            dic['set_y'] = Type_Called('set_y', [float], None)
            dic['set_z'] = Type_Called('set_z', [float], None)
            dic['simple'] = Type_Called('simple', [], bool)
            dic['simplify'] = Type_Called('simplify', [float, bool], GEOSGeometry)
            dic['srid'] = Type_Called('srid', [], int)
            dic['srs'] = Type_Called('srs', [], SpatialReference)
            dic['sym_difference'] = Type_Called('sym_difference', [GEOSGeometry], GEOSGeometry)
            dic['touches'] = Type_Called('touches', [GEOSGeometry], bool)
            dic['transform'] = Type_Called('transform', [int, bool], GEOSGeometry)
            # dic['tuple'] = Type_Called('tuple', [], tuple)
            dic['union'] = Type_Called('union', [GEOSGeometry], GEOSGeometry)
            dic['valid'] = Type_Called('valid', [GEOSGeometry], bool)
            dic['valid_reason'] = Type_Called('valid_reason', [GEOSGeometry], str)
            dic['within'] = Type_Called('within', [GEOSGeometry], bool)
            dic['wkb'] = Type_Called('wkb', [], str)
            dic['wkt'] = Type_Called('wkt', [], str)
            dic['x'] = Type_Called('x', [], float)
            dic['y'] = Type_Called('y', [], float)
            dic['z'] = Type_Called('z', [], float)
            return dic

    def point_operations_dict(self):
        dicti = self.geometry_operations_dict()
        return dicti

    def line_operations_dict(self):
        dicti = self.geometry_operations_dict()
        return dicti

    def polygon_operations_dict(self):
        dicti = self.geometry_operations_dict()
        return dicti

    def boolean_operations_dict(self):
        d = {}
        return d

    def int_operations_dict(self):
        d = {}
        return d

    def float_operations_dict(self):
        d = {}
        return d

    def date_operations_dict(self):
        d = {}
        return d

    def unicode_operations_dict(self):
        return self.string_operations_dict()

    def string_operations_dict(self):
        d = {}
        d['capitalize'] = Type_Called('capitalize', [], str)
        d['center'] = Type_Called('center', [int, str], str)
        d['count'] = Type_Called('count', [str], str)
        d['endswith'] = Type_Called('endswith', [str], bool)
        d['find'] = Type_Called('find', [str], int)
        d['index'] = Type_Called('index', [str], int)
        d['isdigit'] = Type_Called('isdigit', [str], int)
        d['isalnum'] = Type_Called('isalnum', [], bool)
        d['isalpha'] = Type_Called('isalpha', [], bool)
        d['islower'] = Type_Called('islower', [], bool)
        d['isupper'] = Type_Called('isupper', [], bool)
        d['lower'] = Type_Called('lower', [], str)
        d['join'] = Type_Called('join', [[str]], bool)
        d['startswith'] = Type_Called('startswith', [str], bool)
        d['split'] = Type_Called('split', [str], [str])
        d['upper'] = Type_Called('upper', [], str)
        return d

    def collection_operations_dict(self):
        dic = {}
        dic['filter'] = Type_Called('filter', [Q], object)
        dic['map'] = Type_Called('map', [Q], object)
        dic['annotate'] = Type_Called('annotate', [Q], object)
        return dic

    def spatial_collection_operations_dict(self):
        d = self.collection_operations_dict()
        d['bbcontains'] = Type_Called('bbcontains', [GEOSGeometry], bool)
        d['bboverlaps'] = Type_Called('bbcontains', [GEOSGeometry], bool)
        d['contained']  = Type_Called('contained', [GEOSGeometry], bool)
        d['contains']  = Type_Called('contains', [GEOSGeometry], bool)
        d['contains_properly'] = Type_Called('contains_properly', [GEOSGeometry], bool)
        d['coveredby'] = Type_Called('coveredby', [GEOSGeometry], bool)
        d['covers']= Type_Called('covers', [GEOSGeometry], bool)
        d['crosses'] = Type_Called('crosses', [GEOSGeometry], bool)
        d['disjoint']= Type_Called('disjoint', [GEOSGeometry], bool)
        d['equals'] = Type_Called('equals', [GEOSGeometry], bool)
        d['exact'] = Type_Called('exact', [GEOSGeometry], bool)
        d['same_as'] = Type_Called('same_as', [GEOSGeometry], bool)
        d['intersects']  = Type_Called('intersects', [GEOSGeometry], bool)
        d['isvalid']  = Type_Called('isvalid', [GEOSGeometry], bool)
        d['overlaps'] = Type_Called('overlaps', [GEOSGeometry], bool)
        d['relate'] = Type_Called('relate', [tuple], bool)
        d['touches'] = Type_Called('touches', [GEOSGeometry], bool)
        d['within'] = Type_Called('within', [GEOSGeometry], bool)
        d['left'] = Type_Called('left', [GEOSGeometry], bool)
        d['right'] = Type_Called('right', [GEOSGeometry], bool)
        d['overlaps_left']  = Type_Called('overlaps_left', [GEOSGeometry], bool)
        d['overlaps_right'] = Type_Called('overlaps_right', [GEOSGeometry], bool)
        d['overlaps_above'] = Type_Called('overlaps_above', [GEOSGeometry], bool)
        d['overlaps_below'] = Type_Called('overlaps_below', [GEOSGeometry], bool)
        d['strictly_above'] = Type_Called('strictly_above', [GEOSGeometry], bool)
        d['strictly_below'] = Type_Called('strictly_below', [GEOSGeometry], bool)
        d['distance_gt'] = Type_Called('distance_gt', [GEOSGeometry], bool)
        d['distance_gte'] = Type_Called('distance_gte', [GEOSGeometry], bool)
        d['distance_lt'] = Type_Called('distance_lt', [GEOSGeometry], bool)
        d['distance_lte'] = Type_Called('distance_lte', [GEOSGeometry], bool)
        d['dwithin'] = Type_Called('dwithin', [GEOSGeometry], bool)

        return d

    def feature_collection_operations_dict(self):

        return dict(self.collection_operations_dict(), **self.spatial_collection_operations_dict())

    def dict_by_type_geometry_operations_dict(self):
        """
        Retorna um dicionário onde as chaves são
        representadas por tipos geométricos e seus
        respectivos valores são outros dicionários
        contendo operações para este tipo
        :return:
        """
        dicti = {}
        # self.geometry_operation_dict() retorna um dicionário com todas as operações geoespaciais
        # logo o índice GEOSGeometry do dicionário 'dicti' contém outro dicionário de operações
        dicti[GEOSGeometry] = self.geometry_operations_dict()

        # EXEMPLO DE ESTRUTURA DE 'dicti'
        # dicti({
        #    GEOSGeometry: {
        #        'area' :       Type_Called('area', [], float),
        #        'boundary' :   Type_Called('boundary', [], float),
        #        'buffer' :     Type_Called('buffer', [float], GEOSGeometry),
        #        ...
        #    },
        #
        #    Point: {
        #        'area':        Type_Called('area', [], float),
        #        'boundary':    Type_Called('boundary', [], float),
        #        'buffer':      Type_Called('buffer', [float], GEOSGeometry),
        #        ...
        #    }
        #    ...
        # })

        dicti[Point] = self.point_operations_dict()
        dicti[Polygon] = self.polygon_operations_dict()
        dicti[LineString] = self.line_operations_dict()
        dicti[MultiPoint] = self.point_operations_dict()
        dicti[MultiPolygon] = self.polygon_operations_dict()
        dicti[MultiLineString] = self.line_operations_dict()
        dicti[GeometryCollection] = self.geometry_operations_dict()

        # todos os índices acima acabam apontando para o conteúdo advindo
        # de 'geometry_operations_dict()' direta ou indiretamente

        # o retorno será semelhante a do exemplo acima
        return dicti

    def dict_by_type_primitive_operations_dict(self):
        """
        Retorna um dicionário com operações para tipos simples
        :return:
        """
        d = {}
        d[int]= self.int_operations_dict()
        d[float]= self.float_operations_dict()
        d[date]= self.date_operations_dict()
        d[str]= self.string_operations_dict()

        return d

    def dict_all_operation_dict(self):
        """
        Retorna todas as operações para recursos simple
        e operações para recursos gométricos
        :return:
        """
        d =  self.dict_by_type_geometry_operations_dict()
        d.update(self.dict_by_type_primitive_operations_dict())
        return d

    def is_operation(self, an_object, name):
        """
        Define se 'name' representa uma operação
        de 'an_object'
        :param an_object:
        :param name:
        :return:
        """
        # verifica se o objeto passado é um BusinessModel
        if isinstance(an_object, BusinessModel):
            # se for, verifica se 'name' representa uma operação/método de 'an_object'
            return an_object.is_operation(name)#return hasattr(an_object, name) and callable(getattr(an_object, name))
        # se não for instância de BusinessModel armazena o tipo do objeto em 'a_type'
        a_type = type(an_object)
        # se 'a_type' não for um índice de dicionário de dicionários
        # de operações
        if a_type not in self.dict_all_operation_dict():
            # ... retorna False, ou seja, não é uma operação
            return False
        # se 'a_type' é uma das operações (geoespeciais ou não)
        # esta pode estar entre o conjunto de todas as operações
        # lembrando que este conjunto trata-se de um dicionário de dicionários
        # neste caso 'a_type' é um índice do dicionário e o valor deste ínice
        # é outro dicionário que contém o nome (como chave) e o valor
        # (a própria operação)
        operation_dict = self.dict_all_operation_dict()[a_type]
        # retorna True se o nome da operação passado ('name')
        # esta entre representa algum índice dentro do dicionário
        # representado pelo tipo de 'an_object' (a_type)
        return name in operation_dict

    def operation_has_parameters(self, an_object, att_or_method_name):
        """
        Define se a opereração 'att_or_method_name' de 'an_object'
        possui parâmetros
        :param an_object:
        :param att_or_method_name:
        :return:
        """
        # verifica se o objeto passado é um BusinessModel
        if isinstance(an_object, BusinessModel):
            # retorna True se a operação/método possuir algum parâmetro além de 'self'
            return an_object.operation_has_parameters(att_or_method_name)
        a_type=type(an_object)
        # se o tipo do objeto (neste caso, não é BusinessModel)
        # não representa um índice do dicionário de operações (geométricas e primitivas)
        # então retorna False
        if a_type not in self.dict_all_operation_dict():
            return False
        # se o if anterior for False, significa que o tipo do
        # objeto representa um índice do dicionário de operações
        operation_dict = self.dict_all_operation_dict()[a_type]
        if att_or_method_name in operation_dict:
            # - 'att_or_method_name' é um índice do dicionário cujo valor
            # é uma instância de Type_Called
            # 'type_called' possui 'parameters' que é uma lista de parâmetros
            type_called = operation_dict[att_or_method_name]
            # se a lista de parâmetros de type_called não estiver vazia retorna True
            return len(type_called.parameters) > 0
        # nos demais casos, retornamos False
        return False

class BusinessModel(models.Model):

    def id(self):
        """
        Retorna o valor da primary key
        do objeto BusinessModel
        :return:
        """
        return self.pk

    def name_string(self):
        """
        Retorna a representação de string
        do objeto BusinessModel
        :return:
        """
        return self.__str__()

    def attribute_primary_ley(self):
        """
        Retorna o nome do identificador do
        objeto BusinessModel através de seu
        serializer
        :return:
        """
        return self.serializer_class.Meta.identifier

    def model_class(self):
        """
        Retorna o tipo do objeto de modelo
        :return:
        """
        return type(self)

    def _key_is_identifier(self, key):
        """
        Retorna True se 'key' estiver na
        lista de identificadores do modelo
        :param key:
        :return:
        """
        return key in self.serializer_class.Meta.identifiers

    def dic_with_only_identitier_field(self, dict_params):
        """
        'dict_params' é um dicionário com todos os atributos
        do modelo. O retorno é um dicionário oriundo deste
        apenas com os atributos identificadores e seus
        respectivos valores
        :param dict_params:
        :return:
        """
        dic = dict_params.copy()
        a_dict = {}
        for key, value in dic.items():
            if self._key_is_identifier(key):
                a_dict[key] = value
        return a_dict

    def all_operation_name_and_value(self):
        # - self é um objeto de BusinessModel
        # - inspect.getmembers retorna todos os membros (nome e valor) ç
        # de um dado objeto, no caso 'self'ç
        # - o método inspect.ismethod, passado como segundo argumento,
        # retorna true se um dado argumento for um método
        # - ou seja, all_operation_name_and_value() retornará uma lista
        # de métodos referente ao objeto 'self'
        # retorna todos os membros do objeto 'self' que são métodos
        return inspect.getmembers(self, inspect.ismethod)

    def all_operation_name_and_args_length(self):
        # - self.all_operation_name_and_values retorna uma lista com
        # os nomes e métodos do objeto BusinessModel
        # - retorna uma lista de tuplas onde o primeiro elemento da
        # tupla é o nome do método e o segundo elemento é o número
        # de argumentos deste método
        return [(name, len( inspect.getargspec(method).args)) for name, method in self.all_operation_name_and_value()]

    def public_operations_name_and_value(self):
        return [(name, value) for name, value in self.all_operation_name_and_value() if not name.startwith('_')]

    def operation_names(self):
        # self.all_operation_name_and_value() retornará uma lista de métodos
        # neste caso, a compreesão de lista abaixo dará origem a uma lista apenas
        # com os nome dos métodos
        return [ name for name, value in self.all_operation_name_and_value() ]

    def public_operation_names(self):
        return [ name for name, value in self.public_operations_name_and_value() ]

    def operation_has_parameters(self, att_or_method_name):
        # - self.all_operation_name_and_args_length() retorna
        # uma lista de tuplas nesse formato (nome_metodo, num_argumentos)
        # - next() foi usado, neste caso, porque o primeiro argumento de qualquer
        # método em python é 'self', o que não interessa neste caso
        # - o segundo parâmetro de next() é False, que é retornado, caso a lista seja
        # percorrida e nenhum valor True esteja nela
        # - len_args > 1 também foi usado pelo mesmo motivo, pois todo método
        # tem pelo menos 1 argumento (self)
        # - resumindo: se 'att_or_method_name' corresponder a algum elemento da lista
        # de métodos do objeto BusinessModel (self) e este método tiver pelo menos 1
        # parâmetro além de 'self' o retorno é True
        return next((True for name, len_args in self.all_operation_name_and_args_length() if name == att_or_method_name and len_args > 1), False)

    def attribute_names(self):
        # - dir() retorna uma lista de atributos do objeto
        # - getattr() retorna o valor do atributo (o nome do
        # atributo é o segundo parâmetro) do objeto (primeiro parâmetro)
        # - se o atributo não for privado E o valor do atributo não for
        # chamável (um método ou uma classe) adicionamos na nova lista
        # uma lista de atributos não privados e de valores não chamáveis é retornado
        return [ attribute for attribute in dir(self) if not callable(getattr(self, attribute)) and self.is_not_private(attribute)]

    def fields(self):
        """
        Retorna uma lista de campos da classe de modelo,
        no caso retornará uma lista de BusinessModel
        :return:
        """
        return self.model_class()._meta.fields

    def field_names(self):
        return [field.name for field in self.fields()]

    def is_private(self, attribute_or_method_name):
        # atributos ou métodos iniciados por '__' e terminados por '__'
        # são privados, se este for o caso, esté método retorna True
        return attribute_or_method_name.startswith('__') and attribute_or_method_name.endswith('__')

    def is_not_private(self, attribute_or_method_name):
        return not self.is_private(attribute_or_method_name)

    def is_operation(self, operation_name):
        # retona True se o nome da operação esta entre as operações do modelo
        return operation_name in self.operation_names()

    def is_public_operations(self, operation_name):
        return operation_name in self.public_operation_names()

    def is_attribute(self, attribute_name):
        # return attribute_name in self.field_names()
        # - getattr() retorna o valor do atributo 'attribute_name' do objeto self
        # - dir() retorna uma lista de atributos de self
        # - logo, este método retorna uma lista dos atributos de 'self'
        # que não são chamáveis
        return (attribute_name in dir(self) and not callable(getattr(self, attribute_name)))

    def operations_with_parameters_type(self):
        return {}

    def serializer_class(self, a_model_class_name):
        return self.class_for_name('serializers', a_model_class_name + 'Serializer')

    def class_for_name(self, module_name, class_name):
        # load the module, will raise ImportError if module cannot be loaded
        m = importlib.import_module(module_name)
        # get the class, will raise AttributeError if class cannot be found
        c = getattr(m, class_name)
        return c


    class Meta:
        abstract = True

class FeatureModel(BusinessModel):

    # geometry_object é uma instância de GEOSGeometry
    geometry_object = None

    class Meta:
        abstract = True

    def geo_field(self):
        """
        Retorna o primeiro campo do objeto FeaturaModel
        que for do tipo GeometryField
        :return:
        """
        # - self.fields() é o conjunto de campos de FeatureModel
        # - neste caso, estamos pegando todos os campos de FeatureModel
        # que são instâncias da classe GeometryField e retornando o prieiro
        # elemeto deste subconjunto
        return [field for field in self.fields() if isinstance(field, GeometryField)][0]

    def geo_field_name(self):
        """
        Retorna o nome do primeiro campo
        GeometryField do objeto FeatureModel
        :return:
        """
        return self.geo_field().name

    def get_geometry_object(self):
        """
        Retorna FeatureModel.geometry_object.
        Caso este seja None, atribuimos o valor
        do primeiro atributo geométrico (GeometryField)
        do objeto FeatureModel a FeatureModel.geometry_object
        e depois retornamos ele
        :return:
        """
        if self.geometry_object == None:
            # se FeatureModel.geometry_object for None
            # atribuimos o valor do primeiro atributo
            # geométrico (GeometryField) do objeto FeatureModel
            # ou None caso este não exista
            self.geometry_object = getattr(self, self.geo_field_name(), None)

        # caso FeatureModel.geometry_object não seja nulo
        # retornamos este
        return self.geometry_object

    def _get_type_geometry_object(self):
        """
        Retorna o tipo do objeto geométrico ou None
        caso self.get_geometry_object() retorne None
        :return:
        """
        # FeatureModel.get_geometry_object() retorna
        # self.geometry_object relacionado ao objeto
        # FeatureModel (o padrâo é None)
        geo_object = self.get_geometry_object()
        if geo_object is None:
            return None
        return type(geo_object)

    def get_geometry_type(self):
        # FeatureModel._get__type_geometry_object() retorna o tipo do objeto geométrico
        geoType = self._get_type_geometry_object()
        # se geoType não for nulo retorna ele, se for nulo retorna um modelo geométrico
        return geoType if geoType is not None else dict_map_geo_field_geometry()[type(self.geo_field())]

    def operations_with_parameters_type(self):
        """
        Retorna um dicionário com operaões para
        o tipo geométrico < ... >
        :return:
        """
        oc = OperationController()
        # OperationController.dict_by_type_geometry_operations_dict()
        # é um dicionário onde suas chaves são tipos geométricos e seu
        # respectivo valor é outro dicionário com operações geométricas
        # para este tipo
        # self.get_geometry_type() retorna um tipo geométrico que será
        # o índice do dicionário.
        return oc.dict_by_type_geometry_operations_dict()[self.get_geometry_type()]

    def centroid(self):
        return self.get_geometry_object().centroid

    def ring(self):
        return self.get_geometry_object().ring

    def crs(self):
        return self.get_geometry_object().crs

    def wkt(self):
        return self.get_geometry_object().wkt

    def srs(self):
        return self.get_geometry_object().srs

    def hexewkb(self):
        return self.get_geometry_object().hexewkb

    def equals_exact(self, other_GEOSGeometry, tolerance=0):
        return self.get_geometry_object().equals_exact(other_GEOSGeometry, tolerance)

    def set_srid(self, a_srid):
        return self.get_geometry_object().set_srid(a_srid)

    def hex(self):
        return self.get_geometry_object().hex

    def has_cs(self):
        return self.get_geometry_object().has_cs

    def area(self):
        return self.get_geometry_object().area

    def extend(self):
        return self.get_geometry_object().extend

    def wkb(self):
        return self.get_geometry_object().wkb

    def geojson(self):
        return self.get_geometry_object().geojson

    def relate(self, other_GEOSGeometry, pattern):
        return self.get_geometry_object().relate(other_GEOSGeometry, pattern)

    def set_coords(self, coords):
        return self.get_geometry_object().set_coords(coords)

    def simple(self):
        return self.get_geometry_object().simple

    def simplify(self):
        return self.get_geometry_object().simplify


    def geom_type(self):
        return self.get_geometry_object().geom_type

    def set_y(self, y):
        return self.get_geometry_object().set_y(y)

    def normalize(self):
        return self.get_geometry_object().normalize

    def sym_difference(self, other_GEOSGeometry):
        return self.get_geometry_object().sym_difference(other_GEOSGeometry)

    def valid_reason(self):
        return self.get_geometry_object().valid_reason

    def geom_typeid(self):
        return self.get_geometry_object().geom_typeid

    def valid(self):
        return self.get_geometry_object().valid

    def ogr(self):
        return self.get_geometry_object().ogr

    def coords(self):
        return self.get_geometry_object().coords

    def num_coords(self):
        return self.get_geometry_object().num_coords

    def get_srid(self):
        return self.get_geometry_object().get_srid

    def distance(self, other_GEOSGeometry):
        return self.get_geometry_object().distance(other_GEOSGeometry)

    def json(self):
        return self.get_geometry_object().json

    def pop(self):
        return self.get_geometry_object().pop

    def ewkb(self):
        return self.get_geometry_object().ewkb

    def x(self):
        return self.get_geometry_object().x

    def simplify(self, tolerance=0.0, preserve_topology=False):
        return self.get_geometry_object().simplify(tolerance=0.0, preserve_topology=False)

    def set_z(self):
        return self.get_geometry_object().set_z

    def buffer(self, width, quadsegs=8):
        return self.get_geometry_object().buffer(width, quadsegs)

    def relate_pattern(self, other_GEOSGeometry, pattern):
        return self.get_geometry_object().relate_pattern(other_GEOSGeometry, pattern)

    def z(self):
        return self.get_geometry_object().z

    def num_geom(self):
        return self.get_geometry_object().num_geom

    def coord_seq(self):
        return self.get_geometry_object().coord_seq

    def dims(self):
        return self.get_geometry_object().dims

    def get_y(self):
        return self.get_geometry_object().get_y

    def tuple(self):
        return self.get_geometry_object().tuple

    def y(self):
        return self.get_geometry_object().y

    def convex_hull(self):
        return self.get_geometry_object().convex_hull

    def get_x(self):
        return self.get_geometry_object().get_x

    def index(self):
        return self.get_geometry_object().index

    def boundary(self):
        return self.get_geometry_object().boundary

    def kml(self):
        return self.get_geometry_object().kml

    def touches(self, other_GEOSGeometry):
        return self.get_geometry_object().touches(other_GEOSGeometry)

    def empty(self):
        return self.get_geometry_object().empty

    def srid(self):
        return self.get_geometry_object().srid

    def get_z(self):
        return self.get_geometry_object().get_z

    def extent(self):
        return self.get_geometry_object().extent

    def union(self, other_GEOSGeometry):
        return self.get_geometry_object().union(other_GEOSGeometry)

    def intersects(self, other_GEOSGeometry):
        return self.get_geometry_object().intersect(other_GEOSGeometry)

    def contains(self, other_GEOSGeometry):
        return self.get_geometry_object().contains(other_GEOSGeometry)

    def hasz(self):
        return self.get_geometry_object().hasz

    def crosses(self, other_GEOSGeometry):
        return self.get_geometry_object().crosses(other_GEOSGeometry)

    def count(self):
        return self.get_geometry_object().count

    def num_points(self):
        return self.get_geometry_object().num_points

    def within(self, other_GEOSGeometry):
        return self.get_geometry_object().within(other_GEOSGeometry)

    def intersection(self, other_GEOSGeometry):
        return self.get_geometry_object().intersection(other_GEOSGeometry)

    def overlaps(self, other_GEOSGeometry):
        return self.get_geometry_object().overlaps(other_GEOSGeometry)

    def equals(self, other_GeosGeometry):
        return self.get_geometry_object().equals(other_GeosGeometry)

    def point_on_surface(self):
        return self.get_geometry_object().point_on_surface

    def difference(self, other_GEOSGeometry):
        return self.get_geometry_object().difference(other_GEOSGeometry)

    def transform(self, srid, clone=True):
        return self.get_geometry_object().transform(srid, clone=True)

    def set_x(self, x):
        return self.get_geometry_object().set_x(x)

    def get_coords(self):
        return self.get_geometry_object().get_coords

    def envelope(self):
        return self.get_geometry_object().envelope

    def prepared(self):
        return self.get_geometry_object().prepared

    def ewkt(self):
        return self.get_geometry_object().ewkt

    def length(self):
        return self.get_geometry_object().length

    def disjoint(self, other_GEOSGeometry):
        return self.get_geometry_object().disjoint(other_GEOSGeometry)
# Change de secrey key