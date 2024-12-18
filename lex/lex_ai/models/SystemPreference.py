from django.db import models
from django.contrib.auth import get_user_model

class SystemPreference(models.Model):
    key = models.CharField(max_length=100, unique=True)
    value = models.JSONField()
    description = models.TextField(blank=True)
    modified_by = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        null=True
    )
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'lex_ai'




