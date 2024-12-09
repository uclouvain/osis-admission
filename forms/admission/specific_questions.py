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
from dal.forward import Const
from django import forms
from django.utils.translation import gettext_lazy as _

from admission.models import DiplomaticPost
from admission.ddd.admission.formation_continue.domain.model.enums import (
    ChoixInscriptionATitre,
    ChoixTypeAdresseFacturation,
)
from admission.forms import (
    get_diplomatic_post_initial_choices,
)
from admission.forms.admission.coordonnees import BaseAdmissionAddressForm
from admission.forms.specific_question import ConfigurableFormMixin
from base.forms.utils import FIELD_REQUIRED_MESSAGE, autocomplete
from base.forms.utils.fields import RadioBooleanField
from base.forms.utils.file_field import MaxOneFileUploadField
from base.utils.mark_safe_lazy import mark_safe_lazy


class CommonSpecificQuestionsForm(ConfigurableFormMixin, forms.Form):
    configurable_form_field_name = 'reponses_questions_specifiques'

    documents_additionnels = MaxOneFileUploadField(
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
        label=_("You are applying as ..."),
        choices=(
            (False, _("Resident (as defined by government decree)")),
            (True, _("Non-resident (as defined by government decree)")),
        ),
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

    formulaire_modification_inscription = MaxOneFileUploadField(
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

    attestation_inscription_reguliere = MaxOneFileUploadField(
        label=_('Certificate of regular enrolment'),
        max_files=1,
        required=False,
    )

    formulaire_reorientation = MaxOneFileUploadField(
        label=_('Your completed and signed reorientation form'),
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
                'formulaire_reorientation',
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
            data['formulaire_reorientation'] = []

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
                data['formulaire_reorientation'] = []

        return data


class ContinuingSpecificQuestionsForm(ConfigurableFormMixin, BaseAdmissionAddressForm):
    configurable_form_field_name = 'reponses_questions_specifiques'

    copie_titre_sejour = MaxOneFileUploadField(
        label=_(
            'Please provide a copy of the residence permit covering the entire course, including the assessment test '
            '(except for online courses).'
        ),
        max_files=1,
        required=False,
    )
    inscription_a_titre = forms.ChoiceField(
        choices=ChoixInscriptionATitre.choices(),
        label=_('You are registering as'),
        widget=forms.RadioSelect,
    )
    nom_siege_social = forms.CharField(
        label=_('Head office name'),
        required=False,
        max_length=255,
    )
    numero_unique_entreprise = forms.CharField(
        label=_('Unique business number'),
        required=False,
        max_length=255,
    )
    numero_tva_entreprise = forms.CharField(
        label=_('VAT number'),
        required=False,
        max_length=255,
    )
    adresse_mail_professionnelle = forms.EmailField(
        label=_('Please enter your work email address'),
        required=False,
    )

    # Adresse facturation
    type_adresse_facturation = forms.ChoiceField(
        choices=ChoixTypeAdresseFacturation.verbose_choices(),
        label=_('I would like the billing address to be'),
        required=False,
        widget=forms.RadioSelect,
    )
    adresse_facturation_destinataire = forms.CharField(
        label=_('To the attention of'),
        required=False,
        max_length=255,
    )
    documents_additionnels = MaxOneFileUploadField(
        label=_(
            'You can add any document you feel is relevant to your application '
            '(supporting documents, proof of language level, etc.).'
        ),
        required=False,
        max_files=10,
    )

    class Media:
        js = (
            'js/dependsOn.min.js',
            'js/jquery.mask.min.js',
            'admission/formatter.js',
        )

    def __init__(self, display_residence_permit_question, **kwargs):
        super().__init__(**kwargs)
        self.display_residence_permit_question = display_residence_permit_question
        self.check_coordinates_fields = (
            self.data.get(self.add_prefix('inscription_a_titre')) == ChoixInscriptionATitre.PROFESSIONNEL.name
            and self.data.get(self.add_prefix('type_adresse_facturation')) == ChoixTypeAdresseFacturation.AUTRE.name
        )

    def clean(self):
        cleaned_data = super().clean()

        enrollment_as = cleaned_data.get('inscription_a_titre')
        billing_address_type = cleaned_data.get('type_adresse_facturation')

        professional_fields = [
            'nom_siege_social',
            'numero_unique_entreprise',
            'numero_tva_entreprise',
            'adresse_mail_professionnelle',
            'type_adresse_facturation',
        ]

        if enrollment_as == ChoixInscriptionATitre.PROFESSIONNEL.name:
            for field in professional_fields:
                if not cleaned_data.get(field):
                    self.add_error(field, FIELD_REQUIRED_MESSAGE)
        else:
            for field in professional_fields:
                cleaned_data[field] = ''

        if not (
            enrollment_as == ChoixInscriptionATitre.PROFESSIONNEL.name
            and billing_address_type == ChoixTypeAdresseFacturation.AUTRE.name
        ):
            cleaned_data['street'] = ''
            cleaned_data['street_number'] = ''
            cleaned_data['postal_box'] = ''
            cleaned_data['postal_code'] = ''
            cleaned_data['city'] = ''
            cleaned_data['country'] = None
            cleaned_data['be_postal_code'] = ''
            cleaned_data['be_city'] = ''

        if not self.display_residence_permit_question:
            cleaned_data['copie_titre_sejour'] = []

        return cleaned_data
