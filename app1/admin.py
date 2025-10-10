from django.contrib import admin
from .models import SponsorTransaction

@admin.register(SponsorTransaction)
class SponsorTransactionAdmin(admin.ModelAdmin):
    list_display = ('sponsor', 'transaction_type', 'amount', 'balance_after', 'timestamp')
    list_filter = ('transaction_type', 'timestamp')
    search_fields = ('sponsor__username',)
