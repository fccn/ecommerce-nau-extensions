from oscar.core.loading import get_model
from oscar.apps.address.forms import AbstractAddressForm

UserAddress = get_model('address', 'useraddress')

class UserAddressForm(AbstractAddressForm):

    class Meta:
        model = UserAddress
        fields = [
            'title', 'first_name', 'last_name',
            'line1', 'line2', 'line3', 'line4',
            'state', 'postcode', 'country',
        ]

    def __init__(self, user, is_default_for_billing, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance.user = user
        self.instance.is_default_for_billing = is_default_for_billing
