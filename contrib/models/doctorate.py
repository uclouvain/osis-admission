# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2022 Université catholique de Louvain (http://www.uclouvain.be)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
# ##############################################################################
import uuid

from ckeditor.fields import RichTextField
from django.core.cache import cache
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.db.models import OuterRef
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.datetime_safe import date
from django.utils.translation import gettext_lazy as _
from rest_framework.settings import api_settings

from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    ChoixCommissionProximiteCDEouCLSM,
    ChoixCommissionProximiteCDSS,
    ChoixDoctoratDejaRealise,
    ChoixLangueRedactionThese,
    ChoixSousDomaineSciences,
    ChoixStatutProposition,
    ChoixTypeFinancement,
)
from admission.ddd.admission.doctorat.validation.domain.model.enums import ChoixStatutCDD, ChoixStatutSIC
from admission.ddd.parcours_doctoral.domain.model.enums import ChoixStatutDoctorat
from base.models.education_group_year import EducationGroupYear
from base.models.entity_version import EntityVersion
from base.models.enums.education_group_categories import Categories
from base.models.enums.education_group_types import TrainingType
from base.models.enums.entity_type import SECTOR
from base.models.person import Person
from base.utils.cte import CTESubquery
from osis_document.contrib import FileField
from osis_signature.contrib.fields import SignatureProcessField
from .base import BaseAdmission, admission_directory_path

__all__ = [
    "DoctorateAdmission",
    "DoctorateProxy",
    "ConfirmationPaper",
    "REFERENCE_SEQ_NAME",
]


REFERENCE_SEQ_NAME = 'admission_doctorateadmission_reference_seq'


class DoctorateAdmission(BaseAdmission):
    doctorate = models.ForeignKey(
        to="base.EducationGroupYear",
        verbose_name=_("Doctorate"),
        related_name="+",
        on_delete=models.CASCADE,
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
    reference = models.CharField(
        max_length=32,
        verbose_name=_("Reference"),
        unique=True,
        editable=False,
        null=True,
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
    scholarship_grant = models.CharField(
        max_length=255,
        verbose_name=_("Scholarship grant"),
        default='',
        blank=True,
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
        verbose_name=_("Additional training project"),
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

    detailed_status = models.JSONField(
        default=dict,
        encoder=DjangoJSONEncoder,
    )
    archived_record_signatures_sent = FileField(
        verbose_name=_("Archived record when signatures were sent"),
        max_files=1,
        upload_to=admission_directory_path,
        editable=False,
    )

    status = models.CharField(
        choices=ChoixStatutProposition.choices(),
        max_length=30,
        default=ChoixStatutProposition.IN_PROGRESS.name,
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
    admission_submission_date = models.DateTimeField(
        verbose_name=_("Admission submission date"),
        null=True,
    )
    submitted_profile = models.JSONField(
        verbose_name=_("Submitted profile"),
        default=dict,
    )

    supervision_group = SignatureProcessField()

    class Meta:
        verbose_name = _("Doctorate admission")
        ordering = ('-created',)
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
            ('view_doctorateadmission_person', _("Can view the information related to the admission request author")),
            (
                'change_doctorateadmission_person',
                _("Can update the information related to the admission request author"),
            ),
            ('view_doctorateadmission_coordinates', _("Can view the coordinates of the admission request author")),
            ('change_doctorateadmission_coordinates', _("Can update the coordinates of the admission request author")),
            (
                'view_doctorateadmission_secondary_studies',
                _("Can view the information related to the secondary studies"),
            ),
            (
                'change_doctorateadmission_secondary_studies',
                _("Can update the information related to the secondary studies"),
            ),
            ('view_doctorateadmission_languages', _("Can view the information related to language knowledge")),
            ('change_doctorateadmission_languages', _("Can update the information related to language knowledge")),
            ('view_doctorateadmission_curriculum', _("Can view the information related to the curriculum")),
            ('change_doctorateadmission_curriculum', _("Can update the information related to the curriculum")),
            ('view_doctorateadmission_project', _("Can view the information related to the admission project")),
            ('change_doctorateadmission_project', _("Can update the information related to the admission project")),
            ('view_doctorateadmission_cotutelle', _("Can view the information related to the admission cotutelle")),
            ('change_doctorateadmission_cotutelle', _("Can update the information related to the admission cotutelle")),
            ('view_doctorateadmission_supervision', _("Can view the information related to the admission supervision")),
            (
                'change_doctorateadmission_supervision',
                _("Can update the information related to the admission supervision"),
            ),
            ('view_doctorateadmission_confirmation', _("Can view the information related to the confirmation paper")),
            (
                'change_doctorateadmission_confirmation',
                _("Can update the information related to the confirmation paper"),
            ),
            ('add_supervision_member', _("Can add a member to the supervision group")),
            ('remove_supervision_member', _("Can remove a member from the supervision group")),
            ('submit_doctorateadmission', _("Can submit a doctorate admission proposition")),
        ]

    def __str__(self):  # pragma: no cover
        return self.reference

    def save(self, *args, **kwargs) -> None:
        super().save(*args, **kwargs)
        cache.delete('admission_permission_{}'.format(self.uuid))

    def update_detailed_status(self):
        from admission.ddd.admission.doctorat.preparation.commands import (
            VerifierProjetCommand,
            VerifierPropositionCommand,
        )
        from admission.utils import gather_business_exceptions

        error_key = api_settings.NON_FIELD_ERRORS_KEY
        project_errors = gather_business_exceptions(VerifierProjetCommand(self.uuid)).get(error_key, [])
        submission_errors = gather_business_exceptions(VerifierPropositionCommand(self.uuid)).get(error_key, [])
        self.detailed_status = project_errors + submission_errors
        self.save(update_fields=['detailed_status'])


class PropositionManager(models.Manager):
    def get_queryset(self):
        cte = EntityVersion.objects.with_children(entity_id=OuterRef("doctorate__management_entity_id"))
        sector_subqs = (
            cte.join(EntityVersion, id=cte.col.id)
            .with_cte(cte)
            .filter(entity_type=SECTOR)
            .exclude(end_date__lte=date.today())
        )

        return (
            DoctorateAdmission.objects.all()
            .select_related(
                "doctorate__academic_year",
                "candidate__country_of_citizenship",
                "thesis_institute",
                "accounting",
            )
            .annotate(
                code_secteur_formation=CTESubquery(sector_subqs.values("acronym")[:1]),
                intitule_secteur_formation=CTESubquery(sector_subqs.values("title")[:1]),
            )
        )


@receiver(post_save, sender=EducationGroupYear)
def _invalidate_doctorate_cache(sender, instance, **kwargs):
    if (  # pragma: no branch
        instance.education_group_type.category == Categories.TRAINING.name
        and instance.education_group_type.name == TrainingType.PHD.name
    ):
        keys = [
            f'admission_permission_{a_uuid}'
            for a_uuid in DoctorateAdmission.objects.filter(doctorate_id=instance.pk).values_list('uuid', flat=True)
        ]
        if keys:
            cache.delete_many(keys)


@receiver(post_save, sender=Person)
def _invalidate_candidate_cache(sender, instance, **kwargs):
    keys = [
        f'admission_permission_{a_uuid}'
        for a_uuid in DoctorateAdmission.objects.filter(candidate_id=instance.pk).values_list('uuid', flat=True)
    ]
    if keys:
        cache.delete_many(keys)


class PropositionProxy(DoctorateAdmission):
    """Proxy model of base.DoctorateAdmission for Proposition in preparation context"""

    objects = PropositionManager()

    class Meta:
        proxy = True


class DemandeManager(models.Manager):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .only(
                'uuid',
                'pre_admission_submission_date',
                'admission_submission_date',
                'submitted_profile',
                'modified',
                'status_cdd',
                'status_sic',
            )
            .filter(
                status__in=[
                    ChoixStatutProposition.SUBMITTED.name,
                    ChoixStatutProposition.ENROLLED.name,
                ]
            )
        )


class DemandeProxy(DoctorateAdmission):
    """Proxy model of base.DoctorateAdmission for Demande in validation context"""

    objects = DemandeManager()

    class Meta:
        proxy = True


class DoctorateManager(models.Manager):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .only(
                'candidate',
                'doctorate',
                'doctorate__academic_year__year',
                'doctorate__title',
                'doctorate__acronym',
                'post_enrolment_status',
                'proximity_commission',
                'reference',
                'submitted_profile',
                'uuid',
                'project_title',
                'financing_type',
                'scholarship_grant',
            )
            .select_related(
                'candidate',
                'doctorate',
                'doctorate__academic_year',
            )
            .exclude(
                post_enrolment_status=ChoixStatutDoctorat.ADMISSION_IN_PROGRESS.name,
            )
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
        DoctorateAdmission,
        on_delete=models.CASCADE,
        verbose_name=_("Admission"),
    )
    author = models.ForeignKey(
        'base.Person',
        on_delete=models.SET_NULL,
        verbose_name=_("Author"),
        null=True,
    )
    created = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Created'),
    )
    text = RichTextField(
        verbose_name=_("Text"),
    )

    class Meta:
        ordering = ['-created']
