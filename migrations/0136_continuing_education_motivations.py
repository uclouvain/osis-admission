# Generated by Django 3.2.23 on 2024-01-05 11:44

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admission', '0135_alter_baseadmission_determined_pool'),
    ]

    operations = [
        migrations.AddField(
            model_name='continuingeducationadmission',
            name='motivations',
            field=models.TextField(blank=True, default='', max_length=1000, verbose_name='Motivations'),
        ),
        migrations.AddField(
            model_name='continuingeducationadmission',
            name='ways_to_find_out_about_the_course',
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.CharField(
                    choices=[
                        ('SITE_WEB_UCLOUVAIN', 'Via the website of UCLouvain'),
                        ('SITE_FORMATION_CONTINUE', 'Via the website of the continuing education'),
                        ('PRESSE', 'On the press'),
                        ('FACEBOOK', 'Via Facebook'),
                        ('LINKEDIN', 'Via LinkedIn'),
                        ('COURRIER_PERSONNALISE', 'Via a personalized letter'),
                        ('EMAILING', 'Via an emailing'),
                        ('BOUCHE_A_OREILLE', 'Via word of mouth'),
                        ('AMIS', 'Via friends'),
                        ('ANCIENS_ETUDIANTS', 'Via former students'),
                        ('MOOCS', 'Via MOOCs'),
                        ('AUTRE', 'Other'),
                    ],
                    max_length=30,
                ),
                blank=True,
                default=list,
                size=None,
                verbose_name='How did the candidate find out about this course?',
            ),
        ),
    ]
