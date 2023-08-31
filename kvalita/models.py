from django.db import models

class QualityNokDescription(models.Model):
    id = models.BigAutoField(db_column='Id', primary_key=True)  # Field name made lowercase.
    nok_button = models.CharField(db_column='NOK_BUTTON', max_length=255)  # Field name made lowercase.
    description = models.CharField(db_column='DESCRIPTION', max_length=255)

# class Meta:
#     managed = False
#     db_table = 'quality_nokdescription'