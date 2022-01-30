import json
import random
from django.views.generic.base import TemplateView
from matomo.django import MatomoMixin


class HomePageView(MatomoMixin, TemplateView):

    template_name = "home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        current_value = self.matomo.get_attribution_info()
        context["current"] = current_value

        rand_int = random.randint(10000, 99999)
        future_value = ["", "", rand_int, ""]

        json_info = json.dumps(future_value)
        self.matomo.set_attribution_info(json_info)

        context["future"] = future_value

        self.matomo.do_track_page_view("Matomo Cookie Test Page")

        return context
