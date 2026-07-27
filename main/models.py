from django.db import models
from django.contrib.auth.models import User

# 1. 도구(Tool) 모델
class Tool(models.Model):
    name = models.CharField(max_length=100, verbose_name="도구 이름")
    description = models.TextField(verbose_name="도구 설명")
    icon = models.CharField(max_length=10, default="🛠️", verbose_name="아이콘 이모지")
    usage_count = models.PositiveIntegerField(default=0, verbose_name="총 사용 횟수")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-usage_count'] # 사용 횟수가 많은 순(인기순)으로 기본 정렬

    def __str__(self):
        return f"{self.icon} {self.name} (사용: {self.usage_count}회)"


# 2. 유저별 무료 도구 지정 및 구매 내역 모델
class UserToolAccess(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='tool_access')
    # 유저가 무료로 선택한 1개의 도구 (선택 안 했으면 None)
    free_selected_tool = models.ForeignKey(
        Tool, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='free_users',
        verbose_name="선택한 무료 도구"
    )
    # 유저가 추가로 결제해서 해금한 도구들 (N:M 관계)
    paid_tools = models.ManyToManyField(Tool, blank=True, related_name='paid_users', verbose_name="결제한 도구들")

    def __str__(self):
        selected = self.free_selected_tool.name if self.free_selected_tool else "미선택"
        return f"{self.user.username} - [무료 선택: {selected}]"