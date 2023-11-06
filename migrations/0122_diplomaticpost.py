# Generated by Django 3.2.21 on 2023-10-06 11:04

import django.db.models.deletion
from django.db import migrations, models


def add_diplomatic_post_countries(diplomatic_post, all_countries, countries):
    countries_to_add = []

    for country in countries:
        if country in all_countries:
            countries_to_add.append(all_countries[country])

    if countries_to_add:
        diplomatic_post.countries.add(*countries_to_add)


def populate_diplomatic_post(apps, schema_editor):
    Countries = apps.get_model('reference', 'Country')
    all_countries_by_iso_code = {c.iso_code: c for c in Countries.objects.all()}

    DiplomaticPost = apps.get_model('admission', 'DiplomaticPost')
    diplomatic_post = DiplomaticPost.objects.create(
        code=1,
        name_fr='Islamabad',
        name_en='Islamabad',
        email='islamabad.visa@diplobel.fed.be',
    )
    add_diplomatic_post_countries(
        diplomatic_post=diplomatic_post,
        all_countries=all_countries_by_iso_code,
        countries=['AF', 'PK'],
    )
    diplomatic_post = DiplomaticPost.objects.create(
        code=2,
        name_fr='Alger',
        name_en='Algiers',
        email='algiers.visa@diplobel.fed.be',
    )
    add_diplomatic_post_countries(
        diplomatic_post=diplomatic_post,
        all_countries=all_countries_by_iso_code,
        countries=['DZ'],
    )
    diplomatic_post = DiplomaticPost.objects.create(
        code=3,
        name_fr='Berlin',
        name_en='Berlin',
        email='Berlin@diplobel.fed.be',
    )
    add_diplomatic_post_countries(
        diplomatic_post=diplomatic_post,
        all_countries=all_countries_by_iso_code,
        countries=['DE'],
    )
    diplomatic_post = DiplomaticPost.objects.create(
        code=4,
        name_fr='Luanda',
        name_en='Luanda',
        email='luanda.visa@diplobel.fed.be',
    )
    add_diplomatic_post_countries(
        diplomatic_post=diplomatic_post,
        all_countries=all_countries_by_iso_code,
        countries=['AO', 'ST'],
    )
    diplomatic_post = DiplomaticPost.objects.create(
        code=5,
        name_fr='Kingston',
        name_en='Kingston',
        email='Kingston@diplobel.fed.be',
    )
    add_diplomatic_post_countries(
        diplomatic_post=diplomatic_post,
        all_countries=all_countries_by_iso_code,
        countries=['AG', 'BB', 'DM', 'GD', 'GY', 'JM', 'LC', 'SR', 'TT', 'VC'],
    )
    diplomatic_post = DiplomaticPost.objects.create(
        code=6,
        name_fr='Moscou',
        name_en='Moscow',
        email='Moscow@diplobel.fed.be',
    )
    add_diplomatic_post_countries(
        diplomatic_post=diplomatic_post,
        all_countries=all_countries_by_iso_code,
        countries=['AM', 'BY', 'RU', 'UZ'],
    )
    diplomatic_post = DiplomaticPost.objects.create(
        code=7,
        name_fr='Cotonou',
        name_en='Cotonou',
        email='Cotonou@diplobel.fed.be',
    )
    add_diplomatic_post_countries(
        diplomatic_post=diplomatic_post,
        all_countries=all_countries_by_iso_code,
        countries=['BJ', 'TG'],
    )
    diplomatic_post = DiplomaticPost.objects.create(
        code=8,
        name_fr='Hamilton',
        name_en='Hamilton',
        email='Philippe.dutranoit@xlgroup.com',
    )
    add_diplomatic_post_countries(
        diplomatic_post=diplomatic_post,
        all_countries=all_countries_by_iso_code,
        countries=['BM'],
    )
    diplomatic_post = DiplomaticPost.objects.create(
        code=9,
        name_fr='Brasilia',
        name_en='Brasilia',
        email='brasilia@diplobel.fed.be',
    )
    add_diplomatic_post_countries(
        diplomatic_post=diplomatic_post,
        all_countries=all_countries_by_iso_code,
        countries=['BR'],
    )
    diplomatic_post = DiplomaticPost.objects.create(
        code=10,
        name_fr='Rio de Janeiro',
        name_en='Rio de Janeiro',
        email='riodejaneiro@diplobel.fed.be',
    )
    add_diplomatic_post_countries(
        diplomatic_post=diplomatic_post,
        all_countries=all_countries_by_iso_code,
        countries=['BR'],
    )
    diplomatic_post = DiplomaticPost.objects.create(
        code=11,
        name_fr='São Paulo',
        name_en='São Paulo',
        email='saopaulo@diplobel.fed.be',
    )
    add_diplomatic_post_countries(
        diplomatic_post=diplomatic_post,
        all_countries=all_countries_by_iso_code,
        countries=['BR'],
    )
    diplomatic_post = DiplomaticPost.objects.create(
        code=12,
        name_fr='Sofia',
        name_en='Sofia',
        email='Sofia@diplobel.fed.be',
    )
    add_diplomatic_post_countries(
        diplomatic_post=diplomatic_post,
        all_countries=all_countries_by_iso_code,
        countries=['AL', 'BG', 'MK', 'XK'],
    )
    diplomatic_post = DiplomaticPost.objects.create(
        code=13,
        name_fr='Ouagadougou',
        name_en='Ouagadougou',
        email='ouagadougou@diplobel.fed.be',
    )
    add_diplomatic_post_countries(
        diplomatic_post=diplomatic_post,
        all_countries=all_countries_by_iso_code,
        countries=['BF'],
    )
    diplomatic_post = DiplomaticPost.objects.create(
        code=14,
        name_fr='Bujumbura',
        name_en='Bujumbura',
        email='bujumbura@diplobel.fed.be',
    )
    add_diplomatic_post_countries(
        diplomatic_post=diplomatic_post,
        all_countries=all_countries_by_iso_code,
        countries=['BI'],
    )
    diplomatic_post = DiplomaticPost.objects.create(
        code=15,
        name_fr='Ottawa',
        name_en='Ottawa',
        email='ottawa@diplobel.fed.be',
    )
    add_diplomatic_post_countries(
        diplomatic_post=diplomatic_post,
        all_countries=all_countries_by_iso_code,
        countries=['CA'],
    )
    diplomatic_post = DiplomaticPost.objects.create(
        code=16,
        name_fr='Montréal',
        name_en='Montreal',
        email='montreal.visa@diplobel.fed.be',
    )
    add_diplomatic_post_countries(
        diplomatic_post=diplomatic_post,
        all_countries=all_countries_by_iso_code,
        countries=['CA'],
    )
    diplomatic_post = DiplomaticPost.objects.create(
        code=17,
        name_fr='Santiago',
        name_en='Santiago',
        email='Santiago@diplobel.fed.be',
    )
    add_diplomatic_post_countries(
        diplomatic_post=diplomatic_post,
        all_countries=all_countries_by_iso_code,
        countries=['CL'],
    )
    diplomatic_post = DiplomaticPost.objects.create(
        code=18,
        name_fr='Pékin',
        name_en='Beijing',
        email='beijing.consular@diplobel.fed.be',
    )
    add_diplomatic_post_countries(
        diplomatic_post=diplomatic_post,
        all_countries=all_countries_by_iso_code,
        countries=['CN', 'MN'],
    )
    diplomatic_post = DiplomaticPost.objects.create(
        code=19,
        name_fr='Guangzhou',
        name_en='Guangzhou',
        email='guangzhou@diplobel.fed.be',
    )
    add_diplomatic_post_countries(
        diplomatic_post=diplomatic_post,
        all_countries=all_countries_by_iso_code,
        countries=['CN'],
    )
    diplomatic_post = DiplomaticPost.objects.create(
        code=20,
        name_fr='Hong Kong',
        name_en='Hong Kong',
        email='HongKong@diplobel.fed.be',
    )
    add_diplomatic_post_countries(
        diplomatic_post=diplomatic_post,
        all_countries=all_countries_by_iso_code,
        countries=['CN'],
    )
    diplomatic_post = DiplomaticPost.objects.create(
        code=21,
        name_fr='Shanghai',
        name_en='Shanghai',
        email='shanghai.visa@diplobel.fed.be',
    )
    add_diplomatic_post_countries(
        diplomatic_post=diplomatic_post,
        all_countries=all_countries_by_iso_code,
        countries=['CN'],
    )
    diplomatic_post = DiplomaticPost.objects.create(
        code=22,
        name_fr='Athènes',
        name_en='Athens',
        email='Athens@diplobel.fed.be',
    )
    add_diplomatic_post_countries(
        diplomatic_post=diplomatic_post,
        all_countries=all_countries_by_iso_code,
        countries=['CY', 'GR'],
    )
    diplomatic_post = DiplomaticPost.objects.create(
        code=23,
        name_fr='Kinshasa',
        name_en='Kinshasa',
        email='kinshasa@diplobel.fed.be',
    )
    add_diplomatic_post_countries(
        diplomatic_post=diplomatic_post,
        all_countries=all_countries_by_iso_code,
        countries=['CD'],
    )
    diplomatic_post = DiplomaticPost.objects.create(
        code=24,
        name_fr='Lubumbashi',
        name_en='Lubumbashi',
        email='lubumbashi.visa@diplobel.fed.be',
    )
    add_diplomatic_post_countries(
        diplomatic_post=diplomatic_post,
        all_countries=all_countries_by_iso_code,
        countries=['CD'],
    )
    diplomatic_post = DiplomaticPost.objects.create(
        code=25,
        name_fr='Brazzaville',
        name_en='Brazzaville',
        email='Brazzaville@diplobel.fed.be',
    )
    add_diplomatic_post_countries(
        diplomatic_post=diplomatic_post,
        all_countries=all_countries_by_iso_code,
        countries=['CG'],
    )
    diplomatic_post = DiplomaticPost.objects.create(
        code=26,
        name_fr='Séoul',
        name_en='Seoul',
        email='Seoul@diplobel.fed.be',
    )
    add_diplomatic_post_countries(
        diplomatic_post=diplomatic_post,
        all_countries=all_countries_by_iso_code,
        countries=['KP', 'KR'],
    )
    diplomatic_post = DiplomaticPost.objects.create(
        code=27,
        name_fr='Ville de Panama',
        name_en='Panama City',
        email='panama@diplobel.fed.be',
    )
    add_diplomatic_post_countries(
        diplomatic_post=diplomatic_post,
        all_countries=all_countries_by_iso_code,
        countries=['CR', 'GT', 'HN', 'NI', 'PA', 'SV'],
    )
    diplomatic_post = DiplomaticPost.objects.create(
        code=28,
        name_fr='Zagreb',
        name_en='Zagreb',
        email='zagreb@diplobel.fed.be',
    )
    add_diplomatic_post_countries(
        diplomatic_post=diplomatic_post,
        all_countries=all_countries_by_iso_code,
        countries=['HR'],
    )
    diplomatic_post = DiplomaticPost.objects.create(
        code=29,
        name_fr='La Havane',
        name_en='Havana',
        email='Havana@diplobel.fed.be',
    )
    add_diplomatic_post_countries(
        diplomatic_post=diplomatic_post,
        all_countries=all_countries_by_iso_code,
        countries=['CU', 'DO', 'HT'],
    )
    diplomatic_post = DiplomaticPost.objects.create(
        code=30,
        name_fr='Bogota DC',
        name_en='Bogota DC',
        email='bogota.visa@diplobel.fed.be',
    )
    add_diplomatic_post_countries(
        diplomatic_post=diplomatic_post,
        all_countries=all_countries_by_iso_code,
        countries=['CO'],
    )
    diplomatic_post = DiplomaticPost.objects.create(
        code=31,
        name_fr='Copenhague',
        name_en='Copenhagen',
        email='Copenhagen@diplobel.fed.be',
    )
    add_diplomatic_post_countries(
        diplomatic_post=diplomatic_post,
        all_countries=all_countries_by_iso_code,
        countries=['DK', 'GL'],
    )
    diplomatic_post = DiplomaticPost.objects.create(
        code=32,
        name_fr='Addis Abéba',
        name_en='Addis Ababa',
        email='AddisAbaba@diplobel.fed.be',
    )
    add_diplomatic_post_countries(
        diplomatic_post=diplomatic_post,
        all_countries=all_countries_by_iso_code,
        countries=['DJ', 'ET'],
    )
    diplomatic_post = DiplomaticPost.objects.create(
        code=33,
        name_fr='Abou Dhabi',
        name_en='Abu Dhabi',
        email='abudhabi@diplobel.fed.be',
    )
    add_diplomatic_post_countries(
        diplomatic_post=diplomatic_post,
        all_countries=all_countries_by_iso_code,
        countries=['AE'],
    )
    diplomatic_post = DiplomaticPost.objects.create(
        code=34,
        name_fr='Madrid',
        name_en='Madrid',
        email='Madrid@diplobel.fed.be',
    )
    add_diplomatic_post_countries(
        diplomatic_post=diplomatic_post,
        all_countries=all_countries_by_iso_code,
        countries=['ES'],
    )
    diplomatic_post = DiplomaticPost.objects.create(
        code=35,
        name_fr='Alicante',
        name_en='Alicante',
        email='alicante@diplobel.fed.be',
    )
    add_diplomatic_post_countries(
        diplomatic_post=diplomatic_post,
        all_countries=all_countries_by_iso_code,
        countries=['ES'],
    )
    diplomatic_post = DiplomaticPost.objects.create(
        code=36,
        name_fr='Barcelone',
        name_en='Barcelona',
        email='Barcelona@diplobel.fed.be',
    )
    add_diplomatic_post_countries(
        diplomatic_post=diplomatic_post,
        all_countries=all_countries_by_iso_code,
        countries=['ES'],
    )
    diplomatic_post = DiplomaticPost.objects.create(
        code=37,
        name_fr='Santa Cruz de Tenerife',
        name_en='Santa Cruz de Tenerife',
        email='tenerife@diplobel.fed.be',
    )
    add_diplomatic_post_countries(
        diplomatic_post=diplomatic_post,
        all_countries=all_countries_by_iso_code,
        countries=['ES'],
    )
    diplomatic_post = DiplomaticPost.objects.create(
        code=38,
        name_fr='Helsinki',
        name_en='Helsinki',
        email='Helsinki@diplobel.fed.be',
    )
    add_diplomatic_post_countries(
        diplomatic_post=diplomatic_post,
        all_countries=all_countries_by_iso_code,
        countries=['EE', 'FI'],
    )
    diplomatic_post = DiplomaticPost.objects.create(
        code=39,
        name_fr='Washington',
        name_en='Washington',
        email='Washington@diplobel.fed.be',
    )
    add_diplomatic_post_countries(
        diplomatic_post=diplomatic_post,
        all_countries=all_countries_by_iso_code,
        countries=['BS', 'PR', 'TC', 'US'],
    )
    diplomatic_post = DiplomaticPost.objects.create(
        code=40,
        name_fr='Atlanta',
        name_en='Atlanta',
        email='Atlanta@diplobel.fed.be',
    )
    add_diplomatic_post_countries(
        diplomatic_post=diplomatic_post,
        all_countries=all_countries_by_iso_code,
        countries=['US'],
    )
    diplomatic_post = DiplomaticPost.objects.create(
        code=41,
        name_fr='Los Angeles',
        name_en='Los Angeles',
        email='LosAngeles@diplobel.fed.be',
    )
    add_diplomatic_post_countries(
        diplomatic_post=diplomatic_post,
        all_countries=all_countries_by_iso_code,
        countries=['US'],
    )
    diplomatic_post = DiplomaticPost.objects.create(
        code=42,
        name_fr='New York',
        name_en='New York',
        email='NewYork@diplobel.fed.be',
    )
    add_diplomatic_post_countries(
        diplomatic_post=diplomatic_post,
        all_countries=all_countries_by_iso_code,
        countries=['US'],
    )
    diplomatic_post = DiplomaticPost.objects.create(
        code=43,
        name_fr='Canberra',
        name_en='Canberra',
        email='Canberra@diplobel.fed.be',
    )
    add_diplomatic_post_countries(
        diplomatic_post=diplomatic_post,
        all_countries=all_countries_by_iso_code,
        countries=['AU', 'FJ', 'KI', 'NC', 'NZ', 'PF', 'PG', 'SB', 'TO', 'TV', 'VU', 'WF', 'WS'],
    )
    diplomatic_post = DiplomaticPost.objects.create(
        code=44,
        name_fr='Marseille',
        name_en='Marseille',
        email='marseille@diplobel.fed.be',
    )
    add_diplomatic_post_countries(
        diplomatic_post=diplomatic_post,
        all_countries=all_countries_by_iso_code,
        countries=['FR'],
    )
    diplomatic_post = DiplomaticPost.objects.create(
        code=45,
        name_fr='Strasbourg',
        name_en='Strasbourg',
        email='strasbourgPR@diplobel.fed.be',
    )
    add_diplomatic_post_countries(
        diplomatic_post=diplomatic_post,
        all_countries=all_countries_by_iso_code,
        countries=['FR'],
    )
    diplomatic_post = DiplomaticPost.objects.create(
        code=46,
        name_fr='Yaoundé',
        name_en='Yaoundé',
        email='yaounde.visa@diplobel.fed.be',
    )
    add_diplomatic_post_countries(
        diplomatic_post=diplomatic_post,
        all_countries=all_countries_by_iso_code,
        countries=['CF', 'CM', 'GA', 'GQ'],
    )
    diplomatic_post = DiplomaticPost.objects.create(
        code=47,
        name_fr='Baku',
        name_en='Baku',
        email='embassy.baku@diplobel.fed.be',
    )
    add_diplomatic_post_countries(
        diplomatic_post=diplomatic_post,
        all_countries=all_countries_by_iso_code,
        countries=['AZ', 'GE', 'TM'],
    )
    diplomatic_post = DiplomaticPost.objects.create(
        code=48,
        name_fr='Abidjan',
        name_en='Abidjan',
        email='abidjan.visa@diplobel.fed.be',
    )
    add_diplomatic_post_countries(
        diplomatic_post=diplomatic_post,
        all_countries=all_countries_by_iso_code,
        countries=['CI', 'GH', 'LR', 'SL'],
    )
    diplomatic_post = DiplomaticPost.objects.create(
        code=49,
        name_fr='Conakry',
        name_en='Conakry',
        email='Conakry@diplobel.fed.be',
    )
    add_diplomatic_post_countries(
        diplomatic_post=diplomatic_post,
        all_countries=all_countries_by_iso_code,
        countries=['GN'],
    )
    diplomatic_post = DiplomaticPost.objects.create(
        code=50,
        name_fr='Budapest',
        name_en='Budapest',
        email='Budapest@diplobel.fed.be',
    )
    add_diplomatic_post_countries(
        diplomatic_post=diplomatic_post,
        all_countries=all_countries_by_iso_code,
        countries=['HU'],
    )
    diplomatic_post = DiplomaticPost.objects.create(
        code=51,
        name_fr='New Delhi',
        name_en='New Delhi',
        email='newdelhi@diplobel.fed.be',
    )
    add_diplomatic_post_countries(
        diplomatic_post=diplomatic_post,
        all_countries=all_countries_by_iso_code,
        countries=['BD', 'BT', 'IN', 'LK', 'MV', 'NP'],
    )
    diplomatic_post = DiplomaticPost.objects.create(
        code=52,
        name_fr='Mumbai',
        name_en='Mumbai',
        email='Mumbai@diplobel.fed.be',
    )
    add_diplomatic_post_countries(
        diplomatic_post=diplomatic_post,
        all_countries=all_countries_by_iso_code,
        countries=['IN'],
    )
    diplomatic_post = DiplomaticPost.objects.create(
        code=53,
        name_fr='Téhéran',
        name_en='Tehran',
        email='Tehran@diplobel.fed.be',
    )
    add_diplomatic_post_countries(
        diplomatic_post=diplomatic_post,
        all_countries=all_countries_by_iso_code,
        countries=['IR'],
    )
    diplomatic_post = DiplomaticPost.objects.create(
        code=54,
        name_fr='Dublin',
        name_en='Dublin',
        email='Dublin@diplobel.fed.be',
    )
    add_diplomatic_post_countries(
        diplomatic_post=diplomatic_post,
        all_countries=all_countries_by_iso_code,
        countries=['IE'],
    )
    diplomatic_post = DiplomaticPost.objects.create(
        code=55,
        name_fr='Oslo',
        name_en='Oslo',
        email='Oslo@diplobel.fed.be',
    )
    add_diplomatic_post_countries(
        diplomatic_post=diplomatic_post,
        all_countries=all_countries_by_iso_code,
        countries=['IS', 'NO'],
    )
    diplomatic_post = DiplomaticPost.objects.create(
        code=56,
        name_fr='Tel-Aviv',
        name_en='Tel Aviv',
        email='consulate.telaviv@diplobel.fed.be',
    )
    add_diplomatic_post_countries(
        diplomatic_post=diplomatic_post,
        all_countries=all_countries_by_iso_code,
        countries=['IL'],
    )
    diplomatic_post = DiplomaticPost.objects.create(
        code=57,
        name_fr='Tokyo',
        name_en='Tokyo',
        email='Tokyo.consular@diplobel.fed.be',
    )
    add_diplomatic_post_countries(
        diplomatic_post=diplomatic_post,
        all_countries=all_countries_by_iso_code,
        countries=['JP'],
    )
    diplomatic_post = DiplomaticPost.objects.create(
        code=58,
        name_fr='Saint Helier',
        name_en='Saint Helier',
        email='alan.binnington@rbc.com',
    )
    add_diplomatic_post_countries(
        diplomatic_post=diplomatic_post,
        all_countries=all_countries_by_iso_code,
        countries=['JE'],
    )
    diplomatic_post = DiplomaticPost.objects.create(
        code=59,
        name_fr='Jérusalem',
        name_en='Jerusalem',
        email='Jerusalem@diplobel.fed.be',
    )
    add_diplomatic_post_countries(
        diplomatic_post=diplomatic_post,
        all_countries=all_countries_by_iso_code,
        countries=['IL', 'PS'],
    )
    diplomatic_post = DiplomaticPost.objects.create(
        code=60,
        name_fr='Amman',
        name_en='Amman',
        email='amman@diplobel.fed.be',
    )
    add_diplomatic_post_countries(
        diplomatic_post=diplomatic_post,
        all_countries=all_countries_by_iso_code,
        countries=['IQ', 'JO'],
    )
    diplomatic_post = DiplomaticPost.objects.create(
        code=61,
        name_fr='Nairobi',
        name_en='Nairobi',
        email='Nairobi@diplobel.fed.be',
    )
    add_diplomatic_post_countries(
        diplomatic_post=diplomatic_post,
        all_countries=all_countries_by_iso_code,
        countries=['ER', 'KE', 'KM', 'MG', 'SC', 'SO'],
    )
    diplomatic_post = DiplomaticPost.objects.create(
        code=62,
        name_fr='Astana',
        name_en='Astana',
        email='nur-sultan@diplobel.fed.be',
    )
    add_diplomatic_post_countries(
        diplomatic_post=diplomatic_post,
        all_countries=all_countries_by_iso_code,
        countries=['KG', 'KZ', 'TJ'],
    )
    diplomatic_post = DiplomaticPost.objects.create(
        code=63,
        name_fr='Koweit',
        name_en='Kuwait City',
        email='kuwait@diplobel.fed.be',
    )
    add_diplomatic_post_countries(
        diplomatic_post=diplomatic_post,
        all_countries=all_countries_by_iso_code,
        countries=['BH', 'KW'],
    )
    diplomatic_post = DiplomaticPost.objects.create(
        code=64,
        name_fr='Bangkok',
        name_en='Bangkok',
        email='bangkok.visa@diplobel.fed.be',
    )
    add_diplomatic_post_countries(
        diplomatic_post=diplomatic_post,
        all_countries=all_countries_by_iso_code,
        countries=['KH', 'LA', 'MM', 'TH'],
    )
    diplomatic_post = DiplomaticPost.objects.create(
        code=65,
        name_fr='Prétoria',
        name_en='Pretoria',
        email='pretoria.visa@diplobel.fed.be',
    )
    add_diplomatic_post_countries(
        diplomatic_post=diplomatic_post,
        all_countries=all_countries_by_iso_code,
        countries=['BW', 'LS', 'MZ', 'NA', 'ZA', 'ZW'],
    )
    diplomatic_post = DiplomaticPost.objects.create(
        code=66,
        name_fr='Stockholm',
        name_en='Stockholm',
        email='stockholm@diplobel.fed.be',
    )
    add_diplomatic_post_countries(
        diplomatic_post=diplomatic_post,
        all_countries=all_countries_by_iso_code,
        countries=['LV', 'SE'],
    )
    diplomatic_post = DiplomaticPost.objects.create(
        code=67,
        name_fr='Beyrouth',
        name_en='Beirut',
        email='beirut.visa@diplobel.fed.be',
    )
    add_diplomatic_post_countries(
        diplomatic_post=diplomatic_post,
        all_countries=all_countries_by_iso_code,
        countries=['LB'],
    )
    diplomatic_post = DiplomaticPost.objects.create(
        code=68,
        name_fr='Tunis',
        name_en='Tunis',
        email='Tunis@diplobel.fed.be',
    )
    add_diplomatic_post_countries(
        diplomatic_post=diplomatic_post,
        all_countries=all_countries_by_iso_code,
        countries=['LY', 'TN'],
    )
    diplomatic_post = DiplomaticPost.objects.create(
        code=69,
        name_fr='Luxembourg',
        name_en='Luxembourg',
        email='Luxembourg@diplobel.fed.be',
    )
    add_diplomatic_post_countries(
        diplomatic_post=diplomatic_post,
        all_countries=all_countries_by_iso_code,
        countries=['LU'],
    )
    diplomatic_post = DiplomaticPost.objects.create(
        code=70,
        name_fr='Kuala Lumpur',
        name_en='Kuala Lumpur',
        email='kualalumpur@diplobel.fed.be',
    )
    add_diplomatic_post_countries(
        diplomatic_post=diplomatic_post,
        all_countries=all_countries_by_iso_code,
        countries=['BN', 'MY'],
    )
    diplomatic_post = DiplomaticPost.objects.create(
        code=71,
        name_fr='Bamako',
        name_en='Bamako',
        email='bamako@diplobel.fed.be',
    )
    add_diplomatic_post_countries(
        diplomatic_post=diplomatic_post,
        all_countries=all_countries_by_iso_code,
        countries=['ML'],
    )
    diplomatic_post = DiplomaticPost.objects.create(
        code=72,
        name_fr='Rome',
        name_en='Rome',
        email='Rome@diplobel.fed.be',
    )
    add_diplomatic_post_countries(
        diplomatic_post=diplomatic_post,
        all_countries=all_countries_by_iso_code,
        countries=['IT', 'MT', 'SM'],
    )
    diplomatic_post = DiplomaticPost.objects.create(
        code=73,
        name_fr='Rabat',
        name_en='Rabat',
        email='rabat@diplobel.fed.be',
    )
    add_diplomatic_post_countries(
        diplomatic_post=diplomatic_post,
        all_countries=all_countries_by_iso_code,
        countries=['MA', 'MR'],
    )
    diplomatic_post = DiplomaticPost.objects.create(
        code=74,
        name_fr='Manille',
        name_en='Manila',
        email='Manila@diplobel.fed.be',
    )
    add_diplomatic_post_countries(
        diplomatic_post=diplomatic_post,
        all_countries=all_countries_by_iso_code,
        countries=['FM', 'MH', 'PH', 'PW'],
    )
    diplomatic_post = DiplomaticPost.objects.create(
        code=75,
        name_fr='Paris',
        name_en='Paris',
        email='paris@diplobel.fed.be',
    )
    add_diplomatic_post_countries(
        diplomatic_post=diplomatic_post,
        all_countries=all_countries_by_iso_code,
        countries=['FR', 'GF', 'GP', 'MC', 'MF', 'MQ', 'RE', 'YT'],
    )
    diplomatic_post = DiplomaticPost.objects.create(
        code=76,
        name_fr='Mexico',
        name_en='Mexico City',
        email='Mexico@diplobel.fed.be',
    )
    add_diplomatic_post_countries(
        diplomatic_post=diplomatic_post,
        all_countries=all_countries_by_iso_code,
        countries=['BZ', 'MX'],
    )
    diplomatic_post = DiplomaticPost.objects.create(
        code=77,
        name_fr='Niamey',
        name_en='Niamey',
        email='Niamey@diplobel.fed.be',
    )
    add_diplomatic_post_countries(
        diplomatic_post=diplomatic_post,
        all_countries=all_countries_by_iso_code,
        countries=['NE', 'TD'],
    )
    diplomatic_post = DiplomaticPost.objects.create(
        code=78,
        name_fr='Abuja',
        name_en='Abuja',
        email='Abuja.legalisation@diplobel.fed.be',
    )
    add_diplomatic_post_countries(
        diplomatic_post=diplomatic_post,
        all_countries=all_countries_by_iso_code,
        countries=['NG'],
    )
    diplomatic_post = DiplomaticPost.objects.create(
        code=79,
        name_fr='Riyadh',
        name_en='Riyadh',
        email='Riyadh@diplobel.fed.be',
    )
    add_diplomatic_post_countries(
        diplomatic_post=diplomatic_post,
        all_countries=all_countries_by_iso_code,
        countries=['OM', 'SA', 'YD'],
    )
    diplomatic_post = DiplomaticPost.objects.create(
        code=80,
        name_fr='Buenos Aires',
        name_en='Buenos Aires',
        email='BuenosAires@diplobel.fed.be',
    )
    add_diplomatic_post_countries(
        diplomatic_post=diplomatic_post,
        all_countries=all_countries_by_iso_code,
        countries=['AR', 'PY', 'UY'],
    )
    diplomatic_post = DiplomaticPost.objects.create(
        code=81,
        name_fr='La Haye',
        name_en='The Hague',
        email='TheHague@diplobel.fed.be',
    )
    add_diplomatic_post_countries(
        diplomatic_post=diplomatic_post,
        all_countries=all_countries_by_iso_code,
        countries=['NL'],
    )
    diplomatic_post = DiplomaticPost.objects.create(
        code=82,
        name_fr='Lima',
        name_en='Lima',
        email='lima@diplobel.fed.be',
    )
    add_diplomatic_post_countries(
        diplomatic_post=diplomatic_post,
        all_countries=all_countries_by_iso_code,
        countries=['BO', 'EC', 'PE'],
    )
    diplomatic_post = DiplomaticPost.objects.create(
        code=83,
        name_fr='Varsovie',
        name_en='Warsaw',
        email='Warsaw@diplobel.fed.be',
    )
    add_diplomatic_post_countries(
        diplomatic_post=diplomatic_post,
        all_countries=all_countries_by_iso_code,
        countries=['LT', 'PL'],
    )
    diplomatic_post = DiplomaticPost.objects.create(
        code=84,
        name_fr='Lisbonne',
        name_en='Lisbon',
        email='Lisbon@diplobel.fed.be',
    )
    add_diplomatic_post_countries(
        diplomatic_post=diplomatic_post,
        all_countries=all_countries_by_iso_code,
        countries=['PT'],
    )
    diplomatic_post = DiplomaticPost.objects.create(
        code=85,
        name_fr='Doha',
        name_en='Doha',
        email='doha.visa@diplobel.fed.be',
    )
    add_diplomatic_post_countries(
        diplomatic_post=diplomatic_post,
        all_countries=all_countries_by_iso_code,
        countries=['QA'],
    )
    diplomatic_post = DiplomaticPost.objects.create(
        code=86,
        name_fr='Bucarest',
        name_en='Bucharest',
        email='bucharest@diplobel.fed.be',
    )
    add_diplomatic_post_countries(
        diplomatic_post=diplomatic_post,
        all_countries=all_countries_by_iso_code,
        countries=['MD', 'RO'],
    )
    diplomatic_post = DiplomaticPost.objects.create(
        code=87,
        name_fr='Londres',
        name_en='London',
        email='London@diplobel.fed.be',
    )
    add_diplomatic_post_countries(
        diplomatic_post=diplomatic_post,
        all_countries=all_countries_by_iso_code,
        countries=['GB'],
    )
    diplomatic_post = DiplomaticPost.objects.create(
        code=88,
        name_fr='Kigali',
        name_en='Kigali',
        email='Kigali.Visa@diplobel.fed.be',
    )
    add_diplomatic_post_countries(
        diplomatic_post=diplomatic_post,
        all_countries=all_countries_by_iso_code,
        countries=['RW'],
    )
    diplomatic_post = DiplomaticPost.objects.create(
        code=89,
        name_fr='Bogota',
        name_en='Bogota',
        email='bogota.visa@diplobel.fed.be',
    )
    add_diplomatic_post_countries(
        diplomatic_post=diplomatic_post,
        all_countries=all_countries_by_iso_code,
        countries=['AW', 'VE'],
    )
    diplomatic_post = DiplomaticPost.objects.create(
        code=90,
        name_fr='Rome Saint-Siège',
        name_en='Rome Holy See',
        email='RomeHolySee@diplobel.fed.be',
    )
    add_diplomatic_post_countries(
        diplomatic_post=diplomatic_post,
        all_countries=all_countries_by_iso_code,
        countries=['VA'],
    )
    diplomatic_post = DiplomaticPost.objects.create(
        code=91,
        name_fr='Dakar',
        name_en='Dakar',
        email='dakar@diplobel.fed.be',
    )
    add_diplomatic_post_countries(
        diplomatic_post=diplomatic_post,
        all_countries=all_countries_by_iso_code,
        countries=['CV', 'GM', 'GW', 'SN'],
    )
    diplomatic_post = DiplomaticPost.objects.create(
        code=92,
        name_fr='Belgrade',
        name_en='Belgrade',
        email='belgrade@diplobel.fed.be',
    )
    add_diplomatic_post_countries(
        diplomatic_post=diplomatic_post,
        all_countries=all_countries_by_iso_code,
        countries=['ME', 'RS'],
    )
    diplomatic_post = DiplomaticPost.objects.create(
        code=93,
        name_fr='Singapour',
        name_en='Singapore',
        email='Singapore@diplobel.fed.be',
    )
    add_diplomatic_post_countries(
        diplomatic_post=diplomatic_post,
        all_countries=all_countries_by_iso_code,
        countries=['SG'],
    )
    diplomatic_post = DiplomaticPost.objects.create(
        code=94,
        name_fr='Vienne',
        name_en='Vienna',
        email='Vienna@diplobel.fed.be',
    )
    add_diplomatic_post_countries(
        diplomatic_post=diplomatic_post,
        all_countries=all_countries_by_iso_code,
        countries=['AT', 'SI', 'SK'],
    )
    diplomatic_post = DiplomaticPost.objects.create(
        code=95,
        name_fr='Le Caire',
        name_en='Cairo',
        email='cairo.visa@diplobel.fed.be',
    )
    add_diplomatic_post_countries(
        diplomatic_post=diplomatic_post,
        all_countries=all_countries_by_iso_code,
        countries=['EG', 'SD'],
    )
    diplomatic_post = DiplomaticPost.objects.create(
        code=96,
        name_fr='Kampala',
        name_en='Kampala',
        email='Kampala@diplobel.fed.be',
    )
    add_diplomatic_post_countries(
        diplomatic_post=diplomatic_post,
        all_countries=all_countries_by_iso_code,
        countries=['SD', 'UG'],
    )
    diplomatic_post = DiplomaticPost.objects.create(
        code=97,
        name_fr='Berne',
        name_en='Berne',
        email='bern.consular@diplobel.fed.be',
    )
    add_diplomatic_post_countries(
        diplomatic_post=diplomatic_post,
        all_countries=all_countries_by_iso_code,
        countries=['CH', 'LI'],
    )
    diplomatic_post = DiplomaticPost.objects.create(
        code=98,
        name_fr='Lattaquié',
        name_en='Latakia',
        email='cobellat@atiyeh.net',
    )
    add_diplomatic_post_countries(
        diplomatic_post=diplomatic_post,
        all_countries=all_countries_by_iso_code,
        countries=['SY'],
    )
    diplomatic_post = DiplomaticPost.objects.create(
        code=99,
        name_fr='Dar-es-Salaam',
        name_en='Dar-es-Salaam',
        email='DarEsSalaam@diplobel.fed.be',
    )
    add_diplomatic_post_countries(
        diplomatic_post=diplomatic_post,
        all_countries=all_countries_by_iso_code,
        countries=['MU', 'MW', 'TZ', 'ZM'],
    )
    diplomatic_post = DiplomaticPost.objects.create(
        code=100,
        name_fr='Prague',
        name_en='Prague',
        email='Prague@diplobel.fed.be',
    )
    add_diplomatic_post_countries(
        diplomatic_post=diplomatic_post,
        all_countries=all_countries_by_iso_code,
        countries=['CZ'],
    )
    diplomatic_post = DiplomaticPost.objects.create(
        code=101,
        name_fr='Jakarta',
        name_en='Jakarta',
        email='jakarta@diplobel.fed.be',
    )
    add_diplomatic_post_countries(
        diplomatic_post=diplomatic_post,
        all_countries=all_countries_by_iso_code,
        countries=['ID', 'TL'],
    )
    diplomatic_post = DiplomaticPost.objects.create(
        code=102,
        name_fr='Ankara',
        name_en='Ankara',
        email='ankara@diplobel.fed.be',
    )
    add_diplomatic_post_countries(
        diplomatic_post=diplomatic_post,
        all_countries=all_countries_by_iso_code,
        countries=['TR'],
    )
    diplomatic_post = DiplomaticPost.objects.create(
        code=103,
        name_fr='Kyiv',
        name_en='Kyiv',
        email='kiev@diplobel.fed.be',
    )
    add_diplomatic_post_countries(
        diplomatic_post=diplomatic_post,
        all_countries=all_countries_by_iso_code,
        countries=['UA'],
    )
    diplomatic_post = DiplomaticPost.objects.create(
        code=104,
        name_fr='Hanoï',
        name_en='Hanoi',
        email='hanoi@diplobel.fed.be',
    )
    add_diplomatic_post_countries(
        diplomatic_post=diplomatic_post,
        all_countries=all_countries_by_iso_code,
        countries=['VN'],
    )


class Migration(migrations.Migration):

    dependencies = [
        ('reference', '0018_country_active'),
        ('admission', '0121_alter_onlinepayment_method'),
    ]

    operations = [
        migrations.CreateModel(
            name='DiplomaticPost',
            fields=[
                (
                    'code',
                    models.PositiveSmallIntegerField(
                        primary_key=True,
                        serialize=False,
                        verbose_name='Diplomatic post code',
                    ),
                ),
                ('name_fr', models.CharField(max_length=255, verbose_name='Name in french')),
                ('name_en', models.CharField(max_length=255, verbose_name='Name in english')),
                ('email', models.EmailField(max_length=255, verbose_name='Email')),
                (
                    'countries',
                    models.ManyToManyField(
                        related_name='_admission_diplomaticpost_countries_+',
                        to='reference.Country',
                        verbose_name='Countries',
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name='generaleducationadmission',
            name='diplomatic_post',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to='admission.diplomaticpost',
                verbose_name='Diplomatic post',
            ),
        ),
        migrations.RunPython(code=populate_diplomatic_post, reverse_code=migrations.RunPython.noop),
    ]
