import inspect, sys
import os
import re
import django


def convert_camel_case_to_hifen(camel_case_string):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1-\2', camel_case_string)
    return re.sub('([a-z0-9])([A-Z])', r'\1-\2', s1).lower()

def detect_primary_key_field(fields_of_model_class):
    return next((field for field in fields_of_model_class if field.primary_key), [None])

def generate_snippets_to_url(model_class_name, model_class):

    #class MunicipioContext(FeatureContext):
    #   pass

    arr = []
    arr.append('class ' + model_class_name + 'DetailContext(FeatureContext):' + '\n')
    arr.append((' ' * 4) + 'pass\n')
    arr.append('class ' + model_class_name + 'ListContext(FeatureCollectionContext):' + '\n')
    arr.append((' ' * 4) + 'pass\n')
    return arr

def imports_str_as_array():
    arr = []
    arr.append("from hyper_resource.contexts import FeatureContext, FeatureCollectionContext\n")
    return arr

def generate_file(package_name, default_name='contexts.py'):

    classes_from = [(name, method) for name, method in  inspect.getmembers(sys.modules[package_name + '.models'],inspect.isclass)  if (name != 'BusinessModel' and name != 'FeatureModel' and isinstance(method, django.db.models.base.ModelBase)) ]
    with open(default_name, 'w+') as sr:
        for import_str in imports_str_as_array():
            sr.write(import_str)

        for model_class_arr in classes_from:
            for str in generate_snippets_to_url(model_class_arr[0], model_class_arr[1]):
                sr.write(str)
            sr.write('\n')

        sr.close()

if __name__ == "__main__":
    if (len( sys.argv))!= 3:
        print('Usage: python contexter_generator.py django_project_name django_app_name')
        exit()

    prj_name = sys.argv[1]
    app_name = sys.argv[2]
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", prj_name + ".settings")
    django.setup()
    generate_file(app_name)
    print('contexts.py  has been generated')