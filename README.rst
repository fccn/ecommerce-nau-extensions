==================================================================================
NAU extensions to the Open edX Ecommerce
==================================================================================

This is an extensions project to aim to change the Open edX 
`Ecommerce <https://edx-ecommerce.readthedocs.io/en/latest/>`__  
behavior for the NAU project.

Configuration
===============

Add the `nau_extensions` to the `INSTALLED_APPS`, for example if you are using devstack
edit the `ecommerce/settings/private.py` file add change to::
    from .production import INSTALLED_APPS
    INSTALLED_APPS += ("paygate", "nau_extensions", )

    LANGUAGE_CODE = "pt"
    from django.utils.translation import ugettext_lazy as _
    LANGUAGES = (
        ('pt-pt', _('Português')),
        ('en', _('English')),
    )
    LOGO_URL = "https://lms.nau.edu.pt/static/nau-basic/images/nau_azul.svg"

    NAU_FINANCIAL_MANAGER = {
        "edx": {
            "url": "http://financial-manager.local.nau.fccn.pt:8000/api/billing/transaction-complete/",
            "token": "Bearer abcdABCD1234",
        }
    }

Development
=============

To create migrations for this project the next command inside ecommerce container::
    python manage.py makemigrations nau_extensions

Then run the migrations::
    python manage.py migrate

License
=======

This work is licensed under the terms of the `GNU Affero General Public License (AGPL) <https://github.com/fccn/ecommerce-nau-extensions/blob/master/LICENSE.txt>`_.
