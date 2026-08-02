import os
import io
import json
from datetime import datetime
import pandas as pd

from django.conf import settings
from django.http import FileResponse, Http404, JsonResponse, HttpResponse, HttpResponseForbidden
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Case, When, Value, IntegerField

from .models import Tool, UserToolAccess, Post, Inquiry, Profile
from .forms import PostForm, InquiryForm


@login_required
def set_nickname(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    if profile.nickname:
        return redirect('index')
        
    if request.method == 'POST':
        nickname = request.POST.get('nickname', '').strip()
        if nickname:
            if Profile.objects.filter(nickname=nickname).exists():
                return render(request, 'main/set_nickname.html', {'error': '이미 사용 중인 닉네임입니다.'})
            profile.nickname = nickname
            profile.save()
            return redirect('index')
            
    return render(request, 'main/set_nickname.html')


# 1. 메인 페이지
def index(request):
    tools = Tool.objects.all().order_by('-purchase_count')
    top_tools = tools[:3]  # 선택/구매 수 TOP 3
    
    user_access = None
    free_tool = None
    paid_tool_ids = []

    if request.user.is_authenticated:
        user_access, _ = UserToolAccess.objects.get_or_create(user=request.user)
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


# 2. 무료 도구 선택 처리
@login_required
def select_free_tool(request, tool_id):
    tool = get_object_or_404(Tool, id=tool_id)
    user_access, _ = UserToolAccess.objects.get_or_create(user=request.user)

    if user_access.free_selected_tool is not None:
        messages.error(request, "이미 무료 도구를 선택하셨습니다! 다른 도구는 결제 후 이용 가능합니다.")
    else:
        user_access.free_selected_tool = tool
        user_access.save()
        
        tool.purchase_count += 1
        tool.save()
        
        messages.success(request, f"'{tool.name}'이(가) 나만의 무료 도구로 등록되었습니다!")

    return redirect('index')


# 3. 결제 완료 검증 API
@login_required
def complete_payment(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            tool_id = data.get('tool_id')

            tool = get_object_or_404(Tool, id=tool_id)
            user_access, _ = UserToolAccess.objects.get_or_create(user=request.user)

            user_access.paid_tools.add(tool)
            tool.purchase_count += 1
            tool.save()

            return JsonResponse({'status': 'success', 'message': f'{tool.name} 구매가 완료되었습니다!'})
        
        except Exception as e:
            return JsonResponse({'status': 'fail', 'message': str(e)}, status=400)
    
    return JsonResponse({'status': 'fail', 'message': '잘못된 요청입니다.'}, status=400)


# 4. 동적 도구 가이드 뷰
@login_required
def tool_guide(request, tool_id):
    tool = get_object_or_404(Tool, id=tool_id)
    
    # 💡 도구명이 '비즈니스 재무 자금관리'이거나 id로 분기
    if "재무" in tool.name or tool_id == 1:
        return render(request, 'main/profit_guide.html', {'tool': tool})
    elif "마케팅" in tool.name or tool_id == 2:
            return render(request, 'main/tool_guide.html', {'tool': tool})
    return render(request, 'main/system_guide.html', {'tool': tool})

# 5. 동적 도구 실행 뷰 (권한 검증 및 사용량 증가)
@login_required
def run_tool(request, tool_id):
    tool = get_object_or_404(Tool, id=tool_id)
    user_access, _ = UserToolAccess.objects.get_or_create(user=request.user)

    is_free = (user_access.free_selected_tool_id == tool.id)
    is_paid = user_access.paid_tools.filter(id=tool.id).exists()

    if not (is_free or is_paid):
        messages.error(request, "이 도구를 사용하기 위한 권한이 없습니다.")
        return redirect('index')

    # ⬇️ hasattr 검사를 거쳐 필드가 있을 때만 1 증가시키거나, 이 줄을 삭제/주석 처리합니다.
    if hasattr(tool, 'usage_count'):
        tool.usage_count += 1
        tool.save()

    context = {
        'tool': tool,
        'today_date': datetime.now().strftime('%Y-%m-%d')
    }

# 1. 재무 관련 도구
    if "재무" in tool.name or tool_id == 1:
        return render(request, 'main/profit_flow.html', context)
    
    # 2. 다른 특정 도구 추가 예시 (예: 마케팅 또는 ID 2번)
    elif "마케팅" in tool.name or tool_id == 2:
        return render(request, 'main/value_builder.html', context)

    # 3. 그 외 기본 도구
    return render(request, 'main/system_builder.html', context)


# 6. 엑셀 다운로드 API
def profit_download_excel(request):
    export_type = request.GET.get('type', 'distribution')
    today = datetime.now().strftime("%Y-%m-%d")
    output = io.BytesIO()
    
    if export_type == 'distribution':
        data = [{
            "날짜": today,
            "총매출액(원)": int(request.GET.get('total_rev', 0)),
            "메모": request.GET.get('memo', '')
        }]
        df = pd.DataFrame(data)
        sheet_name = '수익금_분배_기록'
        filename = f"profit_distribution_{today}.xlsx"
    else:
        df = pd.DataFrame()
        sheet_name = '재무_체력_진단'
        filename = f"financial_assessment_{today}.xlsx"

    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
        worksheet = writer.sheets[sheet_name]
        
        for col in worksheet.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = col[0].column_letter
            worksheet.column_dimensions[col_letter].width = max(max_len + 5, 14)

    output.seek(0)
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


def download_excel_template(request):
    file_path = os.path.join(settings.BASE_DIR, 'main', 'static', 'files', 'profit_first_template.xlsx')
    if os.path.exists(file_path):
        return FileResponse(open(file_path, 'rb'), as_attachment=True, filename='Profit_First_Template.xlsx')
    raise Http404("다운로드할 템플릿 파일을 찾을 수 없습니다.")


# 게시판 / 문의하기 / 기타 뷰
def board_list(request):
    posts = Post.objects.annotate(
        is_admin=Case(
            When(author__username='admin', then=Value(1)),
            default=Value(2),
            output_field=IntegerField(),
        )
    ).order_by('is_admin', '-is_notice', '-created_at')
    return render(request, 'main/board_list.html', {'posts': posts})


def inquiry_list(request):
    if request.user.is_staff:
        inquiries = Inquiry.objects.all().order_by('-created_at')
    else:
        inquiries = Inquiry.objects.filter(author=request.user).order_by('-created_at')
    return render(request, 'main/inquiry_list.html', {'inquiries': inquiries})


@login_required
def post_create(request):
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('board_list')
    else:
        form = PostForm()
    return render(request, 'main/post_form.html', {'form': form, 'title': '✏️ 커뮤니티 글쓰기'})


@login_required
def inquiry_create(request):
    if request.method == 'POST':
        form = InquiryForm(request.POST)
        if form.is_valid():
            inquiry = form.save(commit=False)
            inquiry.author = request.user
            inquiry.save()
            return redirect('inquiry_list')
    else:
        form = InquiryForm()
    return render(request, 'main/post_form.html', {'form': form, 'title': '❓ 1:1 문의하기'})


@login_required
def post_delete(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if post.author != request.user:
        return HttpResponseForbidden("본인의 글만 삭제할 수 있습니다.")
    if request.method == 'POST':
        post.delete()
    return redirect('board_list')