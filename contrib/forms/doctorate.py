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
from dal import autocomplete
from django import forms
from django.utils.translation import gettext_lazy as _

from admission.contrib.models import AdmissionType
from ddd.logic.admission.preparation.projet_doctoral.domain.model._detail_projet import ChoixLangueRedactionThese
from ddd.logic.admission.preparation.projet_doctoral.domain.model._experience_precedente_recherche import \
    ChoixDoctoratDejaRealise
from ddd.logic.admission.preparation.projet_doctoral.domain.model._financement import ChoixTypeFinancement
from ddd.logic.admission.preparation.projet_doctoral.domain.model._enums import ChoixBureauCDE
from osis_document.contrib import FileUploadField


class DoctorateAdmissionProjectForm(forms.Form):
    type_admission = forms.ChoiceField(
        label=_("Admission type"),
        choices=AdmissionType.choices(),
        widget=forms.RadioSelect,
    )
    justification = forms.CharField(
        label=_("Brief justification"),
        widget=forms.Textarea(attrs={
            'rows': 2,
            'placeholder': _("Detail here the reasons which justify the recourse to a provisory admission.")
        }),
        required=False,
    )
    sector = forms.CharField(
        label=_("Sector"),
        widget=autocomplete.ListSelect2(url="admission:autocomplete:sector"),
    )
    doctorate = forms.CharField(
        label=_("Doctorate"),
        widget=autocomplete.ListSelect2(url="admission:autocomplete:doctorate", forward=['sector']),
    )
    bureau_cde = forms.ChoiceField(
        label=_("Bureau"),
        choices=(('', ' - '),) + ChoixBureauCDE.choices(),
        required=False,
    )

    type_financement = forms.ChoiceField(
        label=_("Financing type"),
        choices=(('', ' - '),) + ChoixTypeFinancement.choices(),
        required=False,
    )
    type_contrat_travail = forms.ChoiceField(
        label=_("Work contract type"),
        choices=(('', ' - '),),  # FIXME
        required=False,
    )
    type_contrat_travail_other = forms.CharField(
        label=_("Specify work contract"),
        required=False,
    )
    eft = forms.IntegerField(
        label=_("Full-time equivalent"),
        min_value=0,
        max_value=100,
        required=False,
    )
    bourse_recherche = forms.ChoiceField(
        label=_("Scholarship grant"),
        choices=(('', ' - '),),  # FIXME
        required=False,
    )
    bourse_recherche_other = forms.CharField(
        label=_("Specify scholarship grant"),
        max_length=255,
        required=False,
    )
    duree_prevue = forms.IntegerField(
        label=_("Estimated time"),
        min_value=0,
        required=False,
    )
    temps_consacre = forms.IntegerField(
        label=_("Allocated time"),
        min_value=0,
        required=False,
    )

    titre_projet = forms.CharField(
        label=_("Project title"),
        required=False,
    )
    resume_projet = forms.CharField(
        label=_("Project resume"),
        required=False,
        widget=forms.Textarea,
    )
    documents_projet = FileUploadField(
        label=_("Project documents"),
        required=False,
    )
    graphe_gantt = FileUploadField(
        label=_("Gantt graph"),
        required=False,
    )
    proposition_programme_doctoral = FileUploadField(
        label=_("Doctoral project proposition"),
        required=False,
    )
    projet_formation_complementaire = FileUploadField(
        label=_("Complementary training project"),
        required=False,
    )
    langue_redaction_these = forms.ChoiceField(
        label=_("Thesis redacting language"),
        choices=ChoixLangueRedactionThese.choices(),
        initial=ChoixLangueRedactionThese.UNDECIDED.name,
        required=False,
    )
    doctorat_deja_realise = forms.ChoiceField(
        label=_("PhD already done"),
        choices=ChoixDoctoratDejaRealise.choices(),
        initial=ChoixDoctoratDejaRealise.NO.name,
        required=False,
    )
    institution = forms.CharField(
        label=_("Institution"),
        required=False,
    )
    date_soutenance = forms.DateField(
        label=_("Defense date"),
        required=False,
    )
    raison_non_soutenue = forms.CharField(
        label=_("No defense reason"),
        widget=forms.Textarea(attrs={
            'rows': 2,
        }),
        required=False,
    )

    class Media:
        js = ('dependsOn.min.js',)
