# main/forms.py
from django import forms
from .models import Post, Inquiry

# 1. 커뮤니티 글쓰기 폼
class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['tool', 'title', 'content']
        widgets = {
            'tool': forms.Select(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '제목을 입력하세요'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 6, 'placeholder': '내용을 작성해주세요'}),
        }

# 2. 1:1 문의하기 폼
class InquiryForm(forms.ModelForm):
    class Meta:
        model = Inquiry
        fields = ['title', 'content']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '문의 제목을 입력하세요'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 6, 'placeholder': '궁금하신 점이나 오류 내용을 상세히 적어주세요'}),
        }