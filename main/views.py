from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import Tool, UserToolAccess
from .models import Post, Inquiry
from .forms import PostForm, InquiryForm
from django.db.models import Case, When, Value, IntegerField
from django.http import HttpResponseForbidden
from .models import Profile
import json

@login_required
def set_nickname(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    if profile.nickname:
        return redirect('/')
        
    if request.method == 'POST':
        nickname = request.POST.get('nickname', '').strip()
        if nickname:
            if Profile.objects.filter(nickname=nickname).exists():
                return render(request, 'main/set_nickname.html', {'error': '이미 사용 중인 닉네임입니다.'})
            profile.nickname = nickname
            profile.save()
            return redirect('/')
            
    return render(request, 'main/set_nickname.html')

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

# main/views.py
def board_list(request):
    # admin 글(우선순위 1) -> 일반 글(우선순위 2) 순으로 정렬 후 최신순 정렬
    posts = Post.objects.annotate(
        is_admin=Case(
            When(author__username='admin', then=Value(1)),
            default=Value(2),
            output_field=IntegerField(),
        )
    ).order_by('is_admin', '-is_notice', '-created_at')

    return render(request, 'main/board_list.html', {'posts': posts})

# 2. 1:1 문의 게시판 목록
def inquiry_list(request):
    # 로그인한 사용자의 문의 내역만 조회 (관리자는 전체 조회)
    if request.user.is_staff:
        inquiries = Inquiry.objects.all().order_by('-created_at')
    else:
        inquiries = Inquiry.objects.filter(author=request.user).order_by('-created_at')
        
    return render(request, 'main/inquiry_list.html', {'inquiries': inquiries})

# 1. 커뮤니티 글쓰기
@login_required
def post_create(request):
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user # 현재 로그인한 유저 세팅
            post.save()
            return redirect('board_list')
    else:
        form = PostForm()
    return render(request, 'main/post_form.html', {'form': form, 'title': '✏️ 커뮤니티 글쓰기'})

# 2. 1:1 문의하기 작성
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
    
    # 작성자 본인인지 확인 (관리자 superuser에게도 권한을 주려면 request.user.is_superuser 추가 가능)
    if post.author != request.user:
        return HttpResponseForbidden("본인의 글만 삭제할 수 있습니다.")
    
    if request.method == 'POST':
        post.delete()
        return redirect('board_list')
        
    return redirect('board_list')