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
import datetime
import uuid

import factory

from admission.ddd.parcours_doctoral.jury.domain.model.jury import Jury, JuryIdentity, MembreJury


class JuryIdentityFactory(factory.Factory):
    class Meta:
        model = JuryIdentity
        abstract = False

    uuid = factory.LazyFunction(lambda: str(uuid.uuid4()))


class MembreJuryFactory(factory.Factory):
    class Meta:
        model = MembreJury
        abstract = False

    uuid = factory.LazyFunction(lambda: str(uuid.uuid4()))
    est_promoteur = False
    matricule = None
    role = 'MEMBRE'
    institution = 'AUTRE'
    autre_institution = ''
    pays = 'pays'
    nom = 'nom'
    prenom = 'prenom'
    email = 'email'
    titre = 'DOCTEUR'
    justification_non_docteur = None
    genre = 'AUTRE'


class JuryFactory(factory.Factory):
    class Meta:
        model = Jury
        abstract = False

    entity_id = factory.SubFactory(JuryIdentityFactory)

    titre_propose = 'titre_propose'

    cotutelle = False
    institution_cotutelle = ''

    membres = factory.LazyFunction(lambda: [])

    formule_defense = 'DEUX_TEMPS'
    date_indicative = datetime.date(2022, 1, 1)
    langue_redaction = 'english'
    langue_soutenance = 'english'
    commentaire = ''
    situation_comptable = None
    approbation_pdf = None
