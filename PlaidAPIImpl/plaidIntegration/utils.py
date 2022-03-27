from .models import Account

# utility functions for cleaning up user accounts and transactional data


def clean_accounts_data(item_id, accounts):
    accounts_data = []

    for acc in accounts:
        data = {}
        data['item'] = item_id
        data['account_id'] = acc['account_id']

        if not 'balances' in acc:
            acc['balances'] = {}
            acc['balances']['available'] = 0
            acc['balances']['current'] = 0

        if acc['balances']['available'] is None:
            acc['balances']['available'] = 0
        if acc['balances']['current'] is None:
            acc['balances']['current'] = 0

        if not 'name' in acc or acc['name'] is None:
            acc['name'] = ""
        if not 'type' in acc or acc['type'] is None:
            acc['type'] = ""
        if not 'subtype' in acc or acc['subtype'] is None:
            acc['subtype'] = ""

        data['available_balance'] = acc['balances']['available']
        data['current_balance'] = acc['balances']['current']
        data['name'] = acc['name']
        data['account_type'] = acc['type'].value
        data['account_subtype'] = acc['subtype'].value

        accounts_data.append(data)

    return accounts_data


def clean_itemmetadata(item_id, item):
    item_meta_data = {}

    item_meta_data['item_meta'] = item_id
    if item.webhook is None:
        item_meta_data['webhook'] = ""
    else:
        item_meta_data["webhook"] = item.webhook
    item_meta_data['update_type'] = item.update_type

    return item_meta_data


def clean_transaction_data(transactions):
    transactions_data = []

    for trans in transactions:
        data = {}
        data['account'] = Account.objects.filter(
            account_id=trans.account_id)[0].pk

        if trans.transaction_id is None:
            trans.transaction_id = ""
        data['transaction_id'] = trans.transaction_id
        data['amount'] = trans.amount
        data['date'] = trans.date
        data['name'] = trans.name
        data['payment_channel'] = trans.payment_channel

        transactions_data.append(data)

    return transactions_data
