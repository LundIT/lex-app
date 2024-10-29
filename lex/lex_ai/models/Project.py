from django.db import models

class Project(models.Model):
    id = models.AutoField(primary_key=True)
    overview = models.TextField(blank=True, null=True)
    input_files = models.ManyToManyField('ProjectInputFiles')
    output_files = models.ManyToManyField('ProjectOutputFiles')
    files_with_analysis = models.TextField(blank=True, null=True)
    structure = models.JSONField(blank=True, null=True)
    detailed_structure = models.JSONField(blank=True, null=True)
    functionalities = models.TextField(blank=True, null=True)
    models_fields = models.JSONField(blank=True, null=True)
    classes_and_their_paths = models.JSONField(blank=True, null=True)
    business_logic_calcs = models.TextField(blank=True, null=True)
    # db_table_field_mapping = models.TextField(blank=True, null=True)
    specification_doc = models.TextField(blank=True, null=True)
    generated_code = models.TextField(blank=True, null=True)

    class Meta:
        app_label = 'lex_ai'

