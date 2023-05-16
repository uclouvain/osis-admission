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

from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from base.models.utils.utils import ChoiceEnum


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


dynamic_person_concerned = '<span class="relationship">{}</span>'.format(_('The person concerned'))
dynamic_person_concerned_lowercase = '<span class="relationship-lw">{}</span>'.format(_('the person concerned'))


class ChoixAssimilation5(ChoiceEnum):
    A_NATIONALITE_UE = _(
        '%(person_concerned)s has the nationality of a country of a Member State of the European Union'
    )
    TITULAIRE_TITRE_SEJOUR_LONGUE_DUREE = _(
        '%(person_concerned)s has a long-term residence permit (B, C, D, F, F+, K, L or M cards) in Belgium'
    )
    CANDIDATE_REFUGIE_OU_REFUGIE_OU_APATRIDE_OU_PROTECTION_SUBSIDIAIRE_TEMPORAIRE = _(
        '%(person_concerned)s is a refugee applicant, refugee, stateless person, or has '
        'temporary/subsidiary protection'
    )
    AUTORISATION_SEJOUR_ET_REVENUS_PROFESSIONNELS_OU_REMPLACEMENT = _(
        '%(person_concerned)s has a residence permit for more than 3 months and receives professional or '
        'replacement income'
    )
    PRIS_EN_CHARGE_OU_DESIGNE_CPAS = _(
        '%(person_concerned)s is supported by the CPAS, or by a CPAS rest home or designated by the CPAS'
    )


class ChoixAssimilation6(ChoiceEnum):
    A_BOURSE_ETUDES_COMMUNAUTE_FRANCAISE = _(
        'I benefit from a grant given by the study allowance service of the French Community'
    )
    A_BOURSE_COOPERATION_DEVELOPPEMENT = _('I benefit from a Development Cooperation grant')


class ChoixAffiliationSport(ChoiceEnum):
    LOUVAIN_WOLUWE = _('Yes, in Louvain-la-Neuve and/or Woluwe-Saint-Lambert (60 EUR)')
    MONS_UCL = _('Yes, in Mons and other UCLouvain sites (60 EUR)')
    MONS = _('Yes, only in Mons (10 EUR)')
    SAINT_GILLES_UCL = _('Yes, in Saint-Gilles and other UCLouvain sites (60 EUR)')
    SAINT_GILLES = _('Yes, only in Saint-Gilles (10 EUR)')
    TOURNAI_UCL = _('Yes, in Tournai and other UCLouvain sites (60 EUR)')
    TOURNAI = _('Yes, only in Tournai (10 EUR)')
    NON = _('No')


class LienParente(ChoiceEnum):
    PERE = _('My father')
    MERE = _('My mother')
    TUTEUR_LEGAL = _('My legal tutor')
    CONJOINT = _('My partner')
    COHABITANT_LEGAL = _('My legal cohabitant')


class ChoixTypeCompteBancaire(ChoiceEnum):
    IBAN = _('Yes, an account number in IBAN format')
    AUTRE_FORMAT = _('Yes, an account number in another format')
    NON = _('No')


FORMATTED_RELATIONSHIPS = {
    'PERE': _('your father'),
    'MERE': _('your mother'),
    'TUTEUR_LEGAL': _('your legal tutor'),
    'CONJOINT': _('your partner'),
    'COHABITANT_LEGAL': _('your legal cohabitant'),
}
