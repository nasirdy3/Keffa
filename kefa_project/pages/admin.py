from django.contrib import admin
from .models import FAQ

@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ('question', 'order', 'is_visible', 'updated_at')
    list_editable = ('order', 'is_visible')
    search_fields = ('question', 'answer')
    list_filter = ('is_visible',)
