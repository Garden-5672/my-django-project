from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('select-free/<int:tool_id>/', views.select_free_tool, name='select_free_tool'),
    path('run/<int:tool_id>/', views.run_tool, name='run_tool'),
    path('complete-payment/', views.complete_payment, name='complete_payment'),
    path('board/', views.board_list, name='board_list'),
    path('inquiry/', views.inquiry_list, name='inquiry_list'),
]