# Generated by Django 3.2.23 on 2024-01-17 16:17

from django.db import migrations, models


def set_initial_order(apps, schema_editor):
    RefusalReason = apps.get_model('admission', 'RefusalReason')

    reasons = RefusalReason.objects.select_related('category').all().order_by('category__name', 'name')

    previous_category = None
    reason_index = 0
    category_index = 0

    for reason in reasons:
        if reason.category != previous_category:
            # Update the category
            previous_category = reason.category
            previous_category.order = category_index
            previous_category.save(update_fields=['order'])

            # Update the indexes
            reason_index = 0
            category_index += 1

        # Update the reason
        reason.order = reason_index
        reason.save(update_fields=['order'])

        # Update the indexes
        reason_index += 1


class Migration(migrations.Migration):

    dependencies = [
        ('admission', '0140_sic_mail_templates'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='refusalreason',
            options={
                'ordering': ('order',),
                'verbose_name': 'Refusal reason',
                'verbose_name_plural': 'Refusal reasons',
            },
        ),
        migrations.AlterModelOptions(
            name='refusalreasoncategory',
            options={
                'ordering': ('order',),
                'verbose_name': 'Refusal reason category',
                'verbose_name_plural': 'Refusal reason categories',
            },
        ),
        migrations.AddField(
            model_name='refusalreason',
            name='order',
            field=models.PositiveIntegerField(db_index=True, default=0, editable=False, verbose_name='order'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='refusalreasoncategory',
            name='order',
            field=models.PositiveIntegerField(db_index=True, default=0, editable=False, verbose_name='order'),
            preserve_default=False,
        ),
        migrations.RunPython(set_initial_order, migrations.RunPython.noop),
    ]