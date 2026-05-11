from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views import View

# You may need to adjust imports/models depending on your project structure
#from .models import MBPaymentReference

@method_decorator(login_required, name='dispatch')
class PendingPaymentsView(View):
    """
    Shows all MB payment references for the logged-in user and their statuses.
    """
    def get(self, request):
        user = request.user
        # TODO: Replace with actual query for MB references for this user
        mb_references = []  # Example: MBPaymentReference.objects.filter(user=user)
        return render(request, 'pending_payments/pending_payments.html', {
            'mb_references': mb_references,
        })
