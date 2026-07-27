from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Tool, UserToolAccess

# 1. 메인 페이지: 도구 목록 & 인기 순위표(Leaderboard)
def index(request):
    # 인기순(usage_count 내림차순)으로 전체 도구 조회
    tools = Tool.objects.all()
    top_tools = tools[:3] # 인기 TOP 3 도구
    
    user_access = None
    free_tool = None
    paid_tool_ids = []

    if request.user.is_authenticated:
        # 유저 권한 정보 가져오기 (없으면 자동 생성)
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


# 2. 무료 도구 선택 처리 (1회 한정)
@login_required
def select_free_tool(request, tool_id):
    tool = get_object_or_404(Tool, id=tool_id)
    user_access, created = UserToolAccess.objects.get_or_create(user=request.user)

    # 이미 무료 도구를 선택했는지 검증
    if user_access.free_selected_tool is not None:
        messages.error(request, "이미 무료 도구를 선택하셨습니다! 다른 도구는 유료로 이용할 수 있습니다.")
    else:
        user_access.free_selected_tool = tool
        user_access.save()
        messages.success(request, f"'{tool.name}'이(가) 나만의 무료 도구로 등록되었습니다!")

    return redirect('index')


# 3. 도구 실행 및 사용량 카운트 증가 (권한 검증)
@login_required
def run_tool(request, tool_id):
    tool = get_object_or_404(Tool, id=tool_id)
    user_access, created = UserToolAccess.objects.get_or_create(user=request.user)

    # 접근 권한 체크 (무료로 선택한 도구이거나, 결제한 도구인지 확인)
    is_free_match = (user_access.free_selected_tool == tool)
    is_paid_match = user_access.paid_tools.filter(id=tool.id).exists()

    if not (is_free_match or is_paid_match):
        messages.warning(request, "이 도구를 사용하려면 구매가 필요합니다.")
        return redirect('index')

    # 도구 사용 횟수 1 증가 (순위표 반영)
    tool.usage_count += 1
    tool.save()

    context = {
        'tool': tool,
    }
    return render(request, 'main/run_tool.html', context)