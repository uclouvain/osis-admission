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

import json

import requests
from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse
from django.views import View


__all__ = [
    "RequestDigitAccountCreationView",
    "SearchDigitAccountView"
]

from django.views.generic import FormView

from admission.contrib.models.base import BaseAdmission
from base.views.common import display_error_messages

from django.utils.translation import gettext_lazy as _


class RequestDigitAccountCreationView(FormView):

    urlpatterns = {'request-account': 'request-account/<uuid:uuid>'}

    def post(self, request, *args, **kwargs):

        admission = BaseAdmission.objects.get(uuid=kwargs['uuid'])

        if self._is_valid_for_account_creation(request, admission):
            return redirect(to=reverse('admission:doctorate:coordonnees', kwargs={'uuid': kwargs['uuid']}))

        response = request_digit_account_creation({
            "last_name": admission.candidate.last_name,
            "first_name": admission.candidate.first_name,
            "birth_date": str(admission.candidate.birth_date),
            "gender": admission.candidate.gender,
            "national_register": admission.candidate.national_number,
            "nationality": admission.candidate.country_of_citizenship.iso_code,
            "registration_id": "",  # noma à déterminer
            "residence_address": admission.candidate.personaddress_set.first(),  # adresse de résidence à déterminer
        })
        return response

    @staticmethod
    def _is_valid_for_account_creation(request, admission):
        candidate_required_fields = [
            "last_name", "first_name", "birth_date", "gender", "national_number", "country_of_citizenship",
        ]
        missing_fields = [field for field in candidate_required_fields if not getattr(admission.candidate, field)]
        has_missing_fields = any(missing_fields)

        if has_missing_fields:
            display_error_messages(request, _(
                "Admission is not yet valid for UCLouvain account creation. The following fields are required: "
            ) + ", ".join(missing_fields))

        return has_missing_fields


class SearchDigitAccountView(FormView):

    urlpatterns = {'search-account': 'search-account/<uuid:uuid>'}

    def post(self, request, *args, **kwargs):

        admission = BaseAdmission.objects.get(uuid=kwargs['uuid'])

        if self._is_valid_for_search(request, admission):
            return redirect(to=reverse('admission:doctorate:person', kwargs={'uuid': kwargs['uuid']}))

        response = search_digit_account(request, admission)
        return response

    @staticmethod
    def _is_valid_for_search(request, admission):
        candidate_required_fields = [
            "last_name", "first_name", "birth_date",
        ]
        missing_fields = [field for field in candidate_required_fields if not getattr(admission.candidate, field)]
        has_missing_fields = any(missing_fields)

        if has_missing_fields:
            display_error_messages(request, _(
                "Admission is not yet valid for searching UCLouvain. The following fields are required: "
            ) + ", ".join(missing_fields))

        return has_missing_fields


def request_digit_account_creation(data):
    response = requests.post(
        headers={'Content-Type': 'application/json', 'Authorization': 'Bearer ab2dbc5b-5278-3370-98de-40df855c2265'},
        data=json.dumps({
            "provider": {
                "source": "ETU",
                "sourceId": data["registration_id"],  # noma
                "actif": True,
            },
            "person": {
                "lastName": data['last_name'],
                "firstName": data['first_name'],
                "birthDate": data['birth_date'],
                "gender": data["gender"],
                "nationalRegister": data["national_register"],
                "nationality": data["nationality"],
            },
            "addresses": [
                {
                    "addressType": "RES",
                    "country": data["residence_address"].country.iso_code,
                    "postalCode": data["residence_address"].postal_code,
                    "locality": data["residence_address"].city,
                    "street": data["residence_address"].street,
                    "number": data["residence_address"].street_number,
                    "box": data["residence_address"].postal_box,
                }
            ],
            "physicalPerson": True,
        }),
        url=settings.DIGIT_ACCOUNT_CREATION_URL,
    )
    return response


def search_digit_account(request, admission):
    mock = True

    if mock:
        matches = _mock_search_digit_account_return_response()
        request.session['search_context'] = {'matches': matches}
        return redirect(reverse('admission:services:search-account-modal', kwargs={'uuid': admission.uuid}))

    response = requests.post(
        headers={'Content-Type': 'application/json', 'Authorization': 'Bearer ab2dbc5b-5278-3370-98de-40df855c2265'},
        data=json.dumps({
            "last_name": admission.candidate.last_name,
            "first_name": admission.candidate.first_name,
            "birth_date": str(admission.candidate.birth_date),
        }),
        url=settings.DIGIT_ACCOUNT_SEARCH_URL,
    )
    return response


def _mock_search_digit_account_return_response():
    return json.loads(
            '['
            '   {'
            '        "person" : {'
            '          "matricule" : "217017" ,'
            '          "lastName" : "Bosman" ,'
            '          "firstName" : "Vincianne" ,'
            '          "birthDate" : "1975-11-27" ,'
            '          "gender" : "F" ,'
            '          "nationalRegister" : "75112730354" ,'
            '          "nationality" : "BE" ,'
            '          "deceased" : false ,'
            '          "displayLastname" : null ,'
            '          "displayFirstname" : null ,'
            '          "otherFirstName" : null ,'
            '          "placeOfBirth" : null ,'
            '          "postname" : null'
            '        } ,'
            '        "similarityRate" : 406.0 ,'
            '        "links" : {'
            '          "financialCustomer" : "/identity/applicationsAccount/financialCustomer/217017" ,'
            '          "addresses" : "/identity/addresses/find/217017"'
            '        } ,'
            '        "transition" : {'
            '          "previousFirstname" : "Vincent" ,'
            '          "previousGender" : "M" ,'
            '          "previousNationalRegister" : null'
            '        } ,'
            '        "applicationAccounts" : ['
            '          {'
            '            "source" : "ETU" ,'
            '            "sourceId" : "00000000" ,'
            '            "actif" : true'
            '          } ,'
            '          {'
            '            "source" : "ETU" ,'
            '            "sourceId" : "00000001" ,'
            '            "actif" : false'
            '          }'
            '        ]'
            '      } ,'
            '      {'
            '        "person" : {'
            '          "matricule" : "379409" ,'
            '          "lastName" : "Boesmans" ,'
            '          "firstName" : "Vincent" ,'
            '          "birthDate" : "1973-10-20" ,'
            '          "gender" : "M" ,'
            '          "nationalRegister" : "" ,'
            '          "nationality" : "BE" ,'
            '          "deceased" : false ,'
            '          "displayLastname" : null ,'
            '          "displayFirstname" : null ,'
            '          "otherFirstName" : null ,'
            '          "placeOfBirth" : null ,'
            '          "postname" : null'
            '        } ,'
            '        "similarityRate" : 380.0 ,'
            '        "links" : {'
            '          "financialCustomer" : "/identity/applicationsAccount/financialCustomer/379409" ,'
            '          "addresses" : "/identity/addresses/find/379409"'
            '        } ,'
            '        "transition" : null ,'
            '        "applicationAccounts" : []'
            '      } ,'
            '      {'
            '        "person" : {'
            '          "matricule" : "12345678" ,'
            '          "lastName" : "Bigger" ,'
            '          "firstName" : "Match" ,'
            '          "birthDate" : "1980-10-20" ,'
            '          "gender" : "M" ,'
            '          "nationalRegister" : "12345678910" ,'
            '          "nationality" : "BE" ,'
            '          "deceased" : false ,'
            '          "displayLastname" : null ,'
            '          "displayFirstname" : null ,'
            '          "otherFirstName" : null ,'
            '          "placeOfBirth" : null ,'
            '          "postname" : null'
            '        } ,'
            '        "similarityRate" : 1000.0 ,'
            '        "links" : {'
            '          "financialCustomer" : "/identity/applicationsAccount/financialCustomer/379409" ,'
            '          "addresses" : "/identity/addresses/find/379409"'
            '        } ,'
            '        "transition" : null ,'
            '        "applicationAccounts" : []'
            '      }'
            '    ]'
    )

