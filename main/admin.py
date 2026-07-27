from django.contrib import admin
from .models import Tool, UserToolAccess

@admin.register(Tool)
class ToolAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon', 'usage_count', 'created_at')
    search_fields = ('name', 'description')

@admin.register(UserToolAccess)
class UserToolAccessAdmin(admin.ModelAdmin):
    list_display = ('user', 'free_selected_tool')