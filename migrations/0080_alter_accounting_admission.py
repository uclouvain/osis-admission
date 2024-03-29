# Generated by Django 3.2.16 on 2022-12-13 15:00

from django.db import migrations, models
import django.db.models.deletion


def forward(apps, _):
    base_admission_model = apps.get_model('admission', 'BaseAdmission')
    accounting_model = apps.get_model('admission', 'Accounting')

    # Create an empty accounting related to each admission
    accountings = [
        accounting_model(admission_id=admission.pk)
        for admission in base_admission_model.objects.all()
        if not getattr(admission, 'accounting', None)
    ]

    accounting_model.objects.bulk_create(accountings)


def backward(apps, _):
    doctorate_admission_model = apps.get_model('admission', 'DoctorateAdmission')
    accounting_model = apps.get_model('admission', 'Accounting')

    # Only keep accounting data related to the doctorate admissions
    accounting_model.objects.exclude(
        admission_id__in=doctorate_admission_model.objects.all().values('pk').order_by()
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('admission', '0079_alter_internalnote_admission'),
    ]

    operations = [
        migrations.AlterField(
            model_name='accounting',
            name='admission',
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='accounting',
                to='admission.baseadmission',
            ),
        ),
        migrations.RunPython(forward, backward),
    ]
