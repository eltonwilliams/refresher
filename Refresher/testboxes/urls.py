from django.conf.urls import url
from django.contrib.auth import views as auth_views
from django.urls import include, path
from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^selection/$', views.selection, name='selection'),
    url(r'^apply/$', views.apply, name='apply'),
    url(r'^progress_update/$', views.progress_update, name='ajax_progress'),
    url(r'^task_control/$', views.task_control, name='task_control'),
    url(r'^summary/$', views.summary, name='summary'),
   # url(r'^login/$', auth_views.login, name='login'),
   # url(r'^logout/$', auth_views.logout,{'template_name': 'dashboard.html'}, name='logout'),
    path('login', auth_views.LoginView.as_view(), {'template_name': 'login.html'}, name='login'),
    path('logout', auth_views.LogoutView.as_view(), {'next_page': '/'}, name='logout'),
    
]