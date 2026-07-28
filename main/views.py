from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import Tool, UserToolAccess
from .models import Post, Inquiry
import json

# 1. 메인 페이지 & 구매/선택 순위표
def index(request):
    tools = Tool.objects.all()
    top_tools = tools[:3] # 구매/선택 수 TOP 3 도구
    
    user_access = None
    free_tool = None
    paid_tool_ids = []

    if request.user.is_authenticated:
        user_access, created = UserToolAccess.objects.get_or_create(user=request.user)
        free_tool = user_access.free_selected_tool
        paid_tool_ids = list(user_access.paid_tools.values_list('id', flat=True))

    context = {
        'tools': tools,
        'top_tools': top_tools,
        'user_access': user_access,
        'free_tool': free_tool,
        'paid_tool_ids': paid_tool_ids,
    }
    return render(request, 'main/index.html', context)


# 2. 무료 도구 선택 처리 (구매 횟수 +1)
@login_required
def select_free_tool(request, tool_id):
    tool = get_object_or_404(Tool, id=tool_id)
    user_access, created = UserToolAccess.objects.get_or_create(user=request.user)

    if user_access.free_selected_tool is not None:
        messages.error(request, "이미 무료 도구를 선택하셨습니다! 다른 도구는 결제 후 이용 가능합니다.")
    else:
        user_access.free_selected_tool = tool
        user_access.save()
        
        # 💡 선택 횟수 증가 (순위표 반영)
        tool.purchase_count += 1
        tool.save()
        
        messages.success(request, f"'{tool.name}'이(가) 나만의 무료 도구로 등록되었습니다!")

    return redirect('index')


# 3. 도구 안내 및 비밀번호 제공 페이지 (권한 검증 필수!)
@login_required
def run_tool(request, tool_id):
    tool = get_object_or_404(Tool, id=tool_id)
    user_access, created = UserToolAccess.objects.get_or_create(user=request.user)

    # 접근 권한 체크 (무료 선택 도구 또는 결제한 도구인가?)
    is_free_match = (user_access.free_selected_tool == tool)
    is_paid_match = user_access.paid_tools.filter(id=tool.id).exists()

    if not (is_free_match or is_paid_match):
        messages.warning(request, "이 도구의 접속 정보를 보려면 먼저 해금(구매)해야 합니다.")
        return redirect('index')

    context = {
        'tool': tool,
    }
    return render(request, 'main/run_tool.html', context)

# main/views.py

# 💡 결제 완료 검증 및 해금 API
@login_required
def complete_payment(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            tool_id = data.get('tool_id')
            payment_id = data.get('payment_id') # 👈 imp_uid에서 payment_id로 변경!

            tool = get_object_or_404(Tool, id=tool_id)
            user_access, created = UserToolAccess.objects.get_or_create(user=request.user)

            # 1. 유저의 결제된 도구 목록에 추가
            user_access.paid_tools.add(tool)
            
            # 2. 도구 구매 횟수 +1 증가 (순위표 반영)
            tool.purchase_count += 1
            tool.save()

            return JsonResponse({'status': 'success', 'message': f'{tool.name} 구매가 완료되었습니다!'})
        
        except Exception as e:
            return JsonResponse({'status': 'fail', 'message': str(e)}, status=400)
    
    return JsonResponse({'status': 'fail', 'message': '잘못된 요청입니다.'}, status=400)

# 1. 커뮤니티 게시판 목록
def board_list(request):
    posts = Post.objects.all().order_by('-created_at') # 최신순 정렬
    return render(request, 'main/board_list.html', {'posts': posts})

# 2. 1:1 문의 게시판 목록
def inquiry_list(request):
    # 로그인한 사용자의 문의 내역만 조회 (관리자는 전체 조회)
    if request.user.is_staff:
        inquiries = Inquiry.objects.all().order_by('-created_at')
    else:
        inquiries = Inquiry.objects.filter(author=request.user).order_by('-created_at')
        
    return render(request, 'main/inquiry_list.html', {'inquiries': inquiries})