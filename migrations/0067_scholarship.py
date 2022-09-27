# Generated by Django 3.2.12 on 2022-10-07 17:39

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('admission', '0066_training_contexts'),
    ]

    operations = [
        migrations.CreateModel(
            name='Scholarship',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True)),
                ('short_name', models.CharField(max_length=50, verbose_name='Short name')),
                ('long_name', models.CharField(blank=True, default='', max_length=255, verbose_name='Long name')),
                ('deleted', models.BooleanField(default=False, verbose_name='Deleted')),
                (
                    'type',
                    models.CharField(
                        choices=[
                            ('DOUBLE_TRIPLE_DIPLOMATION', 'Double or triple diplomation'),
                            ('BOURSE_INTERNATIONALE_DOCTORAT', 'International for doctorate'),
                            ('BOURSE_INTERNATIONALE_FORMATION_GENERALE', 'International for general education'),
                            ('ERASMUS_MUNDUS', 'Erasmus Mundus'),
                        ],
                        max_length=50,
                        verbose_name='Type',
                    ),
                ),
            ],
            options={
                'verbose_name': 'Scholarship',
            },
        ),
    ]
