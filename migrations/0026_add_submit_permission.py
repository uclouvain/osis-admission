# Generated by Django 2.2.24 on 2022-02-10 12:43

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('admission', '0025_thesis_language_default'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='doctorateadmission',
            options={
                'ordering': ('-created',),
                'permissions': [
                    ('download_jury_approved_pdf', 'Can download jury-approved PDF'),
                    ('upload_jury_approved_pdf', 'Can upload jury-approved PDF'),
                    ('upload_signed_scholarship', 'Can upload signed scholarship'),
                    ('check_publication_authorisation', 'Can check publication autorisation'),
                    ('validate_registration', 'Can validate registration'),
                    ('approve_jury', 'Can approve jury'),
                    ('approve_confirmation_paper', 'Can approve confirmation paper'),
                    ('validate_doctoral_training', 'Can validate doctoral training'),
                    ('download_pdf_confirmation', 'Can download PDF confirmation'),
                    ('upload_pdf_confirmation', 'Can upload PDF confirmation'),
                    ('fill_thesis', 'Can fill thesis'),
                    ('submit_thesis', 'Can submit thesis'),
                    ('appose_cdd_notice', 'Can appose CDD notice'),
                    ('appose_sic_notice', 'Can appose SIC notice'),
                    ('upload_defense_report', 'Can upload defense report'),
                    ('check_copyright', 'Can check copyright'),
                    ('sign_diploma', 'Can sign diploma'),
                    ('request_signatures', 'Can request signatures'),
                    ('approve_proposition', 'Can approve proposition'),
                    (
                        'view_doctorateadmission_person',
                        'Can view the information related to the admission request author',
                    ),
                    (
                        'change_doctorateadmission_person',
                        'Can update the information related to the admission request author',
                    ),
                    ('view_doctorateadmission_coordinates', 'Can view the coordinates of the admission request author'),
                    (
                        'change_doctorateadmission_coordinates',
                        'Can update the coordinates of the admission request author',
                    ),
                    (
                        'view_doctorateadmission_secondary_studies',
                        'Can view the information related to the secondary studies',
                    ),
                    (
                        'change_doctorateadmission_secondary_studies',
                        'Can update the information related to the secondary studies',
                    ),
                    ('view_doctorateadmission_languages', 'Can view the information related to language knowledge'),
                    ('change_doctorateadmission_languages', 'Can update the information related to language knowledge'),
                    ('view_doctorateadmission_curriculum', 'Can view the information related to the curriculum'),
                    ('change_doctorateadmission_curriculum', 'Can update the information related to the curriculum'),
                    ('view_doctorateadmission_project', 'Can view the information related to the admission project'),
                    (
                        'change_doctorateadmission_project',
                        'Can update the information related to the admission project',
                    ),
                    (
                        'view_doctorateadmission_cotutelle',
                        'Can view the information related to the admission cotutelle',
                    ),
                    (
                        'change_doctorateadmission_cotutelle',
                        'Can update the information related to the admission cotutelle',
                    ),
                    (
                        'view_doctorateadmission_supervision',
                        'Can view the information related to the admission supervision',
                    ),
                    (
                        'change_doctorateadmission_supervision',
                        'Can update the information related to the admission supervision',
                    ),
                    ('add_supervision_member', 'Can add a member to the supervision group'),
                    ('remove_supervision_member', 'Can remove a member from the supervision group'),
                    ('submit_doctorateadmission', 'Can submit a doctorate admission proposition'),
                ],
                'verbose_name': 'Doctorate admission',
            },
        ),
    ]
