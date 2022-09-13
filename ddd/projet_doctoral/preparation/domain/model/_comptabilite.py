##############################################################################
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
##############################################################################
from typing import List, Optional

import attr
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from base.models.utils.utils import ChoiceEnum
from osis_common.ddd import interface


class TypeSituationAssimilation(ChoiceEnum):
    AUTORISATION_ETABLISSEMENT_OU_RESIDENT_LONGUE_DUREE = _(
        'I have a settlement permit or I am a long-term resident in Belgium (assimilation 1)'
    )
    REFUGIE_OU_APATRIDE_OU_PROTECTION_SUBSIDIAIRE_TEMPORAIRE = _(
        'I am a refugee, stateless person, or have been granted a subsidiary or temporary protection (assimilation 2)'
    )
    AUTORISATION_SEJOUR_ET_REVENUS_PROFESSIONNELS_OU_REMPLACEMENT = _(
        'I have a residence permit for more than 3 months, and I also have professional or replacement '
        'income (assimilation 3)'
    )
    PRIS_EN_CHARGE_OU_DESIGNE_CPAS = _(
        'I am supported by the CPAS, or by a CPAS rest home or designated by the CPAS (assimilation 4)'
    )
    PROCHE_A_NATIONALITE_UE_OU_RESPECTE_ASSIMILATIONS_1_A_4 = _(
        'My father, mother, legal tutor, spouse or legal cohabitant has the nationality of a country of a Member State '
        'of the European Union, or fulfills the conditions referred to by one of the assimilations from 1 to 4 '
        '(assimilation 5)'
    )
    A_BOURSE_ARTICLE_105_PARAGRAPH_2 = _(
        'I benefit from a grant covered by the paragraph 2 of article 105 of the decree of 7 November 2013 '
        '(assimilation 6)'
    )
    RESIDENT_LONGUE_DUREE_UE_HORS_BELGIQUE = _(
        'I am a long-term resident in the European Union outside Belgium (assimilation 7)'
    )
    AUCUNE_ASSIMILATION = _('None of these proposals are relevant to me')


class ChoixAssimilation1(ChoiceEnum):
    TITULAIRE_CARTE_RESIDENT_LONGUE_DUREE = _('I have a long-term resident card')
    TITULAIRE_CARTE_ETRANGER = _('I have a foreigner\'s card')
    TITULAIRE_CARTE_SEJOUR_MEMBRE_UE = _('I have a residence card as a family member of an EU citizen.')
    TITULAIRE_CARTE_SEJOUR_PERMANENT_MEMBRE_UE = _(
        'I have a permanent residence card as a family member of a European Union citizen'
    )


class ChoixAssimilation2(ChoiceEnum):
    REFUGIE = _('I am a refugee')
    DEMANDEUR_ASILE = _('I am an asylum seeker')
    PROTECTION_SUBSIDIAIRE = _('I benefit from subsidiary protection')
    PROTECTION_TEMPORAIRE = _('I benefit from temporary protection')


class ChoixAssimilation3(ChoiceEnum):
    AUTORISATION_SEJOUR_ET_REVENUS_PROFESSIONNELS = _(
        'I have a residence permit for more than 3 months, and I have a professional income'
    )
    AUTORISATION_SEJOUR_ET_REVENUS_DE_REMPLACEMENT = _(
        'I have a residence permit for more than 3 months, and I receive a replacement income'
    )


class LienParente(ChoiceEnum):
    PERE = _('My father')
    MERE = _('My mother')
    TUTEUR_LEGAL = _('My legal tutor')
    CONJOINT = _('My partner')
    COHABITANT_LEGAL = _('My legal cohabitant')


FORMATTED_RELATIONSHIPS = {
    'PERE': _('your father'),
    'MERE': _('your mother'),
    'TUTEUR_LEGAL': _('your legal tutor'),
    'CONJOINT': _('your partner'),
    'COHABITANT_LEGAL': _('your legal cohabitant'),
}

dynamic_person_concerned = '<span class="relationship">{}</span>'.format(_('The person concerned'))
dynamic_person_concerned_lowercase = '<span class="relationship-lw">{}</span>'.format(_('the person concerned'))


class ChoixAssimilation5(ChoiceEnum):
    A_NATIONALITE_UE = mark_safe(
        _(
            '%(person_concerned)s has the nationality of a country of a Member State of the European Union'
            % {'person_concerned': dynamic_person_concerned}
        )
    )
    TITULAIRE_TITRE_SEJOUR_LONGUE_DUREE = mark_safe(
        _(
            '%(person_concerned)s has a long-term residence permit (B, C, D, F, F+ or M cards) in Belgium'
            % {'person_concerned': dynamic_person_concerned}
        )
    )
    CANDIDATE_REFUGIE_OU_REFUGIE_OU_APATRIDE_OU_PROTECTION_SUBSIDIAIRE_TEMPORAIRE = mark_safe(
        _(
            '%(person_concerned)s is a refugee applicant, refugee, stateless person, or has '
            'temporary/subsidiary protection' % {'person_concerned': dynamic_person_concerned}
        )
    )
    AUTORISATION_SEJOUR_ET_REVENUS_PROFESSIONNELS_OU_REMPLACEMENT = mark_safe(
        _(
            '%(person_concerned)s has a residence permit for more than 3 months and receives professional or '
            'replacement income' % {'person_concerned': dynamic_person_concerned}
        )
    )
    PRIS_EN_CHARGE_OU_DESIGNE_CPAS = mark_safe(
        _(
            '%(person_concerned)s is supported by the CPAS, or by a CPAS rest home or designated by the CPAS'
            % {'person_concerned': dynamic_person_concerned}
        )
    )


class ChoixAssimilation6(ChoiceEnum):
    A_BOURSE_ETUDES_COMMUNAUTE_FRANCAISE = _(
        'I benefit from a grant given by the study allowance service of the French Community'
    )
    A_BOURSE_COOPERATION_DEVELOPPEMENT = _('I benefit from a Development Cooperation grant')


class ChoixAffiliationSport(ChoiceEnum):
    LOUVAIN_WOLUWE = _('Yes, in Louvain-la-Neuve and/or Woluwe-Saint-Lambert (50 EUR)')
    MONS_UCL = _('Yes, in Mons and other UCLouvain sites (50 EUR)')
    MONS = _('Yes, only in Mons (10 EUR)')
    SAINT_GILLES_UCL = _('Yes, in Saint-Gilles and other UCLouvain sites (50 EUR)')
    SAINT_GILLES = _('Yes, only in Saint-Gilles (10 EUR)')
    TOURNAI_UCL = _('Yes, in Tournai and other UCLouvain sites (50 EUR)')
    TOURNAI = _('Yes, only in Tournai (10 EUR)')
    NON = _('No')


class ChoixTypeCompteBancaire(ChoiceEnum):
    IBAN = _('Yes, an account number in IBAN format')
    AUTRE_FORMAT = _('Yes, an account number in another format')
    NON = _('No')


@attr.dataclass(frozen=True, slots=True)
class Comptabilite(interface.ValueObject):
    # Absence de dettes
    attestation_absence_dette_etablissement: List[str] = attr.Factory(list)

    # Réduction des droits d'inscription
    demande_allocation_d_etudes_communaute_francaise_belgique: Optional[bool] = None
    enfant_personnel: Optional[bool] = None
    attestation_enfant_personnel: List[str] = attr.Factory(list)

    # Assimilation
    type_situation_assimilation: Optional[TypeSituationAssimilation] = None

    # Assimilation 1
    sous_type_situation_assimilation_1: Optional[ChoixAssimilation1] = None
    carte_resident_longue_duree: List[str] = attr.Factory(list)
    carte_cire_sejour_illimite_etranger: List[str] = attr.Factory(list)
    carte_sejour_membre_ue: List[str] = attr.Factory(list)
    carte_sejour_permanent_membre_ue: List[str] = attr.Factory(list)

    # Assimilation 2
    sous_type_situation_assimilation_2: Optional[ChoixAssimilation2] = None
    carte_a_b_refugie: List[str] = attr.Factory(list)
    annexe_25_26_refugies_apatrides: List[str] = attr.Factory(list)
    attestation_immatriculation: List[str] = attr.Factory(list)
    carte_a_b: List[str] = attr.Factory(list)
    decision_protection_subsidiaire: List[str] = attr.Factory(list)
    decision_protection_temporaire: List[str] = attr.Factory(list)

    # Assimilation 3
    sous_type_situation_assimilation_3: Optional[ChoixAssimilation3] = None
    titre_sejour_3_mois_professionel: List[str] = attr.Factory(list)
    fiches_remuneration: List[str] = attr.Factory(list)
    titre_sejour_3_mois_remplacement: List[str] = attr.Factory(list)
    preuve_allocations_chomage_pension_indemnite: List[str] = attr.Factory(list)

    # Assimilation 4
    attestation_cpas: List[str] = attr.Factory(list)

    # Assimilation 5
    relation_parente: Optional[LienParente] = None
    sous_type_situation_assimilation_5: Optional[ChoixAssimilation5] = None
    composition_menage_acte_naissance: List[str] = attr.Factory(list)
    acte_tutelle: List[str] = attr.Factory(list)
    composition_menage_acte_mariage: List[str] = attr.Factory(list)
    attestation_cohabitation_legale: List[str] = attr.Factory(list)
    carte_identite_parent: List[str] = attr.Factory(list)
    titre_sejour_longue_duree_parent: List[str] = attr.Factory(list)
    annexe_25_26_refugies_apatrides_decision_protection_parent: List[str] = attr.Factory(list)
    titre_sejour_3_mois_parent: List[str] = attr.Factory(list)
    fiches_remuneration_parent: List[str] = attr.Factory(list)
    attestation_cpas_parent: List[str] = attr.Factory(list)

    # Assimilation 6
    sous_type_situation_assimilation_6: Optional[ChoixAssimilation6] = None
    decision_bourse_cfwb: List[str] = attr.Factory(list)
    attestation_boursier: List[str] = attr.Factory(list)

    # Assimilation 7
    titre_identite_sejour_longue_duree_ue: List[str] = attr.Factory(list)
    titre_sejour_belgique: List[str] = attr.Factory(list)

    # Affiliations
    affiliation_sport: Optional[ChoixAffiliationSport] = None
    etudiant_solidaire: Optional[bool] = None

    # Compte bancaire
    type_numero_compte: Optional[ChoixTypeCompteBancaire] = None
    numero_compte_iban: Optional[str] = ''
    numero_compte_autre_format: Optional[str] = ''
    code_bic_swift_banque: Optional[str] = ''
    prenom_titulaire_compte: Optional[str] = ''
    nom_titulaire_compte: Optional[str] = ''


comptabilite_non_remplie = Comptabilite()
