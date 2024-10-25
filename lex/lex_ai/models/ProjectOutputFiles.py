from django.db import models

class ProjectOutputFiles(models.Model):
    id = models.AutoField(primary_key=True)
    file = models.FileField(upload_to='output_files/')
    explanation = models.TextField(blank=True, null=True)

    class Meta:
        app_label = 'lex_ai'