from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required, user_passes_test

from .models import DispatchOrder, Engineer, Leave

from datetime import date, datetime
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

    # 🔥 當天資料
    orders = DispatchOrder.objects.filter(date=selected_date_obj)
    leaves = Leave.objects.filter(
        date=selected_date_obj,
        status='approved'
    )

    # 🔥 月曆
    year = selected_date_obj.year
    month = selected_date_obj.month
    cal = calendar.monthcalendar(year, month)

    # 🔥 每天派工整理
    orders_by_day = {}
    month_orders = DispatchOrder.objects.filter(
        date__year=year,
        date__month=month
    )

    for o in month_orders:
        day = o.date.day
        if day not in orders_by_day:
            orders_by_day[day] = []
        orders_by_day[day].append(o.customer_name)

    # 🔥 台灣假日
    tw_holidays = holidays.Taiwan(years=year, language='zh_TW')

    holidays_list = []
    holiday_names = {}

    for d, name in tw_holidays.items():
        if d.month == month:
            holidays_list.append(d.day)
            holiday_names[d.day] = name
   
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
        scheduled_time = request.POST.get('scheduled_time')
        note = request.POST.get('note')

        customer_name = request.POST.get('customer_name')
        contact_person = request.POST.get('contact_person')
        customer_phone = request.POST.get('customer_phone')
        description = request.POST.get('description')
        engineer_ids = request.POST.getlist('engineers')

        try:
            my_engineer = Engineer.objects.get(user=request.user)
            if str(my_engineer.id) not in engineer_ids:
                engineer_ids.append(str(my_engineer.id))
        except:
            pass

        order = DispatchOrder.objects.create(
            date=date_value,
            scheduled_time=scheduled_time if scheduled_time else None,
            note=note,
            customer_name=customer_name,
            contact_person=contact_person,
            customer_phone=customer_phone,
            description=description
        )

        order.engineers.set(engineer_ids)

        return redirect('/')

    today = date.today().strftime('%Y-%m-%d')

    return render(request, 'dispatch/form.html', {
        'engineers': engineers,
        'today': today
    })

# ✏ 修改派工
@login_required
def dispatch_update(request, order_id):
    order = get_object_or_404(DispatchOrder, id=order_id)
    engineers = Engineer.objects.all()

    if request.method == 'POST':
        order.date = request.POST.get('date')
        order.scheduled_time = request.POST.get('scheduled_time') or None
        order.note = request.POST.get('note')

        order.customer_name = request.POST.get('customer_name')
        order.contact_person = request.POST.get('contact_person')
        order.customer_phone = request.POST.get('customer_phone')
        order.description = request.POST.get('description')

        engineer_ids = request.POST.getlist('engineers')
        order.engineers.set(engineer_ids)

        order.save()
        return redirect('/')

    return render(request, 'dispatch/dispatch_update.html', {
        'order': order,
        'engineers': engineers,
    })

# ❌ 刪除派工
@login_required
def dispatch_delete(request, order_id):
    order = get_object_or_404(DispatchOrder, id=order_id)
    order.delete()
    return redirect('/')


# 📅 休假日曆
def leave_calendar(request):
    year = datetime.today().year
    month = datetime.today().month

    cal = calendar.monthcalendar(year, month)

    leaves = Leave.objects.filter(
        date__year=year,
        date__month=month,
        status='approved'
    )

    return render(request, 'dispatch/leave_calendar.html', {
        'calendar': cal,
        'leaves': leaves,
    })


# 📝 申請休假
@login_required
def leave_create(request):

    if request.method == 'POST':
        date_value = request.POST.get('date')
        period = request.POST.get('period')
        reason = request.POST.get('reason')

        try:
            engineer = Engineer.objects.get(user=request.user)
        except Engineer.DoesNotExist:
            return HttpResponseForbidden("你沒有對應的工程師資料")

        Leave.objects.create(
            engineer=engineer,
            date=date_value,
            period=period,
            reason=reason,
            status='pending'
        )

        return redirect('/calendar/')

    try:
        engineer = Engineer.objects.get(user=request.user)
        engineer_name = engineer.name
    except Engineer.DoesNotExist:
        engineer_name = request.user.username

    return render(request, 'dispatch/leave_form.html', {
        'engineer_name': engineer_name
    })


# ❌ 刪除休假
@login_required
def leave_delete(request, leave_id):
    leave = get_object_or_404(Leave, id=leave_id)

    if not leave.engineer.user or leave.engineer.user != request.user:
        return HttpResponseForbidden("你不能刪別人的申請")

    if leave.status != 'pending':
        return HttpResponseForbidden("已核准或駁回，不能刪除")

    leave.delete()
    return redirect('/')


# 👤 我的休假
@login_required
def my_leaves(request):
    try:
        engineer = Engineer.objects.get(user=request.user)
        leaves = Leave.objects.filter(engineer=engineer).order_by('-date')
    except Engineer.DoesNotExist:
        leaves = []

    return render(request, 'dispatch/my_leaves.html', {
        'leaves': leaves
    })


# 👨‍💼 判斷主管
def is_manager(user):
    return user.is_staff


# 📋 審核頁
@user_passes_test(is_manager)
def leave_approval(request):
    leaves = Leave.objects.filter(status='pending').order_by('date')

    # 🔥 取得切換月份
    year = request.GET.get('year')
    month = request.GET.get('month')

    if year and month:
        year = int(year)
        month = int(month)
    else:
        today = datetime.today()
        year = today.year
        month = today.month

    # 🔥 月曆
    cal = calendar.monthcalendar(year, month)

    # 🔥 該月份休假
    month_leaves = Leave.objects.filter(
        date__year=year,
        date__month=month
    )

    leave_days = [l.date.day for l in month_leaves]

    # 🔥 今天
    today = datetime.today().date()

    # 🔥 國定假日
    tw_holidays = holidays.Taiwan(years=year, language='zh_TW')
    holidays_list = [d.day for d in tw_holidays if d.month == month]

    return render(request, 'dispatch/leave_approval.html', {
        'leaves': leaves,
        'calendar': cal,
        'year': year,
        'month': month,
        'leave_days': leave_days,
        'today': today,
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