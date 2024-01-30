# Generated by Django 3.2.23 on 2024-01-17 13:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admission', '0141_refusal_reason_and_category_order'),
    ]

    operations = [
        migrations.AlterField(
            model_name='continuingeducationadmission',
            name='status',
            field=models.CharField(choices=[('EN_BROUILLON', 'In draft form'), ('CONFIRMEE', 'Application confirmed'), ('ANNULEE', 'Cancelled application'), ('INSCRIPTION_AUTORISEE', 'Application accepted')], default='EN_BROUILLON', max_length=30),
        ),
        migrations.AlterField(
            model_name='doctorateadmission',
            name='status',
            field=models.CharField(choices=[('EN_BROUILLON', 'In draft form'), ('EN_ATTENTE_DE_SIGNATURE', 'Waiting for signature'), ('CONFIRMEE', 'Application confirmed'), ('ANNULEE', 'Cancelled application'), ('INSCRIPTION_AUTORISEE', 'Application accepted')], default='EN_BROUILLON', max_length=30),
        ),
        migrations.AlterField(
            model_name='generaleducationadmission',
            name='status',
            field=models.CharField(choices=[('EN_BROUILLON', 'In draft form'), ('FRAIS_DOSSIER_EN_ATTENTE', 'Pending application fee'), ('CONFIRMEE', 'Application confirmed'), ('ANNULEE', 'Cancelled application'), ('A_COMPLETER_POUR_SIC', 'To be completed for the Enrolment Office (SIC)'), ('COMPLETEE_POUR_SIC', 'Completed for SIC'), ('TRAITEMENT_FAC', 'Processing by Fac'), ('A_COMPLETER_POUR_FAC', 'To be completed for Fac'), ('COMPLETEE_POUR_FAC', 'Completed for Fac'), ('RETOUR_DE_FAC', 'Feedback from Fac'), ('ATTENTE_VALIDATION_DIRECTION', 'Awaiting management approval'), ('INSCRIPTION_AUTORISEE', 'Application accepted'), ('INSCRIPTION_REFUSEE', 'Application denied'), ('CLOTUREE', 'Closed')], default='EN_BROUILLON', max_length=30),
        ),
    ]
