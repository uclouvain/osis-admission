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

from admission.ddd.preparation.projet_doctoral.domain.model._enums import ChoixBureauCDE, ChoixStatutProposition
from admission.ddd.preparation.projet_doctoral.domain.model._experience_precedente_recherche import \
    ChoixDoctoratDejaRealise
from admission.ddd.preparation.projet_doctoral.domain.model._financement import ChoixTypeFinancement
from admission.ddd.preparation.projet_doctoral.domain.model._detail_projet import ChoixLangueRedactionThese
from osis_document.contrib import FileField
from osis_signature.contrib.fields import SignatureProcessField
from .base import BaseAdmission


class DoctorateAdmission(BaseAdmission):
    doctorate = models.ForeignKey(
        to="base.EducationGroupYear",
        verbose_name=_("Doctorate"),
        related_name="+",
        on_delete=models.CASCADE,
    )
    bureau = models.CharField(
        max_length=255,
        verbose_name=_("Bureau"),
        choices=ChoixBureauCDE.choices(),
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
        default='',
        blank=True,
    )
    thesis_institute = models.CharField(
        max_length=255,
        verbose_name=_("Thesis institute"),
        default='',
        blank=True,
    )
    thesis_location = models.CharField(
        max_length=255,
        verbose_name=_("Thesis location"),
        default='',
        blank=True,
    )
    project_document = FileField(
        verbose_name=_("Project"),
    )
    gantt_graph = FileField(
        verbose_name=_("Gantt graph"),
    )
    program_proposition = FileField(
        verbose_name=_("Program proposition"),
    )
    additional_training_project = FileField(
        verbose_name=_("Additional training project"),
    )
    recommendation_letters = FileField(
        verbose_name=_("Recommendation letters"),
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
    )
    cotutelle_convention = FileField(
        verbose_name=_("Cotutelle convention"),
        max_files=1,
    )
    cotutelle_other_documents = FileField(
        verbose_name=_("Other cotutelle-related documents"),
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
            ('access_doctorateadmission', _("Can access doctorate admission list")),
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
            ('approve_proposition', _("Can approve proposition")),
        ]

    def get_absolute_url(self):
        return reverse("admission:doctorate-detail", args=[self.pk])
