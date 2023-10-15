from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('alert_and_redirect/', views.alert_and_redirect, name='alert_and_redirect'),
    path('similarities/', views.similarities, name='similarities'),
    path('save_similarities', views.save_similarities, name='save_similarities'),
    path('finish_similarities', views.finish_similarities, name='finish_similarities'),
    #path('graph_test/', views.graph_test, name='graph_test'),
    path('login/', views.login_user, name='login_user'),
    path('register/', views.register, name='register'),
    path('logout/', views.logout_view, name='logout_view'),
    path('create_project/', views.create_project, name='create_project'),
    path('delete_project/', views.delete_project, name='delete_project'),
    path('scraper/', views.scraper, name='scraper'),
    path('import/', views.import_csv, name='import_csv'),
    path('set_project', views.set_project, name='set_project'),
    path('mpa/', views.mpa, name='mpa'),
    path('infos/', views.infos, name='infos'),
    #path('get_mpa_data/', views.get_mpa_data, name='get_mpa_data'),
]