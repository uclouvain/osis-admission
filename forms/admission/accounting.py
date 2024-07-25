# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
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

from typing import List

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _, ngettext
from localflavor.generic.forms import BICFormField, IBAN_MIN_LENGTH

from admission.ddd.admission.domain.validator._should_comptabilite_etre_completee import DEPENDANCES_CHAMPS_ASSIMILATION
from admission.ddd.admission.enums import (
    TypeSituationAssimilation,
    ChoixAssimilation1,
    ChoixAssimilation2,
    ChoixAssimilation3,
    LienParente,
    ChoixAssimilation5,
    dynamic_person_concerned,
    ChoixAssimilation6,
    ChoixTypeCompteBancaire,
    ChoixAffiliationSport,
)
from base.forms.utils import get_example_text, FIELD_REQUIRED_MESSAGE
from base.forms.utils.fields import RadioBooleanField
from base.forms.utils.file_field import MaxOneFileUploadField
from base.utils.mark_safe_lazy import mark_safe_lazy
from education_group.templatetags.academic_year_display import get_academic_year
from reference.services.iban_validator import (
    IBANValidatorService,
    IBANValidatorException,
    IBANValidatorRequestException,
)


class AccountingForm(forms.Form):
    # Absence of debt
    attestation_absence_dette_etablissement = MaxOneFileUploadField(
        label=_('Certificate stating no debts to the institution attended during the academic year'),
        required=False,
    )

    # Reduced tuition fee
    demande_allocation_d_etudes_communaute_francaise_belgique = RadioBooleanField(
        label=mark_safe_lazy(
            _(
                "Have you applied <a href='https://allocations-etudes.cfwb.be/etudes-superieures/' target='_blank'>"
                "for a student grant</a> from the French Community of Belgium?"
            )
        ),
        required=False,
    )
    enfant_personnel = RadioBooleanField(
        label=_('Are you the child of a UCLouvain or Martin V staff member?'),
        help_text=_("Martin V comprises both the Martin V Ecole Fondamentale and the Martin V Lycee."),
        required=False,
    )
    attestation_enfant_personnel = MaxOneFileUploadField(
        label=_('Certificate for children of staff'),
        required=False,
    )

    # Assimilation
    type_situation_assimilation = forms.ChoiceField(
        choices=TypeSituationAssimilation.choices(),
        label=_('Please select the Belgian student status situation that most applies to you'),
        required=False,
        widget=forms.RadioSelect,
    )

    # Assimilation 1
    sous_type_situation_assimilation_1 = forms.ChoiceField(
        choices=ChoixAssimilation1.choices(),
        label=_('Choose from the following'),
        required=False,
        widget=forms.RadioSelect,
    )
    carte_resident_longue_duree = MaxOneFileUploadField(
        label=_('Copy of both sides of EC long-term resident card (D or L Card)'),
        required=False,
    )
    carte_cire_sejour_illimite_etranger = MaxOneFileUploadField(
        label=_(
            "Copy of both sides of Certificate of Registration in the Foreigners Registry (CIRE), unlimited stay "
            "(B Card), or of Foreign National's Card, unlimited stay (C or K Card)"
        ),
        required=False,
    )
    carte_sejour_membre_ue = MaxOneFileUploadField(
        label=_('Copy of both sides of residence permit for a family member of a European Union citizen (F Card)'),
        required=False,
    )
    carte_sejour_permanent_membre_ue = MaxOneFileUploadField(
        label=_(
            'Copy of both sides of permanent residence card of a family member of a European Union citizen (F+ Card)'
        ),
        required=False,
    )

    # Assimilation 2
    sous_type_situation_assimilation_2 = forms.ChoiceField(
        choices=ChoixAssimilation2.choices(),
        label=_('Choose from the following'),
        required=False,
        widget=forms.RadioSelect,
    )
    carte_a_b_refugie = MaxOneFileUploadField(
        label=_('Copy of both sides of A or B Card (with "refugee" on card back)'),
        required=False,
    )
    annexe_25_26_refugies_apatrides = MaxOneFileUploadField(
        label=_(
            'Copy of Annex 25 or 26 completed by the Office of the Commissioner General for Refugees and '
            'Stateless Persons'
        ),
        required=False,
    )
    attestation_immatriculation = MaxOneFileUploadField(
        label=_('Copy of "orange card" enrolment certificate'),
        required=False,
    )
    preuve_statut_apatride = MaxOneFileUploadField(
        label=_(
            'Copy of official document from the local authority or Foreign Nationals Office proving stateless status'
        ),
        required=False,
    )
    carte_a_b = MaxOneFileUploadField(
        label=_('Copy of both sides of A or B Card'),
        required=False,
    )
    decision_protection_subsidiaire = MaxOneFileUploadField(
        label=_('Copy of Foreign Nationals Office decision granting subsidiary protection'),
        required=False,
    )
    decision_protection_temporaire = MaxOneFileUploadField(
        label=_('Copy of Foreign Nationals Office decision granting temporary protection'),
        required=False,
    )
    carte_a = MaxOneFileUploadField(
        label=_('Copy of both sides of A Card'),
        required=False,
    )

    # Assimilation 3
    sous_type_situation_assimilation_3 = forms.ChoiceField(
        choices=ChoixAssimilation3.choices(),
        label=_('Choose from the following'),
        required=False,
        widget=forms.RadioSelect,
    )

    titre_sejour_3_mois_professionel = MaxOneFileUploadField(
        label=_('Copy of both sides of residence permit valid for more than 3 months'),
        required=False,
    )
    fiches_remuneration = MaxOneFileUploadField(
        label=_('Copy of 6 payslips issued in the 12 months preceding application'),
        required=False,
        help_text=_(
            'You must have worked in Belgium and your monthly salary must be at least half of the guaranteed minimum '
            'average monthly salary set by the National Labour Council. This corresponded to E903 in 2023.'
        ),
    )
    titre_sejour_3_mois_remplacement = MaxOneFileUploadField(
        label=_('Copy of both sides of residence permit valid for more than 3 months'),
        required=False,
    )
    preuve_allocations_chomage_pension_indemnite = MaxOneFileUploadField(
        label=_('Proof of receipt of unemployment benefit, pension or compensation from the mutual insurance company'),
        required=False,
    )

    # Assimilation 4
    attestation_cpas = MaxOneFileUploadField(
        label=_('Recent CPAS certificate of coverage'),
        required=False,
    )

    # Assimilation 5
    relation_parente = forms.ChoiceField(
        choices=LienParente.choices(),
        label=_('Tick the relationship'),
        required=False,
        widget=forms.RadioSelect,
    )
    sous_type_situation_assimilation_5 = forms.ChoiceField(
        choices=ChoixAssimilation5.choices_with_interpolation({'person_concerned': dynamic_person_concerned}),
        label=_('Choose from the following'),
        required=False,
        widget=forms.RadioSelect,
    )
    composition_menage_acte_naissance = MaxOneFileUploadField(
        label=_('Household composition, or copy of your birth certificate'),
        required=False,
    )
    acte_tutelle = MaxOneFileUploadField(
        label=_('Copy of guardianship appointment legalised by Belgian authorities'),
        required=False,
    )
    composition_menage_acte_mariage = MaxOneFileUploadField(
        label=_('Household composition or marriage certificate authenticated by the Belgian authorities'),
        required=False,
    )
    attestation_cohabitation_legale = MaxOneFileUploadField(
        label=_('Certificate of legal cohabitation'),
        required=False,
    )
    carte_identite_parent = MaxOneFileUploadField(
        label=mark_safe_lazy(
            _('Copy of both sides of identity card of %(person_concerned)s'),
            person_concerned=dynamic_person_concerned,
        ),
        required=False,
    )
    titre_sejour_longue_duree_parent = MaxOneFileUploadField(
        label=mark_safe_lazy(
            _(
                'Copy of both sides of long-term residence permit in Belgium of %(person_concerned)s (B, C, D, F, F+, '
                'K, L or M Card)'
            ),
            person_concerned=dynamic_person_concerned,
        ),
        required=False,
    )
    annexe_25_26_refugies_apatrides_decision_protection_parent = MaxOneFileUploadField(
        label=mark_safe_lazy(
            _(
                "Copy of Annex 25 or 26 or A/B Card indicating refugee status or copy of Foreign Nationals Office "
                "decision confirming temporary/subsidiary protection of %(person_concerned)s or copy of official "
                "Foreign Nationals Office or municipality document proving the stateless status of %(person_concerned)s"
            ),
            person_concerned=dynamic_person_concerned,
        ),
        required=False,
    )
    titre_sejour_3_mois_parent = MaxOneFileUploadField(
        label=mark_safe_lazy(
            _('Copy of both sides of residence permit valid for more than 3 months of %(person_concerned)s'),
            person_concerned=dynamic_person_concerned,
        ),
        required=False,
    )
    fiches_remuneration_parent = MaxOneFileUploadField(
        label=mark_safe_lazy(
            _(
                'Copy of 6 payslips issued in the 12 months preceding application or proof of receipt of '
                'unemployment benefit, pension or allowance from a mutual insurance company of %(person_concerned)s'
            ),
            person_concerned=dynamic_person_concerned,
        ),
        required=False,
        help_text=_(
            'You must have worked in Belgium and your monthly salary must be at least half of the guaranteed minimum '
            'average monthly salary set by the National Labour Council. This corresponded to E903 in 2023.'
        ),
    )
    attestation_cpas_parent = MaxOneFileUploadField(
        label=mark_safe_lazy(
            _('Recent CPAS certificate of coverage for %(person_concerned)s'),
            person_concerned=dynamic_person_concerned,
        ),
        required=False,
    )

    # Assimilation 6
    sous_type_situation_assimilation_6 = forms.ChoiceField(
        choices=ChoixAssimilation6.choices(),
        label=_('Choose from the following'),
        required=False,
        widget=forms.RadioSelect,
    )
    decision_bourse_cfwb = MaxOneFileUploadField(
        label=_('Copy of decision to grant CFWB scholarship'),
        required=False,
    )
    attestation_boursier = MaxOneFileUploadField(
        label=_(
            "Copy of holder's certificate of scholarship issued by the General Administration for Development "
            "Cooperation"
        ),
        required=False,
    )

    # Assimilation 7
    titre_identite_sejour_longue_duree_ue = MaxOneFileUploadField(
        label=_('Copy of both sides of identity document proving long-term residence in a European Union member state'),
        required=False,
    )
    titre_sejour_belgique = MaxOneFileUploadField(
        label=_('Copy of both sides of residence permit in Belgium'),
        required=False,
    )

    # Memberships
    affiliation_sport = forms.ChoiceField(
        label=mark_safe_lazy(
            _(
                "Would you like to join the <a href='https://uclouvain.be/en/study/sport' "
                "target='_blank'>sports activities</a>? If so, the cost of membership will be added to your tuition "
                "fee."
            )
        ),
        widget=forms.RadioSelect,
        required=False,
    )
    etudiant_solidaire = RadioBooleanField(
        label=mark_safe_lazy(
            _(
                "Would you like to become a <a href='https://uclouvain.be/fr/decouvrir/carte-solidaire.html' "
                "target='_blank'>Solidarity Student</a>, that is, a member of a programme proposed by UCLouvain's NGO, "
                "Louvain Cooperation? This membership will give you access to a fund for your solidarity projects. "
                "If so, the membership cost, which is E12, will be added to your tuition fee."
            )
        ),
    )

    # Bank account
    type_numero_compte = forms.ChoiceField(
        choices=ChoixTypeCompteBancaire.choices(),
        label=_('Would you like to enter an account number so that we can issue a refund?'),
        widget=forms.RadioSelect,
    )
    numero_compte_iban = forms.CharField(
        label=_('IBAN account number'),
        min_length=IBAN_MIN_LENGTH,
        max_length=34,
        required=False,
        widget=forms.TextInput(
            attrs={
                "placeholder": get_example_text('BE43 0689 9999 9501'),
            },
        ),
        help_text=mark_safe_lazy(
            _(
                'The IBAN contains up to 34 alphanumeric characters, which correspond to:'
                '<ul>'
                '<li>country code (two letters)</li>'
                '<li>verification key (two digits)</li>'
                '<li>the Basic Bank Account Number (BBAN) (up to 30 alphanumeric characters)</li>'
                '</ul>'
            )
        ),
    )
    numero_compte_autre_format = forms.CharField(
        label=_('Account number'),
        required=False,
    )
    code_bic_swift_banque = BICFormField(
        label=_('BIC/SWIFT code identifying the bank from which the account originates'),
        required=False,
        widget=forms.TextInput(
            attrs={
                "placeholder": get_example_text('GKCC BE BB'),
            },
        ),
        help_text=mark_safe_lazy(
            _(
                'The BIC/SWIFT code consists of 8 or 11 characters, which correspond to:'
                '<ul>'
                '<li>bank code (four letters)</li>'
                '<li>country code (two letters)</li>'
                '<li>location code (two letters or numbers)</li>'
                '<li>branch code (optional, three letters or numbers)</li>'
                '</ul>'
            )
        ),
    )
    prenom_titulaire_compte = forms.CharField(
        label=_('Account holder first name'),
        required=False,
    )
    nom_titulaire_compte = forms.CharField(
        label=_('Account holder surname'),
        required=False,
    )

    def __init__(self, is_general_admission, with_assimilation, **kwargs):
        self.is_general_admission = is_general_admission
        self.with_assimilation = with_assimilation
        self.education_site = kwargs.pop('education_site', None)
        self.last_french_community_high_education_institutes_attended = kwargs.pop(
            'last_french_community_high_education_institutes_attended',
            None,
        )
        self.valid_iban = None
        self.display_sport_question = False

        super().__init__(**kwargs)

        if self.last_french_community_high_education_institutes_attended:
            names = self.last_french_community_high_education_institutes_attended.get('names')
            academic_year = self.last_french_community_high_education_institutes_attended.get('academic_year')

            self.fields['attestation_absence_dette_etablissement'].label = ngettext(
                'Certificate stating no debts to the institution attended during the academic year'
                ' %(academic_year)s: %(names)s.',
                'Certificates stating no debts to the institutions attended during the academic year'
                ' %(academic_year)s: %(names)s.',
                len(names),
            ) % {
                'academic_year': get_academic_year(academic_year),
                'names': ', '.join(names),
            }

        # Only display the sport question for the right campuses
        self.fields['affiliation_sport'].choices = ChoixAffiliationSport.choices_by_education_site(
            self.education_site
        )

        if self.is_general_admission:
            self.fields['demande_allocation_d_etudes_communaute_francaise_belgique'].required = True
            self.fields['enfant_personnel'].required = True

            if len(self.fields['affiliation_sport'].choices) > 1:
                self.fields['affiliation_sport'].required = True
                self.display_sport_question = True
            else:
                self.fields['affiliation_sport'].widget = forms.HiddenInput()

        if self.with_assimilation:
            self.fields['type_situation_assimilation'].required = True

        setattr(
            self.fields['sous_type_situation_assimilation_2'],
            'tooltips',
            {
                ChoixAssimilation2.PROTECTION_SUBSIDIAIRE.name: _(
                    'Subsidiary protection status is granted to a foreign national who cannot be considered a refugee '
                    'but with respect to whom there are serious grounds for believing that, if returned to his or '
                    'her country of origin, he or she would face a genuine risk of suffering serious harm'
                ),
                ChoixAssimilation2.PROTECTION_TEMPORAIRE.name: _(
                    'Temporary protection is granted for a period of one year, which can be extended. This protection '
                    'is granted in the event of a mass influx of refugees.'
                ),
            },
        )

        setattr(
            self.fields['relation_parente'],
            'tooltips',
            {
                LienParente.TUTEUR_LEGAL.name: _(
                    "A legal guardian has the prerogatives of parental authority over the child in the event of "
                    "the parents' death or their inability to exercise parental authority following a court decision. "
                    "A student of legal age cannot have a guardian. Under no circumstances is a guarantor a "
                    "legal guardian."
                ),
            },
        )

        setattr(
            self.fields['type_situation_assimilation'],
            'tooltips',
            {
                TypeSituationAssimilation.AUTORISATION_ETABLISSEMENT_OU_RESIDENT_LONGUE_DUREE.name: _(
                    'You are considered a long-term resident if you hold a residence permit valid for at least 5 years.'
                ),
                TypeSituationAssimilation.RESIDENT_LONGUE_DUREE_UE_HORS_BELGIQUE.name: _(
                    'To claim this Belgian student status, you will need to reside in Belgium during your studies and '
                    'therefore obtain a residence permit in Belgium.'
                ),
            },
        )

    class Media:
        js = (
            'js/dependsOn.min.js',
            'js/jquery.mask.min.js',
        )

    ASSIMILATION_FILE_FIELDS = [
        'carte_resident_longue_duree',
        'carte_cire_sejour_illimite_etranger',
        'carte_sejour_membre_ue',
        'carte_sejour_permanent_membre_ue',
        'carte_a_b_refugie',
        'annexe_25_26_refugies_apatrides',
        'attestation_immatriculation',
        'preuve_statut_apatride',
        'carte_a_b',
        'decision_protection_subsidiaire',
        'decision_protection_temporaire',
        'carte_a',
        'titre_sejour_3_mois_professionel',
        'fiches_remuneration',
        'titre_sejour_3_mois_remplacement',
        'preuve_allocations_chomage_pension_indemnite',
        'attestation_cpas',
        'composition_menage_acte_naissance',
        'acte_tutelle',
        'composition_menage_acte_mariage',
        'attestation_cohabitation_legale',
        'carte_identite_parent',
        'titre_sejour_longue_duree_parent',
        'annexe_25_26_refugies_apatrides_decision_protection_parent',
        'titre_sejour_3_mois_parent',
        'fiches_remuneration_parent',
        'attestation_cpas_parent',
        'decision_bourse_cfwb',
        'attestation_boursier',
        'titre_identite_sejour_longue_duree_ue',
        'titre_sejour_belgique',
    ]

    ASSIMILATION_CHOICE_FIELDS = [
        'sous_type_situation_assimilation_1',
        'sous_type_situation_assimilation_2',
        'sous_type_situation_assimilation_3',
        'relation_parente',
        'sous_type_situation_assimilation_5',
        'sous_type_situation_assimilation_6',
    ]

    @classmethod
    def get_assimilation_required_fields(cls, field_name, data) -> List[str]:
        current_fields = DEPENDANCES_CHAMPS_ASSIMILATION.get(field_name, {}).get(data[field_name], [])
        new_fields = []
        for field in current_fields:
            if field in DEPENDANCES_CHAMPS_ASSIMILATION:
                new_fields += cls.get_assimilation_required_fields(field, data)
        return current_fields + new_fields

    def clean_numero_compte_iban(self):
        value = self.cleaned_data.get('numero_compte_iban')
        if value:
            try:
                IBANValidatorService.validate(value)
                self.valid_iban = True
            except IBANValidatorException as e:
                self.valid_iban = False
                raise ValidationError(e.message)
            except IBANValidatorRequestException:
                pass
        return value

    def clean_attestation_absence_dette_etablissement(self):
        if not self.last_french_community_high_education_institutes_attended:
            return []
        return self.cleaned_data.get('attestation_absence_dette_etablissement')

    def clean(self):
        cleaned_data = super().clean()

        if not self.display_sport_question:
            cleaned_data['affiliation_sport'] = ''

        if self.is_general_admission:
            if not cleaned_data.get('enfant_personnel'):
                cleaned_data['attestation_enfant_personnel'] = []
        else:
            for field in [
                'demande_allocation_d_etudes_communaute_francaise_belgique',
                'attestation_enfant_personnel',
                'enfant_personnel',
                'affiliation_sport',
            ]:
                cleaned_data.pop(field, None)

        # Assimilation
        self.clean_assimilation_fields(cleaned_data)

        # Bank account
        self.clean_bank_fields(cleaned_data)

        return cleaned_data

    def clean_assimilation_fields(self, cleaned_data):
        assimilation_required_fields = {}

        # Can have assimilation
        if self.with_assimilation:

            if cleaned_data.get('type_situation_assimilation'):
                assimilation_required_fields = set(
                    self.get_assimilation_required_fields(
                        'type_situation_assimilation',
                        cleaned_data,
                    )
                )

        for field in self.ASSIMILATION_FILE_FIELDS:
            if field not in assimilation_required_fields:
                cleaned_data[field] = []

        for field in self.ASSIMILATION_CHOICE_FIELDS:
            if field in assimilation_required_fields:
                if not cleaned_data.get(field):
                    self.add_error(field, FIELD_REQUIRED_MESSAGE)
            else:
                cleaned_data[field] = ''

    def clean_bank_fields(self, cleaned_data):
        type_numero_banque = cleaned_data.get('type_numero_compte')
        cleaned_data['iban_valide'] = self.valid_iban

        if type_numero_banque == ChoixTypeCompteBancaire.IBAN.name:
            if not cleaned_data.get('numero_compte_iban') and 'numero_compte_iban' not in self.errors:
                self.add_error('numero_compte_iban', FIELD_REQUIRED_MESSAGE)
        else:
            cleaned_data['numero_compte_iban'] = ''

        if type_numero_banque == ChoixTypeCompteBancaire.AUTRE_FORMAT.name:
            if not cleaned_data.get('numero_compte_autre_format'):
                self.add_error('numero_compte_autre_format', FIELD_REQUIRED_MESSAGE)
            if not cleaned_data.get('code_bic_swift_banque') and 'code_bic_swift_banque' not in self.errors:
                self.add_error('code_bic_swift_banque', FIELD_REQUIRED_MESSAGE)
        else:
            cleaned_data['numero_compte_autre_format'] = ''
            cleaned_data['code_bic_swift_banque'] = ''

        if not type_numero_banque or type_numero_banque == ChoixTypeCompteBancaire.NON.name:
            cleaned_data['prenom_titulaire_compte'] = ''
            cleaned_data['nom_titulaire_compte'] = ''
        else:
            if not cleaned_data.get('prenom_titulaire_compte'):
                self.add_error('prenom_titulaire_compte', FIELD_REQUIRED_MESSAGE)
            if not cleaned_data.get('nom_titulaire_compte'):
                self.add_error('nom_titulaire_compte', FIELD_REQUIRED_MESSAGE)
