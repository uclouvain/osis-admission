# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
#
# ##############################################################################
import datetime
from contextlib import suppress

from django.contrib.postgres.fields import ArrayField
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from osis_document.contrib import FileField
from rest_framework.settings import api_settings

from admission.contrib.models.base import BaseAdmission, BaseAdmissionQuerySet, admission_directory_path
from admission.ddd import DUREE_MINIMALE_PROGRAMME, DUREE_MAXIMALE_PROGRAMME
from admission.ddd.admission.domain.model.enums.equivalence import (
    TypeEquivalenceTitreAcces,
    StatutEquivalenceTitreAcces,
    EtatEquivalenceTitreAcces,
)
from admission.ddd.admission.dtos.conditions import InfosDetermineesDTO
from admission.ddd.admission.formation_generale.domain.model.enums import (
    ChoixStatutPropositionGenerale,
    RegleDeFinancement,
    RegleCalculeResultatAvecFinancable,
    PoursuiteDeCycle,
    BesoinDeDerogation,
    DroitsInscriptionMontant,
    DispenseOuDroitsMajores,
    MobiliteNombreDeMois,
    TypeDeRefus,
    DerogationFinancement,
)
from base.forms.utils.file_field import PDF_MIME_TYPE
from base.models.academic_year import AcademicYear
from base.models.person import Person
from epc.models.enums.condition_acces import ConditionAcces
from osis_common.ddd.interface import BusinessException


class GeneralEducationAdmission(BaseAdmission):
    status = models.CharField(
        choices=ChoixStatutPropositionGenerale.choices(),
        max_length=30,
        default=ChoixStatutPropositionGenerale.EN_BROUILLON.name,
        # db_comment='Proposition.statut',
    )

    double_degree_scholarship = models.ForeignKey(
        to="admission.Scholarship",
        verbose_name=_("Dual degree scholarship"),
        related_name="+",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        # db_comment='Proposition.bourse_double_diplome_id',
    )

    international_scholarship = models.ForeignKey(
        to="admission.Scholarship",
        verbose_name=_("International scholarship"),
        related_name="+",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        # db_comment='Proposition.bourse_internationale_id',
    )

    erasmus_mundus_scholarship = models.ForeignKey(
        to="admission.Scholarship",
        verbose_name=_("Erasmus Mundus scholarship"),
        related_name="+",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        # db_comment='Proposition.bourse_erasmus_mundus_id',
    )
    is_belgian_bachelor = models.BooleanField(
        verbose_name=_("Is belgian bachelor"),
        null=True,
        # db_comment='Proposition.est_bachelier_belge',
    )
    is_external_reorientation = models.BooleanField(
        verbose_name=_("Is an external reorientation"),
        null=True,
        # db_comment='Proposition.is_external_reorientation',
    )
    registration_change_form = FileField(
        verbose_name=_("Change of enrolment form"),
        max_files=1,
        upload_to=admission_directory_path,
        blank=True,
        # db_comment='Proposition.formulaire_modification_inscription',
    )
    is_external_modification = models.BooleanField(
        verbose_name=_("Is an external modification"),
        null=True,
        # db_comment='Proposition.est_modification_inscription_externe',
    )
    regular_registration_proof = FileField(
        verbose_name=_("Proof of regular registration"),
        max_files=1,
        upload_to=admission_directory_path,
        blank=True,
        # db_comment='Proposition.attestation_inscription_reguliere',
    )
    is_non_resident = models.BooleanField(
        verbose_name=_("Is non-resident (as defined in decree)"),
        null=True,
        # db_comment='Proposition.est_non_resident_au_sens_decret',
    )

    diploma_equivalence = FileField(
        blank=True,
        upload_to=admission_directory_path,
        verbose_name=_('Diploma equivalence'),
        # db_comment='Proposition.equivalence_diplome',
    )
    late_enrollment = models.BooleanField(
        blank=True,
        null=True,
        verbose_name=_('Late enrollment'),
        # db_comment='Proposition.est_inscription_tardive',
    )
    cycle_pursuit = models.CharField(
        choices=PoursuiteDeCycle.choices(),
        max_length=30,
        default=PoursuiteDeCycle.TO_BE_DETERMINED.name,
        # db_comment='Proposition.poursuite_de_cycle',
    )
    additional_documents = FileField(
        blank=True,
        upload_to=admission_directory_path,
        verbose_name=_('Additional documents'),
        max_files=10,
        # db_comment='Proposition.documents_additionnels',
    )

    # Financability
    financability_computed_rule = models.CharField(
        verbose_name=_('Financability computed rule'),
        choices=RegleCalculeResultatAvecFinancable.choices(),
        max_length=100,
        default='',
        editable=False,
        # db_comment='Proposition.financabilite_regle_calcule',
    )
    financability_computed_rule_on = models.DateTimeField(
        verbose_name=_('Financability computed rule on'),
        null=True,
        editable=False,
        # db_comment='Proposition.financabilite_regle_calcule_le',
    )
    financability_rule = models.CharField(
        verbose_name=_('Financability rule'),
        choices=RegleDeFinancement.choices(),
        max_length=100,
        default='',
        # db_comment='Proposition.financabilite_regle',
    )
    financability_rule_established_by = models.ForeignKey(
        'base.Person',
        verbose_name=_('Financability rule established by'),
        on_delete=models.PROTECT,
        related_name='+',
        null=True,
        editable=False,
        # db_comment='Proposition.financabilite_regle_etabli_par',
    )

    financability_dispensation_status = models.CharField(
        verbose_name=_('Financability dispensation status'),
        choices=DerogationFinancement.choices(),
        max_length=100,
        default='',
        # db_comment='Proposition.financabilite_derogation_statut',
    )
    financability_dispensation_first_notification_on = models.DateTimeField(
        verbose_name=_('Financability dispensation first notification on'),
        null=True,
        editable=False,
        # db_comment='Proposition.financabilite_derogation_premiere_notification_le',
    )
    financability_dispensation_first_notification_by = models.ForeignKey(
        'base.Person',
        verbose_name=_('Financability dispensation first notification by'),
        on_delete=models.PROTECT,
        related_name='+',
        null=True,
        editable=False,
        # db_comment='Proposition.financabilite_derogation_premiere_notification_par',
    )
    financability_dispensation_last_notification_on = models.DateTimeField(
        verbose_name=_('Financability dispensation last notification on'),
        null=True,
        editable=False,
        # db_comment='Proposition.financabilite_derogation_derniere_notification_le',
    )
    financability_dispensation_last_notification_by = models.ForeignKey(
        'base.Person',
        verbose_name=_('Financability dispensation last notification by'),
        on_delete=models.PROTECT,
        related_name='+',
        null=True,
        editable=False,
        # db_comment='Proposition.financabilite_derogation_derniere_notification_par',
    )

    # FAC & SIC approval
    fac_approval_certificate = FileField(
        blank=True,
        upload_to=admission_directory_path,
        verbose_name=_('Approval certificate of faculty'),
        mimetypes=[PDF_MIME_TYPE],
        # db_comment='Proposition.certificat_approbation_fac',
    )
    fac_refusal_certificate = FileField(
        blank=True,
        upload_to=admission_directory_path,
        verbose_name=_('Refusal certificate of faculty'),
        mimetypes=[PDF_MIME_TYPE],
        # db_comment='Proposition.certificat_refus_fac',
    )
    sic_approval_certificate = FileField(
        blank=True,
        upload_to=admission_directory_path,
        verbose_name=_('Approval certificate from SIC'),
        mimetypes=[PDF_MIME_TYPE],
        # db_comment='Proposition.certificat_approbation_sic',
    )
    sic_annexe_approval_certificate = FileField(
        blank=True,
        upload_to=admission_directory_path,
        verbose_name=_('Annexe approval certificate from SIC'),
        mimetypes=[PDF_MIME_TYPE],
        # db_comment='Proposition.certificat_approbation_sic_annexe',
    )
    sic_refusal_certificate = FileField(
        blank=True,
        upload_to=admission_directory_path,
        verbose_name=_('Refusal certificate from SIC'),
        mimetypes=[PDF_MIME_TYPE],
        # db_comment='Proposition.certificat_refus_sic',
    )
    refusal_type = models.CharField(
        verbose_name=_('Refusal type'),
        max_length=50,
        default='',
        choices=TypeDeRefus.choices(),
        # db_comment='Proposition.type_de_refus',
    )
    refusal_reasons = models.ManyToManyField(
        blank=True,
        related_name='+',
        to='admission.RefusalReason',
        verbose_name=_('Refusal reasons'),
        # db_comment='Proposition.motifs_refus',
    )
    other_refusal_reasons = ArrayField(
        base_field=models.TextField(),
        blank=True,
        default=list,
        verbose_name=_('Other refusal reasons'),
        # db_comment='Proposition.autres_motifs_refus',
    )
    with_additional_approval_conditions = models.BooleanField(
        blank=True,
        null=True,
        verbose_name=_('Are there any additional conditions (subject to ...)?'),
        # db_comment='Proposition.avec_conditions_complementaires',
    )
    additional_approval_conditions = models.ManyToManyField(
        blank=True,
        related_name='+',
        to='admission.AdditionalApprovalCondition',
        verbose_name=_('Additional approval conditions'),
        # db_comment='Proposition.conditions_complementaires_existantes',
    )
    other_training_accepted_by_fac = models.ForeignKey(
        blank=True,
        null=True,
        on_delete=models.PROTECT,
        related_name='+',
        to='base.EducationGroupYear',
        verbose_name=_('Other course accepted by the faculty'),
        # db_comment='Proposition.autre_formation_choisie_fac_id',
    )
    with_prerequisite_courses = models.BooleanField(
        blank=True,
        null=True,
        verbose_name=_('Are there any prerequisite courses?'),
        # db_comment='Proposition.avec_complements_formation',
    )
    prerequisite_courses = models.ManyToManyField(
        to='base.LearningUnitYear',
        blank=True,
        through='AdmissionPrerequisiteCourses',
        through_fields=(
            'admission',
            'course',
        ),
        verbose_name=_('Prerequisite courses'),
        # db_comment='Proposition.complements_formation',
    )
    prerequisite_courses_fac_comment = models.TextField(
        blank=True,
        default='',
        verbose_name=_('Other communication for the candidate about the prerequisite courses'),
        # db_comment='Proposition.commentaire_complements_formation',
    )
    program_planned_years_number = models.SmallIntegerField(
        blank=True,
        null=True,
        verbose_name=_('Number of years required for the full program (including prerequisite courses)'),
        validators=[MinValueValidator(DUREE_MINIMALE_PROGRAMME), MaxValueValidator(DUREE_MAXIMALE_PROGRAMME)],
        # db_comment='Proposition.nombre_annees_prevoir_programme',
    )
    annual_program_contact_person_name = models.CharField(
        blank=True,
        default='',
        max_length=255,
        verbose_name=_('Name of the contact person for the design of the annual program'),
        # db_comment='Proposition.nom_personne_contact_programme_annuel_annuel',
    )
    annual_program_contact_person_email = models.EmailField(
        blank=True,
        default='',
        verbose_name=_('Email of the contact person for the design of the annual program'),
        # db_comment='Proposition.email_personne_contact_programme_annuel_annuel',
    )
    join_program_fac_comment = models.TextField(
        blank=True,
        default='',
        verbose_name=_('Faculty comment about the collaborative program'),
        # db_comment='Proposition.commentaire_programme_conjoint',
    )
    dispensation_needed = models.CharField(
        max_length=50,
        default='',
        choices=BesoinDeDerogation.choices(),
        verbose_name=_('Dispensation needed'),
        # db_comment='Proposition.besoin_de_derogation',
    )
    tuition_fees_amount = models.CharField(
        max_length=50,
        default='',
        choices=DroitsInscriptionMontant.choices(),
        verbose_name=_("Tuition fees amount"),
        # db_comment='Proposition.droits_inscription_montant',
    )
    tuition_fees_amount_other = models.DecimalField(
        verbose_name=_("Amount (without EUR/)"),
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        # db_comment='Proposition.tuition_fees_amount_other',
    )
    tuition_fees_dispensation = models.CharField(
        max_length=50,
        default='',
        choices=DispenseOuDroitsMajores.choices(),
        verbose_name=_("Dispensation or increased fees"),
        # db_comment='Proposition.dispense_ou_droits_majores',
    )
    particular_cost = models.TextField(
        default='',
        verbose_name=_("Particular cost"),
        blank=True,
        # db_comment='Proposition.tarif_particulier',
    )
    rebilling_or_third_party_payer = models.TextField(
        default='',
        verbose_name=_("Rebilling or third-party payer"),
        # db_comment='Proposition.refacturation_ou_tiers_payant',
        blank=True,
    )
    first_year_inscription_and_status = models.TextField(
        default='',
        verbose_name=_("First year of inscription + status"),
        # db_comment='Proposition.annee_de_premiere_inscription_et_statut',
        blank=True,
    )
    is_mobility = models.BooleanField(
        null=True,
        verbose_name=_('The candidate is doing a mobility'),
        # db_comment='Proposition.est_mobilite',
    )
    mobility_months_amount = models.CharField(
        max_length=50,
        default='',
        choices=MobiliteNombreDeMois.choices(),
        verbose_name=_("Mobility months amount"),
        # db_comment='Proposition.nombre_de_mois_de_mobilite',
    )
    must_report_to_sic = models.BooleanField(
        blank=True,
        null=True,
        verbose_name=_('The candidate must report to SIC'),
        # db_comment='Proposition.doit_se_presenter_en_sic',
    )
    communication_to_the_candidate = models.TextField(
        default='',
        verbose_name=_("Communication to the candidate"),
        blank=True,
        # db_comment='Proposition.communication_au_candidat',
    )
    must_provide_student_visa_d = models.BooleanField(
        blank=True,
        null=True,
        verbose_name=_('The candidate must provide a student visa'),
        # db_comment='Proposition.doit_fournir_visa_etudes',
    )
    student_visa_d = FileField(
        verbose_name=_("Student visa D"),
        upload_to=admission_directory_path,
        blank=True,
        mimetypes=[PDF_MIME_TYPE],
        # db_comment='Proposition.visa_etudes_d',
    )
    signed_enrollment_authorization = FileField(
        verbose_name=_("Signed enrollment authorization"),
        upload_to=admission_directory_path,
        blank=True,
        mimetypes=[PDF_MIME_TYPE],
        # db_comment='Proposition.signed_enrollment_authorization',
    )
    diplomatic_post = models.ForeignKey(
        blank=True,
        null=True,
        on_delete=models.PROTECT,
        to='admission.DiplomaticPost',
        verbose_name=_('Diplomatic post'),
        # db_comment='Proposition.poste_diplomatique',
    )
    admission_requirement = models.CharField(
        choices=ConditionAcces.choices(),
        blank=True,
        default='',
        max_length=30,
        verbose_name=_('Admission requirement'),
        # db_comment='Proposition.condition_acces',
    )
    admission_requirement_year = models.ForeignKey(
        to="base.AcademicYear",
        related_name="+",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name=_('Admission requirement year'),
        # db_comment='Proposition.millesime_condition_acces',
    )
    foreign_access_title_equivalency_type = models.CharField(
        choices=TypeEquivalenceTitreAcces.choices(),
        blank=True,
        default='',
        max_length=50,
        verbose_name=_('Foreign access title equivalence type'),
        # db_comment='Proposition.type_equivalence_titre_acces',
    )
    foreign_access_title_equivalency_status = models.CharField(
        choices=StatutEquivalenceTitreAcces.choices(),
        blank=True,
        default='',
        max_length=30,
        verbose_name=_('Foreign access title equivalence status'),
        # db_comment='Proposition.statut_equivalence_titre_acces',
    )
    foreign_access_title_equivalency_restriction_about = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Information about the restriction'),
        # db_comment='Proposition.information_a_propos_de_la_restriction',
    )
    foreign_access_title_equivalency_state = models.CharField(
        choices=EtatEquivalenceTitreAcces.choices(),
        blank=True,
        default='',
        max_length=30,
        verbose_name=_('Foreign access title equivalence state'),
        # db_comment='Proposition.etat_equivalence_titre_acces',
    )
    foreign_access_title_equivalency_effective_date = models.DateField(
        blank=True,
        null=True,
        verbose_name=_('Foreign access title equivalence effective date'),
        # db_comment='Proposition.date_prise_effet_equivalence_titre_acces',
    )

    class Meta:
        verbose_name = _("General education admission")
        ordering = ('-created_at',)
        # db_table_comment = "Modèle utilisé dans le cadre d'une admission pour une formation générale"
        permissions = []

    def update_detailed_status(self, author: 'Person' = None):
        """Gather exceptions from verification and update determined pool and academic year"""
        from admission.ddd.admission.formation_generale.commands import (
            VerifierPropositionQuery,
            DeterminerAnneeAcademiqueEtPotQuery,
        )
        from admission.utils import gather_business_exceptions
        from infrastructure.messages_bus import message_bus_instance

        error_key = api_settings.NON_FIELD_ERRORS_KEY
        self.detailed_status = gather_business_exceptions(VerifierPropositionQuery(self.uuid)).get(error_key, [])
        self.last_update_author = author

        update_fields = [
            'detailed_status',
            'determined_academic_year',
            'determined_pool',
        ]

        if author:
            self.last_update_author = author
            self.modified_at = datetime.datetime.now()
            update_fields.append('last_update_author')
            update_fields.append('modified_at')

        with suppress(BusinessException):
            dto: 'InfosDetermineesDTO' = message_bus_instance.invoke(DeterminerAnneeAcademiqueEtPotQuery(self.uuid))
            self.determined_academic_year = AcademicYear.objects.get(year=dto.annee)
            self.determined_pool = dto.pool.name

        self.save(update_fields=update_fields)

    def update_requested_documents(self):
        """Update the requested documents depending on the admission data."""
        from admission.ddd.admission.formation_generale.commands import (
            RecalculerEmplacementsDocumentsNonLibresPropositionCommand,
        )
        from infrastructure.messages_bus import message_bus_instance

        message_bus_instance.invoke(RecalculerEmplacementsDocumentsNonLibresPropositionCommand(self.uuid))

    def update_financability_computed_rule(self, author: 'Person'):
        from admission.ddd.admission.formation_generale.commands import (
            SpecifierFinancabiliteResultatCalculCommand,
        )
        from infrastructure.messages_bus import message_bus_instance

        # TODO à faire dans le DDD ? + Calculer à la soumission
        financabilite_regle_calcule = 'INDISPONIBLE'

        message_bus_instance.invoke(
            SpecifierFinancabiliteResultatCalculCommand(
                uuid_proposition=self.uuid,
                gestionnaire=author.global_id,
                financabilite_regle_calcule=financabilite_regle_calcule,
                financabilite_regle_calcule_le=timezone.now(),
            )
        )


class AdmissionPrerequisiteCourses(models.Model):
    """Prerequisite courses of an admission."""

    admission = models.ForeignKey(
        GeneralEducationAdmission,
        on_delete=models.CASCADE,
    )
    course = models.ForeignKey(
        'base.LearningUnitYear',
        on_delete=models.PROTECT,
        related_name='+',
        to_field='uuid',
    )


class GeneralEducationAdmissionManager(models.Manager.from_queryset(BaseAdmissionQuerySet)):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related(
                "candidate__country_of_citizenship",
                "training__academic_year",
                "training__education_group_type",
                "determined_academic_year",
                "double_degree_scholarship",
                "international_scholarship",
                "erasmus_mundus_scholarship",
                "diplomatic_post",
            )
            .annotate_pool_end_date()
        )

    def for_dto(self):
        return (
            self.get_queryset()
            .select_related(
                "training__main_domain",
                "training__enrollment_campus",
            )
            .annotate_campus()
            .annotate_training_management_entity()
            .annotate_training_management_faculty()
            .annotate_with_reference()
        )

    def for_manager_dto(self):
        return (
            self.for_dto()
            .annotate_campus(
                training_field='other_training_accepted_by_fac',
                annotation_name='other_training_accepted_by_fac_teaching_campus',
            )
            .annotate_with_student_registration_id()
        )


class GeneralEducationAdmissionProxy(GeneralEducationAdmission):
    """Proxy model of base.GeneralEducationAdmission"""

    objects = GeneralEducationAdmissionManager()

    class Meta:
        proxy = True
