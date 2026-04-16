from django.contrib import admin
from .models import Engineer, DispatchOrder, Leave


# 工程師
admin.site.register(Engineer)

# 派工
admin.site.register(DispatchOrder)


# 🔥 休假（升級版）
@admin.register(Leave)
class LeaveAdmin(admin.ModelAdmin):
    list_display = ('engineer', 'date', 'period', 'status')
    list_editable = ('status',)