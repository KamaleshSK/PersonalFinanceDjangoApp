from __future__ import absolute_import, unicode_literals
from datetime import datetime
from datetime import timedelta
from celery import shared_task
from PlaidAPIImpl.settings import PLAID_CLIENT_ID, PLAID_SECRET
from .models import Item, RequestIdentifier, Transaction, Account, ItemMetadata
from .serializers import AccountSerializer, TransactionSerializer, ItemMetadataSerializer
import plaid
from plaid.api import plaid_api
from datetime import datetime
from datetime import timedelta
from .utils import clean_accounts_data, clean_itemmetadata, clean_transaction_data
from plaid.model.accounts_get_request import AccountsGetRequest
from plaid.model.item_get_request import ItemGetRequest
from plaid.model.transactions_get_request import TransactionsGetRequest
from plaid.model.transactions_get_request_options import TransactionsGetRequestOptions
from django.contrib.auth.models import User


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


@shared_task
def fetch_item_metadata(item_id):
    item = Item.objects.filter(item_id=item_id)
    access_token = item[0].access_token
    response = None

    # pull item meta data for associated with an item from plaid
    metadata_fetch_request = ItemGetRequest(access_token=access_token)
    try:
        response = client.item_get(metadata_fetch_request)
    except:
        print("item meta data fetch request failed")

    # log plaid API request response
    requestIdentifier = RequestIdentifier.objects.create(
        request_id=response['request_id'], request_body=str(response.data))
    requestIdentifier.save()

    data = clean_itemmetadata(item[0].pk, response['item'])

    # validate and save Item metadata
    serialier = ItemMetadataSerializer(data=data)
    serialier.is_valid(raise_exception=True)
    serialier.save()

    return "User Item metadata saved to DB"


@shared_task
def delete_transactions_from_db(removed_transactions):

    for trans_id in removed_transactions:
        Transaction.objects.filter(transaction_id=trans_id).delete()

    return "Transactions removed"


@shared_task
def save_transactions_to_db(item_id):
    item = Item.objects.filter(item_id=item_id)
    access_token = item[0].access_token

    # fetching all the transactions of last 30 days: can be changed on developer discretion
    start_dt = (datetime.now() - timedelta(days=30))
    end_dt = datetime.now()

    # offset filters out newer transactions as received from webhook
    request = TransactionsGetRequest(
        access_token=access_token,
        start_date=start_dt.date(),
        end_date=end_dt.date(),
        options=TransactionsGetRequestOptions()
    )
    try:
        response = client.transactions_get(request)
        if response['item'].error is not None:
            raise Exception("Plaid API Error: " +
                            response['item'].error.error_message)
    except Exception as error:
        print(repr(error))

    # log plaid API request response
    requestIdentifier = RequestIdentifier.objects.create(
        request_id=response['request_id'], request_body=str(response.data))
    requestIdentifier.save()

    # print(response['transactions'])
    accounts = clean_accounts_data(item[0].pk, response['accounts'])

    accnts = Account.objects.filter(item=item[0])

    # Update records in user accounts table
    for acc in accnts:
        account_value = next(
            (elem for elem in accounts if elem["account_id"] == acc.account_id), None)

        if account_value:
            accnts.filter(account_id=acc.account_id).update(
                available_balance=account_value['available_balance'],
                current_balance=account_value['current_balance'],
                name=account_value['name'],
                account_type=account_value['account_type'],
                account_subtype=account_value['account_subtype']
            )

    # Save new account records in accounts table
    save_accounts = []
    for acc in accounts:
        # if account_id fetched from request is not already present in DB, save the accounts
        if not accnts.filter(account_id=acc['account_id']).exists():
            save_accounts.append(acc)

    # validate and save new user accounts
    acc_serializer = AccountSerializer(data=save_accounts, many=True)
    acc_serializer.is_valid(raise_exception=True)
    acc_serializer.save()

    transactions = clean_transaction_data(response['transactions'])

    trans_id = [trans['transaction_id'] for trans in transactions]

    # filter transactions that already exist in DB (in case one or many fields are updated)
    trans = Transaction.objects.filter(transaction_id__in=trans_id)

    # Update existing records in transactions table
    for tran in trans:
        trans_value = next(
            (elem for elem in transactions if elem["transaction_id"] == tran.transaction_id), None)

        if trans_value:
            trans.filter(transaction_id=tran.transaction_id).update(
                amount=trans_value['amount'],
                date=trans_value['date'],
                name=trans_value['name'],
                payment_channel=trans_value['payment_channel']
            )

    # Save new records in transactions table
    save_transactions = []
    for tran in transactions:
        # transactions that are not already present in DB (new transactions)
        if not trans.filter(transaction_id=tran['transaction_id']).exists():
            save_transactions.append(tran)

    # validate and save new transactions to DB
    tr_serializer = TransactionSerializer(data=save_transactions, many=True)
    tr_serializer.is_valid(raise_exception=True)
    tr_serializer.save()

    result = f"DB entries updated, {len(save_accounts)} created. {len(save_transactions)} created"
    # print(result)

    return result


"""
@shared_task
def fetch_account_data(item_id):
    item = Item.objects.filter(item_id=item_id)
    access_token = item[0].access_token
    response = None

    # pull realtime account information for each account associated with the item from plaid
    accounts_fetch_request = AccountsGetRequest(access_token=access_token)
    try:
        response = client.accounts_get(accounts_fetch_request)
    except:
        print("")

    accounts = clean_accounts_data(item[0].pk, response['accounts'])

    # validate and save user accounts
    serializer = AccountSerializer(data=accounts, many=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()

    return "User Accounts saved to DB"


@shared_task
def fetch_transaction_data(item_id):
    # fetching transactions for past 30 days: developer descretion
    start_dt = (datetime.now() - timedelta(days=30))
    end_dt = datetime.now()
    item = Item.objects.filter(item_id=item_id)
    access_token = item[0].access_token

    # fetch transactions associated with user from plaid
    request = TransactionsGetRequest(
        access_token=access_token,
        start_date=start_dt.date(),
        end_date=end_dt.date(),
        options=TransactionsGetRequestOptions()
    )
    try:
        response = client.transactions_get(request)
    except:
        print("")

    transactions = response['transactions']
    # print(transactions)

    transactions = clean_transaction_data(transactions)

    # validate and save transactions to db
    serializer = TransactionSerializer(data=transactions, many=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()

    return "User Transactions saved to DB"

"""
