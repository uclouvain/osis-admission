# Generated by Django 2.2.13 on 2021-10-27 16:22

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('osis_signature', '0001_initial'),
        ('base', '0615_auto_20211026_1027'),
        ('admission', '0003_cotutelle'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='CommitteeActor',
            new_name='SupervisionActor',
        ),
        migrations.RenameField(
            model_name='doctorateadmission',
            old_name='committee',
            new_name='supervision_group',
        ),
    ]
