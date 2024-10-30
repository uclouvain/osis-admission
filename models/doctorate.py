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
import uuid
from contextlib import suppress

from ckeditor.fields import RichTextField
from django.contrib.postgres.fields import ArrayField
from django.core.cache import cache
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models import OuterRef, Prefetch
from django.utils.datetime_safe import date
from django.utils.translation import gettext_lazy as _
from osis_signature.contrib.fields import SignatureProcessField
from rest_framework.settings import api_settings

from admission.ddd import DUREE_MINIMALE_PROGRAMME, DUREE_MAXIMALE_PROGRAMME
from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    ChoixCommissionProximiteCDEouCLSM,
    ChoixCommissionProximiteCDSS,
    ChoixDoctoratDejaRealise,
    ChoixLangueRedactionThese,
    ChoixSousDomaineSciences,
    ChoixStatutPropositionDoctorale,
    ChoixTypeAdmission,
    ChoixTypeFinancement,
)
from admission.ddd.admission.doctorat.preparation.domain.model.enums.checklist import (
    DerogationFinancement,
    BesoinDeDerogation,
    DroitsInscriptionMontant,
    DispenseOuDroitsMajores,
    MobiliteNombreDeMois,
)
from admission.ddd.admission.doctorat.validation.domain.model.enums import ChoixStatutCDD, ChoixStatutSIC
from admission.ddd.admission.domain.model.enums.equivalence import (
    TypeEquivalenceTitreAcces,
    StatutEquivalenceTitreAcces,
    EtatEquivalenceTitreAcces,
)
from admission.ddd.admission.dtos.conditions import InfosDetermineesDTO
from admission.ddd.parcours_doctoral.domain.model.enums import ChoixStatutDoctorat
from admission.ddd.parcours_doctoral.jury.domain.model.enums import FormuleDefense
from base.forms.utils.file_field import PDF_MIME_TYPE
from base.models.academic_year import AcademicYear
from base.models.entity_version import EntityVersion
from base.models.enums.entity_type import SECTOR
from base.models.person import Person
from base.utils.cte import CTESubquery
from ddd.logic.financabilite.commands import DeterminerSiCandidatEstFinancableQuery
from ddd.logic.financabilite.domain.model.enums.etat import EtatFinancabilite
from ddd.logic.financabilite.domain.model.enums.situation import SituationFinancabilite
from epc.models.enums.condition_acces import ConditionAcces
from osis_common.ddd.interface import BusinessException
from osis_document.contrib import FileField
from .base import BaseAdmission, BaseAdmissionQuerySet, admission_directory_path

__all__ = [
    "DoctorateAdmission",
    "DoctorateProxy",
    "ConfirmationPaper",
]

from .checklist import RefusalReason


class DoctorateAdmission(BaseAdmission):
    type = models.CharField(
        verbose_name=_("Type"),
        max_length=255,
        choices=ChoixTypeAdmission.choices(),
        db_index=True,
        default=ChoixTypeAdmission.ADMISSION.name,
    )
    # TODO: remove this field in the future
    valuated_experiences = models.ManyToManyField(
        'osis_profile.Experience',
        related_name='valuated_from',
        verbose_name=_('The experiences that have been valuated from this admission.'),
    )
    proximity_commission = models.CharField(
        max_length=255,
        verbose_name=_("Proximity commission"),
        choices=ChoixCommissionProximiteCDEouCLSM.choices()
        + ChoixCommissionProximiteCDSS.choices()
        + ChoixSousDomaineSciences.choices(),
        default='',
        blank=True,
    )
    # Financement
    financing_type = models.CharField(
        max_length=255,
        verbose_name=_("Funding type"),
        choices=ChoixTypeFinancement.choices(),
        default='',
        blank=True,
    )
    financing_work_contract = models.CharField(
        max_length=255,
        verbose_name=_("Working contract type"),
        default='',
        blank=True,
    )
    financing_eft = models.PositiveSmallIntegerField(
        verbose_name=_("EFT"),
        blank=True,
        null=True,
    )
    scholarship_start_date = models.DateField(
        verbose_name=_("Scholarship start date"),
        null=True,
        blank=True,
    )
    scholarship_end_date = models.DateField(
        verbose_name=_("Scholarship end date"),
        null=True,
        blank=True,
    )
    scholarship_proof = FileField(
        verbose_name=_("Proof of scholarship"),
        upload_to=admission_directory_path,
    )
    planned_duration = models.PositiveSmallIntegerField(
        verbose_name=_("Planned duration"),
        blank=True,
        null=True,
    )
    dedicated_time = models.PositiveSmallIntegerField(
        verbose_name=_("Dedicated time (in EFT)"),
        blank=True,
        null=True,
    )
    is_fnrs_fria_fresh_csc_linked = models.BooleanField(
        verbose_name=_("Is your admission request linked with a FNRS, FRIA, FRESH or CSC application?"),
        null=True,
        blank=True,
    )
    financing_comment = models.TextField(
        verbose_name=_("Financing comment"),
        default='',
        blank=True,
    )

    # Projet
    project_title = models.CharField(
        max_length=1023,
        verbose_name=_("Project title"),
        default='',
        blank=True,
    )
    project_abstract = models.TextField(
        verbose_name=_("Abstract"),
        default='',
        blank=True,
    )
    thesis_language = models.ForeignKey(
        'reference.Language',
        on_delete=models.PROTECT,
        verbose_name=_("Thesis language"),
        null=True,
        blank=True,
    )
    thesis_institute = models.ForeignKey(
        'base.EntityVersion',
        related_name="+",
        verbose_name=_("Thesis institute"),
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    thesis_location = models.CharField(
        max_length=255,
        verbose_name=_("Thesis location"),
        default='',
        blank=True,
    )
    phd_alread_started = models.BooleanField(
        verbose_name=_("Has your PhD project already started?"),
        null=True,
        blank=True,
    )
    phd_alread_started_institute = models.CharField(
        max_length=255,
        verbose_name=_("Institution"),
        default='',
        blank=True,
    )
    work_start_date = models.DateField(
        verbose_name=_("Work start date"),
        null=True,
        blank=True,
    )
    project_document = FileField(
        verbose_name=_("Project"),
        upload_to=admission_directory_path,
    )
    gantt_graph = FileField(
        verbose_name=_("Gantt chart"),
        upload_to=admission_directory_path,
    )
    program_proposition = FileField(
        verbose_name=_("Program proposition"),
        upload_to=admission_directory_path,
    )
    additional_training_project = FileField(
        verbose_name=_("Complementary training proposition"),
        upload_to=admission_directory_path,
    )
    recommendation_letters = FileField(
        verbose_name=_("Letters of recommendation"),
        upload_to=admission_directory_path,
    )

    # Experience précédente de recherche
    phd_already_done = models.CharField(
        max_length=255,
        choices=ChoixDoctoratDejaRealise.choices(),
        verbose_name=_("PhD already done"),
        default=ChoixDoctoratDejaRealise.NO.name,
        blank=True,
    )
    phd_already_done_institution = models.CharField(
        max_length=255,
        verbose_name=_("Institution"),
        default='',
        blank=True,
    )
    phd_already_done_thesis_domain = models.CharField(
        max_length=255,
        verbose_name=_("Thesis field"),
        default='',
        blank=True,
    )
    phd_already_done_defense_date = models.DateField(
        verbose_name=_("Defense"),
        null=True,
        blank=True,
    )
    phd_already_done_no_defense_reason = models.CharField(
        max_length=255,
        verbose_name=_("No defense reason"),
        default='',
        blank=True,
    )
    cotutelle_motivation = models.CharField(
        max_length=255,
        verbose_name=_("Motivation"),
        default='',
        blank=True,
    )
    cotutelle = models.BooleanField(
        null=True,
        blank=True,
    )
    cotutelle_institution_fwb = models.BooleanField(
        verbose_name=_("Institution Federation Wallonie-Bruxelles"),
        blank=True,
        null=True,
    )
    cotutelle_institution = models.UUIDField(
        verbose_name=_("Institution"),
        default=None,
        null=True,
        blank=True,
    )
    cotutelle_other_institution_name = models.CharField(
        max_length=255,
        verbose_name=_("Other institution name"),
        default='',
        blank=True,
    )
    cotutelle_other_institution_address = models.CharField(
        max_length=255,
        verbose_name=_("Other institution address"),
        default='',
        blank=True,
    )
    cotutelle_opening_request = FileField(
        verbose_name=_("Cotutelle request document"),
        max_files=1,
        upload_to=admission_directory_path,
    )
    cotutelle_convention = FileField(
        verbose_name=_("Joint supervision agreement"),
        max_files=1,
        upload_to=admission_directory_path,
    )
    cotutelle_other_documents = FileField(
        verbose_name=_("Other cotutelle-related documents"),
        upload_to=admission_directory_path,
    )
    archived_record_signatures_sent = FileField(
        verbose_name=_("Archived record when signatures were sent"),
        max_files=1,
        upload_to=admission_directory_path,
        editable=False,
    )

    status = models.CharField(
        choices=ChoixStatutPropositionDoctorale.choices(),
        max_length=30,
        default=ChoixStatutPropositionDoctorale.EN_BROUILLON.name,
    )
    status_cdd = models.CharField(
        choices=ChoixStatutCDD.choices(),
        max_length=30,
        default=ChoixStatutCDD.TO_BE_VERIFIED.name,
    )
    status_sic = models.CharField(
        choices=ChoixStatutSIC.choices(),
        max_length=30,
        default=ChoixStatutSIC.TO_BE_VERIFIED.name,
    )
    post_enrolment_status = models.CharField(
        choices=ChoixStatutDoctorat.choices(),
        max_length=30,
        default=ChoixStatutDoctorat.ADMISSION_IN_PROGRESS.name,
        verbose_name=_("Post-enrolment status"),
    )

    supervision_group = SignatureProcessField()

    other_international_scholarship = models.CharField(
        max_length=255,
        verbose_name=_("Other international scholarship"),
        default='',
        blank=True,
    )
    international_scholarship = models.ForeignKey(
        to="admission.Scholarship",
        verbose_name=_("International scholarship"),
        related_name="+",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )

    # Jury
    thesis_proposed_title = models.CharField(
        max_length=255,
        verbose_name=_("Proposed thesis title"),
        default='',
        blank=True,
    )
    defense_method = models.CharField(
        max_length=255,
        verbose_name=_("Defense method"),
        choices=FormuleDefense.choices(),
        default='',
        blank=True,
    )
    defense_indicative_date = models.DateField(
        verbose_name=_("Defense indicative date"),
        null=True,
        blank=True,
    )
    defense_language = models.CharField(
        max_length=255,
        verbose_name=_("Defense language"),
        choices=ChoixLangueRedactionThese.choices(),
        default=ChoixLangueRedactionThese.UNDECIDED.name,
        blank=True,
    )
    comment_about_jury = models.TextField(
        default="",
        verbose_name=_("Comment about jury"),
        blank=True,
    )
    accounting_situation = models.BooleanField(
        null=True,
        blank=True,
    )
    jury_approval = FileField(
        verbose_name=_("Jury approval"),
        upload_to=admission_directory_path,
    )

    # Financability
    financability_computed_rule = models.CharField(
        verbose_name=_('Financability computed rule'),
        choices=EtatFinancabilite.choices(),
        max_length=100,
        default='',
        editable=False,
    )
    financability_computed_rule_situation = models.CharField(
        verbose_name=_('Financability computed rule situation'),
        choices=SituationFinancabilite.choices(),
        max_length=100,
        default='',
        editable=False,
    )
    financability_computed_rule_on = models.DateTimeField(
        verbose_name=_('Financability computed rule on'),
        null=True,
        editable=False,
    )
    financability_rule = models.CharField(
        verbose_name=_('Financability rule'),
        choices=SituationFinancabilite.choices(),
        max_length=100,
        default='',
        blank=True,
    )
    financability_established_by = models.ForeignKey(
        'base.Person',
        verbose_name=_('Financability established by'),
        on_delete=models.PROTECT,
        related_name='+',
        null=True,
        editable=False,
    )
    financability_established_on = models.DateTimeField(
        verbose_name=_('Financability established on'),
        null=True,
        editable=False,
    )

    financability_dispensation_status = models.CharField(
        verbose_name=_('Financability dispensation status'),
        choices=DerogationFinancement.choices(),
        max_length=100,
        default='',
        blank=True,
    )
    financability_dispensation_first_notification_on = models.DateTimeField(
        verbose_name=_('Financability dispensation first notification on'),
        null=True,
        editable=False,
    )
    financability_dispensation_first_notification_by = models.ForeignKey(
        'base.Person',
        verbose_name=_('Financability dispensation first notification by'),
        on_delete=models.PROTECT,
        related_name='+',
        null=True,
        editable=False,
    )
    financability_dispensation_last_notification_on = models.DateTimeField(
        verbose_name=_('Financability dispensation last notification on'),
        null=True,
        editable=False,
    )
    financability_dispensation_last_notification_by = models.ForeignKey(
        'base.Person',
        verbose_name=_('Financability dispensation last notification by'),
        on_delete=models.PROTECT,
        related_name='+',
        null=True,
        editable=False,
    )

    # CDD & SIC approval
    cdd_approval_certificate = FileField(
        blank=True,
        upload_to=admission_directory_path,
        verbose_name=_('Approval certificate of the CDD'),
        mimetypes=[PDF_MIME_TYPE],
    )
    sic_approval_certificate = FileField(
        blank=True,
        upload_to=admission_directory_path,
        verbose_name=_('Approval certificate from SIC'),
        mimetypes=[PDF_MIME_TYPE],
    )
    sic_annexe_approval_certificate = FileField(
        blank=True,
        upload_to=admission_directory_path,
        verbose_name=_('Annexe approval certificate from SIC'),
        mimetypes=[PDF_MIME_TYPE],
    )
    refusal_reasons = models.ManyToManyField(
        blank=True,
        related_name='+',
        to='admission.RefusalReason',
        verbose_name=_('Refusal reasons'),
    )
    other_refusal_reasons = ArrayField(
        base_field=models.TextField(),
        blank=True,
        default=list,
        verbose_name=_('Other refusal reasons'),
    )
    with_prerequisite_courses = models.BooleanField(
        blank=True,
        null=True,
        verbose_name=_('Are there any prerequisite courses?'),
    )
    prerequisite_courses = models.ManyToManyField(
        to='base.LearningUnitYear',
        blank=True,
        through='DoctorateAdmissionPrerequisiteCourses',
        through_fields=(
            'admission',
            'course',
        ),
        verbose_name=_('Prerequisite courses'),
    )
    prerequisite_courses_fac_comment = models.TextField(
        blank=True,
        default='',
        verbose_name=_('Other communication for the candidate about the prerequisite courses'),
    )
    program_planned_years_number = models.SmallIntegerField(
        blank=True,
        null=True,
        verbose_name=_('Number of years required for the full program (including prerequisite courses)'),
        validators=[MinValueValidator(DUREE_MINIMALE_PROGRAMME), MaxValueValidator(DUREE_MAXIMALE_PROGRAMME)],
    )
    annual_program_contact_person_name = models.CharField(
        blank=True,
        default='',
        max_length=255,
        verbose_name=_('Name of the contact person for the design of the annual program'),
    )
    annual_program_contact_person_email = models.EmailField(
        blank=True,
        default='',
        verbose_name=_('Email of the contact person for the design of the annual program'),
    )
    join_program_fac_comment = models.TextField(
        blank=True,
        default='',
        verbose_name=_('CDD comment about the collaborative program'),
    )
    dispensation_needed = models.CharField(
        max_length=50,
        default='',
        choices=BesoinDeDerogation.choices(),
        verbose_name=_('Dispensation needed'),
    )
    tuition_fees_amount = models.CharField(
        max_length=50,
        default='',
        choices=DroitsInscriptionMontant.choices(),
        verbose_name=_("Tuition fees amount"),
    )
    tuition_fees_amount_other = models.DecimalField(
        verbose_name=_("Amount (without EUR/)"),
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
    )
    tuition_fees_dispensation = models.CharField(
        max_length=50,
        default='',
        choices=DispenseOuDroitsMajores.choices(),
        verbose_name=_("Dispensation or increased fees"),
    )
    is_mobility = models.BooleanField(
        null=True,
        verbose_name=_('The candidate is doing a mobility'),
    )
    mobility_months_amount = models.CharField(
        max_length=50,
        default='',
        choices=MobiliteNombreDeMois.choices(),
        verbose_name=_("Mobility months amount"),
    )
    must_report_to_sic = models.BooleanField(
        blank=True,
        null=True,
        verbose_name=_('The candidate must report to SIC'),
    )
    communication_to_the_candidate = models.TextField(
        default='',
        verbose_name=_("Communication to the candidate"),
        blank=True,
    )
    must_provide_student_visa_d = models.BooleanField(
        blank=True,
        null=True,
        verbose_name=_('The candidate must provide a student visa'),
    )
    student_visa_d = FileField(
        verbose_name=_("Student visa D"),
        upload_to=admission_directory_path,
        blank=True,
        mimetypes=[PDF_MIME_TYPE],
    )
    signed_enrollment_authorization = FileField(
        verbose_name=_("Signed enrollment authorization"),
        upload_to=admission_directory_path,
        blank=True,
        mimetypes=[PDF_MIME_TYPE],
    )
    diplomatic_post = models.ForeignKey(
        blank=True,
        null=True,
        on_delete=models.PROTECT,
        to='admission.DiplomaticPost',
        verbose_name=_('Diplomatic post'),
    )
    admission_requirement = models.CharField(
        choices=ConditionAcces.choices(),
        blank=True,
        default='',
        max_length=30,
        verbose_name=_('Admission requirement'),
    )
    admission_requirement_year = models.ForeignKey(
        to="base.AcademicYear",
        related_name="+",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name=_('Admission requirement year'),
    )
    foreign_access_title_equivalency_type = models.CharField(
        choices=TypeEquivalenceTitreAcces.choices(),
        blank=True,
        default='',
        max_length=50,
        verbose_name=_('Foreign access title equivalence type'),
    )
    foreign_access_title_equivalency_status = models.CharField(
        choices=StatutEquivalenceTitreAcces.choices(),
        blank=True,
        default='',
        max_length=30,
        verbose_name=_('Foreign access title equivalence status'),
    )
    foreign_access_title_equivalency_restriction_about = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Information about the restriction'),
    )
    foreign_access_title_equivalency_state = models.CharField(
        choices=EtatEquivalenceTitreAcces.choices(),
        blank=True,
        default='',
        max_length=30,
        verbose_name=_('Foreign access title equivalence state'),
    )
    foreign_access_title_equivalency_effective_date = models.DateField(
        blank=True,
        null=True,
        verbose_name=_('Foreign access title equivalence effective date'),
    )

    def update_financability_computed_rule(self, author: 'Person'):
        from admission.ddd.admission.doctorat.preparation.commands import (
            SpecifierFinancabiliteResultatCalculCommand,
        )
        from infrastructure.messages_bus import message_bus_instance

        financabilite = message_bus_instance.invoke(
            DeterminerSiCandidatEstFinancableQuery(
                matricule_fgs=self.candidate.global_id,
                sigle_formation=self.training.acronym,
                annee=self.training.academic_year.year,
                est_en_reorientation=False,
            )
        )

        message_bus_instance.invoke(
            SpecifierFinancabiliteResultatCalculCommand(
                uuid_proposition=self.uuid,
                financabilite_regle_calcule=financabilite.etat,
                financabilite_regle_calcule_situation=financabilite.situation,
            )
        )

    # The following properties are here to alias the training_id field to doctorate_id
    @property
    def doctorate(self):
        return self.training

    @doctorate.setter
    def doctorate(self, value):
        self.training = value

    @property
    def doctorate_id(self):
        return self.training_id

    @doctorate_id.setter
    def doctorate_id(self, value):
        self.training_id = value

    class Meta:
        verbose_name = _("Doctorate admission")
        ordering = ('-created_at',)
        permissions = [
            ('download_jury_approved_pdf', _("Can download jury-approved PDF")),
            ('upload_jury_approved_pdf', _("Can upload jury-approved PDF")),
            ('upload_signed_scholarship', _("Can upload signed scholarship")),
            ('check_publication_authorisation', _("Can check publication autorisation")),
            ('validate_registration', _("Can validate registration")),
            ('approve_jury', _("Can approve jury")),
            ('approve_confirmation_paper', _("Can approve confirmation paper")),
            ('validate_doctoral_training', _("Can validate doctoral training")),
            ('download_pdf_confirmation', _("Can download PDF confirmation")),
            ('upload_pdf_confirmation', _("Can upload PDF confirmation")),
            ('fill_thesis', _("Can fill thesis")),
            ('submit_thesis', _("Can submit thesis")),
            ('appose_cdd_notice', _("Can appose CDD notice")),
            ('appose_sic_notice', _("Can appose SIC notice")),
            ('upload_defense_report', _("Can upload defense report")),
            ('check_copyright', _("Can check copyright")),
            ('sign_diploma', _("Can sign diploma")),
            ('request_signatures', _("Can request signatures")),
            ('approve_proposition', _("Can approve proposition")),
            ('view_admission_person', _("Can view the information related to the admission request author")),
            (
                'change_admission_person',
                _("Can update the information related to the admission request author"),
            ),
            ('view_admission_coordinates', _("Can view the coordinates of the admission request author")),
            ('change_admission_coordinates', _("Can update the coordinates of the admission request author")),
            (
                'view_admission_secondary_studies',
                _("Can view the information related to the secondary studies"),
            ),
            (
                'change_admission_secondary_studies',
                _("Can update the information related to the secondary studies"),
            ),
            ('view_admission_languages', _("Can view the information related to language knowledge")),
            ('change_admission_languages', _("Can update the information related to language knowledge")),
            ('view_admission_curriculum', _("Can view the information related to the curriculum")),
            ('change_admission_curriculum', _("Can update the information related to the curriculum")),
            ('view_admission_project', _("Can view the information related to the admission project")),
            ('change_admission_project', _("Can update the information related to the admission project")),
            ('view_admission_cotutelle', _("Can view the information related to the admission cotutelle")),
            ('change_admission_cotutelle', _("Can update the information related to the admission cotutelle")),
            ('view_admission_supervision', _("Can view the information related to the admission supervision")),
            (
                'change_admission_supervision',
                _("Can update the information related to the admission supervision"),
            ),
            ('view_admission_jury', _("Can view the information related to the admission jury")),
            ('change_admission_jury', _("Can update the information related to the admission jury")),
            ('view_admission_confirmation', _("Can view the information related to the confirmation paper")),
            (
                'change_admission_confirmation',
                _("Can update the information related to the confirmation paper"),
            ),
            ('add_supervision_member', _("Can add a member to the supervision group")),
            ('remove_supervision_member', _("Can remove a member from the supervision group")),
            ('submit_doctorateadmission', _("Can submit a doctorate admission proposition")),
        ]

    def save(self, *args, **kwargs) -> None:
        super().save(*args, **kwargs)
        cache.delete('admission_permission_{}'.format(self.uuid))

    def update_detailed_status(self, author: 'Person' = None):
        from admission.ddd.admission.doctorat.preparation.commands import (
            VerifierProjetQuery,
            VerifierPropositionQuery,
            DeterminerAnneeAcademiqueEtPotQuery,
        )
        from admission.utils import gather_business_exceptions
        from infrastructure.messages_bus import message_bus_instance

        error_key = api_settings.NON_FIELD_ERRORS_KEY
        project_errors = gather_business_exceptions(VerifierProjetQuery(self.uuid)).get(error_key, [])
        submission_errors = gather_business_exceptions(VerifierPropositionQuery(self.uuid)).get(error_key, [])
        self.detailed_status = project_errors + submission_errors
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
        from admission.ddd.admission.doctorat.preparation.commands import (
            RecalculerEmplacementsDocumentsNonLibresPropositionCommand,
        )
        from infrastructure.messages_bus import message_bus_instance

        message_bus_instance.invoke(RecalculerEmplacementsDocumentsNonLibresPropositionCommand(self.uuid))


class PropositionManager(models.Manager.from_queryset(BaseAdmissionQuerySet)):
    def get_queryset(self):
        cte = EntityVersion.objects.with_children(entity_id=OuterRef("training__management_entity_id"))
        sector_subqs = (
            cte.join(EntityVersion, id=cte.col.id)
            .with_cte(cte)
            .filter(entity_type=SECTOR)
            .exclude(end_date__lte=date.today())
        )

        return (
            super()
            .get_queryset()
            .select_related(
                "training__academic_year",
                "training__education_group_type",
                "training__enrollment_campus",
                "candidate__country_of_citizenship",
                "determined_academic_year",
                "thesis_institute",
                "thesis_language",
                "accounting",
                "international_scholarship",
                "last_update_author",
                "financability_established_by",
                "financability_dispensation_first_notification_by",
                "financability_dispensation_last_notification_by",
            )
            .annotate(
                code_secteur_formation=CTESubquery(sector_subqs.values("acronym")[:1]),
                intitule_secteur_formation=CTESubquery(sector_subqs.values("title")[:1]),
            )
            .annotate_pool_end_date()
            .annotate_training_management_entity()
            .annotate_with_reference(with_management_faculty=False)
        )

    def for_domain_model(self):
        return (
            self.get_queryset()
            .select_related(
                "admission_requirement_year",
            )
            .prefetch_related(
                "refusal_reasons",
                "prerequisite_courses",
            )
        )

    def for_dto(self):
        return (
            self.get_queryset()
            .select_related(
                'training__enrollment_campus__country',
            )
            .annotate_campus_info()
        )

    def for_manager_dto(self):
        return (
            self.for_dto()
            .select_related(
                "financability_established_by",
                "financability_dispensation_first_notification_by",
                "financability_dispensation_last_notification_by",
                "admission_requirement_year",
            )
            .annotate_with_student_registration_id()
            .annotate_several_admissions_in_progress()
            .annotate_submitted_profile_countries_names()
            .annotate_last_status_update()
            .prefetch_related(
                'prerequisite_courses__academic_year',
                Prefetch(
                    'refusal_reasons',
                    queryset=RefusalReason.objects.select_related('category').order_by('category__order', 'order'),
                ),
            )
        )


class PropositionProxy(DoctorateAdmission):
    """Proxy model of base.DoctorateAdmission for Proposition in preparation context"""

    objects = PropositionManager()

    class Meta:
        proxy = True


class DemandeManager(models.Manager.from_queryset(BaseAdmissionQuerySet)):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .only(
                'uuid',
                'submitted_at',
                'submitted_profile',
                'modified_at',
                'status_cdd',
                'status_sic',
            )
            .annotate_submitted_profile_countries_names()
            .filter(
                status__in=[
                    ChoixStatutPropositionDoctorale.CONFIRMEE.name,
                    ChoixStatutPropositionDoctorale.INSCRIPTION_AUTORISEE.name,
                ]
            )
        )


class DemandeProxy(DoctorateAdmission):
    """Proxy model of base.DoctorateAdmission for Demande in validation context"""

    objects = DemandeManager()

    class Meta:
        proxy = True


class DoctorateManager(models.Manager.from_queryset(BaseAdmissionQuerySet)):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .only(
                'candidate',
                'training',
                'training__academic_year__year',
                'training__title',
                'training__acronym',
                'training__enrollment_campus__name',
                'post_enrolment_status',
                'proximity_commission',
                'reference',
                'submitted_profile',
                'uuid',
                'project_title',
                'financing_type',
                'international_scholarship',
                'other_international_scholarship',
                'supervision_group_id',
            )
            .select_related(
                'candidate',
                'training__academic_year',
                "training__enrollment_campus",
                'international_scholarship',
            )
            .annotate_training_management_entity()
            .annotate_with_reference(with_management_faculty=False)
        )


class DoctorateProxy(DoctorateAdmission):
    """Proxy model of base.DoctorateAdmission for Doctorat in doctorat context"""

    objects = DoctorateManager()

    class Meta:
        proxy = True


def confirmation_paper_directory_path(confirmation, filename: str):
    """Return the file upload directory path."""
    return 'admission/{}/{}/confirmation/{}/{}'.format(
        confirmation.admission.candidate.uuid,
        confirmation.admission.uuid,
        confirmation.uuid,
        filename,
    )


class ConfirmationPaper(models.Model):
    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        db_index=True,
    )

    admission = models.ForeignKey(
        DoctorateAdmission,
        verbose_name=_("Admission"),
        on_delete=models.CASCADE,
    )

    confirmation_date = models.DateField(
        verbose_name=_("Confirmation exam date"),
        null=True,
        blank=True,
    )
    confirmation_deadline = models.DateField(
        verbose_name=_("Confirmation deadline"),
        blank=True,
    )
    research_report = FileField(
        verbose_name=_("Research report"),
        upload_to=confirmation_paper_directory_path,
        max_files=1,
    )
    supervisor_panel_report = FileField(
        verbose_name=_("Support Committee minutes"),
        upload_to=confirmation_paper_directory_path,
        max_files=1,
    )
    supervisor_panel_report_canvas = FileField(
        verbose_name=_("Canvas of the report of the supervisory panel"),
        upload_to=confirmation_paper_directory_path,
        max_files=1,
    )
    research_mandate_renewal_opinion = FileField(
        verbose_name=_("Opinion on research mandate renewal"),
        upload_to=confirmation_paper_directory_path,
        max_files=1,
    )

    # Result of the confirmation
    certificate_of_failure = FileField(
        verbose_name=_("Certificate of failure"),
        upload_to=confirmation_paper_directory_path,
    )
    certificate_of_achievement = FileField(
        verbose_name=_("Certificate of achievement"),
        upload_to=confirmation_paper_directory_path,
    )

    # Extension
    extended_deadline = models.DateField(
        verbose_name=_("Deadline extended"),
        null=True,
        blank=True,
    )
    cdd_opinion = models.TextField(
        default="",
        verbose_name=_("CDD opinion"),
        blank=True,
    )
    justification_letter = FileField(
        verbose_name=_("Justification letter"),
        upload_to=confirmation_paper_directory_path,
    )
    brief_justification = models.TextField(
        default="",
        verbose_name=_("Brief justification"),
        blank=True,
        max_length=2000,
    )

    class Meta:
        ordering = ["-id"]


class InternalNote(models.Model):
    admission = models.ForeignKey(
        BaseAdmission,
        on_delete=models.CASCADE,
        verbose_name=_("Admission"),
    )
    author = models.ForeignKey(
        'base.Person',
        on_delete=models.SET_NULL,
        verbose_name=_("Author"),
        null=True,
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Created'),
    )
    text = RichTextField(
        verbose_name=_("Text"),
    )

    class Meta:
        ordering = ['-created_at']


class DoctorateAdmissionPrerequisiteCourses(models.Model):
    """Prerequisite courses of a doctorate admission."""

    admission = models.ForeignKey(
        DoctorateAdmission,
        on_delete=models.CASCADE,
    )
    course = models.ForeignKey(
        'base.LearningUnitYear',
        on_delete=models.PROTECT,
        related_name='+',
        to_field='uuid',
    )
