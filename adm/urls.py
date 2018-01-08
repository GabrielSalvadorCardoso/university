from django.conf.urls import include, url
from rest_framework.urlpatterns import format_suffix_patterns
from adm import views 

urlpatterns = format_suffix_patterns([
    url(r'^$', views.APIRoot.as_view(), name='api_root'),

    url(r'^aluno-list/(?P<pk>[0-9]+)/$', views.AlunoDetail.as_view(), name='Aluno_detail'),
    url(r'^aluno-list/(?P<pk>[0-9]+)/(?P<attributes_functions>.*)/$', views.AlunoDetail.as_view(), name='Aluno_detail_af'),
    url(r'^aluno-list/$', views.AlunoList.as_view(), name='Aluno_list'),
    url(r'^aluno-list/(?P<attributes_functions>.*)/?$', views.AlunoList.as_view(), name='Aluno_list_af'),

    url(r'^curso-list/(?P<pk>[0-9]+)/$', views.CursoDetail.as_view(), name='Curso_detail'),
    url(r'^curso-list/(?P<pk>[0-9]+)/(?P<attributes_functions>.*)/$', views.CursoDetail.as_view(), name='Curso_detail_af'),
    url(r'^curso-list/$', views.CursoList.as_view(), name='Curso_list'),
    url(r'^curso-list/(?P<attributes_functions>.*)/?$', views.CursoList.as_view(), name='Curso_list_af'),

    url(r'^curso-disciplina-list/(?P<pk>[0-9]+)/$', views.CursoDisciplinaDetail.as_view(), name='CursoDisciplina_detail'),
    url(r'^curso-disciplina-list/(?P<pk>[0-9]+)/(?P<attributes_functions>.*)/$', views.CursoDisciplinaDetail.as_view(), name='CursoDisciplina_detail_af'),
    url(r'^curso-disciplina-list/$', views.CursoDisciplinaList.as_view(), name='CursoDisciplina_list'),
    url(r'^curso-disciplina-list/(?P<attributes_functions>.*)/?$', views.CursoDisciplinaList.as_view(), name='CursoDisciplina_list_af'),

    url(r'^disciplina-list/(?P<pk>[0-9]+)/$', views.DisciplinaDetail.as_view(), name='Disciplina_detail'),
    url(r'^disciplina-list/(?P<pk>[0-9]+)/(?P<attributes_functions>.*)/$', views.DisciplinaDetail.as_view(), name='Disciplina_detail_af'),
    url(r'^disciplina-list/$', views.DisciplinaList.as_view(), name='Disciplina_list'),
    url(r'^disciplina-list/(?P<attributes_functions>.*)/?$', views.DisciplinaList.as_view(), name='Disciplina_list_af'),


])
