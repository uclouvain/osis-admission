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
from dal.forward import Const
from django import forms
from django.utils.translation import gettext_lazy as _

from admission.constants import FIELD_REQUIRED_MESSAGE
from admission.contrib.models import DiplomaticPost
from admission.forms import (
    AdmissionFileUploadField,
    autocomplete,
    RadioBooleanField,
    get_diplomatic_post_initial_choices,
)
from admission.forms.specific_question import ConfigurableFormMixin
from admission.mark_safe_lazy import mark_safe_lazy


class CommonSpecificQuestionsForm(ConfigurableFormMixin, forms.Form):
    configurable_form_field_name = 'reponses_questions_specifiques'

    documents_additionnels = AdmissionFileUploadField(
        label=_(
            'You can add any document you feel is relevant to your application '
            '(supporting documents, proof of language level, etc.).'
        ),
        required=False,
        max_files=10,
    )


class GeneralSpecificQuestionsForm(CommonSpecificQuestionsForm):
    # Visa
    poste_diplomatique = forms.IntegerField(
        label=_('Competent diplomatic post'),
        required=False,
        widget=autocomplete.ListSelect2(
            url='admission:autocomplete:diplomatic-posts',
            attrs={
                'data-html': True,
                'data-allow-clear': 'true',
            },
        ),
    )

    # Pool questions
    est_non_resident_au_sens_decret = RadioBooleanField(
        label=_("Are you a non-resident (as defined by government decree)?"),
        required=False,
    )

    est_bachelier_belge = RadioBooleanField(
        label=_(
            "Are you currently enrolled in the first year of a bachelor's degree at a French Community "
            "of Belgium haute ecole or university?"
        ),
        required=False,
    )

    est_modification_inscription_externe = RadioBooleanField(
        label=mark_safe_lazy(
            _(
                "Would you like to change your UCLouvain enrolment for this academic year? "
                '(<a href="%(url)s" target="_blank">Informations</a>)'
            ),
            url='https://uclouvain.be/fr/etudier/inscriptions/suivi-particulier.html#modificationinscr',
        ),
        required=False,
    )

    formulaire_modification_inscription = AdmissionFileUploadField(
        label=_('Change of enrolment form'),
        max_files=1,
        required=False,
    )

    est_reorientation_inscription_externe = RadioBooleanField(
        label=mark_safe_lazy(
            _(
                'Would you like to switch courses this academic year at UCLouvain? '
                '(<a href="%(url)s" target="_blank">Informations</a>)'
            ),
            url='https://uclouvain.be/fr/etudier/inscriptions/suivi-particulier.html#r%C3%A9orientation',
        ),
        required=False,
    )

    attestation_inscription_reguliere = AdmissionFileUploadField(
        label=_('Certificate of regular enrolment'),
        max_files=1,
        required=False,
    )

    class Media:
        js = ('js/dependsOn.min.js',)

    def __init__(
        self,
        display_visa,
        residential_country,
        display_pool_questions,
        enrolled_for_contingent_training,
        *args,
        **kwargs,
    ):
        self.display_pool_questions = display_pool_questions
        self.enrolled_for_contingent_training = enrolled_for_contingent_training

        super().__init__(*args, **kwargs)

        if display_visa:
            self.fields['poste_diplomatique'].required = True

            if residential_country:
                self.fields['poste_diplomatique'].widget.forward = [Const(residential_country, 'country')]

            initial_code = self.initial.get('poste_diplomatique')
            submitted_code = self.data.get(self.add_prefix('poste_diplomatique'))

            diplomatic_post = DiplomaticPost.objects.filter(
                code=int(submitted_code) if submitted_code and submitted_code.isdigit() else initial_code
            ).first()

            self.fields['poste_diplomatique'].choices = get_diplomatic_post_initial_choices(diplomatic_post)
            self.fields['poste_diplomatique'].widget.choices = self.fields['poste_diplomatique'].choices
        else:
            self.fields['poste_diplomatique'].disabled = True

        if not self.display_pool_questions:
            for field in [
                'est_non_resident_au_sens_decret',
                'est_bachelier_belge',
                'est_modification_inscription_externe',
                'formulaire_modification_inscription',
                'est_reorientation_inscription_externe',
                'attestation_inscription_reguliere',
            ]:
                del self.fields[field]
        elif not self.enrolled_for_contingent_training:
            del self.fields['est_non_resident_au_sens_decret']

    def clean(self):
        data = super().clean()

        if 'est_non_resident_au_sens_decret' in self.fields and data['est_non_resident_au_sens_decret'] is None:
            self.add_error('est_non_resident_au_sens_decret', FIELD_REQUIRED_MESSAGE)

        if not data.get('est_bachelier_belge'):
            # not belgian bachelor, clean modification and reorientation fields
            data['est_modification_inscription_externe'] = data.get('est_bachelier_belge')
            data['formulaire_modification_inscription'] = []
            data['est_reorientation_inscription_externe'] = data.get('est_bachelier_belge')
            data['attestation_inscription_reguliere'] = []

        if (
            'est_bachelier_belge' in data
            and data['est_bachelier_belge'] is None
            and data.get('est_non_resident_au_sens_decret') is not True
        ):
            self.add_error('est_bachelier_belge', FIELD_REQUIRED_MESSAGE)

        elif data.get('est_bachelier_belge') is True:
            # belgian bachelor, modification and reorientation asked

            if data.get('est_modification_inscription_externe') and data.get('est_reorientation_inscription_externe'):
                self.add_error(None, _('You cannot ask for both modification and reorientation at the same time.'))

            if data.get('est_modification_inscription_externe') is None:
                self.add_error('est_modification_inscription_externe', FIELD_REQUIRED_MESSAGE)
            elif not data['est_modification_inscription_externe']:
                data['formulaire_modification_inscription'] = []

            if data.get('est_reorientation_inscription_externe') is None:
                self.add_error('est_reorientation_inscription_externe', FIELD_REQUIRED_MESSAGE)
            elif not data['est_reorientation_inscription_externe']:
                data['attestation_inscription_reguliere'] = []

        return data
