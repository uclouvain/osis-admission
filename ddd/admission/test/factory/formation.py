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
import attr
import factory.fuzzy

from admission.ddd.admission.domain.model._campus import Campus
from admission.ddd.admission.domain.model.formation import Formation, FormationIdentity


class FormationIdentityFactory(factory.Factory):
    class Meta:
        model = FormationIdentity
        abstract = False

    sigle = factory.Sequence(lambda n: 'SIGLE%02d' % n)
    annee = factory.fuzzy.FuzzyInteger(1999, 2099)


@attr.dataclass(frozen=True, slots=True)
class FormationEtendue(Formation):
    intitule: str
    campus: Campus
    campus_inscription: Campus
    sigle_entite_gestion: str
    code: str
    credits: int


class CampusFactory(factory.Factory):
    class Meta:
        model = Campus

    nom = factory.Iterator(
        [
            "Louvain-la-Neuve",
            "Mons",
            "Bruxelles Woluwe",
            "Namur",
            "Charleroi",
            "Tournai",
            "St-Gilles",
        ]
    )
    code_postal = 'code_postal'
    ville = 'ville'
    pays_iso_code = 'pays'
    nom_pays = 'nom_pays'
    rue = 'rue'
    numero_rue = 'numero_rue'
    localisation = 'localisation'
    email_inscription_sic = 'email@example.com'


class FormationFactory(factory.Factory):
    class Meta:
        model = FormationEtendue
        abstract = False

    entity_id = factory.SubFactory(FormationIdentityFactory)
    intitule = factory.Faker('sentence')
    code = factory.Sequence(lambda n: 'code%02d' % n)
    code_domaine = '01A'
    campus = factory.SubFactory(CampusFactory)
    campus_inscription = factory.SubFactory(CampusFactory)
    sigle_entite_gestion = factory.Sequence(lambda n: 'SIGLE%02d' % n)
    credits = 180
