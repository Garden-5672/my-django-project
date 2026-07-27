# main/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'), # 기본 루트 주소 ('') 접근 시 views.index 실행
]