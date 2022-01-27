# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
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

from django.contrib.postgres.fields import JSONField
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from admission.ddd.preparation.projet_doctoral.domain.model._enums import (
    ChoixCommissionProximiteCDEouCLSM,
    ChoixCommissionProximiteCDSS,
    ChoixStatutProposition,
)
from admission.ddd.preparation.projet_doctoral.domain.model._experience_precedente_recherche import \
    ChoixDoctoratDejaRealise
from admission.ddd.preparation.projet_doctoral.domain.model._financement import ChoixTypeFinancement
from admission.ddd.preparation.projet_doctoral.domain.model._detail_projet import ChoixLangueRedactionThese
from osis_document.contrib import FileField
from osis_signature.contrib.fields import SignatureProcessField
from .base import BaseAdmission, admission_directory_path

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
        choices=ChoixCommissionProximiteCDEouCLSM.choices() + ChoixCommissionProximiteCDSS.choices(),
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
    other_thesis_location = models.CharField(
        max_length=255,
        verbose_name=_("Other thesis location"),
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

    detailed_status = JSONField(default=dict)

    status = models.CharField(
        choices=ChoixStatutProposition.choices(),
        max_length=30,
        default=ChoixStatutProposition.IN_PROGRESS.name,
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
            ('change_doctorateadmission_person',
             _("Can update the information related to the admission request author")),
            ('view_doctorateadmission_coordinates', _("Can view the coordinates of the admission request author")),
            ('change_doctorateadmission_coordinates', _("Can update the coordinates of the admission request author")),
            ('view_doctorateadmission_secondary_studies',
             _("Can view the information related to the secondary studies")),
            ('change_doctorateadmission_secondary_studies',
             _("Can update the information related to the secondary studies")),
            ('view_doctorateadmission_languages', _("Can view the information related to language knowledge")),
            ('change_doctorateadmission_languages', _("Can update the information related to language knowledge")),
            ('view_doctorateadmission_curriculum', _("Can view the information related to the curriculum")),
            ('change_doctorateadmission_curriculum', _("Can update the information related to the curriculum")),
            ('view_doctorateadmission_project', _("Can view the information related to the admission project")),
            ('change_doctorateadmission_project', _("Can update the information related to the admission project")),
            ('view_doctorateadmission_cotutelle', _("Can view the information related to the admission cotutelle")),
            ('change_doctorateadmission_cotutelle', _("Can update the information related to the admission cotutelle")),
            ('view_doctorateadmission_supervision', _("Can view the information related to the admission supervision")),
            ('change_doctorateadmission_supervision',
             _("Can update the information related to the admission supervision")),
            ('add_supervision_member', _("Can add a member to the supervision group")),
            ('remove_supervision_member', _("Can remove a member from the supervision group")),
        ]

    def get_absolute_url(self):
        return reverse("admission:doctorate-detail", args=[self.pk])
