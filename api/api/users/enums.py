from django.db import models
from django.utils.translation import gettext_lazy as _


class SetUpStatus(models.IntegerChoices):
    SIGN_UP_VALIDATION = 0, _('Sign Up Validation')
    VALIDATED = 1, _('Validated')


class PasswordStatus(models.IntegerChoices):
    CHANGE = 0, _('Requires password Change')
    ACTIVE = 1, _('ACTIVE')
    EXTERNAL = 2, _('External')


class Industry(models.TextChoices):
    AUTOMOTIVE = 'Automotive', _('Automotive')
    TECHNOLOGY = 'Technology', _('Technology')
    ENERGY = 'Energy', _('Energy')
    CHEMICAL = 'Chemical', _('Chemical')
    FOOD = 'Food', _('Food')
    PHARMACEUTICAL = 'Pharmaceutical', _('Pharmaceutical')
    TEXTILE_AND_FASHION = 'Textile and Fashion', _('Textile and Fashion')
    CONSTRUCTION = 'Construction', _('Construction')
    FINANCIAL_SERVICES = 'Financial Services', _('Financial Services')
    TOURISM_AND_HOSPITALITY = 'Tourism and Hospitality', _('Tourism and Hospitality')
    ENTERTAINMENT = 'Entertainment', _('Entertainment')
    MINING = 'Mining', _('Mining')
    TRANSPORTATION_AND_LOGISTICS = 'Transportation and Logistics', _('Transportation and Logistics')
    SHIPBUILDING = 'Shipbuilding', _('Shipbuilding')
    AGRICULTURE_AND_LIVESTOCK = 'Agriculture and Livestock', _('Agriculture and Livestock')
    HEALTHCARE_AND_BIOTECHNOLOGY = 'Healthcare and Biotechnology', _('Healthcare and Biotechnology')
    DEFENSE_AND_SECURITY = 'Defense and Security', _('Defense and Security')
    PROFESSIONAL_SERVICES = 'Professional Services', _('Professional Services')

class Country(models.TextChoices):
    from django.utils.translation import gettext_lazy as _

    class Country(models.TextChoices):
        ARGENTINA = 'Argentina', _('Argentina')
        BAHAMAS = 'Bahamas', _('Bahamas')
        BARBADOS = 'Barbados', _('Barbados')
        BELIZE = 'Belize', _('Belize')
        BOLIVIA = 'Bolivia', _('Bolivia')
        BRAZIL = 'Brazil', _('Brazil')
        CHILE = 'Chile', _('Chile')
        COLOMBIA = 'Colombia', _('Colombia')
        COSTA_RICA = 'Costa Rica', _('Costa Rica')
        CUBA = 'Cuba', _('Cuba')
        DOMINICA = 'Dominica', _('Dominica')
        ECUADOR = 'Ecuador', _('Ecuador')
        EL_SALVADOR = 'El Salvador', _('El Salvador')
        GRENADA = 'Grenada', _('Grenada')
        GUATEMALA = 'Guatemala', _('Guatemala')
        GUYANA = 'Guyana', _('Guyana')
        HAITI = 'Haiti', _('Haiti')
        HONDURAS = 'Honduras', _('Honduras')
        JAMAICA = 'Jamaica', _('Jamaica')
        MEXICO = 'Mexico', _('Mexico')
        NICARAGUA = 'Nicaragua', _('Nicaragua')
        PANAMA = 'Panama', _('Panama')
        PARAGUAY = 'Paraguay', _('Paraguay')
        PERU = 'Peru', _('Peru')
        PUERTO_RICO = 'Puerto Rico', _('Puerto Rico')
        DOMINICAN_REPUBLIC = 'Dominican Republic', _('Dominican Republic')
        SAINT_KITTS_AND_NEVIS = 'Saint Kitts and Nevis', _('Saint Kitts and Nevis')
        SAINT_LUCIA = 'Saint Lucia', _('Saint Lucia')
        SAINT_VINCENT_AND_THE_GRENADINES = 'Saint Vincent and the Grenadines', _('Saint Vincent and the Grenadines')
        SURINAME = 'Suriname', _('Suriname')
        TRINIDAD_AND_TOBAGO = 'Trinidad and Tobago', _('Trinidad and Tobago')
        URUGUAY = 'Uruguay', _('Uruguay')
        VENEZUELA = 'Venezuela', _('Venezuela')


