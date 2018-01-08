import ast
import re
import json
import random
import jwt
import requests

from django.contrib.gis.db.models.functions import AsGeoJSON
from django.contrib.gis.gdal import SpatialReference
from django.db.models.base import ModelBase
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
# Create your views here.
from requests import ConnectionError
from requests import HTTPError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.gis.geos import GEOSGeometry, GeometryCollection
from hyper_resource.contexts import *
from rest_framework.negotiation import BaseContentNegotiation
from django.contrib.gis.db import models
from abc import ABCMeta, abstractmethod

from encoder import encode


from hyper_resource.models import  FactoryComplexQuery, OperationController, BusinessModel, ConverterType
from image_generator.img_generator import BuilderPNG

SECRET_KEY = '-&t&pd%%((qdof5m#=cp-=-3q+_+pjmu(ru_b%e+6u#ft!yb$$'


class IgnoreClientContentNegotiation(BaseContentNegotiation):
    def select_parser(self, request, parsers):
        """
        Select the first parser in the `.parser_classes` list.
        """
        return parsers[0]

    def select_renderer(self, request, renderers, format_suffix):
        """
        Select the first renderer in the `.renderer_classes` list.
        """
        return (renderers[0], renderers[0].media_type)

class BaseContext(object):

    def __init__(self, contextclassname, serializer_object=None):
        self.serializer_object = serializer_object
        self.contextclassname = contextclassname

    def options(self, request):
        response = Response(self.getContextData(request), status=status.HTTP_200_OK, content_type="application/ld+json")
        response = self.createLinkOfContext(request, response)
        return response

    def addContext(self, request, response):
        return self.createLinkOfContext(request, response)

    def createLinkOfContext(self, request, response, properties=None):
        # if properties is None:
        #     url = reverse('context:detail', args=[self.contextclassname], request=request)
        # else:
        #     url = reverse('context:detail-property', args=[self.contextclassname, ",".join(properties)], request=request)

        # pega a url absoluta, desde o host
        url = request.build_absolute_uri()
        # se houver uma barra no final da url ela é retirada
        url = url if url[-1] != '/' else url[:-1]
        # e adicionamos '.jsonld' ao ínvés da barra
        url = url + ".jsonld"

        # este link de contexto, quando clicado em um navegador,
        # deve levar a uma representação de uma requisição OPTIONS
        # da página atual

        # 'rel' é de relationship, isso significa que o tercho '<ulr>'
        # representa um contexto para algo, neste caso este relacionamento
        # é representado por dados no formato jsonld
        context_link = ' <'+url+'>; rel=\"http://www.w3.org/ns/json-ld#context\"; type=\"application/ld+json\" '
        if "Link" not in response:
            response['Link'] = context_link
        else:
            response['Link'] += "," + context_link

        return response

    def getHydraData(self, request):
        #classobject = Class.objects.get(name=self.contextclassname)
        #serializerHydra = HydraSerializer(classobject, request)
        return {}

    def addIriTamplate(self, context, request, serializer_object):
        url = request.build_absolute_uri()
        iriTemplate = {
            "@context": "http://www.w3.org/ns/hydra/context.jsonld",
            "@type": "IriTemplate",
            "template": url if url[-1] != '/' else url[:-1] +"{/attribute}",
            "variableRepresentation": "BasicRepresentation",
            "mapping": []
        }
        if serializer_object is not None:
            # percorre uma lista de atributos identificadores
            # encontrados no serializer
            for attr in serializer_object.Meta.identifiers:
                iriTemplate['mapping'].append({
                    "@type": "IriTemplateMapping",
                    "variable": "attribute",
                    "property": attr,
                    "required": True
                })
        else:
            iriTemplate['mapping'].append({
                "@type": "IriTemplateMapping",
                "variable": "attribute",
                "property": "hydra:supportedProperties",
                "required": True
            })

        context['iriTemplate'] = iriTemplate
        return context

    def getContextData(self, request):
        try:
            classobject = None #Class.objects.get(name=self.contextclassname)
        except:
            return ""
        serializer = None #ContextSerializer(classobject)
        contextdata = {} #serializer.data
        # BaseContext.getHydraData() retorna um dicionário vazio
        hydradata = self.getHydraData(request)
        if "@context" in hydradata:
            hydradata["@context"].update(contextdata["@context"])
        contextdata.update(hydradata)
        contextdata = self.addIriTamplate(contextdata, request, self.serializer_object)
        return contextdata

class AbstractResource(APIView):
    """
    AbstractResource é uma das pricipais views deste arquivo
    (se não a principal), pois várias outras derivam dela
    'APIView' vem do rest framework
    """

    # teoriacamente isso torna a classe abstrata
    __metaclass__ = ABCMeta

    serializer_class = None
    contextclassname= ''
    def __init__(self):
        # super().__init__() chama o contrutor da superclasse ç
        # como python permite herança multipla precisamos deixar
        # explicito de que classe estamos chamando o contrutor ç
        super(AbstractResource, self).__init__()
        self.current_object_state = None
        self.object_model = None
        self.name_of_last_operation_executed = None
        self.context_resource = None
        self.initialize_context()
        self.iri_metadata = None
        self.operation_controller = OperationController()
        self.token_need = self.token_is_need()

    # indicando a classe de negociação de conteúdo
    content_negotiation_class = IgnoreClientContentNegotiation

    # retorna uma string que representa o algorítmo JSON Web Token usado
    # JWT provê uma forma segura de transmitir informações entre partes
    def jwt_algorithm(self):
        return 'HS256'

    # verifica se um token passado é válido
    def token_is_ok(self, a_token):
        try:
            # jwt.decode() recebe o token, uma chave secreta e o algorítmo
            payload = jwt.decode(a_token, SECRET_KEY, algorithm=self.jwt_algorithm())
            return True
        # caso esta operação um InvalidTokenError concluimos que o token não é válido
        except jwt.InvalidTokenError:
            return False

    def token_is_need(self):
        return  False

    def add_key_value_in_header(self, response, key, value ):
        """
        Esta função adiciona um cabeçalho (key) a resposta
        com o valor 'value'
        :param response:
        :param key:
        :param value:
        :return:
        """

        response[key] = value

    def add_url_in_header(self, url, response, rel):
        link = ' <'+url+'>; rel=\"'+rel+'\" '
        if "Link" not in response:
            # podemos adicionar informações no header através
            # das chave do objeto Response que é um dicionário
            response['Link'] = link
        else:
            # adicionamos este conteúdo no header do objeto Response
            # este conteúdo estará disponível na página api root
            response['Link'] += "," + link
        return response

    def add_base_headers(self, request, response):
        iri_base = request.build_absolute_uri()
        if self.contextclassname not in iri_base:
            return;
        idx = iri_base.index(self.contextclassname)
        iri_father = iri_base[:idx]
        self.add_url_in_header(iri_father,response, 'up')
        self.add_url_in_header(iri_base[:-1] + '.jsonld',response, rel='http://www.w3.org/ns/json-ld#context"; type="application/ld+json')

    def dispatch(self, request, *args, **kwargs):

        if self.token_is_need():
            # dependendo de como a autorização ocorre 'HTTP_AUTHORIZATION' já pode
            # ser uma informação do header da requisição até este ponto (não é, por padrão)
            http_auth = 'HTTP_AUTHORIZATION'

            # Request.META é uma dicionário contendo todos os cabeçalhos disponíveis
            # se HTTP_AUTHORIZATION for um indice do cabeçalho e seu valor correspondente
            # começão com 'Bearer'
            if http_auth in request.META and request.META[http_auth].startswith('Bearer'):
                # strip() remove os espaços do início e do fim da string
                # neste caso, estamos pegando todos os caracteres do sétimo até o final
                # ou seja, os caracteres depois da string 'Bearer'
                # resumindo: o token será uma string advinda do valor referente ao
                # índice HTTP_AUTHORIZATION do dicionário de headers Request.META
                a_token = request.META['HTTP_AUTHORIZATION'][7:].strip()

                if self.token_is_ok(a_token):
                    # se o token for válido, acionamos o método 'dispatch' da superclasse
                    return super(AbstractResource, self).dispatch(request, *args, **kwargs)

            # json.dumps transforma o dicionário em um JSON
            # o primeiro arâmetro são os dados do body
            resp = HttpResponse(json.dumps({"token": "token is needed or it is not ok"}), status=401,  content_type='application/json')
            resp['WWW-Authenticate'] = 'Bearer realm="Access to the staging site"'
            return resp
        else:
            # se o token não for necessário, acionamos o método 'dispatch' da superclasse
            return  super(AbstractResource, self).dispatch(request, *args, **kwargs)

    #@abstractmethod #Could be override
    def initialize_context(self):
        # __class__ mostra em que classe a instrução esta sendo executada
        # (isso servirá para o herdeiro desta classe, e não esta em si)
        # __module__ mostra de que módulo é esta classe (o caminho todo)
        # teremos então algo como administrativo.AlunoView.views (com o nome da pasta também)
        # que será dividido em partes pelo ponto e pegaremos a primeira parte (que contém o nome da pasta)
        # no final teremos algo como: administrtivo.contexts que é o módulo onde encontra-se os contextos
        context_module_name = self.__class__.__module__.split('.')[0] + '.contexts'

        # importando o módulo de contextos referente a string criada na linha anterior
        context_module = importlib.import_module(context_module_name)

        # pegamos o nome da classe atual (lembrando que a classe atual ç
        # herdará de AbstractResource ou uma de suas filhas)
        # e adicionando 'Context'. Teremos algo como: 'AlunoDetailContext' ç
        context_class_name = self.__class__.__name__ + 'Context'

        # retornando a classe de contexto (dentro do módulo indicado) referente a view atual
        # no caso de AlunoDetail retornará a classe AlunoDetailContext
        context_class = getattr(context_module, context_class_name )

        # atribuindo a classe retornada ao atributo context_resource da classe atual ç
        # classe atual refere-se view que herda de AbstractResource ou de suas filhas ç
        self.context_resource = context_class()
        self.context_resource.resource = self


    # todo
    def path_request_is_ok(self, a_path):
        return True

    def operations_with_parameters_type(self):
        """
        Retorna um dicionário com operações geométricas para FeatureModel
        ou retorna um dicionário vazio para BusinessModel
        :return:
        """
        dic = self.object_model.operations_with_parameters_type()
        return dic

    def model_class(self):
        # retorna a classe de modelo atravé do atributo 'model'
        # da metaclasse do serialize referente a esta view ç
        return self.serializer_class.Meta.model #return self.object_model.model_class()

    def model_class_name(self):
        # retorna o nome da classe de modelo usando o método anterior
        return self.model_class().__name__

    def attribute_names_to_web(self):
        # retorna uma lista com os nomes dos campos presentes na serializer class desta view ç
        return [field.name for field in self.object_model.fields()]
        #return self.serializer_class.Meta.fields

    def field_for(self, attribute_name):
        fields_model = self.object_model.fields()
        for field in fields_model:
            if field.name == attribute_name:
                return field
        return None

    def fields_to_web_for_attribute_names(self, attribute_names):
        # retorna o conjunto de campo referente a object_model ç
        fields_model = self.object_model.fields()

        # Poderia ser ModelClass._meta.get_field(field_name) Obs: raise FieldDoesNotExist
        # retorna um subconjunto de nome da campos do modelo ç
        # cujos elementos estão também em 'attribute_names'. Funciona como um filtro
        return [field for field in fields_model if field.name in attribute_names ]

    def fields_to_web(self):
        # envia o conjunto de compos do serializer para o método acima
        # para que o conjunto de campos do modelo seja comparado com estes ç
        # retorna um subconjunto ç
        return self.fields_to_web_for_attribute_names(self.attribute_names_to_web())

    def _base_path(self, full_path):
        arr = full_path.split('/')

        # index() irá retornar o primeiro índice que se encontra
        # o nome da classe de contexto dentro da url passada ç
        ind = arr.index(self.contextclassname)

        # o path retornado será a url do nome da classe de contexto para frente
        return '/'.join(arr[:ind+1])

    def _set_context_to_model(self):
        # context_resource representa a classe de contexto referente a view ç
        # aqui estamos configurando object_model como um modelo de contexto para este contexto ç
        self.context_resource.contextModel(self.object_model)

    def _set_context_to_attributes(self, attribute_name_array):
        # aparentemente atribui um contexto para cada um dos atributos do array ç
        # set_context_to_attributes() é um método da classe ContextResource
        self.context_resource.set_context_to_attributes(attribute_name_array)

    def _set_context_to_only_one_attribute(self, attribute_name):
        # aparentemente atribui um contexto para atributo especificado ç
        # set_context_to_only_one_attribute() é um metodo de ContextResource
        attribute_type = self.field_for(attribute_name)
        self.context_resource.set_context_to_only_one_attribute(self.current_object_state, attribute_name, attribute_type)

    def _set_context_to_operation(self, operation_name):
        # aparentemente atribui um contexto para uma operação
        # set_context_to_operation() é um método de ContextResource
        self.context_resource.set_context_to_operation(self.current_object_state, operation_name)

    def set_basic_context_resource(self, request ):
        # define o host no recurso de contexto através do cabeçalho da requisição
        self.context_resource.host = request.META['HTTP_HOST']

        # define a url da requisição no recurso de contexto através do cabeçalho da requisição
        # esta url será o pedaço da url completa que é tudo que estiver depois do nome da classe de contexto para frente
        self.context_resource.basic_path = self._base_path(request.META['PATH_INFO'])

        if len(self.kwargs.values()):
            # pegamos o primeiro argumento da lista e atribuimos seu valor ao atributo ç
            # complement_path do recurso de contexto desta view ç
            self.context_resource.complement_path = list(self.kwargs.values())[0]
        else:
            # se não houver argumentos, complement_path será apenas uma string vazia
            self.context_resource.complement_path = ''


    def key_is_identifier(self, key):
        # retorna True caso a chave passada esteja na lista de identifiers ç
        # do serializer desta view ç
        return key in self.serializer_class.Meta.identifiers

    def dic_with_only_identitier_field(self, dict_params):
        # retorna um dicionário com um subconjunto de elementos do dicionário passado
        # este subconjunto contém apenas os elementos que são identifiers no serializer desta view
        dic = dict_params.copy()
        a_dict = {}
        for key, value in dic.items():
            if self.key_is_identifier(key):
                a_dict[key] = value

        return a_dict

    '''
    def get_object(self, arr_of_term=[]):
        first_term = arr_of_term[0]
        if self.is_attribute(self, first_term):
            self.current_object_state =  getattr(self.object_model, first_term, None)
            arr_of_term = arr_of_term[1:]

        for term in arr_of_term:
            self.current_object_state = getattr(self.current_object_state, term, None)
        return  self.current_object_state
    '''
    def attributes_functions_name_template(self):
        return 'attributes_functions'

    def get_object(self, a_dict):
        # dicti será um dicionário composto apenas por elementos chave do modelo
        dicti = self.dic_with_only_identitier_field(a_dict)
        # queyset será algo como um select * from Model; neste caso. Onde Model é um modelo determinado
        queryset = self.model_class().objects.all()
        # retorna um objeto usando os identificadores do dicionário para retornar um objeto específico
        obj = get_object_or_404(queryset, **dicti)
        #self.check_object_permissions(self.request, obj)
        return obj

    def get(self, request, *args, **kwargs):
        # chama a função get() de APIView
        return super(AbstractResource, self).get(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        # usa o método patch da classe superior repassando os arqumentos da requisição
        return super(AbstractResource, self).patch(request, *args, **kwargs)

    def head(self, request, *args, **kwargs):
        # retorna um código 200 para a requisição HEAD
        resp =  Response(status=status.HTTP_200_OK)
        return resp

    def put(self, request, *args, **kwargs):
        # retorna um objeto usando o dicionário kwargs passado como argumento
        obj = self.get_object(kwargs)

        # monta um objeto serializer com o objeto retornado, os dados da requisição
        # (a serem comparadas com o objeto retornado de self.get_object()) e um contexto (a própria requisição)
        serializer = self.serializer_class(obj, data=request.data, context={'request': request})

        if serializer.is_valid():
            # se os dados forem válidos, o objeto é salvo (atualizado)
            serializer.save()
            resp =  Response(status=status.HTTP_204_NO_CONTENT)
            return resp

        # se os dados não forem váldos retornamos serializer.errors como os dados de resposta
        # junto com um código 400
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        # recupera o objeto baseado no dicionário kwargs
        obj = self.get_object(kwargs)
        # deleta o objeto do banco de dados
        obj.delete()
        # responde com um código 204
        return Response(status=status.HTTP_204_NO_CONTENT)



    def operation_names_model(self):
        # retorna uma lista com todos os nomes de métodos referentes
        # ao objeto de modelo
        return self.object_model.operation_names()

    def attribute_names_model(self):
        # retorna uma lista de atributos simples (não chamáveis)
        return self.object_model.attribute_names()

    # ESTE MÉTODO JÁ ESTÁ IMPLEMENTADO EM models.BussinesModel
    def is_private(self, attribute_or_method_name):
        # atributos ou métodos iniciados por '__' e terminados por '__'
        # são privados, se este for o caso, esté método retorna True
        return attribute_or_method_name.startswith('__') and attribute_or_method_name.endswith('__')

    # ESTE MÉTODO JÁ ESTÁ IMPLEMENTADO EM models.BussinesModel
    def is_not_private(self, attribute_or_method_name):
        # possui exatamente a lógica inversa do método anterior
        return not self.is_private(attribute_or_method_name)

    def is_operation(self, operation_name):
        # retorna True caso 'operation_name' esteja entre as ç
        # operações do modelo desta view
        return operation_name in self.operation_names_model()

    def is_attribute(self, attribute_name):
        # retorna uma lista de atributos de 'object_model' ç
        # que não são chamáveis
        return self.object_model.is_attribute(attribute_name)

    def is_spatial_attribute(self, attribute_name):
        return False

    def _has_method(self,  method_name):
        # retorna True caso 'method_name' esteja dentro da ç
        # lista de métodos de 'self.object_model'
        return method_name in self.operation_names_model()

    def is_simple_path(self, attributes_functions_str):
        # se attributes_function_str for nulo ou string de tamanho 0 retorna True ç
        return attributes_functions_str is None or len(attributes_functions_str) == 0

    def path_has_operations(self, attributes_functions_name):
        # attrs_functs é uma lista com os segmentos da url
        attrs_functs = attributes_functions_name.split('/')
        # retorna uma lista com nomes de métodos de 'self.object_model'
        operations = self.operation_names_model()
        # percorre a lista
        for att_func in attrs_functs:
            # se algum dos seguimentos corresponder a ç
            # aglum elemento da lista de métodos do
            # objeto de modelo, retornamos True ç
            if  att_func in operations:
                return True
        # se a lista for percorrida sem coincidências, retornamos False
        return False

    def path_has_only_attributes(self,  attributes_functions_name):
        # attrs_functs é uma lista com os seguimentos da url
        attrs_functs = attributes_functions_name.split('/')
        # se a lista de seguimentos tem mais de 1 elemento, então não temos só atributos
        if len(attrs_functs) > 1:
            return False
        # se o primeiro elemento da lista tiver ',', então temos só atributos na url
        if ',' in attrs_functs[0]:
            return True
        # retorna False caso o primeiro elemento a lista seja um método do modelo
        if self._has_method(attrs_functs[0]):
            return False
        # retorna True caso 'attrs_functs[0]' seja uma atributo não chamável do modelo
        return self.object_model.is_attribute(attrs_functs[0])

    def transform_path_with_url_as_array(self, arr_of_term):

        arr = []
        http_str = ''
        # arr_term será uma lista sem strings vazias
        arr_term =  [ele for ele in arr_of_term if ele != '']

        found_url = False
        size_of_term = len(arr_term)
        for idx, token in enumerate(arr_term):
            # lower() converte a string para minúsculo
            # so o token for http, https ou www, achamos a url ç
            if self.token_is_http_or_https_or_www(token.lower()):
                found_url = True

            if  found_url:
                if self.token_is_http_or_https(token):
                    # se o token for http ou https, 'concatenamos a http_str ç
                   http_str += token + '//'
                elif self.is_end_of_term(token):
                    # se o token for end_of_term 'found_url' se torna False ç
                    found_url = False
                    # adicionamos 'http_str' a lista 'arr' ç
                    arr.append(http_str)
                    # e adicionamos o token a lista 'arr' ç
                    arr.append(token)
                    # 'http_str' vira uma string vazia ç
                    http_str = ''
                elif (idx == size_of_term -1):
                    # se o índice atual é representa o penúltimo item da lista 'arr_term'
                    # 'found_url' torna-se False ç
                    found_url = False
                    # concatenamos o token e uma barra a 'http_str' ç
                    http_str+= token + '/'
                    # adicionamos 'http_str' a lista 'arr' ç
                    arr.append(http_str)
                    # e 'http_str' torna-se uma string vazia ç
                    http_str = ''

                else:
                    # para todos os outros casos, apenas concatenamos o token e uma barra a 'http_str' ç
                    http_str += token + '/'
            else:
                # se não acharmos a url nesta iteração, adicionamos a string a 'arr'
                arr.append(token)
        return arr

    def attributes_functions_splitted_by_url(self, attributes_functions_str_url):
        # retorna o índice onde encontra-se a substring 'http:'
        res = attributes_functions_str_url.lower().find('http:')
        # se a substring não for encontrada ...
        if res == -1:
            # proucure pela substring 'https:' ç
            res = attributes_functions_str_url.lower().find('https:')
            # se ainda não encontrar ...
            if res == -1:
                # proucure por 'www.' ç
                res = attributes_functions_str_url.lower().find('www.')
                if res == -1:
                    # se mesmo assim não encontrar, retorna o conteúdo original em forma de lista
                    return [attributes_functions_str_url]

        # se 'http' for encontrado retornamos uma lista onde o primeiro elemento é a string do início
        # até 'http' (sem incluir o 'http') e o segundo elemento é o restante da string
        return [attributes_functions_str_url[0:res], attributes_functions_str_url[res:]]

    def path_has_url(self, attributes_functions_str_url):
        # retornna True se 'attributes_function_str_url' contiver ç
        # qualquer uma das seguintes substring: http, https ou www. ç
        return (attributes_functions_str_url.find('http:') > -1) or (attributes_functions_str_url.find('https:') > -1)\
               or (attributes_functions_str_url.find('www.') > -1)

    def _execute_attribute_or_method(self, object, attribute_or_method_name, array_of_attribute_or_method_name):
        dic = {}
        parameters = []
        # verifica se 'atribute_or_method_name' é uma operação/método de 'object'
        if OperationController().is_operation(object, attribute_or_method_name):
            # se 'attribute_or_method_name' for uma operação de 'object', verifica se a operação tem parâmetros
            if OperationController().operation_has_parameters(object, attribute_or_method_name):
                # se a operação tiver parâmetros, pegamos o primeiro elemento da
                # lista de atributos e/ou métodos passada como ultimo argumento
                # dividimo-o pelo caracter '&' e atribuimos a 'parameters' ç
                parameters = array_of_attribute_or_method_name[0].split('&')
                # eliminamos o primeiro elemento da lista
                array_of_attribute_or_method_name = array_of_attribute_or_method_name[1:]

        # chama uma função da classe AbstractResource (implementada abaixo) e envia
        # o objeto, o método deste e a lista de parâmetros advinda da divisão do
        # primeiro elemento de 'array_of_attribute_or_method_name'
        obj = self._value_from_object(object, attribute_or_method_name, parameters)

        # se a lista de atributos/métodos estiver vazio, apenas retorna o objeto
        if len(array_of_attribute_or_method_name) == 0:
            return obj

        # se a lista de atributos/métodos não estiver vazia, acione este método recursivamente
        # enviando o objeto recebido por esta função, o primeiro elemento de 'array_of_attributes_or_method_name'
        # como segundo argumento e a lista com o restante do elementos de 'array_of_attributes_or_method_name'
        # como terceiro argumento
        return self._execute_attribute_or_method(obj, array_of_attribute_or_method_name[0], array_of_attribute_or_method_name[1:])

    def is_operation_and_has_parameters(self, attribute_or_method_name):
        """
       Retorna True se 'attribute_or_method_name'
       for uma operação de BusinnesModel ou FeatureModel
       que tenha parâmetros
       :param attribute_or_method_name:
       :return:
       """
        # 'dic' é um dicionário com operações para FeatureModel ou um dicionário vazio para BusinessModel
        dic = self.operations_with_parameters_type()
        # 'se attribute_or_method_name' esta em 'dic'
        # (ou seja, se attribute_or_method_name é uma operação)
        # e o número de parâmetros é maior que 1, retorna True
        return (attribute_or_method_name in dic) and len(dic[attribute_or_method_name].parameters)



    def function_name(self, attributes_functions_str):
        functions_dic = self.operations_with_parameters_type()
        if str(attributes_functions_str[-1]) in functions_dic:
            return str(attributes_functions_str[-1])
        return str(attributes_functions_str[-2])



    def response_resquest_with_attributes(self,  attributes_functions_name):
        """
        Fonece uma resposta para requisições com atributos
        :param attributes_functions_name:
        :return:
        """

        a_dict ={}
        # 'attributes_functions_name' possívelmente é uma
        # string com nome de atributos ou de funções
        attributes = attributes_functions_name.strip().split(',')
        #self.current_object = self.object_model

        for attr_name in attributes:
            # pega cada nome de atibuto ou de função da lista e submete
            # a AbstractResource._value_from_object,
            # junto com o objeto de modelo e uma lista vazia ...
            obj = self._value_from_object(self.object_model, attr_name, [])
            # ... e adiciona o retorno da função no índice do dicionário
            # que é o nome do atributo/função da iteração atual
            a_dict[attr_name] = obj

        # o dicionário gerado torna-se o estado atual do objeto
        self.current_object_state = a_dict

        # o retorno é uma resposta a uma requisição com:
        # 'a_dict' como o dado da resposta, 'application/json'
        # como content_type da resposta, um status 200 e o object model
        # (provavelmente no header)
        return (a_dict, 'application/json', self.object_model, {'status': 200})

    # NOT COMPLETLY COMMENTED
    def all_parameters_converted(self, attribute_or_function_name, parameters):
        """
        'attribute_or_function_name' é uma string que
        representa um possível atributo ou função de um modelo e
        'parameters' são os parâmetros deste atributo ou função
        :param attribute_or_function_name:
        :param parameters:
        :return:
        """

        parameters_converted = []
        # se 'attribute_or_function_name' for uma função de BusinessModel
        # ou de FeatureModel que tenha parâmetros ...

        if self.is_operation_and_has_parameters(attribute_or_function_name):
            # - Para o caso de AbstractResource.object_model ser um FeatureModel,
            # AbstractResource.operations_with_parameters_type() retorna um dicionário
            # onde cada um de seus índices, que são tipos geométricos, corresponde a outro
            # dicionário com operações (Type_called) referentes aquele tipo
            # - Para o caso de AbstractResource.object_model ser um BusinessModel,
            # AbstractResource.operations_with_parameters_type() retorna apenas um dicionário
            # vazio, isso causará um KeyError
            # 'parameters_type' será uma lista com todos os 'parameters' do Type_Called
            parameters_type = self.operations_with_parameters_type()[attribute_or_function_name].parameters

            for i in range(0, len(parameters)):
               parameters_converted.append(parameters_type[i](parameters[i]))

            return parameters_converted

        return self.parametersConverted(parameters)

    def is_attribute_for(self, object, attribute_or_function_name):
        """
        Se 'attribute_or_function_name' for um atributo não
        chamável de object, retorna True
        :param object:
        :param attribute_or_function_name:
        :return:
        """
        # - hasattr() verifica se 'atribute_or_function_name' é um atributo de object
        # - getattr() retorna o valor do atributo representado por 'attribute_or_function_name'
        # se este existir, depois callable() verifica se este valor é chamável (uma classe ou método)
        return  hasattr(object, attribute_or_function_name) and not callable(getattr(object, attribute_or_function_name))

    # NOT COMPLETLY COMMENTED
    def _value_from_object(self, object, attribute_or_function_name, parameters):
        """
               Retorna o valor do atributo do objeto que é representado pela
               string 'attribute_or_function_name'. Se 'attribute_or_function_name'
               não for um atributo ou função de 'object' provavelmente lançará uma
               exceção
               :param object:
               :param attribute_or_function_name:
               :param parameters:
               :return:
               """

        # retira os espaços das estremidades de 'attribute_or_function_name'
        attribute_or_function_name_striped = attribute_or_function_name.strip()

        # 'attribute_or_function_name_striped' torna-se o nome da ultima operação executada
        self.name_of_last_operation_executed = attribute_or_function_name_striped

        # se 'attribute_or_function_name' for um atributo não chamável de 'object' ...
        if self.is_attribute_for(object, attribute_or_function_name):
            # ... o valor do atributo de object representado por
            # 'attribute_or_function_name_striped' é retornado
            return getattr(object, attribute_or_function_name_striped)

        # se 'attribute_or_function_name' não for um atributo não chamável de 'object'
        # então ele é uma função, neste caso
        # verificamos se o número de parâmetros passados em 'parameters' e maior que 0
        if len(parameters)> 0:

            # se 'object' for uma instância de BusinessModel ou de GOESGeomety ...
            if (isinstance(object, BusinessModel) or isinstance(object, GEOSGeometry)):
                # passamos a função e os parâmetros para AbstractResource.all_parameters_converted()
                params = self.all_parameters_converted(attribute_or_function_name_striped, parameters)
                # VERIFICAR O QUE ESTA FUNÇÃO FAZ
            else:
                # se não for uma instância de BusinessModel nem de FeatureModel
                # submetemos 'parameters' a função 'attribute_or_function_name'
                # que é uma operação do conjunto de operações referentes ao tipo de 'object'
                params = ConverterType().convert_parameters(type(object), attribute_or_function_name, parameters)

            # neste caso 'attribute_or_function_name_striped' é uma função com
            # parâmetros. Depois do tratamento adequado dado a 'params' acima,
            # pegamos o valor do atributo de 'object' representado por
            # 'attribute_or_method_name_striped' e passamos 'params' para este valor
            return getattr(object, attribute_or_function_name_striped)(*params)

        # em qualquer outro caso, concluimos que 'attribute_or_function_name_striped'
        # é um atributo chamável (função) de 'object' que não possui parâmetros,
        # neste caso executamos este chamável
        # retornando o valor que o chamável retornar
        return getattr(object, attribute_or_function_name_striped)()

    def parametersConverted(self, params_as_array):
        paramsConveted = []

        for value in params_as_array:
            if value.lower() == 'true':
                paramsConveted.append(True)
                continue
            elif value.lower() == 'false':
                paramsConveted.append(False)
                continue

            try:
                paramsConveted.append(int( value ) )
                continue
            except ValueError:
                pass
            try:
               paramsConveted.append( float( value ) )
               continue
            except ValueError:
                pass
            try:
               paramsConveted.append( GEOSGeometry( value ) )
               continue
            except ValueError:
                pass
            try:
                http_str = (value[0:4]).lower()
                if (http_str == 'http'):
                    resp = requests.get(value)
                    if 400 <= resp.status_code <= 599:
                        raise HTTPError({resp.status_code: resp.reason})
                    js = resp.json()

                    if (js.get("type") and js["type"].lower() in ['feature', 'featurecollection']):
                        a_geom = js["geometry"]
                    else:
                        a_geom = js
                    paramsConveted.append(GEOSGeometry((json.dumps(a_geom))))
            except (ConnectionError,  HTTPError) as err:
                print('Error: '.format(err))
                #paramsConveted.append (value)

        return paramsConveted

    def generate_tmp_file(self, suffix='', length_name=10):
        return ''.join([random.choice('0123456789ABCDEF') for i in range(length_name)]) + suffix

    def get_style_file(self, request):
        if 'HTTP_LAYERSTYLE' in request.META:
            layer_style_url = request.META['HTTP_LAYERSTYLE']
            response = requests.get(layer_style_url)
            if response.status_code == 200:
                file_name = self.generate_tmp_file(suffix="_tmp_style.xml")
                with open(file_name, "w+") as st:
                    st.write(response.text.encode('UTF-8'))
                    st.close()
                return file_name
        return None

    def get_png(self, queryset, request):
        style = self.get_style_file(request)

        if isinstance(queryset, GEOSGeometry):
            wkt = queryset.wkt
            geom_type = queryset.geom_type
        else:
            wkt = queryset.geom.wkt
            geom_type = queryset.geom.geom_type

        config = {'wkt': wkt, 'type': geom_type}
        if style is not None:
            config["style"] = style
            config["deleteStyle"] = True
        builder_png = BuilderPNG(config)
        return builder_png.generate()

class NonSpatialResource(AbstractResource):

    def response_of_request(self,  attributes_functions_str):
        att_funcs = attributes_functions_str.split('/')
        if (not self.is_operation(att_funcs[0])) and self.is_attribute(att_funcs[0]):
            att_funcs = att_funcs[1:]

        self.current_object_state = self._execute_attribute_or_method(self.object_model, att_funcs[0], att_funcs[1:])

        if hasattr(self.current_object_state, 'model') and issubclass(self.current_object_state.model, Model):
            class_name = self.current_object_state.model.__name__ + 'Serializer'
            serializer_cls = self.object_model.class_for_name(self.serializer_class.__module__, class_name)
            if isinstance(self.current_object_state, QuerySet):
                self.current_object_state = serializer_cls(self.current_object_state, many=True,
                                                           context={'request': self.request}).data
            elif isinstance(self.current_object_state.field, OneToOneField):
                self.current_object_state = serializer_cls(self.current_object_state, context={'request': self.request}).data
            else:
                self.current_object_state = serializer_cls(self.current_object_state, many=True, context={'request': self.request}).data

        a_value = {self.name_of_last_operation_executed: self.current_object_state}

        return (a_value, 'application/json', self.object_model, {'status': 200})

    def basic_get(self, request, *args, **kwargs):

        self.object_model = self.get_object(kwargs)
        self.current_object_state = self.object_model
        self.set_basic_context_resource(request)
        # self.request.query_params.
        attributes_functions_str = kwargs.get(self.attributes_functions_name_template())

        if self.is_simple_path(attributes_functions_str):

            serializer = self.serializer_class(self.object_model, context={'request': self.request})
            output = (serializer.data, 'application/json', self.object_model, {'status': 200})

        elif self.path_has_only_attributes(attributes_functions_str):
            output = self.response_resquest_with_attributes(attributes_functions_str.replace(" ", ""))
            dict_attribute = output[0]
            if len(attributes_functions_str.split(',')) > 1:
                self._set_context_to_attributes(dict_attribute.keys())
            else:
                self._set_context_to_only_one_attribute(attributes_functions_str)
        elif self.path_has_url(attributes_functions_str.lower()):
            output = self.response_request_attributes_functions_str_with_url( attributes_functions_str)
            self.context_resource.set_context_to_object(self.current_object_state, self.name_of_last_operation_executed)
        else:
            output = self.response_of_request(attributes_functions_str)
            self._set_context_to_operation(self.name_of_last_operation_executed)

        return output

    def get(self, request, *args, **kwargs):

        dict_for_response = self.basic_get(request, *args, **kwargs)
        status = dict_for_response[3]['status']
        if status in [400, 401,404]:
            return Response({'Error ': 'The request has problem. Status:' + str(status)}, status=status)

        if status in [500]:
           return Response({'Error ': 'The server can not process this request. Status:' + str(status)}, status=status)

        accept = request.META['HTTP_ACCEPT']


        return Response(data=dict_for_response[0], content_type=dict_for_response[1])

    def options(self, request, *args, **kwargs):
        self.basic_get(request, *args, **kwargs)
        #return self.context_resource.context()
        return Response ( data=self.context_resource.context(), content_type='application/ld+json' )

class StyleResource(AbstractResource):
    pass

class SpatialResource(AbstractResource):

    def __init__(self):
        super(SpatialResource, self).__init__()
        self.iri_style = None

    def get_geometry_object(self, object_model):
        return getattr(object_model, self.geometry_field_name(), None)

    def geometry_field_name(self):
        return self.serializer_class.Meta.geo_field

    def make_geometrycollection_from_featurecollection(self, feature_collection):
        geoms = []
        features = json.loads(feature_collection)
        for feature in features['features']:
            feature_geom = json.dumps(feature['geometry'])
            geoms.append(GEOSGeometry(feature_geom))
        return GeometryCollection(tuple(geoms))

    def all_parameters_converted(self, attribute_or_function_name, parameters):
        parameters_converted = []
        if self.is_operation_and_has_parameters(attribute_or_function_name):
            parameters_type = self.operations_with_parameters_type()[attribute_or_function_name].parameters
            for i in range(0, len(parameters)):
                if GEOSGeometry == parameters_type[i]:
                    if not (parameters[i][0] == '{' or parameters[i][0] == '['):
                        parameters_converted.append(GEOSGeometry(parameters[i]))

                    else:
                        geometry_dict = json.loads(parameters[i])

                        if isinstance(geometry_dict, dict) and geometry_dict['type'].lower() == 'feature':
                            parameters_converted.append(parameters_type[i](json.dumps(geometry_dict['geometry'])))
                        elif isinstance(geometry_dict, dict) and geometry_dict['type'].lower() == 'featurecollection':
                            geometry_collection = self.make_geometrycollection_from_featurecollection(parameters[i])
                            parameters_converted.append(parameters_type[i](geometry_collection))
                        else:
                            parameters_converted.append(parameters_type[i](parameters[i]))
                else:
                    parameters_converted.append(parameters_type[i](parameters[i]))


            return parameters_converted

        return self.parametersConverted(parameters)

    def _value_from_objectOLD(self, object, attribute_or_function_name, parameters):

        attribute_or_function_name_striped = attribute_or_function_name.strip()
        self.name_of_last_operation_executed = attribute_or_function_name_striped
        if len(parameters):
            params = self.all_parameters_converted(attribute_or_function_name_striped, parameters)
            return getattr(object, attribute_or_function_name_striped)(*params)

        return getattr(object, attribute_or_function_name_striped)

    def parametersConverted(self, params_as_array):
        paramsConveted = []

        for value in params_as_array:
            if value.lower() == 'true':
                paramsConveted.append(True)
                continue
            elif value.lower() == 'false':
                paramsConveted.append(False)
                continue

            try:
                paramsConveted.append(int( value ) )
                continue
            except ValueError:
                pass
            try:
               paramsConveted.append( float( value ) )
               continue
            except ValueError:
                pass
            try:
               paramsConveted.append( GEOSGeometry( value ) )
               continue
            except ValueError:
                pass
            try:
                http_str = (value[0:4]).lower()
                if (http_str == 'http'):
                    resp = requests.get(value)
                    if 400 <= resp.status_code <= 599:
                        raise HTTPError({resp.status_code: resp.reason})
                    js = resp.json()

                    if (js.get("type") and js["type"].lower() in ['feature', 'featurecollection']):
                        a_geom = js["geometry"]
                    else:
                        a_geom = js
                    paramsConveted.append(GEOSGeometry((json.dumps(a_geom))))
            except (ConnectionError,  HTTPError) as err:
                print('Error: '.format(err))
                #paramsConveted.append (value)

        return paramsConveted

    def dict_as_geojson(self, a_dict):
        d = {}
        d["type"] = "Feature"
        d["geometry"] = a_dict[self.geometry_field_name()]
        a_dict.pop(self.geometry_field_name(), None)
        d["properties"] = a_dict
        return d

    def response_resquest_with_attributes(self,  attributes_functions_name):
        a_dict ={}
        attributes = attributes_functions_name.strip().split(',')

        #self.current_object = self.object_model
        for attr_name in attributes:
           obj = self._value_from_object(self.object_model, attr_name, [])
           if isinstance(obj, GEOSGeometry):
               geom = obj
               obj = json.loads(obj.geojson)
               if len(attributes) == 1:
                   return (obj, 'application/vnd.geo+json', geom, {'status': 200})
           a_dict[attr_name] = obj
        if self.geometry_field_name() in attributes:
            a_dict = self.dict_as_geojson(a_dict)
        self.current_object_state = a_dict

        return (a_dict, 'application/json', self.object_model, {'status': 200})

    def response_request_attributes_functions_str_with_url(self, attributes_functions_str):
        attributes_functions_str = re.sub(r':/+', '://', attributes_functions_str)
        arr_of_two_url = self.attributes_functions_splitted_by_url(attributes_functions_str)
        resp = requests.get(arr_of_two_url[1])
        if resp.status_code in[400, 401, 404]:
            return ({},'application/json', self.object_model, {'status': resp.status_code})
        if resp.status_code == 500:
            return ({},'application/json', self.object_model,{'status': resp.status_code})
        j = resp.text
        attributes_functions_str = arr_of_two_url[0] + j

        return self.response_of_request(attributes_functions_str)

    def response_of_request(self,  attributes_functions_str):
        att_funcs = attributes_functions_str.split('/')

        #obj = self.get_geometry_object(self.object_model)

       # if (not self.is_operation(att_funcs[0])) and self.is_attribute(att_funcs[0]):
        #    att_funcs = att_funcs[1:]

        self.current_object_state = self._execute_attribute_or_method(self.object_model, att_funcs[0], att_funcs[1:])
        a_value = self.current_object_state
        if isinstance(a_value, GEOSGeometry):
            geom = a_value
            a_value = json.loads(a_value.geojson)
            return (a_value, 'application/vnd.geo+json', geom, {'status': 200})
        elif isinstance(a_value, SpatialReference):
           a_value = { self.name_of_last_operation_executed: a_value.pretty_wkt}
        elif isinstance(a_value, memoryview):
            return (a_value, 'application/octet-stream', self.object_model, {'status': 200})
        else:
            a_value = {self.name_of_last_operation_executed: a_value}

        return (a_value, 'application/json', self.object_model, {'status': 200})

class FeatureResource(SpatialResource):

    def __init__(self):
        super(FeatureResource, self).__init__()

    # Must be override
    def initialize_context(self):
        pass

    def is_spatial_attribute(self, attribute_name):
        return self.model.geo_field_name() == attribute_name.lower()

    def operations_with_parameters_type(self):

        dic = self.object_model.operations_with_parameters_type()

        return dic

    def basic_get(self, request, *args, **kwargs):

        self.object_model = self.get_object(kwargs)
        self.current_object_state = self.object_model
        self.set_basic_context_resource(request)
        # self.request.query_params.
        attributes_functions_str = kwargs.get(self.attributes_functions_name_template())

        if self.is_simple_path(attributes_functions_str):
            serializer = self.serializer_class(self.object_model)
            output = (serializer.data, 'application/vnd.geo+json', self.object_model, {'status': 200})

        elif self.path_has_only_attributes(attributes_functions_str):
            output = self.response_resquest_with_attributes(attributes_functions_str.replace(" ", ""))
            dict_attribute = output[0]
            att_names = attributes_functions_str.split(',')
            if len(att_names) > 1:
                self._set_context_to_attributes(att_names)
            else:
                self._set_context_to_only_one_attribute(attributes_functions_str)
        elif self.path_has_url(attributes_functions_str.lower()):
            output = self.response_request_attributes_functions_str_with_url( attributes_functions_str)
            self.context_resource.set_context_to_object(self.current_object_state, self.name_of_last_operation_executed)
        else:
            s = str(attributes_functions_str)
            if s[-1] == '/':
               s = s[:-1]
            output = self.response_of_request(s)
            self._set_context_to_operation(self.name_of_last_operation_executed)

        return output

    def get(self, request, *args, **kwargs):

        dict_for_response = self.basic_get(request, *args, **kwargs)
        status = dict_for_response[3]['status']
        if status in [400, 401,404]:
            return Response({'Error ': 'The request has problem. Status:' + str(status)}, status=status)

        if status in [500]:
           return Response({'Error ': 'The server can not process this request. Status:' + str(status)}, status=status)
        if 'HTTP_ACCEPT'  not in request.META:
            request.META['HTTP_ACCEPT'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8'
        accept = request.META['HTTP_ACCEPT']
        if accept.lower() == "image/png" or kwargs.get('format', None) == 'png':
            if len(dict_for_response) == 3:
                queryset = dict_for_response[2]
                image = self.get_png(queryset, request)
                # headers = response._headers
                return HttpResponse(image, content_type="image/png")
                # headers.update(response._headers)
                # response._headers = headers
            else:
                return Response({'Erro': 'The server can generate an image only from a geometry data'},
                                status=status.HTTP_404_NOT_FOUND)
        if dict_for_response[1] =='application/octet-stream':
            return HttpResponse(dict_for_response[0], content_type='application/octet-stream')
        return Response(data=dict_for_response[0], content_type=dict_for_response[1])

    def options(self, request, *args, **kwargs):
        self.basic_get(request, *args, **kwargs)
        #return self.context_resource.context()
        return Response ( data=self.context_resource.context(), content_type='application/ld+json' )

class AbstractCollectionResource(AbstractResource):
    def __init__(self):
        super(AbstractCollectionResource, self).__init__()
        self.queryset = None


    def token_is_http_or_https(self, token):
        return  token.lower() in ['http:', 'https:']

    def token_is_http(self, token):
        return 'http:' == token

    def token_is_https(self, token):
        return 'https:' == token

    def token_is_www(self, token):
        return True if token.find('www.') > -1 else False

    def token_is_http_or_https_or_www(self, token):
        return  self.token_is_http_or_https(token) or self.token_is_www(token)

    def logical_operators(self):
        return FactoryComplexQuery().logical_operators()

    def attributes_functions_str_is_filter_with_spatial_operation(self, attributes_functions_str):

        arr_str = attributes_functions_str.split('/')[1:]

        geom_ops = self.operation_controller.geometry_operations_dict()

        for str in arr_str:
            if self.is_spatial_attribute(str):
              ind = arr_str.index(str)
              if ind +1 <= len(arr_str):
                return arr_str[ind + 1] in geom_ops()

        return False

    def path_has_filter_operation(self, attributes_functions_str):
        att_funcs = attributes_functions_str.split('/')
        return len(att_funcs) > 1 and  (att_funcs[0].lower() == 'filter')

    def path_has_map_operation(self, attributes_functions_str):
        att_funcs = attributes_functions_str.split('/')
        return len(att_funcs) > 1 and (att_funcs[0].lower() == 'map')


    def q_object_for_filter_array_of_terms(self, array_of_terms):
        return FactoryComplexQuery().q_object_for_filter_expression(None, self.model_class(), array_of_terms)

    def q_object_for_filter_expression(self, attributes_functions_str):
        arr = attributes_functions_str.split('/')

        if self.path_has_url(attributes_functions_str):
           arr = self.transform_path_with_url_as_array(arr)

        return self.q_object_for_filter_array_of_terms(arr[1:])

    def get_objects_from_filter_operation(self, attributes_functions_str):
        q_object = self.q_object_for_filter_expression(attributes_functions_str)
        return self.model_class().objects.filter(q_object)

    def get_objects_from_map_operation(self, attributes_functions_str):
        q_object = self.q_object_for_filter_expression(attributes_functions_str)
        return self.model_class().objects.filter(q_object)

    def operation_names_model(self):
        return self.operation_controller.collection_operations_dict()

    def get(self, request, *args, **kwargs):

        response = self.basic_get(request, *args, **kwargs)
        self.add_base_headers(request, response)
        return response

    def basic_options(self, request, *args, **kwargs):
        self.object_model = self.model_class()()
        self.set_basic_context_resource(request)
        attributes_functions_str = self.kwargs.get("attributes_functions", None)

        if self.is_simple_path(attributes_functions_str):  # to get query parameters
            return {"data": {},"status": 200, "content_type": "application/json"}

        elif self.path_has_only_attributes(attributes_functions_str):
            output = self.response_resquest_with_attributes(attributes_functions_str.replace(" ", ""))
            dict_attribute = output[0]
            if len(attributes_functions_str.split(',')) > 1:
                self._set_context_to_attributes(dict_attribute.keys())
            else:
                self._set_context_to_only_one_attribute(attributes_functions_str)
            return {"data": {},"status": 200, "content_type": "application/json"}

        #elif self.path_has_url(attributes_functions_str.lower()):
        #    pass
        elif self.path_has_only_spatial_operation(attributes_functions_str):
            return {"data": self.get_objects_with_spatial_operation_serialized(attributes_functions_str), "status": 200,
                    "content_type": "application/json"}

        elif self.path_has_operations(attributes_functions_str) and self.path_request_is_ok(attributes_functions_str):
            return {"data": self.get_objects_serialized_by_functions(attributes_functions_str),"status": 200, "content_type": "application/json"}

        else:
            return {"data": "This request has invalid attribute or operation","status": 400, "content_type": "application/json"}

    def options(self, request, *args, **kwargs):
        self.basic_options(request, *args, **kwargs)
        #return self.context_resource.context()
        return Response ( data=self.context_resource.context(), content_type='application/ld+json' )

    def basic_post(self, request):
        response =  Response(status=status.HTTP_201_CREATED, content_type='application/json')
        response['Content-Location'] = request.path + str(self.object_model.pk)
        return response

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        if serializer.is_valid():
            obj =  serializer.save()
            self.object_model = obj
            return self.basic_post(request)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CollectionResource(AbstractCollectionResource):

    def operations_with_parameters_type(self):
        return self.operation_controller.collection_operations_dict()



    def get_objects_serialized(self):
        objects = self.model_class().objects.all()
        return self.serializer_class(objects, many=True, context={'request': self.request}).data

    def get_objects_by_only_attributes(self, attribute_names_str):
        arr = []
        attribute_names_str_as_array = attribute_names_str.split(',')

        return self.model_class().objects.values(*attribute_names_str_as_array)

    def get_objects_serialized_by_only_attributes(self, attribute_names_str, query_set):
        arr = []
        attribute_names_str_as_array = attribute_names_str.split(',')
        for obj in query_set:
            a_dic = {}
            for att_name in attribute_names_str_as_array:
                a_dic[att_name] = obj[att_name]
                arr.append(a_dic)
        return arr

    def get_objects_by_functions(self, attributes_functions_str):

        objects = []
        if self.path_has_filter_operation(attributes_functions_str):
            objects = self.get_objects_from_filter_operation(attributes_functions_str)
        return objects

    def basic_get(self, request, *args, **kwargs):
        self.object_model = self.model_class()()
        self.set_basic_context_resource(request)
        attributes_functions_str = self.kwargs.get("attributes_functions", None)

        if self.is_simple_path(attributes_functions_str):  # to get query parameters
            objects = self.model_class().objects.all()
            serialized_data =  self.serializer_class(objects, many=True, context={'request': request})#.data
            resp =  Response(data= serialized_data.data,status=200, content_type="application/json")
            #self.add_key_value_in_header(resp, 'Etag', str(hash(objects)))
            self.add_key_value_in_header(resp, 'Etag', encode(objects))
            return resp

        elif self.path_has_only_attributes(attributes_functions_str):
            query_set = self.get_objects_by_only_attributes(attributes_functions_str)
            serialized_data = self.get_objects_serialized_by_only_attributes(attributes_functions_str, query_set)
            resp =  Response(data= serialized_data,status=200, content_type="application/json")
            #self.add_key_value_in_header(resp, 'Etag', str(hash(query_set)))
            self.add_key_value_in_header(resp, 'Etag', encode(query_set))
            return resp

        elif self.path_has_operations(attributes_functions_str) and self.path_request_is_ok(attributes_functions_str):
            objects = self.get_objects_by_functions(attributes_functions_str)
            serialized_data = self.serializer_class(objects, many=True).data
            resp =  Response(data= serialized_data,status=200, content_type="application/json")
            # self.add_key_value_in_header(resp, 'Etag', str(hash(objects)))
            self.add_key_value_in_header(resp, 'Etag', encode(objects))
            return resp

        else:

            return Response(data="This request has invalid attribute or operation", status=400, content_type="application/json")

class SpatialCollectionResource(AbstractCollectionResource):

    #To do
    def path_request_is_ok(self, attributes_functions_str):
        return True

    def geometry_field_name(self):
        return self.serializer_class.Meta.geo_field

    def operation_names_model(self):
        return self.operation_controller.feature_collection_operations_dict().keys()

    def path_has_only_spatial_operation(self, attributes_functions_str):
        pass

class FeatureCollectionResource(SpatialCollectionResource):

    def geometry_operations(self):
        return self.operation_controller.geometry_operations_dict()

    def geometry_field_name(self):
        return self.serializer_class.Meta.geo_field

    def is_spatial_attribute(self, attribute_name):
        return attribute_name == self.geometry_field_name()

    def is_spatial_operation(self, operation_name):
        return operation_name in self.geometry_operations()

    def path_has_only_spatial_operation(self, attributes_functions_str):

        att_funcs = attributes_functions_str.split('/')
        spatial_operation_names = self.geometry_operations().keys()

        if (len(att_funcs) > 1 and (att_funcs[0].lower() in spatial_operation_names)):
           return True

        return  (att_funcs[1].lower() in spatial_operation_names)

    def is_filter_with_spatial_operation(self, attributes_functions_str):
        att_funcs = attributes_functions_str.split('/')
        return (len(att_funcs) > 1 and (att_funcs[0].lower() in self.geometry_operations().keys())) or self.attributes_functions_str_is_filter_with_spatial_operation(attributes_functions_str)

    def operations_with_parameters_type(self):
        return self.operation_controller.feature_collection_operations_dict()

    def get_serialized(self, objects):
          return self.serializer_class(objects, many=True).data

    def get_objects_serialized(self):
        objects = self.model_class().objects.all()
        return self.serializer_class(objects, many=True).data

    def get_objects_from_spatial_operation(self, array_of_terms):
        q_object = self.q_object_for_filter_array_of_terms(array_of_terms)
        return self.model_class().objects.filter(q_object)

    def is_end_of_term(self, term):
        return term in self.logical_operators()

    def inject_geometry_attribute_in_spatial_operation_for_path(self, arr_of_term):
        indexes = []
        for idx, term in enumerate(arr_of_term):
            if term in self.geometry_operations():
                indexes.append(idx)
        count = 0
        for i in indexes:
            arr_of_term.insert(i + count, self.geometry_field_name())
            count+=1

        return arr_of_term

    def path_has_geometry_attribute(self, term_of_path):
        return term_of_path.lower() == self.geometry_field_name()

    def get_objects_with_spatial_operation(self, attributes_functions_str):
        att_func_arr = attributes_functions_str.split('/')
        arr = att_func_arr
        if self.is_spatial_operation(att_func_arr[0]) and not self.path_has_geometry_attribute(att_func_arr[0]):
            if self.path_has_url(attributes_functions_str):
                arr = self.transform_path_with_url_as_array(att_func_arr)
            arr = self.inject_geometry_attribute_in_spatial_operation_for_path(arr)
        return self.get_objects_from_spatial_operation(arr)

    def get_objects_by_only_attributes(self, attribute_names_str):
        arr = []
        attribute_names_str_as_array = attribute_names_str.split(',')
        return self.model_class().objects.values(*attribute_names_str_as_array)

    def get_objects_serialized_by_only_attributes(self, attribute_names_str, objects):
        arr = []
        attribute_names_str_as_array = attribute_names_str.split(',')
        for dic in objects:
            a_dic = {}
            for att_name in attribute_names_str_as_array:
                a_dic[att_name] = dic[att_name] if not isinstance(dic[att_name], GEOSGeometry) else json.loads(dic[att_name].json)
                arr.append(a_dic)
        return arr

    def get_objects_by_functions(self, attributes_functions_str):

        objects = []
        if self.path_has_filter_operation(attributes_functions_str) or self.path_has_spatial_operation(attributes_functions_str) or  self.is_filter_with_spatial_operation(attributes_functions_str):
            objects = self.get_objects_from_filter_operation(attributes_functions_str)
        elif self.path_has_map_operation(attributes_functions_str):
            objects = self.get_objects_from_map_operation(attributes_functions_str)

        return objects

    def basic_response(self, request, model_object):
        response = Response(status=status.HTTP_201_CREATED, content_type='application/geojson')
        response['Content-Location'] = request.path + str(model_object.id)
        return response

    def basic_get(self, request, *args, **kwargs):
        self.object_model = self.model_class()()
        self.set_basic_context_resource(request)
        attributes_functions_str = self.kwargs.get("attributes_functions", None)

        if self.is_simple_path(attributes_functions_str):  # to get query parameters
            objects = self.model_class().objects.all()
            serialized_data =  self.serializer_class(objects, many=True).data
            resp =  Response(data= serialized_data,status=200, content_type="application/json")
            self.add_key_value_in_header(resp, 'Etag', str(hash(objects)))
            return resp

        elif self.path_has_only_attributes(attributes_functions_str):
            objects = self.get_objects_by_only_attributes(attributes_functions_str)
            serialized_data = self.get_objects_serialized_by_only_attributes(attributes_functions_str, objects)
            resp =  Response(data= serialized_data,status=200, content_type="application/json")
            self.add_key_value_in_header(resp, 'Etag', str(hash(objects)))
            return resp

        #elif self.path_has_url(attributes_functions_str.lower()):
        #    pass
        elif self.path_has_only_spatial_operation(attributes_functions_str):
            objects = self.get_objects_with_spatial_operation(attributes_functions_str)
            serialized_data = self.serializer_class(objects, many=True).data
            resp =  Response(data= serialized_data,status=200, content_type="application/json")
            self.add_key_value_in_header(resp, 'Etag', str(hash(objects)))
            return resp


        elif self.path_has_operations(attributes_functions_str) and self.path_request_is_ok(attributes_functions_str):
            objects = self.get_objects_by_functions(attributes_functions_str)
            serialized_data = self.serializer_class(objects, many=True).data
            resp =  Response(data= serialized_data,status=200, content_type="application/json")
            self.add_key_value_in_header(resp, 'Etag', str(hash(objects)))
            return resp


        else:
            return Response(data="This request has invalid attribute or operation", status=400, content_type="application/json")


