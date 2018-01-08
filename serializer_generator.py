import os
import sys, inspect
import django
from django.contrib.gis.db import models
from django.contrib.gis.db.models import GeometryField
from django.db.models import ForeignKey, ManyToOneRel

from django.contrib.gis.db.models.fields import GeometryField

from hyper_resource.models import FeatureModel


def is_spatial(model_class):
    if isinstance(model_class, models.Model) or isinstance(model_class, FeatureModel):
        for field in model_class._meta.get_fields():
            if isinstance(field, GeometryField):
                return True

    return False
def generate_snippet_field_relationship_to_validate_dict(field_names):
    new_str = ''
    new_str = (" " * 4) + "def field_relationship_to_validate_dict(self):\n"
    new_str += (' ' * 8) + "a_dict = {}\n"
    for field_name in field_names:
         new_str += (" " * 8) + "a_dict[" + "'" +field_name + '_id' +"'] = " + "'" + field_name + "'\n"
    new_str += (" " * 8) + "return a_dict\n"
    return new_str

def generate_snippets_to_serializer(package_name, model_class_name, model_class):
    arr = []
    field_names_fk = []
    if is_spatial(model_class):
        class_name = 'Serializer(GeoBusinessSerializer)'
    else:
        class_name = 'Serializer(BusinessSerializer)'
    arr.append('class ' +model_class_name + class_name+':\n')
    for field in model_class._meta.get_fields():
        if isinstance(field, ForeignKey):
            field_names_fk.append(field.name)
            view_name = type(field.related_model()).__name__ + "_detail"
            arr.append((' ' * 4) + field.name+" = HyperlinkedRelatedField(view_name='"+package_name +':'+view_name+"', many=False, read_only=True)\n")
        elif isinstance(field, ManyToOneRel) and field.related_name is not None:
            view_name = type(field.related_model()).__name__ + "_detail" #view_name = field.name + "_detail"
            arr.append((
                       ' ' * 4) + field.name + " = HyperlinkedRelatedField(view_name='" +package_name +':'+ view_name + "', many=True, read_only=True)\n")
    arr.append((' ' * 4) + 'class Meta:\n')
    arr.append((' ' * 8) + 'model = ' +model_class_name + '\n')
    identifier = None
    geom = None
    fields = model_class._meta.get_fields()
    arr.append((' ' * 8) + 'fields = [')
    for i, field in enumerate(fields):
        if isinstance(field, ManyToOneRel) and field.related_name is None:
            continue
        arr.append("'" + field.name + "'")
        if i < len(fields) - 1:
            arr.append(',')
        else:
            arr.append(']\n')
        if hasattr(field, 'primary_key') and field.primary_key:
            identifier = field.name
        if isinstance(field, GeometryField):
            geom = field.name
    if geom is not None:
        arr.append((' ' * 8) + "geo_field = '" + geom + "'\n")
    arr.append((' ' * 8) + "identifier = '" + identifier + "'\n")
    arr.append((' ' * 8) + "identifiers = ['pk', " + "'" + identifier + "'"+ "]\n")
    if len(field_names_fk) > 0:
        arr.append("\n")
        arr.append(generate_snippet_field_relationship_to_validate_dict(field_names_fk))
    arr.append("\n")
    return arr

def generate_file(package_name, default_name= '\serializers.py'):

    classes_from = [(name, method) for name, method in  inspect.getmembers(sys.modules[package_name + '.models'],inspect.isclass)  if (name != 'BusinessModel' and name != 'FeatureModel' and isinstance(method, django.db.models.base.ModelBase)) ]

    with open(default_name, 'w+') as sr:
        sr.write("from "+package_name+".models import *\n")
        sr.write("from hyper_resource.serializers import *\n")
        sr.write("from rest_framework_gis.serializers import GeoFeatureModelSerializer\n\n")
        sr.write("from rest_framework.serializers import HyperlinkedRelatedField\n\n")

        for model_class_arr in classes_from:
            for snippet in generate_snippets_to_serializer(package_name, model_class_arr[0], model_class_arr[1]):
                sr.write(snippet)
        sr.write('\n\n')
        sr.write('serializers_dict = {}')
        sr.close()

if __name__ == "__main__":
    if (len(sys.argv)) != 3:
        print('Usage: python serializer_generator.py django_project_name django_app_name')
        exit()
    prj_name = sys.argv[1]
    app_name = sys.argv[2]
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", prj_name + ".settings")
    django.setup()
    generate_file(app_name)
    print('serializers.py  has been generated')