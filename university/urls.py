from django.conf.urls import include, url
urlpatterns = [

    url(r'^adm-list/',include('adm.urls',namespace='adm')),


]
urlpatterns += [

    url(r'^api-auth/', include('rest_framework.urls',namespace='rest_framework')),

]


