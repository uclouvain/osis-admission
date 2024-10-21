# Generated by Django 3.2.25 on 2024-10-29 16:25

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('admission', '0232_cdd_configuration_for_more_entities'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='activity',
            name='country',
        ),
        migrations.RemoveField(
            model_name='activity',
            name='doctorate',
        ),
        migrations.RemoveField(
            model_name='activity',
            name='learning_unit_year',
        ),
        migrations.RemoveField(
            model_name='activity',
            name='parent',
        ),
        migrations.RemoveField(
            model_name='cddconfiguration',
            name='cdd',
        ),
        migrations.RemoveField(
            model_name='cddconfigurator',
            name='entity',
        ),
        migrations.RemoveField(
            model_name='cddconfigurator',
            name='person',
        ),
        migrations.AlterUniqueTogether(
            name='cddmailtemplate',
            unique_together=None,
        ),
        migrations.RemoveField(
            model_name='cddmailtemplate',
            name='cdd',
        ),
        migrations.RemoveField(
            model_name='confirmationpaper',
            name='admission',
        ),
        migrations.RemoveField(
            model_name='internalnote',
            name='admission',
        ),
        migrations.RemoveField(
            model_name='internalnote',
            name='author',
        ),
        migrations.RemoveField(
            model_name='jurymember',
            name='country',
        ),
        migrations.RemoveField(
            model_name='jurymember',
            name='doctorate',
        ),
        migrations.RemoveField(
            model_name='jurymember',
            name='person',
        ),
        migrations.RemoveField(
            model_name='jurymember',
            name='promoter',
        ),
        migrations.RemoveField(
            model_name='jurysecretary',
            name='person',
        ),
        migrations.DeleteModel(
            name='DoctorateProxy',
        ),
        migrations.AlterModelOptions(
            name='doctorateadmission',
            options={'ordering': ('-created_at',), 'permissions': [('upload_signed_scholarship', 'Can upload signed scholarship'), ('check_publication_authorisation', 'Can check publication autorisation'), ('validate_registration', 'Can validate registration'), ('download_pdf_confirmation', 'Can download PDF confirmation'), ('upload_pdf_confirmation', 'Can upload PDF confirmation'), ('fill_thesis', 'Can fill thesis'), ('submit_thesis', 'Can submit thesis'), ('appose_cdd_notice', 'Can appose CDD notice'), ('appose_sic_notice', 'Can appose SIC notice'), ('upload_defense_report', 'Can upload defense report'), ('check_copyright', 'Can check copyright'), ('sign_diploma', 'Can sign diploma'), ('request_signatures', 'Can request signatures'), ('approve_proposition', 'Can approve proposition'), ('view_admission_person', 'Can view the information related to the admission request author'), ('change_admission_person', 'Can update the information related to the admission request author'), ('view_admission_coordinates', 'Can view the coordinates of the admission request author'), ('change_admission_coordinates', 'Can update the coordinates of the admission request author'), ('view_admission_secondary_studies', 'Can view the information related to the secondary studies'), ('change_admission_secondary_studies', 'Can update the information related to the secondary studies'), ('view_admission_languages', 'Can view the information related to language knowledge'), ('change_admission_languages', 'Can update the information related to language knowledge'), ('view_admission_curriculum', 'Can view the information related to the curriculum'), ('change_admission_curriculum', 'Can update the information related to the curriculum'), ('view_admission_project', 'Can view the information related to the admission project'), ('change_admission_project', 'Can update the information related to the admission project'), ('view_admission_cotutelle', 'Can view the information related to the admission cotutelle'), ('change_admission_cotutelle', 'Can update the information related to the admission cotutelle'), ('view_admission_supervision', 'Can view the information related to the admission supervision'), ('change_admission_supervision', 'Can update the information related to the admission supervision'), ('add_supervision_member', 'Can add a member to the supervision group'), ('remove_supervision_member', 'Can remove a member from the supervision group'), ('submit_doctorateadmission', 'Can submit a doctorate admission proposition')], 'verbose_name': 'Doctorate admission'},
        ),
        migrations.RemoveField(
            model_name='doctorateadmission',
            name='accounting_situation',
        ),
        migrations.RemoveField(
            model_name='doctorateadmission',
            name='comment_about_jury',
        ),
        migrations.RemoveField(
            model_name='doctorateadmission',
            name='defense_indicative_date',
        ),
        migrations.RemoveField(
            model_name='doctorateadmission',
            name='defense_language',
        ),
        migrations.RemoveField(
            model_name='doctorateadmission',
            name='defense_method',
        ),
        migrations.RemoveField(
            model_name='doctorateadmission',
            name='jury_approval',
        ),
        migrations.RemoveField(
            model_name='doctorateadmission',
            name='post_enrolment_status',
        ),
        migrations.RemoveField(
            model_name='doctorateadmission',
            name='thesis_proposed_title',
        ),
        migrations.DeleteModel(
            name='Activity',
        ),
        migrations.DeleteModel(
            name='CddConfiguration',
        ),
        migrations.DeleteModel(
            name='CddConfigurator',
        ),
        migrations.DeleteModel(
            name='CddMailTemplate',
        ),
        migrations.DeleteModel(
            name='ConfirmationPaper',
        ),
        migrations.DeleteModel(
            name='InternalNote',
        ),
        migrations.DeleteModel(
            name='JuryMember',
        ),
        migrations.DeleteModel(
            name='JurySecretary',
        ),
    ]
