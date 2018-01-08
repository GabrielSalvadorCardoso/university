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

    context_name = convert_camel_case_to_hifen(model_class_name) + '-list'
    #primary_key_name = detect_primary_key_field(model_class._meta.get_fields()).name
    primary_key_name = 'pk'
    arr = []
    arr.append((' ' * 4) + 'url(r' +"'^"+  context_name +'/(?P<'+ primary_key_name +'>[0-9]+)/$' +"'"+ ', views.' +
               model_class_name + 'Detail.as_view(), name=' + "'" + model_class_name +'_detail' +"'" + '),\n')
    arr.append((' ' * 4) + 'url(r' + "'^" + context_name + '/(?P<' + primary_key_name +
               '>[0-9]+)/(?P<attributes_functions>.*)/$' + "'" + ', views.' +
               model_class_name + 'Detail.as_view(), name=' + "'" + model_class_name + '_detail_af' + "'" + '),\n')
    arr.append((' ' * 4) + 'url(r' + "'^" + context_name + '/$' + "'" + ', views.' +
               model_class_name + 'List.as_view(), name=' + "'" + model_class_name + '_list' + "'" + '),\n')
    arr.append((' ' * 4) + 'url(r' + "'^" + context_name + '/(?P<attributes_functions>.*)/?$' +
               "'" + ', views.' + model_class_name + 'List.as_view(), name=' + "'" + model_class_name + '_list_af' +
               "'" + '),\n')
    return arr

def imports_str_as_array(a_name):
    arr = []
    arr.append("from django.conf.urls import include, url\n")
    arr.append("from rest_framework.urlpatterns import format_suffix_patterns\n")
    arr.append("from " + a_name + " import views \n\n")
    return arr

def generate_file(package_name, default_name='urls.py'):
    classes_from = [(name, method) for name, method in  inspect.getmembers(sys.modules[package_name + '.models'],inspect.isclass)  if (name != 'BusinessModel' and name != 'FeatureModel' and isinstance(method, django.db.models.base.ModelBase)) ]
    with open(default_name, 'w+') as sr:
        for import_str in imports_str_as_array(package_name):
            sr.write(import_str)
        sr.write( 'urlpatterns = format_suffix_patterns([\n')
        sr.write((' ' * 4) + 'url(r' +"'"+'^$'+"'"+', views.APIRoot.as_view(), name='+"'"+'api_root'+"'"+'),\n\n')
        for model_class_arr in classes_from:
            for str in generate_snippets_to_url(model_class_arr[0], model_class_arr[1]):
                sr.write(str)
            sr.write('\n')
        sr.write('\n])\n')
        sr.close()

if __name__ == "__main__":
    if (len( sys.argv))!= 3:
        print('Usage: python viewer_generator.py django_project_name django_app_name')
        exit()

    prj_name = sys.argv[1]
    app_name = sys.argv[2]
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", prj_name + ".settings")
    django.setup()
    generate_file(app_name)
    print('urls.py  has been generated')