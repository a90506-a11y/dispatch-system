from django.db import models
from django.contrib.auth.models import User


class Engineer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class DispatchOrder(models.Model):
    date = models.DateField()
    customer_name = models.CharField(max_length=100)
    contact_person = models.CharField(max_length=100, blank=True)
    customer_phone = models.CharField(max_length=20)
    description = models.TextField()
    engineers = models.ManyToManyField(Engineer)

    def __str__(self):
        return f"{self.date} - {self.customer_name}"


class Leave(models.Model):
    STATUS_CHOICES = [
        ('pending', '待審核'),
        ('approved', '已核准'),
        ('rejected', '已駁回'),
    ]

    engineer = models.ForeignKey(Engineer, on_delete=models.CASCADE)
    date = models.DateField()

    PERIOD_CHOICES = [
        ('morning', '上午'),
        ('afternoon', '下午'),
        ('full', '全天'),
    ]

    period = models.CharField(max_length=10, choices=PERIOD_CHOICES)
    reason = models.CharField(max_length=100, blank=True)

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"{self.engineer.name} - {self.date} ({self.status})"