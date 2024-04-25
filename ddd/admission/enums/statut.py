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
import itertools

from admission.ddd.admission.doctorat.preparation.domain.model.enums import (
    ChoixStatutPropositionDoctorale,
    STATUTS_PROPOSITION_DOCTORALE_NON_SOUMISE,
)
from admission.ddd.admission.formation_continue.domain.model.enums import (
    ChoixStatutPropositionContinue,
    STATUTS_PROPOSITION_CONTINUE_NON_SOUMISE,
)
from admission.ddd.admission.formation_generale.domain.model.enums import (
    ChoixStatutPropositionGenerale,
    STATUTS_PROPOSITION_GENERALE_NON_SOUMISE_OU_FRAIS_DOSSIER_EN_ATTENTE,
    STATUTS_PROPOSITION_GENERALE_NON_SOUMISE,
)


def choix_statuts_toute_proposition_ordonnes():
    """
    Correspond aux statuts de la proposition générale avec les statuts spécifiques de proposition continue
    et de proposition doctorale intercalés à l'endroit souhaité.
    :return: une liste de tuples (nom, valeur) des statuts ordonnés.
    """
    choix = [(statut.name, statut.value) for statut in ChoixStatutPropositionGenerale]

    # Association entre les statuts déjà présents de formation générale et les statuts spécifiques à placer juste après
    choix_specifiques = {
        ChoixStatutPropositionGenerale.EN_BROUILLON.name: ChoixStatutPropositionDoctorale.EN_ATTENTE_DE_SIGNATURE,
        ChoixStatutPropositionGenerale.ANNULEE.name: ChoixStatutPropositionContinue.ANNULEE_PAR_GESTIONNAIRE,
        ChoixStatutPropositionGenerale.CONFIRMEE.name: ChoixStatutPropositionContinue.EN_ATTENTE,
    }

    nb_choix = len(choix) + len(choix_specifiques)
    index = 0

    while index < nb_choix:
        choix_courant = choix[index]

        if choix_courant[0] in choix_specifiques:
            statut_specifique = choix_specifiques[choix_courant[0]]
            index += 1
            choix.insert(index, (statut_specifique.name, statut_specifique.value))

        index += 1

    return choix


CHOIX_STATUT_TOUTE_PROPOSITION = choix_statuts_toute_proposition_ordonnes()

CHOIX_STATUT_TOUTE_PROPOSITION_DICT = {statut[0]: statut[1] for statut in CHOIX_STATUT_TOUTE_PROPOSITION}

STATUTS_TOUTE_PROPOSITION = set(
    itertools.chain(
        ChoixStatutPropositionGenerale.get_names(),
        ChoixStatutPropositionDoctorale.get_names(),
        ChoixStatutPropositionContinue.get_names(),
    )
)

STATUTS_TOUTE_PROPOSITION_SOUMISE_HORS_FRAIS_DOSSIER = (
    STATUTS_TOUTE_PROPOSITION
    - STATUTS_PROPOSITION_GENERALE_NON_SOUMISE_OU_FRAIS_DOSSIER_EN_ATTENTE
    - STATUTS_PROPOSITION_CONTINUE_NON_SOUMISE
    - STATUTS_PROPOSITION_DOCTORALE_NON_SOUMISE
)

STATUTS_TOUTE_PROPOSITION_SOUMISE = list(
    STATUTS_TOUTE_PROPOSITION
    - STATUTS_PROPOSITION_GENERALE_NON_SOUMISE
    - STATUTS_PROPOSITION_CONTINUE_NON_SOUMISE
    - STATUTS_PROPOSITION_DOCTORALE_NON_SOUMISE
)
