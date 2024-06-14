# Generated by Django 3.2.25 on 2024-05-22 14:49

from django.db import migrations, models
import django.db.models.deletion
from osis_mail_template import MailTemplateMigration

from admission.mail_templates import ADMISSION_EMAIL_FINANCABILITY_DISPENSATION_NOTIFICATION


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0681_auto_20240422_1702'),
        ('admission', '0184_alter_categorizedfreedocument_checklist_tab'),
    ]

    operations = [
        migrations.AddField(
            model_name='generaleducationadmission',
            name='financability_dispensation_first_notification_by',
            field=models.ForeignKey(
                editable=False,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='+',
                to='base.person',
                verbose_name='Financability dispensation first notification by',
            ),
        ),
        migrations.AddField(
            model_name='generaleducationadmission',
            name='financability_dispensation_first_notification_on',
            field=models.DateTimeField(
                editable=False, null=True, verbose_name='Financability dispensation first notification on'
            ),
        ),
        migrations.AddField(
            model_name='generaleducationadmission',
            name='financability_dispensation_last_notification_by',
            field=models.ForeignKey(
                editable=False,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='+',
                to='base.person',
                verbose_name='Financability dispensation last notification by',
            ),
        ),
        migrations.AddField(
            model_name='generaleducationadmission',
            name='financability_dispensation_last_notification_on',
            field=models.DateTimeField(
                editable=False, null=True, verbose_name='Financability dispensation last notification on'
            ),
        ),
        migrations.AddField(
            model_name='generaleducationadmission',
            name='financability_dispensation_status',
            field=models.CharField(
                choices=[
                    ('NON_CONCERNE', 'NON_CONCERNE'),
                    ('CANDIDAT_NOTIFIE', 'CANDIDAT_NOTIFIE'),
                    ('ABANDON_DU_CANDIDAT', 'ABANDON_DU_CANDIDAT'),
                    ('REFUS_DE_DEROGATION_FACULTAIRE', 'REFUS_DE_DEROGATION_FACULTAIRE'),
                    ('ACCORD_DE_DEROGATION_FACULTAIRE', 'ACCORD_DE_DEROGATION_FACULTAIRE'),
                ],
                default='',
                max_length=100,
                verbose_name='Financability dispensation status',
            ),
        ),
        MailTemplateMigration(
            ADMISSION_EMAIL_FINANCABILITY_DISPENSATION_NOTIFICATION,
            {
                'en': '{academic_year} enrolment application ineligible for funding: exemption required',
                'fr-be': "Demande d'inscription {academic_year} non finançable : Dérogation nécessaire",
            },
            {
                'en': '''<p>Your file number: {admission_reference}</p>
    <p>Dear {candidate_first_name} {candidate_last_name},</p>
    <p>Thank you for applying to enrol in the course {training_title} [{training_acronym}] ({training_campus}).</p>
    <p>After reviewing your academic curriculum and in accordance with the decree of 11 April 2014 adapting the funding of higher education institutions to the latest restructuring of higher education, it appears from the information you have provided and/or at our disposal that, per the meaning of the aforementioned decree, you are ineligible for funding.</p>
    <p>However, if you have specific arguments to put forward, you can apply for a faculty exemption with a view to enrolment. To do so, please contact your faculty (<a href="{contact_link}">{contact_link}</a>) as soon as possible to learn how to apply for an exemption.</p>
    <p>For your information, and as a general rule, an exemption application must be made in writing and accompanied by a curriculum vitae, a letter of motivation and a copy of the detailed results of all previous years of higher education (transcripts).</p>
    <p>The faculty will inform the Enrolment Office of its decision. If the faculty’s decision is favourable, the Enrolment Office will validate your application for (re)enrolment as soon as it is received. If the decision is not favourable, you will receive as soon as possible an official letter denying enrolment.</p>
    <p>We are aware of the disappointment that this letter may cause. Please do consult your faculty to determine whether an exemption is possible.</p>
    <p>Sincerely,</p>
    <p>The UCLouvain Enrolment Office</p>
    <p><a href="https://uclouvain.be/en/study/inscriptions">https://uclouvain.be/en/study/inscriptions</a></p>
    ''',
                'fr-be': '''<p>Votre numéro de dossier : {admission_reference}</p>
    <p>{greetings} {candidate_first_name} {candidate_last_name},</p>
    <p>Votre demande d'inscription au programme {training_title} [{training_acronym}] ({training_campus}) nous est bien parvenue et nous vous en remercions.</p>
    <p>Après analyse de votre curriculum académique et conformément au décret du 11 avril 2014 adaptant le financement des établissements d'enseignement supérieur à la nouvelle organisation des études, il ressort des informations que vous nous avez fournies et/ou dont nous disposons que vous n’êtes pas finançable au sens du décret précité.</p>
    <p>Toutefois, si vous disposez d’arguments particuliers à faire valoir, vous pouvez introduire une demande de dérogation facultaire en vue d’une inscription. Pour ce faire, veuillez contacter votre faculté (<a href="{contact_link}">{contact_link}</a>) dans les plus brefs délais afin de connaître les modalités en vue d'introduire une demande de dérogation.</p>
    <p>Pour votre information et de manière générale, une demande de dérogation doit être introduite par écrit et être accompagnée d'un curriculum vitae, d’une lettre de motivation et d'une copie des résultats détaillés de toutes les années d'études supérieures antérieures (relevés de notes).</p>
    <p>La faculté communiquera sa décision au Service des inscriptions. En cas de décision favorable de la faculté et dès sa réception, le Service des inscriptions validera votre demande de (ré)inscription. Dans le cas contraire, un courrier officiel de refus d’inscription vous parviendra dans les meilleurs délais.</p>
    <p>Consciente de la déception que ce courrier pourrait susciter, nous vous prions néanmoins d’agréer, {greetings_end}, l'expression de nos salutations distinguées.</p>
    <p>Le Service des inscriptions de l'UCLouvain.</p>
    <p><a href="https://uclouvain.be/fr/etudier/inscriptions">https://uclouvain.be/fr/etudier/inscriptions</a>.</p>
    ''',
            },
        ),
    ]
