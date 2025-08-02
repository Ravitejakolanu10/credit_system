from celery import shared_task
from .models import Customer, Loan
import pandas as pd
from datetime import datetime, timedelta

@shared_task
def load_customers_from_excel(path):
    df = pd.read_excel(path)
    for row in df.itertuples():
        income = int(row.monthly_income)
        approved_limit = round((income * 36) / 100000) * 100000
        Customer.objects.create(
            first_name=row.first_name,
            last_name=row.last_name,
            phone_number=row.phone_number,
            age=row.age,
            monthly_income=income,
            approved_limit=approved_limit
        )

@shared_task
def load_loans_from_excel(path):
    df = pd.read_excel(path)
    for row in df.itertuples():
        customer = Customer.objects.get(id=row.customer_id)
        Loan.objects.create(
            customer=customer,
            loan_amount=row.loan_amount,
            interest_rate=row.interest_rate,
            tenure=row.tenure,
            start_date=row.start_date,
            end_date=row.start_date + timedelta(days=30 * row.tenure),
            emi=row.emi,
            emis_paid_on_time=row.emis_paid_on_time
        )
