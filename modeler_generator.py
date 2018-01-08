import inspect, sys
import os
import re
import django

from django.contrib.gis.db.models.fields import GeometryField
from django.contrib.gis.db import models
from hyper_resource.models import FeatureModel


def is_spatial(model_class):
    if isinstance(model_class, models.Model) or isinstance(model_class, FeatureModel):
        for field in model_class._meta.get_fields():
            if isinstance(field, GeometryField):
                return True
    return False

def generate_file(package_name, default_name='models.py'):

    classes_from = inspect.getmembers(sys.modules[package_name + '.models'], inspect.isclass)
    geo_classes = map(lambda x: x[0], filter(lambda x: is_spatial(x[1]), classes_from))
    old_model = default_name
    new_model = default_name+'.new'
    with open(old_model, 'r') as sr:
        with open(new_model, 'w+') as nm:
            nm.write('from __future__ import unicode_literals\n')
            nm.write('from hyper_resource.models import FeatureModel, BusinessModel\n')
            for line in sr.readlines():
                if line == 'from __future__ import unicode_literals\n':
                    continue
                regex_obj = re.search(r'class\s*(?P<class_model>.*)\(', line)
                class_name_in_line = regex_obj if regex_obj is None else regex_obj.group(1)
                if class_name_in_line in geo_classes:
                    line = line.replace('models.Model', 'FeatureModel')
                elif class_name_in_line is not None:
                    line = line.replace('models.Model', 'BusinessModel')
                elif 'models.IntegerField(primary_key=True)' in line:
                    line = line.replace('models.IntegerField(primary_key=True)', 'models.AutoField(primary_key=True)')
                nm.write(line)
            nm.close()
        sr.close()
    os.remove(old_model)
    os.rename(new_model, old_model)


if __name__ == "__main__":
    if (len( sys.argv))!= 3:
        print('Usage: python modeler_generator.py django_project_name django_app_name')
        exit()

    prj_name = sys.argv[1]
    app_name = sys.argv[2]
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", prj_name + ".settings")
    django.setup()
    generate_file(app_name)
    print('models.py  has been generated')