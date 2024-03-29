# Generated by Django 3.2.16 on 2022-11-14 12:14

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('admission', '0072_form_item'),
    ]

    operations = [
        migrations.RenameField(
            model_name='doctorateadmission',
            old_name='scholarship_grant',
            new_name='other_international_scholarship',
        ),
        migrations.AlterField(
            model_name='doctorateadmission',
            name='other_international_scholarship',
            field=models.CharField(
                blank=True,
                default='',
                max_length=255,
                verbose_name='Other international scholarship',
            ),
        ),
        migrations.AddField(
            model_name='doctorateadmission',
            name='international_scholarship',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='+',
                to='admission.scholarship',
                verbose_name='International scholarship',
            ),
        ),
        migrations.AlterField(
            model_name='doctorateadmission',
            name='erasmus_mundus_scholarship',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='+',
                to='admission.scholarship',
                verbose_name='Erasmus Mundus scholarship',
            ),
        ),
        migrations.AlterField(
            model_name='generaleducationadmission',
            name='double_degree_scholarship',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='+',
                to='admission.scholarship',
                verbose_name='Dual degree scholarship',
            ),
        ),
        migrations.AlterField(
            model_name='generaleducationadmission',
            name='erasmus_mundus_scholarship',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='+',
                to='admission.scholarship',
                verbose_name='Erasmus Mundus scholarship',
            ),
        ),
        migrations.AlterField(
            model_name='generaleducationadmission',
            name='international_scholarship',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='+',
                to='admission.scholarship',
                verbose_name='International scholarship',
            ),
        ),
    ]
