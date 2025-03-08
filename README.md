# Bank Loans Management Application

This Django application manages bank loans by receiving funds from loan providers and granting loans to customers—while ensuring that the total approved loans never exceed the available funds. It uses Django and Django Rest Framework (DRF) with role-based access control and custom business logic.

---

## Table of Contents

- [Bank Loans Management Application](#bank-loans-management-application)
  - [Table of Contents](#table-of-contents)
  - [Overview](#overview)
  - [Assumptions and Business Logic](#assumptions-and-business-logic)
  - [Models and Their Relationships](#models-and-their-relationships)
    - [User](#user)
    - [LoanProvider](#loanprovider)
    - [FundApplication](#fundapplication)
    - [LoanCustomer](#loancustomer)
    - [Loan](#loan)
    - [LoanPayment](#loanpayment)
    - [LoanPolicy](#loanpolicy)
  - [Installation and Setup](#installation-and-setup)
    - [Create a Virtual Environment](#create-a-virtual-environment)
    - [Activate the Virtual Environment](#activate-the-virtual-environment)
    - [Install Dependencies](#install-dependencies)
    - [Apply Migrations](#apply-migrations)
    - [Create a Superuser](#create-a-superuser)
    - [Running the Application](#running-the-application)
    - [Access the application at:](#access-the-application-at)
    - [Running Unit Tests](#running-unit-tests)
    - [Test cases cover:](#test-cases-cover)

---

## Overview

The application supports three primary roles:

- **Loan Provider:** Contributes funds via FundApplications.
- **Loan Customer:** Applies for loans and makes payments.
- **Bank Personnel:** Sets and manages LoanPolicy records and views all applications from providers and customers.

Key business rules include:

- **Global Funds Constraint:** The sum of approved loans must not exceed the total approved funds from LoanProviders.
- **Category-Specific Policies:** Each loan must comply with an active LoanPolicy for its category (e.g., House Loan, Car Loan) that defines minimum/maximum amounts, required interest rate, and loan term.
- **Auto-Reject Logic:** If a loan update violates the funds constraint, the API can automatically mark the loan as "rejected" and return an explanatory message.

---

## Assumptions and Business Logic

- **User Roles:**  
  Every user is assigned a role (`provider`, `customer`, or `bank`) that controls their access:
  - **Loan Provider:** Can create/view their own FundApplications.
  - **Loan Customer:** Can view and create their own Loans and LoanPayments.
  - **Bank Personnel:** Can view all FundApplications and Loans, and create/manage LoanPolicy records.

- **Loan Policy Enforcement:**  
  Loans are validated against the currently active LoanPolicy for their category. The policy defines the permitted range for the loan amount, interest rate, and term.

- **Global Funds Check:**  
  When approving a loan, the application ensures that the total approved loan amount (including the new loan) does not exceed the available approved funds from FundApplications.

- **Auto-Reject Behavior:**  
  In the API, if an update violates the funds constraint, the system can automatically set the loan’s status to "rejected" and return a message explaining that the available funds cannot cover the loan.

---

## Models and Their Relationships

### User

- **Description:**  
  A custom user model extending Django’s `AbstractUser` with an extra `role` field.
- **Attributes:**  
  - Inherited fields: `username`, `password`, etc.
  - `role`: A `CharField` with choices: `provider`, `customer`, and `bank`.

### LoanProvider

- **Description:**  
  Represents a provider who contributes funds.
- **Attributes:**  
  - `user`: One-to-one relationship with a `User` (must have role `provider`).
  - `total_budget`: A `DecimalField` that holds the total funds available.

### FundApplication

- **Description:**  
  Records a provider’s application to contribute funds.
- **Attributes:**  
  - `provider`: ForeignKey to `LoanProvider`.
  - `amount`: The funds amount applied.
  - `status`: Indicates if the application is `pending`, `approved`, or `rejected`.
  - `created_at`: Timestamp automatically set on creation.

### LoanCustomer

- **Description:**  
  Represents a customer who applies for loans.
- **Attributes:**  
  - `user`: One-to-one relationship with a `User` (must have role `customer`).

### Loan

- **Description:**  
  Represents a loan application.
- **Attributes:**  
  - `customer`: ForeignKey to `LoanCustomer`.
  - `category`: A `CharField` (e.g., `house` or `car`); default is `house`.
  - `amount`: The requested loan amount.
  - `term`: Duration of the loan in months.
  - `interest_rate`: The interest rate for the loan.
  - `status`: Can be `pending`, `approved`, `rejected`, or `paid` (default is `pending`).
  - `created_at`: Auto-set timestamp.
- **Business Logic in `clean()`:**
  1. **Global Funds Check:**  
     When the loan is approved, the sum of approved loans plus this loan's amount must not exceed approved funds.
  2. **Policy Enforcement:**  
     The loan's `amount`, `interest_rate`, and `term` must meet the active LoanPolicy for its category.

### LoanPayment

- **Description:**  
  Records a payment made towards a loan.
- **Attributes:**  
  - `loan`: ForeignKey to a `Loan`.
  - `amount`: Payment amount.
  - `payment_date`: Auto-set timestamp.

### LoanPolicy

- **Description:**  
  Defines policy rules for a loan category.
- **Attributes:**  
  - `bank_personnel`: ForeignKey to `User` (with role `bank`); a bank personnel can have multiple policies.
  - `category`: The loan category (e.g., `house` or `car`).
  - `min_amount` / `max_amount`: Range for valid loan amounts.
  - `interest_rate`: Required interest rate.
  - `duration`: Required loan term in months.
  - `active`: Boolean indicating if this policy is currently active.
  - `created_at`: Auto-set timestamp.

---

## Installation and Setup

### Create a Virtual Environment

```bash
python -m venv venv
```
### Activate the Virtual Environment
- On Windows:
```bash
venv\Scripts\activate
```

### Install Dependencies
```bash
pip install django djangorestframework
```
### Apply Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```
### Create a Superuser
```bash
python manage.py createsuperuser
```

### Running the Application
- Start the server with:

``` bash

python manage.py runserver
```
### Access the application at:

- Admin UI: http://127.0.0.1:8000/admin/
- API Endpoints: As defined in URL configuration
  - Fund Applications:
    GET /api/fund-applications/ 
  - Loan Providers: See only their own applications.
  - Bank Personnel: See all fund applications.
- Loans:
    GET /api/loans/
  - Loan Customers: See only their own loans.
  - Bank Personnel: See all loan applications.
  - PATCH /api/loans/<loan_id>/ (or a custom action like /update-status/)
Updates a loan’s status and triggers validations.
  - If funds are insufficient, the API auto-rejects the loan and returns a message.
- Loan Payments:
  - POST /api/payments/
  -  Only the owner of a loan can create a payment for that loan.
### Running Unit Tests
To run all tests

``` bash

python manage.py test
```
### Test cases cover:

- Valid and Invalid Loan Creation:
Confirm that loans meeting or violating LoanPolicy constraints behave correctly.

- Global Funds Constraint:
Ensure that approving loans exceeding available funds triggers a validation error.

- Auto-Reject Logic:
Verify that when a loan update violates the funds constraint, the loan is auto-rejected and a message is returned.

- Multiple Loans:
Confirm that multiple approved loans whose total is within available funds are accepted.

