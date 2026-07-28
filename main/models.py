from django.db import models
from django.contrib.auth.models import User

# 1. 도구(Tool) 모델
class Tool(models.Model):
    name = models.CharField(max_length=100, verbose_name="도구 이름")
    description = models.TextField(verbose_name="도구 설명")
    icon = models.CharField(max_length=10, default="🛠️", verbose_name="아이콘 이모지")

    price = models.PositiveIntegerField(default=3000, verbose_name="가격(원)")

    # 💡 실행 횟수 대신 '구매/선택 횟수'로 지표 변경
    purchase_count = models.PositiveIntegerField(default=0, verbose_name="총 선택/구매 횟수")
    
    # 🔒 구매자 전용 제공 정보 (비구독자/미구매자에게는 숨김)
    tool_link = models.URLField(blank=True, null=True, verbose_name="도구 실행 링크", help_text="예: https://notion.site/... 또는 외부 앱 URL")
    access_code = models.CharField(max_length=100, blank=True, null=True, verbose_name="접속 비밀번호/키", help_text="구매자에게만 제공할 비밀번호")
    usage_instruction = models.TextField(blank=True, null=True, verbose_name="도구 사용 방법 설명글")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-purchase_count'] # 구매/선택 횟수 많은 순으로 정렬

    def __str__(self):
        return f"{self.icon} {self.name} (선택/구매: {self.purchase_count}회)"


# 2. 유저 권한 모델
class UserToolAccess(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='tool_access')
    free_selected_tool = models.ForeignKey(
        Tool, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='free_users',
        verbose_name="선택한 무료 도구"
    )
    paid_tools = models.ManyToManyField(Tool, blank=True, related_name='paid_users', verbose_name="결제한 도구들")

    def __str__(self):
        selected = self.free_selected_tool.name if self.free_selected_tool else "미선택"
        return f"{self.user.username} - [무료 선택: {selected}]"