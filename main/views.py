from django.shortcuts import render

# Create your views here.
def index(request):
    # main/index.html 템플릿을 렌더링하여 사용자에게 응답
    return render(request, 'main/index.html')