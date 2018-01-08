from adm.models import *
from hyper_resource.serializers import *
from rest_framework_gis.serializers import GeoFeatureModelSerializer

from rest_framework.serializers import HyperlinkedRelatedField

class AlunoSerializer(BusinessSerializer):
    id_curso = HyperlinkedRelatedField(view_name='adm:Curso_detail', many=False, read_only=True)
    class Meta:
        model = Aluno
        fields = ['id_aluno','matricula','nome','id_curso']
        identifier = 'id_aluno'
        identifiers = ['pk', 'id_aluno']

    def field_relationship_to_validate_dict(self):
        a_dict = {}
        a_dict['id_curso_id'] = 'id_curso'
        return a_dict

class CursoSerializer(BusinessSerializer):
    alunos = HyperlinkedRelatedField(view_name='adm:Aluno_detail', many=True, read_only=True)
    class Meta:
        model = Curso
        fields = ['id_curso','codigo','nome', 'alunos']
        identifier = 'id_curso'
        identifiers = ['pk', 'id_curso']

class CursoDisciplinaSerializer(BusinessSerializer):
    id_curso = HyperlinkedRelatedField(view_name='adm:Curso_detail', many=False, read_only=True)
    id_disciplina = HyperlinkedRelatedField(view_name='adm:Disciplina_detail', many=False, read_only=True)
    class Meta:
        model = CursoDisciplina
        fields = ['id_curso_disciplina','id_curso','id_disciplina']
        identifier = 'id_curso_disciplina'
        identifiers = ['pk', 'id_curso_disciplina']

    def field_relationship_to_validate_dict(self):
        a_dict = {}
        a_dict['id_curso_id'] = 'id_curso'
        a_dict['id_disciplina_id'] = 'id_disciplina'
        return a_dict

class DisciplinaSerializer(BusinessSerializer):
    class Meta:
        model = Disciplina
        fields = ['id_disciplina','codigo','nome']
        identifier = 'id_disciplina'
        identifiers = ['pk', 'id_disciplina']



serializers_dict = {}