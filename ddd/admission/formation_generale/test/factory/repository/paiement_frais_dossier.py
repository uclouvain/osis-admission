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
from admission.models.online_payment import PaymentStatus
from admission.ddd.admission.formation_generale.test.factory.paiement import PaiementFactory
from admission.infrastructure.admission.formation_generale.domain.service.in_memory.paiement_frais_dossier import (
    PaiementFraisDossierInMemoryRepository,
)


class PaiementFraisDossierInMemoryRepositoryFactory(PaiementFraisDossierInMemoryRepository):
    def __init__(self):
        PaiementFraisDossierInMemoryRepositoryFactory.paiements = [
            PaiementFactory(uuid_proposition='uuid-MASTER-SCI-CONFIRMED', statut=PaymentStatus.CANCELED.name),
            PaiementFactory(uuid_proposition='uuid-MASTER-SCI', statut=PaymentStatus.OPEN.name),
        ]
