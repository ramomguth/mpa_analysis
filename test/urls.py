from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    #path('<int:question_id>/results/', views.results, name='results'),
    path('results/', views.results, name='results'),
    path('backend_test', views.backend_test, name='backend_test'),
    path('graph_test/', views.graph_test, name='graph_test'),
    path('get_graph_data/', views.get_graph_data, name='get_graph_data'),
    path('login/', views.login_user, name='login_user'),
    path('register/', views.register, name='register'),
    path('logout/', views.logout_view, name='logout_view'),
    path('create_project/', views.create_project, name='create_project'),
    path('scraper/', views.scraper, name='scraper'),
    path('set_project', views.set_project, name='set_project'),
    path('mpa/', views.mpa, name='mpa'),
    path('get_mpa_data/', views.get_mpa_data, name='get_mpa_data'),
]