from django.contrib import admin
from .models import Engineer, DispatchOrder, Leave


# ⭐ 工程師（顯示年假）
@admin.register(Engineer)
class EngineerAdmin(admin.ModelAdmin):
    list_display = ('name', 'hire_date', 'get_annual_leave_display')

    def get_annual_leave_display(self, obj):
        return obj.get_annual_leave()
    get_annual_leave_display.short_description = "年假天數"


# ⭐ 派工（顯示時間）
@admin.register(DispatchOrder)
class DispatchOrderAdmin(admin.ModelAdmin):
    list_display = ('date', 'scheduled_time', 'customer_name')


# ⭐ 休假（升級版）
@admin.register(Leave)
class LeaveAdmin(admin.ModelAdmin):
    list_display = ('engineer', 'date', 'period', 'days', 'status')
    list_editable = ('status',)