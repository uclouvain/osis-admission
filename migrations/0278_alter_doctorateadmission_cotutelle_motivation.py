from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("admission", "0277_alter_baseadmission_determined_pool"),
    ]

    operations = [
        migrations.AlterField(
            model_name="doctorateadmission",
            name="cotutelle_motivation",
            field=models.CharField(blank=True, default="", max_length=1024, verbose_name="Motivation"),
        ),
    ]
