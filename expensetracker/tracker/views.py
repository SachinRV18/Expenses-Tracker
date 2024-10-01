import boto3
from django.shortcuts import render, redirect, get_object_or_404
from .models import Expense
from django.conf import settings
from django.utils import timezone
import os

def add_expense(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        amount = request.POST.get('amount')
        date = request.POST.get('date')
        description = request.POST.get('description')
        receipt = request.FILES.get('receipt')

        # Create a new Expense object
        expense = Expense(title=title, amount=amount, date=date, description=description)

        if receipt:
            # Save the receipt to S3 and link it to the expense
            s3_client = boto3.client('s3')
            timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
            file_extension = os.path.splitext(receipt.name)[1]  # Get the file extension
            unique_filename = f'receipts/{title}_{timestamp}{file_extension}'  # Create unique filename

            # Upload the file to S3
            s3_client.upload_fileobj(receipt, settings.AWS_STORAGE_BUCKET_NAME, unique_filename)
            expense.receipt = unique_filename  # Save the unique path of the file in the Expense model

        expense.save()
        return redirect('expense_list')  # Redirect to the expense list page

    return render(request, 'tracker/add_expense.html')


def expense_list(request):
    expenses = Expense.objects.all()
    for expense in expenses:
        if expense.receipt:
            expense.receipt_url = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/{expense.receipt}"
    return render(request, 'tracker/expense_list.html', {'expenses': expenses})

def delete_expense(request, expense_id):
    expense = get_object_or_404(Expense, id=expense_id)  # Use get_object_or_404 for safety
    if expense.receipt:
        # Delete the receipt from S3
        s3_client = boto3.client('s3')
        receipt_key = expense.receipt  # Ensure this is a string

        # Attempt to delete the object from S3
        try:
            s3_client.delete_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=receipt_key)
        except Exception as e:
            print(f"Error deleting S3 object: {e}")

    expense.delete()  # Delete the expense record from the database
    return redirect('expense_list')  # Redirect back to the expense list page

