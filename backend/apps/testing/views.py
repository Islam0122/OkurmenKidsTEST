from __future__ import annotations
import base64
import logging

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from .services import (
    commit_import,
    export_questions_to_excel,
    generate_template,
    parse_excel,
)

logger = logging.getLogger(__name__)

_CONTENT_TYPE_XLSX = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'


# ── Шаблон ────────────────────────────────────────────────────────────────────

@staff_member_required
def download_template(request):
    """Скачать шаблон Excel для заполнения."""
    response = HttpResponse(generate_template(), content_type=_CONTENT_TYPE_XLSX)
    response['Content-Disposition'] = 'attachment; filename="шаблон_вопросов.xlsx"'
    return response


# ── Шаг 1: Загрузка файла ─────────────────────────────────────────────────────

@staff_member_required
@require_http_methods(['GET', 'POST'])
def import_questions(request):
    """
    GET  — страница загрузки файла.
    POST — парсинг файла и редирект на preview.
    """
    ctx = {
        'title': 'Импорт вопросов из Excel',
        'has_permission': True,
        'opts': _fake_opts(),
    }

    if request.method == 'POST':
        uploaded = request.FILES.get('excel_file')

        if not uploaded:
            messages.error(request, 'Пожалуйста, выберите файл для загрузки.')
            return render(request, 'admin/testing/import_upload.html', ctx)

        if not uploaded.name.lower().endswith(('.xlsx', '.xls')):
            messages.error(request, 'Принимаются только файлы .xlsx и .xls.')
            return render(request, 'admin/testing/import_upload.html', ctx)

        if uploaded.size > 10 * 1024 * 1024:  # 10 MB
            messages.error(request, 'Файл слишком большой. Максимальный размер — 10 МБ.')
            return render(request, 'admin/testing/import_upload.html', ctx)

        file_bytes = uploaded.read()
        preview    = parse_excel(file_bytes)

        # Сохраняем файл в сессии (base64)
        request.session['import_file']     = base64.b64encode(file_bytes).decode()
        request.session['import_filename'] = uploaded.name

        ctx['preview'] = preview
        if preview.errors:
            messages.warning(
                request,
                f'Обнаружены ошибки в файле: {len(preview.errors)} шт. '
                'Исправьте файл и загрузите повторно.',
            )
        else:
            messages.info(
                request,
                f'Файл успешно прочитан. Найдено вопросов: {len(preview.rows)}. '
                'Проверьте данные перед импортом.',
            )
        return render(request, 'admin/testing/import_preview.html', ctx)

    return render(request, 'admin/testing/import_upload.html', ctx)


# ── Шаг 3: Подтверждение импорта ─────────────────────────────────────────────

@staff_member_required
@require_http_methods(['POST'])
def confirm_import(request):
    """Выполнить импорт данных из сохранённого файла в сессии."""
    encoded = request.session.pop('import_file', None)
    request.session.pop('import_filename', None)

    if not encoded:
        messages.error(request, 'Сессия истекла. Пожалуйста, загрузите файл повторно.')
        return redirect('testing-import-questions')

    try:
        file_bytes = base64.b64decode(encoded)
    except Exception:
        messages.error(request, 'Ошибка декодирования файла. Загрузите файл повторно.')
        return redirect('testing-import-questions')

    preview = parse_excel(file_bytes)

    if not preview.is_valid:
        messages.error(
            request,
            f'Импорт отменён: найдено {len(preview.errors)} ошибок валидации. '
            'Исправьте файл и загрузите повторно.',
        )
        return redirect('testing-import-questions')

    result = commit_import(preview)

    if result.success:
        parts = []
        if result.tests_created:
            parts.append(f'тестов создано: {result.tests_created}')
        if result.questions_created:
            parts.append(f'вопросов добавлено: {result.questions_created}')
        if result.questions_updated:
            parts.append(f'вопросов обновлено: {result.questions_updated}')
        if result.options_created:
            parts.append(f'вариантов ответов: {result.options_created}')

        messages.success(
            request,
            'Импорт завершён успешно! ' + (', '.join(parts) if parts else 'Данные актуальны.'),
        )
        logger.info(
            'Import completed: %d tests, %d questions created, %d updated, %d options',
            result.tests_created, result.questions_created,
            result.questions_updated, result.options_created,
        )
    else:
        for err in result.errors:
            messages.error(request, f'Ошибка при импорте: {err}')

    return redirect('admin:testing_question_changelist')


# ── Экспорт ───────────────────────────────────────────────────────────────────

@staff_member_required
def export_questions(request):
    """Экспорт вопросов в Excel. GET param: test_ids (через запятую)."""
    raw_ids  = request.GET.get('test_ids', '')
    test_ids = [t.strip() for t in raw_ids.split(',') if t.strip()] or None

    xlsx = export_questions_to_excel(test_ids)
    response = HttpResponse(xlsx, content_type=_CONTENT_TYPE_XLSX)
    suffix   = f'_{raw_ids[:30]}' if test_ids else '_все'
    response['Content-Disposition'] = (
        f'attachment; filename*=UTF-8\'\'вопросы{suffix}.xlsx'
    )
    return response


def _fake_opts():
    class _Opts:
        app_label    = 'testing'
        model_name   = 'question'
        verbose_name = 'Вопрос'
        verbose_name_plural = 'Вопросы'
    return _Opts()