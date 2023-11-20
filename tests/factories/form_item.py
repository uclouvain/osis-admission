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
import factory
from factory import fuzzy, Faker

from admission.contrib.models import AdmissionFormItem, AdmissionFormItemInstantiation
from admission.ddd.admission.enums.question_specifique import (
    TypeItemFormulaire,
    CritereItemFormulaireFormation,
    CritereItemFormulaireNationaliteCandidat,
    CritereItemFormulaireLangueEtudes,
    CritereItemFormulaireVIP,
    Onglets,
)
from base.tests.factories.academic_year import AcademicYearFactory


class AdmissionFormItemFactory(factory.django.DjangoModelFactory):
    internal_label = Faker('uuid4')

    class Meta:
        model = AdmissionFormItem

    configuration = {}


class MessageAdmissionFormItemFactory(AdmissionFormItemFactory):
    type = TypeItemFormulaire.MESSAGE.name
    text = {'en': 'My very short message.', 'fr-be': 'Mon très court message.'}


class TextAdmissionFormItemFactory(AdmissionFormItemFactory):
    type = TypeItemFormulaire.TEXTE.name
    title = {'en': 'Text field', 'fr-be': 'Champ texte'}
    text = {'en': 'Detailed data.', 'fr-be': 'Données détaillées.'}
    help_text = {'en': 'Write here', 'fr-be': 'Ecrivez ici'}


class DocumentAdmissionFormItemFactory(AdmissionFormItemFactory):
    type = TypeItemFormulaire.DOCUMENT.name
    title = {'en': 'Document field', 'fr-be': 'Champ document'}
    text = {'en': 'Detailed data.', 'fr-be': 'Données détaillées.'}


class SelectionAdmissionFormItemFactory(AdmissionFormItemFactory):
    type = TypeItemFormulaire.SELECTION.name
    title = {'en': 'Selection field', 'fr-be': 'Champ de sélection'}
    text = {'en': 'Detailed data.', 'fr-be': 'Données détaillées.'}
    values = [
        {'key': '1', 'en': 'One', 'fr-be': 'Un'},
        {'key': '2', 'en': 'Two', 'fr-be': 'Deux'},
        {'key': '3', 'en': 'Three', 'fr-be': 'Trois'},
    ]


class RadioButtonSelectionAdmissionFormItemFactory(SelectionAdmissionFormItemFactory):
    configuration = {
        'TYPE_SELECTION': 'BOUTONS_RADIOS',
    }


class CheckboxSelectionAdmissionFormItemFactory(SelectionAdmissionFormItemFactory):
    configuration = {
        'TYPE_SELECTION': 'CASES_A_COCHER',
    }


class AdmissionFormItemInstantiationFactory(factory.django.DjangoModelFactory):
    form_item = factory.SubFactory(AdmissionFormItemFactory)
    academic_year = factory.SubFactory(AcademicYearFactory)

    education_group_type = None
    education_group = None
    admission = None
    required = False

    weight = factory.fuzzy.FuzzyInteger(1, 10)
    tab = factory.fuzzy.FuzzyChoice(Onglets.get_names())

    display_according_education = CritereItemFormulaireFormation.TOUTE_FORMATION.name
    candidate_nationality = CritereItemFormulaireNationaliteCandidat.TOUS.name
    study_language = CritereItemFormulaireLangueEtudes.TOUS.name
    vip_candidate = CritereItemFormulaireVIP.TOUS.name

    class Meta:
        model = AdmissionFormItemInstantiation
