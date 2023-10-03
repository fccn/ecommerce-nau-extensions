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

License
=======

This work is licensed under the terms of the `GNU Affero General Public License (AGPL) <https://github.com/fccn/ecommerce-nau-extensions/blob/master/LICENSE.txt>`_.
