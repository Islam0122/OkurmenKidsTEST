from django.urls import path
from . import views

app_name = 'testing'

urlpatterns = [
    path('import/',         views.import_questions,  name='import-questions'),
    path('import/confirm/', views.confirm_import,    name='confirm-import'),
    path('export/',         views.export_questions,  name='export-questions'),
    path('template/',       views.download_template, name='download-template'),
]