# Generated by Django 3.2.25 on 2024-09-04 15:25

import admission.contrib.models.form_item
import django.contrib.postgres.fields
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import osis_document.contrib.fields
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('osis_profile', '0029_auto_20240507_1158'),
        ('base', '0700_auto_20240831_0115'),
        ('admission', '0222_default_continuing_workinglists'),
    ]

    operations = [
        migrations.CreateModel(
            name='DoctorateWorkingList',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order', models.PositiveIntegerField(db_index=True, editable=False, verbose_name='order')),
                (
                    'name',
                    admission.contrib.models.form_item.TranslatedJSONField(
                        default=dict,
                        validators=[admission.contrib.models.form_item.is_valid_translated_json_field],
                        verbose_name='Name of the working list',
                    ),
                ),
                (
                    'checklist_filters_mode',
                    models.CharField(
                        blank=True,
                        choices=[('INCLUSION', 'Include'), ('EXCLUSION', 'Exclude')],
                        default='',
                        max_length=16,
                        verbose_name='Checklist filters mode',
                    ),
                ),
                ('checklist_filters', models.JSONField(blank=True, default=dict, verbose_name='Checklist filters')),
                (
                    'admission_type',
                    models.CharField(
                        blank=True,
                        choices=[('ADMISSION', 'ADMISSION'), ('INSCRIPTION', 'INSCRIPTION')],
                        default='',
                        max_length=16,
                        verbose_name='Admission type',
                    ),
                ),
                (
                    'admission_statuses',
                    django.contrib.postgres.fields.ArrayField(
                        base_field=models.CharField(
                            choices=[
                                ('EN_BROUILLON', 'In draft form'),
                                ('EN_ATTENTE_DE_SIGNATURE', 'Waiting for signature'),
                                ('CONFIRMEE', 'Application confirmed'),
                                ('ANNULEE', 'Cancelled application'),
                                ('TRAITEMENT_FAC', 'Processing by Fac'),
                                ('A_COMPLETER_POUR_FAC', 'To be completed for Fac'),
                                ('COMPLETEE_POUR_FAC', 'Completed for Fac'),
                                ('RETOUR_DE_FAC', 'Feedback from Fac'),
                                ('A_COMPLETER_POUR_SIC', 'To be completed for the Enrolment Office (SIC)'),
                                ('COMPLETEE_POUR_SIC', 'Completed for SIC'),
                                ('ATTENTE_VALIDATION_DIRECTION', 'Awaiting management approval'),
                                ('CLOTUREE', 'Closed'),
                                ('INSCRIPTION_AUTORISEE', 'Application accepted'),
                                ('INSCRIPTION_REFUSEE', 'Application denied'),
                            ],
                            max_length=30,
                        ),
                        blank=True,
                        default=list,
                        size=None,
                        verbose_name='Admission statuses',
                    ),
                ),
            ],
            options={
                'verbose_name': 'Doctorate working list',
                'verbose_name_plural': 'Doctorate working lists',
                'ordering': ('order',),
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='doctorateadmission',
            name='additional_approval_conditions',
            field=models.ManyToManyField(
                blank=True,
                related_name='_admission_doctorateadmission_additional_approval_conditions_+',
                to='admission.AdditionalApprovalCondition',
                verbose_name='Additional approval conditions',
            ),
        ),
        migrations.AddField(
            model_name='doctorateadmission',
            name='admission_requirement',
            field=models.CharField(
                blank=True,
                choices=[
                    ('NON_CONCERNE', 'Non concerné'),
                    ('SNU_PASSERELLE_1', 'SNU Passerelle 1'),
                    ('SNU_PASSERELLE_3', 'SNU Passerelle 3'),
                    ('VAE', 'VAE'),
                    ('PROGRAMME_AMENAGE', 'Progr. aménagé'),
                    ('VALORISATION_180_ECTS', 'Valorisation 180 ECTS'),
                    ('VALORISATION_240_ECTS', 'Valorisation 240 ECTS'),
                    ('VALORISATION_300_ECTS', 'Valorisation 300 ECTS'),
                    ('SECONDAIRE', 'SEC'),
                    ('BAC', 'BAC'),
                    ('BAC_EPM', 'BAC - EPM'),
                    ('BAMA15', 'BAMA15'),
                    ('MASTER', 'Master'),
                    ('UNI_SNU_AUTRE', 'UNI/SNU Autres'),
                    ('PARCOURS', 'Parcours'),
                    ('EXAMEN_ADMISSION', 'Examen admission'),
                    ('SNU_TYPE_COURT', 'SNU Type court'),
                    ('SNU_TYPE_LONG_1ER_CYCLE', 'SNU Type long 1er cycle'),
                    ('SNU_TYPE_LONG_2EME_CYCLE', 'SNU Type long 2ème cycle'),
                    ('MASTER_EPM', 'Master - EPM'),
                    ('BAC_MASTER_ANTICIPE', 'BAC (Master anticipé)'),
                    ('INDETERMINE', 'indéterminé'),
                ],
                default='',
                max_length=30,
                verbose_name='Admission requirement',
            ),
        ),
        migrations.AddField(
            model_name='doctorateadmission',
            name='admission_requirement_year',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='+',
                to='base.academicyear',
                verbose_name='Admission requirement year',
            ),
        ),
        migrations.AddField(
            model_name='doctorateadmission',
            name='annual_program_contact_person_email',
            field=models.EmailField(
                blank=True,
                default='',
                max_length=254,
                verbose_name='Email of the contact person for the design of the annual program',
            ),
        ),
        migrations.AddField(
            model_name='doctorateadmission',
            name='annual_program_contact_person_name',
            field=models.CharField(
                blank=True,
                default='',
                max_length=255,
                verbose_name='Name of the contact person for the design of the annual program',
            ),
        ),
        migrations.AddField(
            model_name='doctorateadmission',
            name='communication_to_the_candidate',
            field=models.TextField(blank=True, default='', verbose_name='Communication to the candidate'),
        ),
        migrations.AddField(
            model_name='doctorateadmission',
            name='diplomatic_post',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to='admission.diplomaticpost',
                verbose_name='Diplomatic post',
            ),
        ),
        migrations.AddField(
            model_name='doctorateadmission',
            name='dispensation_needed',
            field=models.CharField(
                choices=[
                    ('NON_CONCERNE', 'NON_CONCERNE'),
                    ('AVIS_DIRECTION_DEMANDE', 'AVIS_DIRECTION_DEMANDE'),
                    ('BESOIN_DE_COMPLEMENT', 'BESOIN_DE_COMPLEMENT'),
                    ('REFUS_DIRECTION', 'REFUS_DIRECTION'),
                    ('ACCORD_DIRECTION', 'ACCORD_DIRECTION'),
                ],
                default='',
                max_length=50,
                verbose_name='Dispensation needed',
            ),
        ),
        migrations.AddField(
            model_name='doctorateadmission',
            name='fac_approval_certificate',
            field=osis_document.contrib.fields.FileField(
                base_field=models.UUIDField(),
                blank=True,
                default=list,
                size=None,
                verbose_name='Approval certificate of faculty',
            ),
        ),
        migrations.AddField(
            model_name='doctorateadmission',
            name='fac_refusal_certificate',
            field=osis_document.contrib.fields.FileField(
                base_field=models.UUIDField(),
                blank=True,
                default=list,
                size=None,
                verbose_name='Refusal certificate of faculty',
            ),
        ),
        migrations.AddField(
            model_name='doctorateadmission',
            name='financability_computed_rule',
            field=models.CharField(
                choices=[
                    ('NON_CONCERNE', 'Non concerné'),
                    ('FINANCABLE', 'Financable'),
                    ('NON_FINANCABLE', 'Non financable'),
                    ('A_CLARIFIER', 'A clarifier'),
                    ('AUTORISE_A_POURSUIVRE', 'Autorisé à poursuivre'),
                ],
                default='',
                editable=False,
                max_length=100,
                verbose_name='Financability computed rule',
            ),
        ),
        migrations.AddField(
            model_name='doctorateadmission',
            name='financability_computed_rule_on',
            field=models.DateTimeField(editable=False, null=True, verbose_name='Financability computed rule on'),
        ),
        migrations.AddField(
            model_name='doctorateadmission',
            name='financability_computed_rule_situation',
            field=models.CharField(
                choices=[
                    ('PREMIERE_INSCRIPTION', 'Première inscription au cycle'),
                    ('FINANCABLE_D_OFFICE', "Financable d'office"),
                    ('DROIT_A_ANNEES_SUPPLEMENTAIRES', 'A droit à des années supplémentaires'),
                    ('PARCOURS_A_TOILETTER', 'Parcours antérieur à toiletter'),
                    ('REPRISE_APRES_5_ANS', 'Reprise après interruption de 5 ans'),
                    ('DOUBLE_INSCRIPTION_MEME_CYCLE_A_CLARIFIER', 'Double inscription du même cycle'),
                    ('A_PASSE_CONCOURS_2X', 'A passé 2 fois le concours'),
                    ('ACQUIS_100_POURCENT_EN_N_MOINS_1', 'A acquis 100% année précédente'),
                    ('PLUS_FINANCABLE', "N'est plus financable"),
                    ('CREDITS_ACQUIS_A_CLARIFIER', 'Crédits acquis à clarifier'),
                    ('MORATOIRE_ARTICLE2', 'Moratoire Article 2'),
                    ('FINANCABILITE_2023_A_CLARIFIER', 'Financabilité 2023 à clarifier'),
                    ('PREMIERE_INSCRIPTION_FORMATION_DOCTORALE', 'Première inscription à la formation doctorale'),
                    ('VALIDE_60_CREDITS_BLOC_1', 'A validé 60 crédits de bloc 1'),
                    ('N_A_PAS_VALIDE_60_CREDITS_BLOC_1', "N'a pas validé 60 crédits de bloc 1"),
                    ('REUSSI_1_UE_BLOC_1', 'A réussi 1 UE du bloc 1'),
                    ('N_A_PAS_REUSSI_1_UE_BLOC_1', "N'a pas réussi 1 UE du bloc 1"),
                    ('VALIDE_120_CREDITS_BACHELIER', 'A validé 120 crédits du bachelier'),
                    ('N_A_PAS_VALIDE_120_CREDITS_BACHELIER', "N'a pas validé 120 crédits du bachelier"),
                    ('CREDIT_BLOC1_A_CLARIFIER', 'Crédits du bloc 1 à clarifier'),
                    ('MORATOIRE_ARTICLE3', 'Moratoire Article 3'),
                    (
                        'N_A_PAS_VALIDE_MODULE_COMPLEMENTAIRE_EN_2_ANS',
                        "N'a pas validé le module complémentaire en 2 ans",
                    ),
                    ('A_ATTEINT_BALISES_MASTER', 'A atteint les balises de Master'),
                    ('N_A_PAS_ATTEINT_BALISES_MASTER', "N'a pas atteint les balises de Master"),
                    ('CREDIT_MODULE_COMPLEMENTAIRE_A_CLARIFIER', 'Crédits du module complémentaire à clarifier'),
                ],
                default='',
                editable=False,
                max_length=100,
                verbose_name='Financability computed rule situation',
            ),
        ),
        migrations.AddField(
            model_name='doctorateadmission',
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
            model_name='doctorateadmission',
            name='financability_dispensation_first_notification_on',
            field=models.DateTimeField(
                editable=False,
                null=True,
                verbose_name='Financability dispensation first notification on',
            ),
        ),
        migrations.AddField(
            model_name='doctorateadmission',
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
            model_name='doctorateadmission',
            name='financability_dispensation_last_notification_on',
            field=models.DateTimeField(
                editable=False,
                null=True,
                verbose_name='Financability dispensation last notification on',
            ),
        ),
        migrations.AddField(
            model_name='doctorateadmission',
            name='financability_dispensation_status',
            field=models.CharField(
                blank=True,
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
        migrations.AddField(
            model_name='doctorateadmission',
            name='financability_rule',
            field=models.CharField(
                blank=True,
                choices=[
                    ('PREMIERE_INSCRIPTION', 'Première inscription au cycle'),
                    ('FINANCABLE_D_OFFICE', "Financable d'office"),
                    ('DROIT_A_ANNEES_SUPPLEMENTAIRES', 'A droit à des années supplémentaires'),
                    ('PARCOURS_A_TOILETTER', 'Parcours antérieur à toiletter'),
                    ('REPRISE_APRES_5_ANS', 'Reprise après interruption de 5 ans'),
                    ('DOUBLE_INSCRIPTION_MEME_CYCLE_A_CLARIFIER', 'Double inscription du même cycle'),
                    ('A_PASSE_CONCOURS_2X', 'A passé 2 fois le concours'),
                    ('ACQUIS_100_POURCENT_EN_N_MOINS_1', 'A acquis 100% année précédente'),
                    ('PLUS_FINANCABLE', "N'est plus financable"),
                    ('CREDITS_ACQUIS_A_CLARIFIER', 'Crédits acquis à clarifier'),
                    ('MORATOIRE_ARTICLE2', 'Moratoire Article 2'),
                    ('FINANCABILITE_2023_A_CLARIFIER', 'Financabilité 2023 à clarifier'),
                    ('PREMIERE_INSCRIPTION_FORMATION_DOCTORALE', 'Première inscription à la formation doctorale'),
                    ('VALIDE_60_CREDITS_BLOC_1', 'A validé 60 crédits de bloc 1'),
                    ('N_A_PAS_VALIDE_60_CREDITS_BLOC_1', "N'a pas validé 60 crédits de bloc 1"),
                    ('REUSSI_1_UE_BLOC_1', 'A réussi 1 UE du bloc 1'),
                    ('N_A_PAS_REUSSI_1_UE_BLOC_1', "N'a pas réussi 1 UE du bloc 1"),
                    ('VALIDE_120_CREDITS_BACHELIER', 'A validé 120 crédits du bachelier'),
                    ('N_A_PAS_VALIDE_120_CREDITS_BACHELIER', "N'a pas validé 120 crédits du bachelier"),
                    ('CREDIT_BLOC1_A_CLARIFIER', 'Crédits du bloc 1 à clarifier'),
                    ('MORATOIRE_ARTICLE3', 'Moratoire Article 3'),
                    (
                        'N_A_PAS_VALIDE_MODULE_COMPLEMENTAIRE_EN_2_ANS',
                        "N'a pas validé le module complémentaire en 2 ans",
                    ),
                    ('A_ATTEINT_BALISES_MASTER', 'A atteint les balises de Master'),
                    ('N_A_PAS_ATTEINT_BALISES_MASTER', "N'a pas atteint les balises de Master"),
                    ('CREDIT_MODULE_COMPLEMENTAIRE_A_CLARIFIER', 'Crédits du module complémentaire à clarifier'),
                ],
                default='',
                max_length=100,
                verbose_name='Financability rule',
            ),
        ),
        migrations.AddField(
            model_name='doctorateadmission',
            name='financability_rule_established_by',
            field=models.ForeignKey(
                editable=False,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='+',
                to='base.person',
                verbose_name='Financability rule established by',
            ),
        ),
        migrations.AddField(
            model_name='doctorateadmission',
            name='financability_rule_established_on',
            field=models.DateTimeField(editable=False, null=True, verbose_name='Financability rule established on'),
        ),
        migrations.AddField(
            model_name='doctorateadmission',
            name='first_year_inscription_and_status',
            field=models.TextField(blank=True, default='', verbose_name='First year of inscription + status'),
        ),
        migrations.AddField(
            model_name='doctorateadmission',
            name='foreign_access_title_equivalency_effective_date',
            field=models.DateField(
                blank=True, null=True, verbose_name='Foreign access title equivalence effective date'
            ),
        ),
        migrations.AddField(
            model_name='doctorateadmission',
            name='foreign_access_title_equivalency_restriction_about',
            field=models.TextField(blank=True, null=True, verbose_name='Information about the restriction'),
        ),
        migrations.AddField(
            model_name='doctorateadmission',
            name='foreign_access_title_equivalency_state',
            field=models.CharField(
                blank=True,
                choices=[('DEFINITIVE', 'Definitive'), ('PROVISOIRE', 'Provisional')],
                default='',
                max_length=30,
                verbose_name='Foreign access title equivalence state',
            ),
        ),
        migrations.AddField(
            model_name='doctorateadmission',
            name='foreign_access_title_equivalency_status',
            field=models.CharField(
                blank=True,
                choices=[
                    ('COMPLETE', 'Completed'),
                    ('RESTRICTIVE', 'Restricted'),
                    ('EN_ATTENTE', 'Waiting'),
                    ('NON_RENSEIGNE', 'Not specified'),
                ],
                default='',
                max_length=30,
                verbose_name='Foreign access title equivalence status',
            ),
        ),
        migrations.AddField(
            model_name='doctorateadmission',
            name='foreign_access_title_equivalency_type',
            field=models.CharField(
                blank=True,
                choices=[
                    ('NON_CONCERNE', 'Not concerned'),
                    ('EQUIVALENCE_CESS', 'CESS equivalence'),
                    ('EQUIVALENCE_GRADE_ACADEMIQUE_FWB', 'FWB academic degree equivalence'),
                    ('EQUIVALENCE_DE_NIVEAU', 'Level equivalence'),
                    ('NON_RENSEIGNE', 'Not specified'),
                ],
                default='',
                max_length=50,
                verbose_name='Foreign access title equivalence type',
            ),
        ),
        migrations.AddField(
            model_name='doctorateadmission',
            name='is_mobility',
            field=models.BooleanField(null=True, verbose_name='The candidate is doing a mobility'),
        ),
        migrations.AddField(
            model_name='doctorateadmission',
            name='join_program_fac_comment',
            field=models.TextField(
                blank=True, default='', verbose_name='Faculty comment about the collaborative program'
            ),
        ),
        migrations.AddField(
            model_name='doctorateadmission',
            name='mobility_months_amount',
            field=models.CharField(
                choices=[('SIX', '6'), ('DOUZE', '12')],
                default='',
                max_length=50,
                verbose_name='Mobility months amount',
            ),
        ),
        migrations.AddField(
            model_name='doctorateadmission',
            name='must_provide_student_visa_d',
            field=models.BooleanField(blank=True, null=True, verbose_name='The candidate must provide a student visa'),
        ),
        migrations.AddField(
            model_name='doctorateadmission',
            name='must_report_to_sic',
            field=models.BooleanField(blank=True, null=True, verbose_name='The candidate must report to SIC'),
        ),
        migrations.AddField(
            model_name='doctorateadmission',
            name='other_refusal_reasons',
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.TextField(), blank=True, default=list, size=None, verbose_name='Other refusal reasons'
            ),
        ),
        migrations.AddField(
            model_name='doctorateadmission',
            name='other_training_accepted_by_fac',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='+',
                to='base.educationgroupyear',
                verbose_name='Other course accepted by the faculty',
            ),
        ),
        migrations.AddField(
            model_name='doctorateadmission',
            name='particular_cost',
            field=models.TextField(blank=True, default='', verbose_name='Particular cost'),
        ),
        migrations.AddField(
            model_name='doctorateadmission',
            name='prerequisite_courses_fac_comment',
            field=models.TextField(
                blank=True,
                default='',
                verbose_name='Other communication for the candidate about the prerequisite courses',
            ),
        ),
        migrations.AddField(
            model_name='doctorateadmission',
            name='program_planned_years_number',
            field=models.SmallIntegerField(
                blank=True,
                null=True,
                validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)],
                verbose_name='Number of years required for the full program (including prerequisite courses)',
            ),
        ),
        migrations.AddField(
            model_name='doctorateadmission',
            name='rebilling_or_third_party_payer',
            field=models.TextField(blank=True, default='', verbose_name='Rebilling or third-party payer'),
        ),
        migrations.AddField(
            model_name='doctorateadmission',
            name='refusal_reasons',
            field=models.ManyToManyField(
                blank=True,
                related_name='_admission_doctorateadmission_refusal_reasons_+',
                to='admission.RefusalReason',
                verbose_name='Refusal reasons',
            ),
        ),
        migrations.AddField(
            model_name='doctorateadmission',
            name='refusal_type',
            field=models.CharField(
                choices=[
                    ('REFUS_EQUIVALENCE', 'REFUS_EQUIVALENCE'),
                    ('REFUS_BAC_HUE_ACADEMIQUE', 'REFUS_BAC_HUE_ACADEMIQUE'),
                    ('REFUS_ARTICLE_95_SIC_CONDITIONS_PUBLIESS', 'REFUS_ARTICLE_95_SIC_CONDITIONS_PUBLIESS'),
                    ('REFUS_ARTICLE_95_JURY', 'REFUS_ARTICLE_95_JURY'),
                    ('REFUS_ARTICLE_95_GENERIQUE_IRRECEVABILITE', 'REFUS_ARTICLE_95_GENERIQUE_IRRECEVABILITE'),
                    ('REFUS_AGREGATION', 'REFUS_AGREGATION'),
                    ('REFUS_ARTICLE_96_UE_HUE_ASSIMILES', 'REFUS_ARTICLE_96_UE_HUE_ASSIMILES'),
                    ('REFUS_ARTICLE_96_HUE_RAISON_ACADEMIQUE', 'REFUS_ARTICLE_96_HUE_RAISON_ACADEMIQUE'),
                    ('REFUS_DOSSIER_TARDIF', 'REFUS_DOSSIER_TARDIF'),
                    ('REFUS_COMPLEMENT_TARDIF', 'REFUS_COMPLEMENT_TARDIF'),
                    ('REFUS_ARTICLE_96_HUE_NON_PROGRESSION', 'REFUS_ARTICLE_96_HUE_NON_PROGRESSION'),
                    ('REFUS_LIBRE', 'REFUS_LIBRE'),
                ],
                default='',
                max_length=50,
                verbose_name='Refusal type',
            ),
        ),
        migrations.AddField(
            model_name='doctorateadmission',
            name='sic_annexe_approval_certificate',
            field=osis_document.contrib.fields.FileField(
                base_field=models.UUIDField(),
                blank=True,
                default=list,
                size=None,
                verbose_name='Annexe approval certificate from SIC',
            ),
        ),
        migrations.AddField(
            model_name='doctorateadmission',
            name='sic_approval_certificate',
            field=osis_document.contrib.fields.FileField(
                base_field=models.UUIDField(),
                blank=True,
                default=list,
                size=None,
                verbose_name='Approval certificate from SIC',
            ),
        ),
        migrations.AddField(
            model_name='doctorateadmission',
            name='sic_refusal_certificate',
            field=osis_document.contrib.fields.FileField(
                base_field=models.UUIDField(),
                blank=True,
                default=list,
                size=None,
                verbose_name='Refusal certificate from SIC',
            ),
        ),
        migrations.AddField(
            model_name='doctorateadmission',
            name='signed_enrollment_authorization',
            field=osis_document.contrib.fields.FileField(
                base_field=models.UUIDField(),
                blank=True,
                default=list,
                size=None,
                verbose_name='Signed enrollment authorization',
            ),
        ),
        migrations.AddField(
            model_name='doctorateadmission',
            name='student_visa_d',
            field=osis_document.contrib.fields.FileField(
                base_field=models.UUIDField(),
                blank=True,
                default=list,
                size=None,
                verbose_name='Student visa D',
            ),
        ),
        migrations.AddField(
            model_name='doctorateadmission',
            name='tuition_fees_amount',
            field=models.CharField(
                choices=[
                    ('INSCRIPTION_AU_ROLE', 'INSCRIPTION_AU_ROLE'),
                    ('INSCRIPTION_REGULIERE', 'INSCRIPTION_REGULIERE'),
                    ('DROITS_MAJORES', 'DROITS_MAJORES'),
                    ('NOUVEAUX_DROITS_MAJORES', 'NOUVEAUX_DROITS_MAJORES'),
                    ('AGREGATION', 'AGREGATION'),
                    ('MASTER_DE_SPECIALISATION_SANTE', 'MASTER_DE_SPECIALISATION_SANTE'),
                    ('CERTIFICAT_60_CREDITS', 'CERTIFICAT_60_CREDITS'),
                    ('PAS_DE_DROITS_D_INSCRIPTION', 'PAS_DE_DROITS_D_INSCRIPTION'),
                    ('AUTRE', 'AUTRE'),
                ],
                default='',
                max_length=50,
                verbose_name='Tuition fees amount',
            ),
        ),
        migrations.AddField(
            model_name='doctorateadmission',
            name='tuition_fees_amount_other',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=10,
                null=True,
                verbose_name='Amount (without EUR/)',
            ),
        ),
        migrations.AddField(
            model_name='doctorateadmission',
            name='tuition_fees_dispensation',
            field=models.CharField(
                choices=[
                    ('NON_CONCERNE', 'NON_CONCERNE'),
                    ('DROITS_MAJORES_DEMANDES', 'DROITS_MAJORES_DEMANDES'),
                    ('DISPENSE_LDC', 'DISPENSE_LDC'),
                    ('DISPENSE_REUSSITE', 'DISPENSE_REUSSITE'),
                    ('DISPENSE_BOURSE', 'DISPENSE_BOURSE'),
                    ('DISPENSE_VCRC', 'DISPENSE_VCRC'),
                    ('DISPENSE_OFFRE', 'DISPENSE_OFFRE'),
                    ('DISPENSE_UNIV', 'DISPENSE_UNIV'),
                    ('DISPENSE_DUREE', 'DISPENSE_DUREE'),
                    ('DISPENSE_CESS_FWB', 'DISPENSE_CESS_FWB'),
                    ('REDUCTION_VCRC', 'REDUCTION_VCRC'),
                ],
                default='',
                max_length=50,
                verbose_name='Dispensation or increased fees',
            ),
        ),
        migrations.AddField(
            model_name='doctorateadmission',
            name='with_additional_approval_conditions',
            field=models.BooleanField(
                blank=True,
                null=True,
                verbose_name='Are there any additional conditions (subject to ...)?',
            ),
        ),
        migrations.AddField(
            model_name='doctorateadmission',
            name='with_prerequisite_courses',
            field=models.BooleanField(blank=True, null=True, verbose_name='Are there any prerequisite courses?'),
        ),
        migrations.CreateModel(
            name='DoctorateFreeAdditionalApprovalCondition',
            fields=[
                (
                    'uuid',
                    models.UUIDField(
                        db_index=True,
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ('name_fr', models.TextField(blank=True, default='', verbose_name='French name')),
                ('name_en', models.TextField(blank=True, default='', verbose_name='English name')),
                (
                    'admission',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='freeadditionalapprovalcondition_set',
                        to='admission.doctorateadmission',
                        verbose_name='Admission',
                    ),
                ),
                (
                    'related_experience',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        to='osis_profile.educationalexperience',
                        to_field='uuid',
                        verbose_name='Related experience',
                    ),
                ),
            ],
            options={
                'verbose_name': 'Doctorate free additional approval condition',
                'verbose_name_plural': 'Doctorate free additional approval conditions',
            },
        ),
        migrations.CreateModel(
            name='DoctorateAdmissionPrerequisiteCourses',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                (
                    'admission',
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='admission.doctorateadmission'),
                ),
                (
                    'course',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='+',
                        to='base.learningunityear',
                        to_field='uuid',
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name='doctorateadmission',
            name='prerequisite_courses',
            field=models.ManyToManyField(
                blank=True,
                through='admission.DoctorateAdmissionPrerequisiteCourses',
                to='base.LearningUnitYear',
                verbose_name='Prerequisite courses',
            ),
        ),
    ]