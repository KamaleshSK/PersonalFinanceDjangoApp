from django.urls import path
from . import views

urlpatterns = [
    path('get_access_token/', views.AccessTokenCreate.as_view()),
    path('get_transactions_from_db/', views.TransactionsGetDB.as_view()),
    path('get_account_data_from_db/', views.AccountDataDB.as_view()),

    path('webhook_test/', views.WebhookTest.as_view()),
    path('webhook_transactions/', views.WebhookTransactions.as_view())
]
