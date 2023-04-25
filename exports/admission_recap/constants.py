# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2023 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.utils.translation import gettext as _

from base.models.enums.education_group_types import TrainingType
from osis_profile.models.enums.curriculum import ActivityType

TRAINING_TYPES_WITH_EQUIVALENCE = {
    TrainingType.AGGREGATION.name,
    TrainingType.CAPAES.name,
    TrainingType.UNIVERSITY_FIRST_CYCLE_CERTIFICATE.name,
}
FORMATTED_RELATIONSHIPS = {
    'PERE': _('your father'),
    'MERE': _('your mother'),
    'TUTEUR_LEGAL': _('your legal tutor'),
    'CONJOINT': _('your partner'),
    'COHABITANT_LEGAL': _('your legal cohabitant'),
}
CURRICULUM_ACTIVITY_LABEL = {
    ActivityType.LANGUAGE_TRAVEL.name: _(
        'Certificate justifying your activity, mentioning this activity, for the specified period'
    ),
    ActivityType.INTERNSHIP.name: _('Training certificate, with dates, justifying the specified period'),
    ActivityType.UNEMPLOYMENT.name: _(
        'Unemployment certificate issued by the relevant organisation, justifying the specified period'
    ),
    ActivityType.VOLUNTEERING.name: _('Certificate, with dates, justifying the specified period'),
    ActivityType.WORK.name: _('Employment certificate from the employer, with dates, justifying the specified period'),
}
ACCOUNTING_LABEL = {
    'carte_resident_longue_duree': _('Copy of both sides of the EC long-term resident card (D card)'),
    'carte_cire_sejour_illimite_etranger': _(
        'Copy of both sides of the CIRE - unlimited stay (B card) or copy of the foreigner\'s card - unlimited stay '
        '(C card)'
    ),
    'carte_sejour_membre_ue': _(
        'Copy of both sides of the residence card of a family member of a European Union citizen (F card)'
    ),
    'carte_sejour_permanent_membre_ue': _(
        'Copy of both sides of the permanent residence card of a family member of a European Union citizen (F+ card)'
    ),
    'carte_a_b_refugie': _('Copy of both sides of the A or B card (with "refugee" written on the back of the card)'),
    'annexe_25_26_refugies_apatrides': _(
        'Copy of the Annex 25 or 26 completed by the Office of the Commissioner General for Refugees and Stateless '
        'Persons'
    ),
    'attestation_immatriculation': _('Copy of the registration certificate "orange card"'),
    'carte_a_b': _('Copy of both sides of the A or B Card'),
    'decision_protection_subsidiaire': _(
        'Copy of the decision of the Foreigners\' Office confirming the granting of subsidiary protection'
    ),
    'decision_protection_temporaire': _(
        'Copy of the decision of the Foreigners\' Office confirming the granting of temporary protection'
    ),
    'titre_sejour_3_mois_professionel': _('Copy of both sides of the residence permit valid for more than 3 months'),
    'fiches_remuneration': _('Copy of 6 salary slips issued in the 12 months preceding the application'),
    'titre_sejour_3_mois_remplacement': _('Copy of both sides of the residence permit valid for more than 3 months'),
    'preuve_allocations_chomage_pension_indemnite': _(
        'Proof of receipt of unemployment benefit, pension or compensation from the mutual insurance company'
    ),
    'attestation_cpas': _('Recent certificate of support from the CPAS'),
    'composition_menage_acte_naissance': _('Household composition, or a copy of your birth certificate'),
    'acte_tutelle': _('Copy of the tutorship act authenticated by the Belgian authorities'),
    'composition_menage_acte_mariage': _(
        'Household composition or marriage certificate authenticated by the Belgian authorities'
    ),
    'attestation_cohabitation_legale': _('Certificate of legal cohabitation'),
    'carte_identite_parent': _('Copy of both sides of the identity card of %(person_concerned)s'),
    'titre_sejour_longue_duree_parent': _(
        'Copy of both sides of the long-term residence permit in Belgium of %(person_concerned)s '
        '(B, C, D, F, F+ or M cards)'
    ),
    'annexe_25_26_refugies_apatrides_decision_protection_parent': _(
        'Copy of the Annex 25 or 26 or the A/B card mentioning the refugee status or copy of the decision of the '
        'Foreigners\' Office confirming the temporary/subsidiary protection of %(person_concerned)s'
    ),
    'titre_sejour_3_mois_parent': _(
        'Copy of both sides of the residence permit valid for more than 3 months of %(person_concerned)s'
    ),
    'fiches_remuneration_parent': _(
        'Copy of the 6 salary slips issued in the 12 months preceding the application for registration or proof of '
        'receipt of unemployment benefit, pension or an indemnity from the mutual insurance company of '
        '%(person_concerned)s'
    ),
    'attestation_cpas_parent': _('Recent certificate of support from the CPAS of %(person_concerned)s'),
    'decision_bourse_cfwb': _('Copy of the decision to grant the scholarship from the CFWB'),
    'attestation_boursier': _(
        'Copy of the certificate of scholarship holder issued by the General Administration for Development Cooperation'
    ),
    'titre_identite_sejour_longue_duree_ue': _(
        'Copy of both sides of the identity document proving the long-term stay in a member state of the European Union'
    ),
    'titre_sejour_belgique': _('Copy of both sides of the residence permit in Belgium'),
}
