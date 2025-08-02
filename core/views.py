from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Customer, Loan
from .serializers import CustomerSerializer, LoanSerializer
from datetime import timedelta, date
import math

@api_view(['POST'])
def register(request):
    data = request.data
    income = int(data['monthly_income'])
    approved_limit = round((income * 36) / 100000) * 100000
    customer = Customer.objects.create(
        first_name=data['first_name'],
        last_name=data['last_name'],
        age=data['age'],
        monthly_income=income,
        phone_number=data['phone_number'],
        approved_limit=approved_limit
    )
    return Response(CustomerSerializer(customer).data)

def calculate_emi(p, r, n):
    r = r / (12 * 100)
    emi = (p * r * pow(1 + r, n)) / (pow(1 + r, n) - 1)
    return round(emi, 2)



def get_loan_eligibility(customer, loan_amount, interest_rate, tenure):
    loans = Loan.objects.filter(customer=customer)
    current_year = date.today().year
    credit_score = 100

    if sum(loan.loan_amount for loan in loans) > customer.approved_limit:
        credit_score = 0
    else:
        on_time_ratio = sum(loan.emis_paid_on_time for loan in loans)
        if loans:
            credit_score -= (len(loans) * 5)
            credit_score += on_time_ratio * 2
            credit_score -= sum(1 for l in loans if l.start_date.year == current_year) * 3
            credit_score -= (sum(loan.loan_amount for loan in loans) / customer.approved_limit) * 10

    corrected_rate = interest_rate
    approval = False

    if credit_score > 50:
        approval = True
    elif 30 < credit_score <= 50 and interest_rate > 12:
        approval = True
    elif 10 < credit_score <= 30 and interest_rate > 16:
        approval = True
        corrected_rate = max(interest_rate, 16)
    elif credit_score <= 10:
        approval = False

    existing_emi_sum = sum(l.emi for l in loans)
    new_emi = calculate_emi(loan_amount, corrected_rate, tenure)
    if existing_emi_sum + new_emi > 0.5 * customer.monthly_income:
        approval = False

    return {
        "customer_id": customer.id,
        "approval": approval,
        "interest_rate": interest_rate,
        "corrected_interest_rate": corrected_rate,
        "tenure": tenure,
        "monthly_installment": new_emi
    }



@api_view(['POST'])
def check_eligibility(request):
    data = request.data
    customer = Customer.objects.get(id=data['customer_id'])

    result = get_loan_eligibility(
        customer,
        loan_amount=data['loan_amount'],
        interest_rate=data['interest_rate'],
        tenure=data['tenure']
    )
    return Response(result)

@api_view(['POST'])
def create_loan(request):
    data = request.data
    customer = Customer.objects.get(id=data['customer_id'])

    eligibility = get_loan_eligibility(
        customer,
        loan_amount=data['loan_amount'],
        interest_rate=data['interest_rate'],
        tenure=data['tenure']
    )

    if not eligibility['approval']:
        return Response({
            "loan_id": None,
            "customer_id": customer.id,
            "loan_approved": False,
            "message": "Loan not approved",
            "monthly_installment": 0
        })

    end_date = date.today() + timedelta(days=30 * int(data['tenure']))
    loan = Loan.objects.create(
        customer=customer,
        loan_amount=data['loan_amount'],
        interest_rate=eligibility['corrected_interest_rate'],
        tenure=data['tenure'],
        end_date=end_date,
        emi=eligibility['monthly_installment']
    )

    return Response({
        "loan_id": loan.id,
        "customer_id": customer.id,
        "loan_approved": True,
        "message": "Loan approved",
        "monthly_installment": loan.emi
    })


@api_view(['GET'])
def view_loan(request, loan_id):
    loan = Loan.objects.get(id=loan_id)
    customer = loan.customer
    return Response({
        "loan_id": loan.id,
        "customer": CustomerSerializer(customer).data,
        "loan_amount": loan.loan_amount,
        "interest_rate": loan.interest_rate,
        "monthly_installment": loan.emi,
        "tenure": loan.tenure
    })

@api_view(['GET'])
def view_loans(request, customer_id):
    customer = Customer.objects.get(id=customer_id)
    loans = Loan.objects.filter(customer=customer)
    return Response([
        {
            "loan_id": loan.id,
            "loan_amount": loan.loan_amount,
            "interest_rate": loan.interest_rate,
            "monthly_installment": loan.emi,
            "repayments_left": loan.tenure - loan.emis_paid_on_time
        } for loan in loans
    ])