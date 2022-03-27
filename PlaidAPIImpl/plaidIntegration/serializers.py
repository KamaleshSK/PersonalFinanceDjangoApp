from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from .models import ItemMetadata, Transaction, Account, Item


class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ['item', 'account_id', 'available_balance',
                  'current_balance', 'name', 'account_type', 'account_subtype']


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ['account', 'transaction_id',
                  'amount', 'date', 'name', 'payment_channel']


class ItemMetadataSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemMetadata
        fields = ["item_meta", "webhook", "update_type"]
