from django.urls import path
from . import views

urlpatterns = [
    path('', views.google_home),
    path('google_signout/', views.google_signout, name='google_signout'),
    path('get_shopify_data/', views.get_shopify_data, name='get_shopify_data'),
    path('get_shopify_order/', views.get_shopify_order, name='get_shopify_order'),
    path('get_shopify_product/', views.get_shopify_product,
         name='get_shopify_product'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('download_shopify_csv/', views.download_shopify_csv, name='shopify_csv'),
    path('google_spreadsheet/', views.google_spreadsheet,
         name='google_spreadsheet'),
    path('google_authenticate/', views.google_authenticate,
         name='google_authenticate'),
    path('google_auth_callback/', views.google_auth_callback,
         name='google_auth_callback'),

]
