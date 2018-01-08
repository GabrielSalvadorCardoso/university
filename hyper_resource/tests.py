import django
import rest_framework
#from rest_framework import generics
#from rest_framework.response import Response
#from rest_framework.views import APIView
#from rest_framework import permissions
#from rest_framework import permissions

from django.contrib.gis.geos import Point
from django.test import TestCase
# Create your tests here.
from django.contrib.gis.db import models

from hyper_resource.models import FeatureModel, point_operations, geometry_operations, FactoryComplexQuery
from hyper_resource.views import AbstractResource, FeatureCollectionResource, AbstractCollectionResource
from django.contrib.gis.geos import GEOSGeometry
from django.test import SimpleTestCase

import json
import requests
from django.http import HttpResponse
from django.shortcuts import get_object_or_404


from django.test.runner import DiscoverRunner
#import os
#os.environ['DJANGO_SETTINGS_MODULE'] = 'bc_edgv.settings'
#django.setup()
#python manage.py test bcim.test_utils  --testrunner=bcim.test_utils.NoDbTestRunner
from django.contrib.gis.db.models import Q
class NoDbTestRunner(DiscoverRunner):
   """ A test runner to test without database creation/deletion """

   def setup_databases(self, **kwargs):
     pass

   def teardown_databases(self, old_config, **kwargs):
     pass

class Ponto(FeatureModel):
    id_objeto = models.IntegerField(primary_key=True)
    geom = models.PointField(blank=True, null=True)
class Linha(FeatureModel):
    id_objeto = models.IntegerField(primary_key=True)
    geom = models.LineStringField(blank=True, null=True)
class Poligono(FeatureModel):
    id_objeto = models.IntegerField(primary_key=True)
    geom = models.PolygonField(blank=True, null=True)
class Geometria(FeatureModel):
    id_objeto = models.IntegerField(primary_key=True)
    geom = models.GeometryField(blank=True, null=True)

## ativando virtual environment em: source ~/desenv/env/env_bc_edgv/bin/activate
## Testando
# python manage.py test hyper_resource.tests  --testrunner=hyper_resource.tests.NoDbTestRunner
##
#python manage.py test bcim.test_utils  --testrunner=bcim.test_utils.NoDbTestRunner
from django.test import SimpleTestCase
#from bcim.utils import APIViewHypermedia
#python manage.py test app --testrunner=app.filename.NoDbTestRunner
#python manage.py test bcim.tests  --testrunner=bcim.tests.NoDbTestRunner
#python manage.py test bcim.test_spatial_functions  --testrunner=bcim.test_spatial_functions.NoDbTestRunner
from bcim.models import ModeloTeste

class ModelTest(models.Model):
    id_objeto = models.IntegerField(primary_key=True)
    nome = models.CharField(max_length=100, blank=True, null=True)
    nomeabrev = models.CharField(max_length=50, blank=True, null=True)
    geometriaaproximada = models.CharField(max_length=3, blank=True, null=True)
    operacional = models.CharField(max_length=12, blank=True, null=True)
    situacaofisica = models.TextField(blank=True, null=True)
    tipopostofisc = models.CharField(max_length=22, blank=True, null=True)
    geometry = models.GeometryField(blank=True, null=True)
    polygon = models.PolygonField(blank=True, null=True)
    lineString = models.LineStringField(blank=True, null=True)
    point = models.PointField(blank=True, null=True)
    multipolygon = models.MultiPolygonField(blank=True, null=True)

class TesteResource(AbstractResource):
    def __init__(self, a_name, params, answer):
        self.name = a_name
        self.parameters = params
        self.return_type = answer


class FeatureModelTestCase(SimpleTestCase):
    def setUp(self):
        self.ponto = Ponto()
        self.linha = Linha()
        self.poligono = Poligono()
        self.geometria = Geometria()

    def url_feature(self):
        return ''

    def test_get_geometry_type(self):
        self.assertEquals(self.ponto.get_geometry_type(), Point)

    def test_operations_with_parameters_type(self):
        self.assertEquals(self.ponto.operations_with_parameters_type().keys(), point_operations().keys())

    def test_fields(self):
        self.assertEquals(self.ponto.fields()[0].name, 'id_objeto')
class AbstractResourceTestCase(SimpleTestCase):

    def setUp(self):
        self.tr = TesteResource('name', 'parameters', 'answer')

    def test_attributes(self):
        pass
    def test_operations(self):
        pass


class SpatialResourceTest(SimpleTestCase):

    def test_attributeContextualized(self):
        pass

class FeatureResourceTest(SimpleTestCase):

    def test_basic_get(self):
        pass
    def test_options_url_without_parameters(self):
        pass
    def test_options_url_with_only_attributes(self):
        pass
    def test_options_url_with_only_one_attribute(self):
        pass
    def test_options_url_with_spatia_functions(self):
        pass



class FactoryComplexQueryTest(SimpleTestCase):
    def setUp(self):
        self.fcq = FactoryComplexQuery()
    def test_q_object_for_in(self):

        q = self.fcq.q_object_for_in(str,'sigla', ['ES,RJ'])
        self.assertEquals(Q(sigla__in=['ES,RJ']).__repr__(), q.__repr__())

    def test_q_object_for_eq(self):

        q = self.fcq.q_object_for_eq(str,'sigla', 'ES')
        self.assertEquals(Q(sigla='ES').__repr__(), q.__repr__())

    def test_q_object_for_neq(self):

        q = self.fcq.q_object_for_neq(str, 'sigla', 'ES')
        self.assertEquals((~Q(sigla='ES')).__repr__(), q.__repr__())

    def test_q_object_by_filter_operation(self):
        attribute_operation_str ='filter/sigla/in/rj,es,go/and/data/between/2017-02-01,2017-06-30/'
        import datetime
        start_date = datetime.date(2017, 2, 1)
        end_date = datetime.date(2017, 6, 30)
        q = Q(sigla__in=['rj','es','go']) & Q(data__range=(start_date, end_date))
        model_class = ModeloTeste
        self.fcq.q_object_serialized_by_filter_operation(attribute_operation_str, model_class)

class AbstractCollectionResourceTest(SimpleTestCase):
    def setUp(self):
        self.attributes_functions = ['filter/sigla/in/rj,es,go/', 'filter/sigla/uppercase/in/rj,es,go/and/data/between/2017-02-01,2017-06-30/', 'filter/sigla/in/rj,es,go/and/geom/within/{"type":"Polygon","coordinates":[[[-41.881710164667396,-21.297482165015307],[-28.840495695785098,-21.297482165015307],[-28.840495695785098,-17.886950999070834],[-41.881710164667396,-17.886950999070834],[-41.881710164667396,-21.297482165015307]]]}']
        self.acr = AbstractCollectionResource()

    def test_attributes_functions_str_is_filter_with_spatial_operation(self):
        self.assertTrue(self.acr.attributes_functions_str_is_filter_with_spatial_operation('filter/sigla/in/rj,es,go/and/geom/within/Point(1,2)'))
        self.assertFalse(self.acr.attributes_functions_str_is_filter_with_spatial_operation('/filter'))
        self.assertFalse(self.acr.attributes_functions_str_is_filter_with_spatial_operation('/filter/filter'))
        self.assertFalse(self.acr.attributes_functions_str_is_filter_with_spatial_operation('/filter/ast/eq/ass/geom/within/asd'))
        self.assertFalse(self.acr.attributes_functions_str_is_filter_with_spatial_operation('/filter/within/eq/asd'))
        self.assertTrue(self.acr.attributes_functions_str_is_filter_with_spatial_operation('/filter/within/eq/geom/and/geom/within/asd'))
        self.assertFalse(self.acr.attributes_functions_str_is_filter_with_spatial_operation('/filter/operacao/eq/within'))
        self.assertTrue(self.acr.attributes_functions_str_is_filter_with_spatial_operation('/filter/eq/within/abxgeom'))
        self.assertFalse(self.acr.attributes_functions_str_is_filter_with_spatial_operation('/filter/within/eq/abxx'))
        self.assertFalse(self.acr.attributes_functions_str_is_filter_with_spatial_operation('/within/geom'))
        self.assertFalse(self.acr.attributes_functions_str_is_filter_with_spatial_operation('/within/filter'))


class FeatureCollectionResourceTest(SimpleTestCase):
    def setUp(self):
        self.attributes_functions = ['filter/sigla/in/rj,es,go/', 'filter/sigla/uppercase/in/rj,es,go/and/data/between/2017-02-01,2017-06-30/', 'filter/sigla/in/rj,es,go/and/geom/within/{"type":"Polygon","coordinates":[[[-41.881710164667396,-21.297482165015307],[-28.840495695785098,-21.297482165015307],[-28.840495695785098,-17.886950999070834],[-41.881710164667396,-17.886950999070834],[-41.881710164667396,-21.297482165015307]]]}']
        self.fc = FeatureCollectionResource()

    def test_is_filter_operation(self):
        self.assertTrue(self.fc.path_has_filter_operation('filter/sigla/in/rj,es,go/and/geom'))
        self.assertFalse( self.fc.path_has_filter_operation('/filter'))
        self.assertTrue('filter/sigla/uppercase/in/rj,es,go/and/data/between/2017-02-01,2017-06-30/')

    def test_get_objects_serialized_by_filter_operation(self):
        pass


    def test_q_objects_from_filter_operation(self):
        return True
        result = self.fc.q_objects_from_filter_operation('filter/sigla/eq/ES')[0]
        self.assertEquals(result.__repr__(), Q(sigla='ES').__repr__())
        result = self.fc.q_objects_from_filter_operation('filter/sigla/eq/ES/')[0]
        self.assertEquals(result.__repr__(), Q(sigla='ES').__repr__())
        result = self.fc.q_objects_from_filter_operation('filter/sigla/in/ES,RJ')[0]
        self.assertEquals(result.__repr__(), Q(sigla__in=['ES,RJ']).__repr__())
        result = self.fc.q_objects_from_filter_operation('filter/sigla/in/ES,RJ/')[0]
        self.assertEquals(result, Q(sigla__in=['ES,RJ']))
        result1 = self.fc.q_objects_from_filter_operation('filter/sigla/in/ES,RJ/and/data/between/2017-02-01,2017-06-30')[0]
        result2 = self.fc.q_objects_from_filter_operation('filter/sigla/in/ES,RJ/and/data/between/2017-02-01,2017-06-30')[1]
        self.assertEquals(result1, Q(sigla__in=['ES,RJ']))
        self.assertEquals(result2, Q(data='ES,RJ'))

    def test_token_in_url_array(self):
        self.maxDiff = None
        arr = ['geom', 'contains', 'http:','172.30.10.86:8000','instituicoes','ibge','bcim','municipios','3159407', '*or', 'geom', 'contains', 'http:','172.30.10.86:8000','instituicoes','ibge','bcim','municipios','3159406', '*and', 'contains', 'Point(23,23)']
        self.assertTrue(self.fc.token_in_url_array('http:',2, arr ))
        self.assertFalse(self.fc.token_in_url_array('*or',9 ,arr))
        self.assertTrue(self.fc.token_in_url_array('172.30.10.86:8000',13, arr ))
        self.assertFalse(self.fc.token_in_url_array('Point(23,23)',19 ,arr))

    def test_transform_path_with_spatial_operation_str_and_url_as_array(self):
        self.maxDiff = None
        s = 'geom/contains/http://172.30.10.86:8000/instituicoes/ibge/bcim/municipios/3159407/*or/geom/contains/http://172.30.10.86:8000/instituicoes/ibge/bcim/municipios/3159406'
        arr = ['geom', 'contains', 'http:','172.30.10.86:8000','instituicoes','ibge','bcim','municipios','3159407', '*or', 'geom', 'contains', 'http:','172.30.10.86:8000','instituicoes','ibge','bcim','municipios','3159406']
        arr1 = ['geom', 'contains', 'http://172.30.10.86:8000/instituicoes/ibge/bcim/municipios/3159407/', '*or', 'geom', 'contains', 'http://172.30.10.86:8000/instituicoes/ibge/bcim/municipios/3159406/']

        self.assertEquals(len(self.fc.transform_path_with_url_as_array(arr)), len(arr1))