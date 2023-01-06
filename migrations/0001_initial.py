# Generated by Django 2.2.13 on 2021-09-16 15:20

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion
import osis_document.contrib.fields
import osis_signature.contrib.fields
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('base', '0592_auto_20210812_1142'),
        ('osis_signature', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CommitteeActor',
            fields=[
                ('actor_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='osis_signature.Actor')),
                ('type', models.CharField(default=(('MAIN_PROMOTER', 'Main promoter'), ('PROMOTER', 'Promoter'), ('CA_MEMBER', 'CA Member')), max_length=50)),
            ],
            bases=('osis_signature.actor',),
        ),
        migrations.CreateModel(
            name='EntityProxy',
            fields=[
            ],
            options={
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('base.entity',),
        ),
        migrations.CreateModel(
            name='SicManager',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('with_child', models.BooleanField(default=False)),
                ('entity', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='base.Entity')),
                ('person', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='base.Person')),
            ],
            options={
                'verbose_name': 'Role: SIC manager',
                'verbose_name_plural': 'Role: SIC managers',
            },
        ),
        migrations.CreateModel(
            name='SicDirector',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('with_child', models.BooleanField(default=False)),
                ('entity', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='base.Entity')),
                ('person', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='base.Person')),
            ],
            options={
                'verbose_name': 'Role: SIC director',
                'verbose_name_plural': 'Role: SIC directors',
            },
        ),
        migrations.CreateModel(
            name='Sceb',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('with_child', models.BooleanField(default=False)),
                ('entity', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='base.Entity')),
                ('person', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='base.Person')),
            ],
            options={
                'verbose_name': 'Role: SCEB',
                'verbose_name_plural': 'Role: SCEBs',
            },
        ),
        migrations.CreateModel(
            name='Promoter',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('with_child', models.BooleanField(default=False)),
                ('entity', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='base.Entity')),
                ('person', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='base.Person')),
            ],
            options={
                'verbose_name': 'Role: Promoter',
                'verbose_name_plural': 'Role: Promoters',
            },
        ),
        migrations.CreateModel(
            name='JurySecretary',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('with_child', models.BooleanField(default=False)),
                ('entity', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='base.Entity')),
                ('person', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='base.Person')),
            ],
            options={
                'verbose_name': 'Role: Jury secretary',
                'verbose_name_plural': 'Role: Jury secretaries',
            },
        ),
        migrations.CreateModel(
            name='DoctorateAdmission',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True)),
                ('type', models.CharField(choices=[('ADMISSION', 'Admission'), ('PRE_ADMISSION', 'Pre-Admission')], db_index=True, default='ADMISSION', max_length=255, verbose_name='Type')),
                ('comment', models.TextField(blank=True, default='', verbose_name='Comment')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='Created')),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='Modified')),
                ('bureau', models.CharField(blank=True, choices=[('ECONOMY', 'ECONOMY'), ('MANAGEMENT', 'MANAGEMENT')], default='', max_length=255, verbose_name='Bureau')),
                ('financing_type', models.CharField(blank=True, choices=[('WORK_CONTRACT', 'WORK_CONTRACT'), ('SEARCH_SCHOLARSHIP', 'SEARCH_SCHOLARSHIP'), ('SELF_FUNDING', 'SELF_FUNDING')], default='', max_length=255, verbose_name='Financing type')),
                ('financing_work_contract', models.CharField(blank=True, default='', max_length=255, verbose_name='Working contract type')),
                ('financing_eft', models.PositiveSmallIntegerField(blank=True, null=True, verbose_name='EFT')),
                ('scholarship_grant', models.CharField(blank=True, default='', max_length=255, verbose_name='Scholarship grant')),
                ('planned_duration', models.PositiveSmallIntegerField(blank=True, null=True, verbose_name='Planned duration')),
                ('dedicated_time', models.PositiveSmallIntegerField(blank=True, null=True, verbose_name='Dedicated time (in EFT)')),
                ('project_title', models.CharField(blank=True, default='', max_length=1023, verbose_name='Project title')),
                ('project_abstract', models.TextField(blank=True, default='', verbose_name='Abstract')),
                ('thesis_language', models.CharField(blank=True, default='', max_length=255, verbose_name='Thesis language')),
                ('project_document', osis_document.contrib.fields.FileField(base_field=models.UUIDField(), default=list, size=None, verbose_name='Project')),
                ('gantt_graph', osis_document.contrib.fields.FileField(base_field=models.UUIDField(), default=list, size=None, verbose_name='Gantt graph')),
                ('program_proposition', osis_document.contrib.fields.FileField(base_field=models.UUIDField(), default=list, size=None, verbose_name='Program proposition')),
                ('additional_training_project', osis_document.contrib.fields.FileField(base_field=models.UUIDField(), default=list, size=None, verbose_name='Complementary training proposition')),
                ('phd_already_done', models.CharField(blank=True, choices=[('YES', 'YES'), ('NO', 'NO'), ('PARTIAL', 'PARTIAL')], default='', max_length=255, verbose_name='PhD already done')),
                ('phd_already_done_institution', models.CharField(blank=True, default='', max_length=255, verbose_name='Institution')),
                ('phd_already_done_defense_date', models.DateField(blank=True, null=True, verbose_name='Defense')),
                ('phd_already_done_no_defense_reason', models.CharField(blank=True, default='', max_length=255, verbose_name='No defense reason')),
                ('detailed_status', django.contrib.postgres.fields.jsonb.JSONField(default=dict)),
                ('candidate', models.ForeignKey(editable=False, on_delete=django.db.models.deletion.PROTECT, related_name='admissions', to='base.Person', verbose_name='Candidate')),
                ('committee', osis_signature.contrib.fields.SignatureProcessField(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, to='osis_signature.Process')),
                ('doctorate', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='base.EducationGroupYear', verbose_name='Doctorate')),
            ],
            options={
                'verbose_name': 'Doctorate admission',
                'ordering': ('-created',),
                'permissions': [('access_doctorateadmission', 'Can access doctorate admission list'), ('download_jury_approved_pdf', 'Can download jury-approved PDF'), ('upload_jury_approved_pdf', 'Can upload jury-approved PDF'), ('upload_signed_scholarship', 'Can upload signed scholarship'), ('check_publication_authorisation', 'Can check publication autorisation'), ('validate_registration', 'Can validate registration'), ('approve_jury', 'Can approve jury'), ('approve_confirmation_paper', 'Can approve confirmation paper'), ('validate_doctoral_training', 'Can validate doctoral training'), ('download_pdf_confirmation', 'Can download PDF confirmation'), ('upload_pdf_confirmation', 'Can upload PDF confirmation'), ('fill_thesis', 'Can fill thesis'), ('submit_thesis', 'Can submit thesis'), ('appose_cdd_notice', 'Can appose CDD notice'), ('appose_sic_notice', 'Can appose SIC notice'), ('upload_defense_report', 'Can upload defense report'), ('check_copyright', 'Can check copyright'), ('sign_diploma', 'Can sign diploma')],
            },
        ),
        migrations.CreateModel(
            name='CommitteeMember',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('with_child', models.BooleanField(default=False)),
                ('entity', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='base.Entity')),
                ('person', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='base.Person')),
            ],
            options={
                'verbose_name': 'Role: Committee member',
                'verbose_name_plural': 'Role: Committee members',
            },
        ),
        migrations.CreateModel(
            name='CddManager',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('with_child', models.BooleanField(default=False)),
                ('entity', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='base.Entity')),
                ('person', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='base.Person')),
            ],
            options={
                'verbose_name': 'Role: CDD manager',
                'verbose_name_plural': 'Role: CDD managers',
            },
        ),
        migrations.CreateModel(
            name='Candidate',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('with_child', models.BooleanField(default=False)),
                ('entity', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='base.Entity')),
                ('person', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='base.Person')),
            ],
            options={
                'verbose_name': 'Role: Candidate',
                'verbose_name_plural': 'Role: Candidates',
            },
        ),
        migrations.CreateModel(
            name='Adre',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('with_child', models.BooleanField(default=False)),
                ('entity', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='base.Entity')),
                ('person', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='base.Person')),
            ],
            options={
                'verbose_name': 'Role: ADRE',
                'verbose_name_plural': 'Role: ADREs',
            },
        ),
    ]
