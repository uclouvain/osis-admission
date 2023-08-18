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
from django.utils.translation import gettext_lazy as _

from admission.ddd.admission.enums.emplacement_document import OngletsDemande
from base.models.utils.utils import ChoiceEnum


class TypeItemFormulaire(ChoiceEnum):
    MESSAGE = _('Message')
    TEXTE = _('Text')
    DOCUMENT = _('Document')
    SELECTION = _('Selection')


TYPES_ITEMS_LECTURE_SEULE = {
    TypeItemFormulaire.MESSAGE.name,
}


class TypeChampTexteFormulaire(ChoiceEnum):
    COURT = _('Short')
    LONG = _('Long')


class TypeChampSelectionFormulaire(ChoiceEnum):
    CASES_A_COCHER = _('Tick boxes')
    BOUTONS_RADIOS = _('Radio buttons')
    LISTE = _('List')


class CleConfigurationItemFormulaire(ChoiceEnum):
    TAILLE_TEXTE = _('Text size')
    TYPE_SELECTION = _('Selection type')
    CLASSE_CSS = _('CSS class')
    TYPES_MIME_FICHIER = _('MIME file types')
    NOMBRE_MAX_DOCUMENTS = _('Maximum number of documents')


class CritereItemFormulaireNationaliteCandidat(ChoiceEnum):
    BELGE = _('Belgian')
    NON_BELGE = _('Not Belgian')
    UE = _('UE')
    NON_UE = _('Not UE')
    TOUS = _('All')


class CritereItemFormulaireLangueEtudes(ChoiceEnum):
    AUCUNE_ETUDE_FR = _('No French studies')
    AUCUNE_ETUDE_EN = _('No English studies')
    TOUS = _('All')


class CritereItemFormulaireVIP(ChoiceEnum):
    VIP = _('VIP')
    NON_VIP = _('Not VIP')
    TOUS = _('All')


class Onglets(ChoiceEnum):
    ETUDES_SECONDAIRES = _('Secondary studies')
    CURRICULUM = _('Curriculum')
    CHOIX_FORMATION = _('Course choice')
    INFORMATIONS_ADDITIONNELLES = _('Additional information')
    DOCUMENTS = _('Documents')


class CritereItemFormulaireFormation(ChoiceEnum):
    # Ordre notable des éléments lors de la récupération des questions (par ordre alphabétique)
    TOUTE_FORMATION = _('Every education')
    TYPE_DE_FORMATION = _('An education type')
    UNE_FORMATION = _('A specific education')
    UNE_SEULE_ADMISSION = _('Only one admission')
