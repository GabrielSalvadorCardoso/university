from __future__ import unicode_literals
from hyper_resource.models import FeatureModel, BusinessModel
from hyper_resource.models import FeatureModel, BusinessModel
# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey has `on_delete` set to the desired behavior.
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.

from django.contrib.gis.db import models


class Aluno(BusinessModel):
    id_aluno = models.AutoField(primary_key=True)
    matricula = models.CharField(max_length=10)
    nome = models.CharField(max_length=200)
    id_curso = models.ForeignKey('Curso', models.DO_NOTHING, db_column='id_curso', related_name='alunos')

    class Meta:
        managed = False
        db_table = 'aluno'


class Curso(BusinessModel):
    id_curso = models.AutoField(primary_key=True)
    codigo = models.CharField(max_length=6)
    nome = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'curso'


class CursoDisciplina(BusinessModel):
    id_curso_disciplina = models.AutoField(primary_key=True)
    id_curso = models.ForeignKey(Curso, models.DO_NOTHING, db_column='id_curso')
    id_disciplina = models.ForeignKey('Disciplina', models.DO_NOTHING, db_column='id_disciplina')

    class Meta:
        managed = False
        db_table = 'curso_disciplina'


class Disciplina(BusinessModel):
    id_disciplina = models.AutoField(primary_key=True)
    codigo = models.CharField(max_length=6)
    nome = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'disciplina'
