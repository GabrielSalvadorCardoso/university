from collections import OrderedDict
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView
from rest_framework import permissions
from rest_framework import generics
from rest_framework import status
from hyper_resource.views import *
from adm.models import *
from adm.serializers import *
from adm.contexts import *

def get_root_response(request):
    format = None
    root_links = {

      'aluno-list': reverse('adm:Aluno_list' , request=request, format=format),
      'curso-list': reverse('adm:Curso_list' , request=request, format=format),
      'curso-disciplina-list': reverse('adm:CursoDisciplina_list' , request=request, format=format),
      'disciplina-list': reverse('adm:Disciplina_list' , request=request, format=format),
    }

    ordered_dict_of_link = OrderedDict(sorted(root_links.items(), key=lambda t: t[0]))
    return ordered_dict_of_link

class APIRoot(APIView):

    def __init__(self):
        super(APIRoot, self).__init__()
        self.base_context = BaseContext('api-root')

    def options(self, request, *args, **kwargs):
        context = self.base_context.getContextData(request)
        root_links = get_root_response(request)
        context.update(root_links)
        response = Response(context, status=status.HTTP_200_OK, content_type="application/ld+json")
        response = self.base_context.addContext(request, response)
        return response

    def get(self, request, *args, **kwargs):
        root_links = get_root_response(request)
        response = Response(root_links)
        return self.base_context.addContext(request, response)

class AlunoList(CollectionResource):
    queryset = Aluno.objects.all()
    serializer_class = AlunoSerializer
    contextclassname = 'aluno-list'
    def initialize_context(self):
        self.context_resource = AlunoListContext()
        self.context_resource.resource = self

class AlunoDetail(NonSpatialResource):
    serializer_class = AlunoSerializer
    contextclassname = 'aluno-list'
    def initialize_context(self):
        self.context_resource = AlunoDetailContext()
        self.context_resource.resource = self

class CursoList(CollectionResource):
    queryset = Curso.objects.all()
    serializer_class = CursoSerializer
    contextclassname = 'curso-list'
    def initialize_context(self):
        self.context_resource = CursoListContext()
        self.context_resource.resource = self

class CursoDetail(NonSpatialResource):
    serializer_class = CursoSerializer
    contextclassname = 'curso-list'
    def initialize_context(self):
        self.context_resource = CursoDetailContext()
        self.context_resource.resource = self

class CursoDisciplinaList(CollectionResource):
    queryset = CursoDisciplina.objects.all()
    serializer_class = CursoDisciplinaSerializer
    contextclassname = 'curso-disciplina-list'
    def initialize_context(self):
        self.context_resource = CursoDisciplinaListContext()
        self.context_resource.resource = self

class CursoDisciplinaDetail(NonSpatialResource):
    serializer_class = CursoDisciplinaSerializer
    contextclassname = 'curso-disciplina-list'
    def initialize_context(self):
        self.context_resource = CursoDisciplinaDetailContext()
        self.context_resource.resource = self

class DisciplinaList(CollectionResource):
    queryset = Disciplina.objects.all()
    serializer_class = DisciplinaSerializer
    contextclassname = 'disciplina-list'
    def initialize_context(self):
        self.context_resource = DisciplinaListContext()
        self.context_resource.resource = self

class DisciplinaDetail(NonSpatialResource):
    serializer_class = DisciplinaSerializer
    contextclassname = 'disciplina-list'
    def initialize_context(self):
        self.context_resource = DisciplinaDetailContext()
        self.context_resource.resource = self

