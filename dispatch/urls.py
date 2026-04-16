from django.urls import path
from . import views

urlpatterns = [
    path('', views.dispatch_list),
    path('create/', views.dispatch_create),
    path('calendar/', views.leave_calendar),
    path('leave/create/', views.leave_create),  # 🔥 補這行
    path('leave/delete/<int:leave_id>/', views.leave_delete),
    path('leave/approval/', views.leave_approval),
    path('leave/approve/<int:leave_id>/', views.leave_approve),
    path('leave/reject/<int:leave_id>/', views.leave_reject),
    path('my-leaves/', views.my_leaves),
    path('delete/<int:order_id>/', views.dispatch_delete),
    path('update/<int:order_id>/', views.dispatch_update),
]