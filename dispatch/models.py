from django.db import models
from django.contrib.auth.models import User
from datetime import date


class Engineer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=100)

    hire_date = models.DateField(null=True, blank=True, verbose_name="到職日")

    def __str__(self):
        return self.name

    def get_annual_leave(self):
        if not self.hire_date:
            return 0

        today = date.today()
        years = (today - self.hire_date).days / 365

        if years < 0.5:
            return 0
        elif years < 1:
            return 3
        elif years < 2:
            return 7
        elif years < 3:
            return 10
        elif years < 5:
            return 14
        elif years < 10:
            return 15
        else:
            return 15 + int(years - 10)

    def get_remaining_leave(self):
        approved_leaves = self.leave_set.filter(status='approved')
        used = sum(l.days for l in approved_leaves)
        return self.get_annual_leave() - used


class DispatchOrder(models.Model):
    date = models.DateField()
    scheduled_time = models.TimeField(null=True, blank=True, verbose_name="指定時間")
    customer_name = models.CharField(max_length=100)
    contact_person = models.CharField(max_length=100, blank=True)
    customer_phone = models.CharField(max_length=20)
    description = models.TextField()
    note = models.TextField(blank=True, null=True, verbose_name="備註")
    engineers = models.ManyToManyField(Engineer)

    def __str__(self):
        return f"{self.date} - {self.customer_name}"


class Leave(models.Model):
    STATUS_CHOICES = [
        ('pending', '待審核'),
        ('approved', '已核准'),
        ('rejected', '已駁回'),
    ]

    PERIOD_CHOICES = [
        ('morning', '上午'),
        ('afternoon', '下午'),
        ('full', '全天'),
    ]

    engineer = models.ForeignKey(Engineer, on_delete=models.CASCADE)
    date = models.DateField()
    period = models.CharField(max_length=10, choices=PERIOD_CHOICES)
    reason = models.CharField(max_length=100, blank=True)

    days = models.FloatField(default=0.5, verbose_name="請假天數")

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"{self.engineer.name} - {self.date} ({self.status})"

    def save(self, *args, **kwargs):
        if self.period == 'full':
            self.days = 1
        else:
            self.days = 0.5
        super().save(*args, **kwargs)