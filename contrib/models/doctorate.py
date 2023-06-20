# ##############################################################################
#
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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
import uuid
from contextlib import suppress

from ckeditor.fields import RichTextField
from django.core.cache import cache
from django.db import models
from django.db.models import OuterRef
from django.utils.datetime_safe import date
from django.utils.translation import gettext_lazy as _
from rest_framework.settings import api_settings

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
from admission.ddd.admission.doctorat.validation.domain.model.enums import ChoixStatutCDD, ChoixStatutSIC
from admission.ddd.parcours_doctoral.domain.model.enums import ChoixStatutDoctorat
from base.models.academic_year import AcademicYear
from base.models.entity_version import EntityVersion
from base.models.enums.entity_type import SECTOR
from base.models.person import Person
from base.utils.cte import CTESubquery
from osis_common.ddd.interface import BusinessException
from osis_document.contrib import FileField
from osis_signature.contrib.fields import SignatureProcessField
from reference.models.country import Country
from .base import BaseAdmission, BaseAdmissionQuerySet, admission_directory_path

__all__ = [
    "DoctorateAdmission",
    "DoctorateProxy",
    "ConfirmationPaper",
]

from ...ddd.admission.dtos.conditions import InfosDetermineesDTO
from ...ddd.parcours_doctoral.jury.domain.model.enums import FormuleDefense


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
        verbose_name=_("Financing type"),
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
        verbose_name=_("Scholarship proof"),
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
    thesis_language = models.CharField(
        max_length=255,
        choices=ChoixLangueRedactionThese.choices(),
        verbose_name=_("Thesis language"),
        default=ChoixLangueRedactionThese.UNDECIDED.name,
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
    project_document = FileField(
        verbose_name=_("Project"),
        upload_to=admission_directory_path,
    )
    gantt_graph = FileField(
        verbose_name=_("Gantt graph"),
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
        verbose_name=_("Recommendation letters"),
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
        verbose_name=_("Thesis domain"),
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
    cotutelle_institution = models.CharField(
        max_length=255,
        verbose_name=_("Institution"),
        default='',
        blank=True,
    )
    cotutelle_opening_request = FileField(
        verbose_name=_("Cotutelle request document"),
        max_files=1,
        upload_to=admission_directory_path,
    )
    cotutelle_convention = FileField(
        verbose_name=_("Cotutelle convention"),
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
    pre_admission_submission_date = models.DateTimeField(
        verbose_name=_("Pre-admission submission date"),
        null=True,
    )

    supervision_group = SignatureProcessField()

    erasmus_mundus_scholarship = models.ForeignKey(
        to="admission.Scholarship",
        verbose_name=_("Erasmus Mundus scholarship"),
        related_name="+",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
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

    objects = BaseAdmissionQuerySet.as_manager()

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
            update_fields.append('last_update_author')

        with suppress(BusinessException):
            dto: 'InfosDetermineesDTO' = message_bus_instance.invoke(DeterminerAnneeAcademiqueEtPotQuery(self.uuid))
            self.determined_academic_year = AcademicYear.objects.get(year=dto.annee)
            self.determined_pool = dto.pool.name

        self.save(update_fields=update_fields)


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
                "accounting",
                "erasmus_mundus_scholarship",
                "international_scholarship",
            )
            .annotate(
                code_secteur_formation=CTESubquery(sector_subqs.values("acronym")[:1]),
                intitule_secteur_formation=CTESubquery(sector_subqs.values("title")[:1]),
            )
            .annotate_campus()
            .annotate_pool_end_date()
            .annotate_training_management_entity()
            .annotate_with_reference(with_management_faculty=False)
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
                'pre_admission_submission_date',
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
            .exclude(
                post_enrolment_status=ChoixStatutDoctorat.ADMISSION_IN_PROGRESS.name,
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
        verbose_name=_("Date of confirmation"),
        null=True,
        blank=True,
    )
    confirmation_deadline = models.DateField(
        verbose_name=_("Deadline for confirmation"),
        blank=True,
    )
    research_report = FileField(
        verbose_name=_("Research report"),
        upload_to=confirmation_paper_directory_path,
        max_files=1,
    )
    supervisor_panel_report = FileField(
        verbose_name=_("Report of the supervisory panel"),
        upload_to=confirmation_paper_directory_path,
        max_files=1,
    )
    supervisor_panel_report_canvas = FileField(
        verbose_name=_("Canvas of the report of the supervisory panel"),
        upload_to=confirmation_paper_directory_path,
        max_files=1,
    )
    research_mandate_renewal_opinion = FileField(
        verbose_name=_("Opinion on the renewal of the research mandate"),
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
