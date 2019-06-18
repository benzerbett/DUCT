from __future__ import unicode_literals

from django.apps import AppConfig


class IndicatorConfig(AppConfig):
    name = 'indicator'

    def ready(self):
        import indicator.signals
