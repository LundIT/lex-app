from django.db import models

class ProjectInputFiles(models.Model):
    id = models.AutoField(primary_key=True)
    file = models.FileField(upload_to='input_files/')
    explanation = models.TextField(blank=True, null=True)

    class Meta:
        app_label = 'lex_ai'
