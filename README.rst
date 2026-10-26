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

Exporting the orders
====================

``export_orders`` writes the orders in the ``Complete`` status to a JSON Lines file, one order per
line, with the user, amounts (including the tax and discount split), payment source, raw payment
processor payload and lines. It is the hand-over of the sales history to the LMS payments plugin
(``import_orders`` there) and the archive of that history once this service is gone::

    python manage.py export_orders --output /tmp/orders.jsonl
    python manage.py export_orders --output /tmp/orders.jsonl --site ecommerce.nau.edu.pt --with-receipt-links

``--with-receipt-links`` resolves the Financial Manager receipt link of every order, one request
per order. ``--skip-free`` leaves out the zero-value orders. Orders with a completed refund are
exported with status ``refunded``, the others with ``paid``.

Development
=============

To create migrations for this project the next command inside ecommerce container::
    python manage.py makemigrations nau_extensions

Then run the migrations::
    python manage.py migrate


Use specific Python version, use ecommerce requirements::
    pyenv shell 3.12
    python -m venv venv
    . venv/bin/activate
    pip install -r ../ecommerce/requirements.txt
    pip install -r ../ecommerce/requirements/dev.txt

Lint::
    ECOMMERCE_SOURCE_PATH=`pwd`/../ecommerce make lint


License
=======

This work is licensed under the terms of the `GNU Affero General Public License (AGPL) <https://github.com/fccn/ecommerce-nau-extensions/blob/master/LICENSE.txt>`_.
