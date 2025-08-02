from django.db import models

class Customer(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15)
    monthly_income = models.IntegerField()
    approved_limit = models.IntegerField()
    age = models.IntegerField()


class Loan(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    loan_amount = models.FloatField()
    interest_rate = models.FloatField()
    tenure = models.IntegerField()
    start_date = models.DateField(auto_now_add=True)
    end_date = models.DateField()
    emi = models.FloatField()
    emis_paid_on_time = models.IntegerField(default=0)

