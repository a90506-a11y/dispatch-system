from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required, user_passes_test

from .models import DispatchOrder, Engineer, Leave

from datetime import date, datetime, timedelta
import calendar
import holidays


# 📋 派工列表 + 月曆 + 假日
def dispatch_list(request):
    selected_date = request.GET.get('date')

    if selected_date:
        selected_date_obj = datetime.strptime(selected_date, "%Y-%m-%d").date()
    else:
        selected_date_obj = date.today()
        selected_date = selected_date_obj.strftime('%Y-%m-%d')

    orders = DispatchOrder.objects.filter(date=selected_date_obj).order_by('scheduled_time')

    leaves = Leave.objects.filter(
        date=selected_date_obj,
        status='approved'
    )

    year = selected_date_obj.year
    month = selected_date_obj.month
    cal = calendar.monthcalendar(year, month)

    orders_by_day = {}
    month_orders = DispatchOrder.objects.filter(
        date__year=year,
        date__month=month
    ).order_by('scheduled_time')

    for o in month_orders:
        day = o.date.day
        orders_by_day.setdefault(day, []).append(o)

    # ⭐ 台灣假日
    tw_holidays = holidays.Taiwan(years=year, language='zh_TW')

    holidays_list = []
    holiday_names = {}

    for d, name in tw_holidays.items():
        if d.month == month:
            holidays_list.append(d.day)
            holiday_names[d.day] = name

    return render(request, 'dispatch/list.html', {
        'orders': orders,
        'leaves': leaves,
        'selected_date': selected_date,
        'calendar': cal,
        'orders_by_day': orders_by_day,
        'holidays': holidays_list,
        'holiday_names': holiday_names,
        'year': year,
        'month': month,
    })


# ➕ 新增派工
@login_required
def dispatch_create(request):
    engineers = Engineer.objects.all()

    if request.method == 'POST':
        date_value = request.POST.get('date')
        time_str = request.POST.get('scheduled_time')

        scheduled_time = None
        if time_str and len(time_str) == 4 and time_str.isdigit():
            hour = int(time_str[:2])
            minute = int(time_str[2:])
            scheduled_time = datetime.strptime(f"{hour}:{minute}", "%H:%M").time()

        note = request.POST.get('note') or ''

        order = DispatchOrder.objects.create(
            date=date_value,
            scheduled_time=scheduled_time,
            note=note,
            customer_name=request.POST.get('customer_name'),
            contact_person=request.POST.get('contact_person'),
            customer_phone=request.POST.get('customer_phone'),
            description=request.POST.get('description')
        )

        order.engineers.set(request.POST.getlist('engineers'))
        return redirect('/')

    return render(request, 'dispatch/form.html', {
        'engineers': engineers,
        'today': date.today().strftime('%Y-%m-%d')
    })


# ✏ 修改派工
@login_required
def dispatch_update(request, order_id):
    order = get_object_or_404(DispatchOrder, id=order_id)
    engineers = Engineer.objects.all()

    if request.method == 'POST':
        order.date = request.POST.get('date')

        time_str = request.POST.get('scheduled_time')
        if time_str and len(time_str) == 4 and time_str.isdigit():
            hour = int(time_str[:2])
            minute = int(time_str[2:])
            order.scheduled_time = datetime.strptime(f"{hour}:{minute}", "%H:%M").time()
        else:
            order.scheduled_time = None

        order.note = request.POST.get('note') or ''
        order.customer_name = request.POST.get('customer_name')
        order.contact_person = request.POST.get('contact_person')
        order.customer_phone = request.POST.get('customer_phone')
        order.description = request.POST.get('description')

        order.engineers.set(request.POST.getlist('engineers'))
        order.save()

        return redirect('/')

    return render(request, 'dispatch/dispatch_update.html', {
        'order': order,
        'engineers': engineers,
    })


# ❌ 刪除派工
@login_required
def dispatch_delete(request, order_id):
    get_object_or_404(DispatchOrder, id=order_id).delete()
    return redirect('/')


# 📅 休假日曆（完整版本）
def leave_calendar(request):
    today = datetime.today()
    year = today.year
    month = today.month

    cal = calendar.monthcalendar(year, month)

    leaves = Leave.objects.filter(
        date__year=year,
        date__month=month,
        status='approved'
    )

    tw_holidays = holidays.Taiwan(years=year, language='zh_TW')
    holidays_list = [d.day for d in tw_holidays if d.month == month]

    return render(request, 'dispatch/leave_calendar.html', {
        'calendar': cal,
        'leaves': leaves,
        'year': year,
        'month': month,
        'holidays': holidays_list,
    })


# 📝 申請休假（完整版）
@login_required
def leave_create(request):

    try:
        engineer = Engineer.objects.get(user=request.user)
    except Engineer.DoesNotExist:
        return HttpResponseForbidden("你沒有對應的工程師資料")

    total_days = engineer.get_annual_leave()
    remaining_days = engineer.get_remaining_leave()
    used_days = total_days - remaining_days

    if request.method == 'POST':
        start_date = request.POST.get('date')
        end_date = request.POST.get('end_date') or start_date
        period = request.POST.get('period')
        reason = request.POST.get('reason')

        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")

        total_request_days = 0
        current = start

        while current <= end:
            total_request_days += 1 if period == 'full' else 0.5
            current += timedelta(days=1)

        if total_request_days > remaining_days:
            return render(request, 'dispatch/leave_form.html', {
                'error': '剩餘假不足，無法申請',
                'engineer_name': engineer.name,
                'used_days': used_days,
                'remaining_days': remaining_days,
                'total_days': total_days,
            })

        current = start
        while current <= end:
            Leave.objects.create(
                engineer=engineer,
                date=current.date(),
                period=period,
                reason=reason,
                status='pending'
            )
            current += timedelta(days=1)

        return redirect('/calendar/')

    return render(request, 'dispatch/leave_form.html', {
        'engineer_name': engineer.name,
        'used_days': used_days,
        'remaining_days': remaining_days,
        'total_days': total_days,
    })


# ❌ 刪除休假
@login_required
def leave_delete(request, leave_id):
    leave = get_object_or_404(Leave, id=leave_id)

    if leave.engineer.user != request.user or leave.status != 'pending':
        return HttpResponseForbidden("不可刪除")

    leave.delete()
    return redirect('/')


# 👤 我的休假（完整版）
@login_required
def my_leaves(request):
    try:
        engineer = Engineer.objects.get(user=request.user)

        leaves = Leave.objects.filter(engineer=engineer).order_by('-date')
        approved_leaves = leaves.filter(status='approved')

        used_days = sum(l.days for l in approved_leaves)
        total_days = engineer.get_annual_leave()
        remaining_days = total_days - used_days

    except Engineer.DoesNotExist:
        leaves = []
        used_days = total_days = remaining_days = 0

    return render(request, 'dispatch/my_leaves.html', {
        'leaves': leaves,
        'used_days': used_days,
        'total_days': total_days,
        'remaining_days': remaining_days,
    })


# 👨‍💼 判斷主管
def is_manager(user):
    return user.is_staff


# 📋 審核頁
@user_passes_test(is_manager)
def leave_approval(request):
    leaves = Leave.objects.filter(status='pending').order_by('date')

    today = datetime.today()
    year = today.year
    month = today.month

    cal = calendar.monthcalendar(year, month)

    month_leaves = Leave.objects.filter(date__year=year, date__month=month)
    leave_days = [l.date.day for l in month_leaves]

    tw_holidays = holidays.Taiwan(years=year, language='zh_TW')
    holidays_list = [d.day for d in tw_holidays if d.month == month]

    return render(request, 'dispatch/leave_approval.html', {
        'leaves': leaves,
        'calendar': cal,
        'year': year,
        'month': month,
        'leave_days': leave_days,
        'today': today.date(),
        'holidays': holidays_list,
    })


# ✔ 核准
@user_passes_test(is_manager)
def leave_approve(request, leave_id):
    leave = get_object_or_404(Leave, id=leave_id)
    leave.status = 'approved'
    leave.save()
    return redirect('/leave/approval/')


# ✖ 駁回
@user_passes_test(is_manager)
def leave_reject(request, leave_id):
    leave = get_object_or_404(Leave, id=leave_id)
    leave.status = 'rejected'
    leave.save()
    return redirect('/leave/approval/')