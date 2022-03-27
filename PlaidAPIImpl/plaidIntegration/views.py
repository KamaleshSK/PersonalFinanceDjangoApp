from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import Item, Transaction, Account, RequestIdentifier
from PlaidAPIImpl.settings import PLAID_CLIENT_ID, PLAID_SECRET
from rest_framework.response import Response
from rest_framework import status
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.sandbox_item_fire_webhook_request import SandboxItemFireWebhookRequest
import plaid
from plaid.api import plaid_api
from django.http import HttpResponse
from .tasks import fetch_item_metadata, delete_transactions_from_db, save_transactions_to_db

# Create your views here.

# plaid client configuration
configuration = plaid.Configuration(
    host=plaid.Environment.Sandbox,
    api_key={
        'clientId': PLAID_CLIENT_ID,
        'secret': PLAID_SECRET,
    }
)

api_client = plaid.ApiClient(configuration)
client = plaid_api.PlaidApi(api_client)


# Token Exchange Endpoint (accesstoken for a public token)
class AccessTokenCreate(APIView):
    # access only for logged in users
    permission_classes = [IsAuthenticated]

    def post(self, request):

        tokenExchangeRequest = ItemPublicTokenExchangeRequest(
            public_token=request.data['public_token'])
        response = None

        try:
            response = client.item_public_token_exchange(tokenExchangeRequest)
        except:
            # raise errors here
            print("public token exchange request failed")

        # log plaid API request response
        requestIdentifier = RequestIdentifier.objects.create(
            request_id=response['request_id'], request_body=str(response.data))
        requestIdentifier.save()

        access_token = response['access_token']
        item_id = response['item_id']
        # print(access_token, item_id)

        # saving item to db
        item = Item.objects.create(
            user=self.request.user, item_id=item_id, access_token=access_token)
        item.save()

        # add task to celery queue to fetch account, transaction and item metadata
        # fetch_account_data.delay(item_id)
        fetch_item_metadata.delay(item_id)
        # fetch_transaction_data.delay(item_id)

        # replace all fetch_account_data and fetch_transaction_date with save_transactions_to_db task
        save_transactions_to_db.delay(item_id, 20)

        data = {
            "access_token": access_token,
            "item_id": item_id
        }

        return Response(data, status=status.HTTP_201_CREATED)


# Endpoint for fetching user's Transactions
class TransactionsGetDB(APIView):
    # access only for loggedin users
    permission_classes = [IsAuthenticated]

    def get(self, request):

        # fetch item associated with the loggedin user
        item = Item.objects.filter(user=request.user)

        # fetch accounts associated with the user's plaid item
        accounts = Account.objects.filter(item=item[0].pk)

        # filter out primary key values of the different accounts
        account_id_list = []
        for acc in accounts:
            account_id_list.append(acc.pk)

        # print("account_id_list", account_id_list)

        # fetch transactions associated with user's accounts
        transactions = Transaction.objects.filter(account__in=account_id_list)
        transactions = list(transactions.values())

        return Response(transactions, status=status.HTTP_200_OK)


# Endpoint for fetching user's account details
class AccountDataDB(APIView):
    # access only for logged in users
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # fetch item associated with loggedin user
        item = Item.objects.filter(user=request.user)

        # fetch accounts associated with user's item
        accounts = Account.objects.filter(item_id=item[0].pk)
        accounts = list(accounts.values())

        return Response(accounts, status=status.HTTP_200_OK)


# webhook for handling plaid user transaction and account updates
# webhook exposed to the internet via ngrok
class WebhookTransactions(APIView):
    def post(self, request):
        data = request.data

        webhook_type = data['webhook_type']
        webhook_code = data['webhook_code']

        print(f"{webhook_type} Webhook received. Type {webhook_code}")

        if webhook_type == "TRANSACTIONS":
            item_id = data['item_id']
            if webhook_code == "TRANSACTIONS_REMOVED":
                removed_transactions = data['removed_transactions']
                # delete user transactions from db
                delete_transactions_from_db.delay(removed_transactions)
            else:
                new_transactions = data['new_transactions']
                # print("New transaction: ", new_transactions)
                if new_transactions == 0:
                    new_transactions = 20
                # fetch and save new user transactions to db
                save_transactions_to_db.delay(item_id, new_transactions)

        return HttpResponse("Webhook received", status=status.HTTP_202_ACCEPTED)


# Test endpoint for manually firing webhooks
class WebhookTest(APIView):
    # user authentication needed for particular user identity and corresponding item's webhook firing
    permission_classes = [IsAuthenticated]

    def get(self, request):
        item = Item.objects.filter(user=request.user)
        access_token = item[0].access_token

        # fire a DEFAULT_UPDATE webhook for an item
        request = SandboxItemFireWebhookRequest(
            access_token=access_token,
            webhook_code='DEFAULT_UPDATE'
        )
        response = client.sandbox_item_fire_webhook(request)

        print("Webhook fired: ", response['webhook_fired'])

        return Response({"message": "Webhook fired"}, status=status.HTTP_200_OK)
