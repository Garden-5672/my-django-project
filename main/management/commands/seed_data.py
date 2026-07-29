# main/management/commands/seed_data.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from main.models import Post, Inquiry

User = get_user_model()

class Command(BaseCommand):
    help = '초기 공지사항 및 웰컴 데이터를 생성합니다.'

    def handle(self, *args, **kwargs):
        admin_user, _ = User.objects.get_or_create(username='admin', defaults={'is_staff': True, 'is_superuser': True})
        
        # 기본 공지사항 작성
        posts_data = [
            {"title": "👋 커뮤니티 게시판에 오신 것을 환영합니다!", "content": "도구 사용 팁, 질문, 피드백을 자유롭게 나누어주세요."},
            {"title": "📌 게시판 이용 가이드 및 수칙", "content": "타인을 배려하는 고운 말을 사용해주세요. 광고성 글은 제재될 수 있습니다."},
            {"title": "🛠️ 추천하고 싶은 마이크로 도구가 있으신가요?", "content": "댓글로 자유롭게 의견을 남겨주시면 다음 도구 개발에 반영하겠습니다."}
        ]

        for p in posts_data:
            Post.objects.get_or_create(
                title=p["title"],
                defaults={"content": p["content"], "author": admin_user}
            )

        self.stdout.write(self.style.SUCCESS('✅ 성공적으로 초기 게시글 데이터를 생성했습니다!'))