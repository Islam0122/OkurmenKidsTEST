import json, base64, logging
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from .services import generate_template, parse_excel, commit_import, export_questions_to_excel

logger = logging.getLogger(__name__)


@staff_member_required
def download_template(request):
    response = HttpResponse(generate_template(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="questions_template.xlsx"'
    return response


@staff_member_required
@require_http_methods(['GET', 'POST'])
def import_questions(request):
    ctx = {'title': 'Import Questions from Excel', 'has_permission': True}
    if request.method == 'POST':
        f = request.FILES.get('excel_file')
        if not f:
            messages.error(request, 'Please select a file.')
            return render(request, 'admin/testing/import_upload.html', ctx)
        if not f.name.endswith(('.xlsx', '.xls')):
            messages.error(request, 'Only .xlsx / .xls accepted.')
            return render(request, 'admin/testing/import_upload.html', ctx)
        file_bytes = f.read()
        preview = parse_excel(file_bytes)
        request.session['import_file'] = base64.b64encode(file_bytes).decode()
        ctx['preview'] = preview
        return render(request, 'admin/testing/import_preview.html', ctx)
    return render(request, 'admin/testing/import_upload.html', ctx)


@staff_member_required
@require_http_methods(['POST'])
def confirm_import(request):
    encoded = request.session.pop('import_file', None)
    if not encoded:
        messages.error(request, 'Session expired. Upload again.')
        return redirect('testing:import-questions')
    preview = parse_excel(base64.b64decode(encoded))
    if not preview.is_valid:
        messages.error(request, f'{len(preview.errors)} validation errors. Import cancelled.')
        return redirect('testing:import-questions')
    result = commit_import(preview)
    if result.success:
        messages.success(request, f'Done: {result.tests_created} tests, {result.questions_created} questions, {result.options_created} options.')
    else:
        for e in result.errors:
            messages.error(request, e)
    return redirect('admin:testing_question_changelist')


@staff_member_required
def export_questions(request):
    ids = [t.strip() for t in request.GET.get('test_ids', '').split(',') if t.strip()] or None
    response = HttpResponse(export_questions_to_excel(ids), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="questions_export.xlsx"'
    return response