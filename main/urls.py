from django.urls import path
from . import views

urlpatterns = [
    # 메인 페이지
    path('', views.index, name='index'),
    
    # 닉네임 설정
    path('set-nickname/', views.set_nickname, name='set_nickname'),
    
    # 도구 선택 / 가이드 / 실행 / 결제 연동
    path('tools/<int:tool_id>/select/', views.select_free_tool, name='select_free_tool'),
    path('tools/<int:tool_id>/guide/', views.tool_guide, name='tool_guide'),
    path('tools/<int:tool_id>/run/', views.run_tool, name='run_tool'),
    path('complete-payment/', views.complete_payment, name='complete_payment'),
    
    # 엑셀 다운로드 API
    path('tools/profit-flow/download/', views.profit_download_excel, name='profit_download'),
    path('download/template/', views.download_excel_template, name='download_excel_template'),
    
    # 커뮤니티 게시판
    path('board/', views.board_list, name='board_list'),
    path('board/create/', views.post_create, name='post_create'),
    path('board/<int:pk>/delete/', views.post_delete, name='post_delete'),
    
    # 1:1 문의 게시판
    path('inquiry/', views.inquiry_list, name='inquiry_list'),
    path('inquiry/create/', views.inquiry_create, name='inquiry_create'),
]