from __future__ import annotations
import io
from dataclasses import dataclass, field
import pandas as pd


def _get_models():
    from ..models import Test, Question, QuestionOption, QuestionType, DifficultyLevel
    return Test, Question, QuestionOption, QuestionType, DifficultyLevel


SHEET_NAME = 'questions'
REQUIRED_COLUMNS = {'test_title', 'question_text', 'type', 'difficulty'}
ALL_COLUMNS = [
    'test_title', 'question_text', 'type', 'language',
    'option_1', 'option_2', 'option_3', 'option_4',
    'correct', 'difficulty',
]
VALID_TYPES = {'single_choice', 'multiple_choice', 'text', 'code'}
VALID_DIFFICULTIES = {'easy', 'medium', 'hard'}
VALID_LANGUAGES = {'python', 'javascript', ''}

TEMPLATE_ROWS = [
    {'test_title': 'Python Basics', 'question_text': 'What does len() do?', 'type': 'single_choice', 'language': '', 'option_1': 'Returns length', 'option_2': 'Returns type', 'option_3': 'Returns value', 'option_4': '', 'correct': '1', 'difficulty': 'easy'},
    {'test_title': 'Python Basics', 'question_text': 'Which are mutable types?', 'type': 'multiple_choice', 'language': '', 'option_1': 'list', 'option_2': 'tuple', 'option_3': 'dict', 'option_4': 'str', 'correct': '1,3', 'difficulty': 'medium'},
    {'test_title': 'Python Basics', 'question_text': 'Write a function that returns sum of two numbers.', 'type': 'code', 'language': 'python', 'option_1': '', 'option_2': '', 'option_3': '', 'option_4': '', 'correct': '', 'difficulty': 'hard'},
    {'test_title': 'Python Basics', 'question_text': 'Explain what a decorator is.', 'type': 'text', 'language': '', 'option_1': '', 'option_2': '', 'option_3': '', 'option_4': '', 'correct': '', 'difficulty': 'medium'},
]


@dataclass
class RowError:
    row: int
    column: str
    message: str
    def __str__(self):
        return f'Row {self.row}, "{self.column}": {self.message}'


@dataclass
class ParsedQuestion:
    test_title: str
    question_text: str
    question_type: str
    language: str
    difficulty: str
    options: list
    correct_indices: list
    row_number: int


@dataclass
class ImportPreview:
    rows: list = field(default_factory=list)
    errors: list = field(default_factory=list)

    @property
    def is_valid(self):
        return len(self.errors) == 0

    @property
    def test_titles(self):
        return sorted({r.test_title for r in self.rows})


def generate_template() -> bytes:
    df = pd.DataFrame(TEMPLATE_ROWS, columns=ALL_COLUMNS)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name=SHEET_NAME)
        ws = writer.sheets[SHEET_NAME]
        from openpyxl.styles import Font, PatternFill, Alignment
        for cell in ws[1]:
            cell.fill = PatternFill('solid', fgColor='1F4E79')
            cell.font = Font(bold=True, color='FFFFFF')
            cell.alignment = Alignment(horizontal='center')
        for col in ws.columns:
            ws.column_dimensions[col[0].column_letter].width = min(
                max(len(str(c.value or '')) for c in col) + 4, 40
            )
    output.seek(0)
    return output.read()


def parse_excel(file_bytes: bytes) -> ImportPreview:
    preview = ImportPreview()
    try:
        df = pd.read_excel(io.BytesIO(file_bytes), sheet_name=SHEET_NAME, dtype=str, keep_default_na=False)
    except Exception as exc:
        preview.errors.append(RowError(0, 'file', f'Cannot read file: {exc}'))
        return preview

    missing = REQUIRED_COLUMNS - set(df.columns.str.strip().str.lower())
    if missing:
        preview.errors.append(RowError(0, 'columns', f'Missing columns: {", ".join(sorted(missing))}'))
        return preview

    df.columns = df.columns.str.strip().str.lower()
    for col in ALL_COLUMNS:
        if col not in df.columns:
            df[col] = ''

    for idx, row in df.iterrows():
        _validate_row(row, idx + 2, preview)
    return preview


def _validate_row(row, excel_row, preview):
    errors_before = len(preview.errors)

    def err(col, msg):
        preview.errors.append(RowError(excel_row, col, msg))

    test_title    = str(row.get('test_title', '')).strip()
    question_text = str(row.get('question_text', '')).strip()
    q_type        = str(row.get('type', '')).strip().lower()
    difficulty    = str(row.get('difficulty', '')).strip().lower()
    language      = str(row.get('language', '')).strip().lower()
    correct_raw   = str(row.get('correct', '')).strip()

    if not test_title:     err('test_title', 'Cannot be empty.')
    if not question_text:  err('question_text', 'Cannot be empty.')
    if q_type not in VALID_TYPES:
        err('type', f'Must be one of: {", ".join(VALID_TYPES)}. Got: "{q_type}".')
        return
    if difficulty not in VALID_DIFFICULTIES:
        err('difficulty', f'Must be one of: easy/medium/hard. Got: "{difficulty}".')
    if language not in VALID_LANGUAGES:
        err('language', f'Must be: python, javascript, or empty. Got: "{language}".')
    if q_type == 'code' and not language:
        err('language', 'Code questions must specify a language.')
    if q_type != 'code' and language:
        err('language', 'Language is only for code questions.')

    options = [str(row.get(f'option_{i}', '')).strip() for i in range(1, 5)]
    non_empty = [o for o in options if o]

    if q_type in ('single_choice', 'multiple_choice') and len(non_empty) < 2:
        err('option_1', 'Choice questions need at least 2 options.')

    correct_indices = []
    if q_type == 'single_choice':
        if not correct_raw:
            err('correct', 'single_choice requires correct answer (1-4).')
        else:
            try:
                i = int(correct_raw) - 1
                if not (0 <= i <= 3): raise ValueError
                correct_indices = [i]
            except ValueError:
                err('correct', f'Must be 1-4. Got: "{correct_raw}".')
    elif q_type == 'multiple_choice':
        if not correct_raw:
            err('correct', 'multiple_choice requires answers e.g. "1,3".')
        else:
            try:
                for p in correct_raw.split(','):
                    i = int(p.strip()) - 1
                    if not (0 <= i <= 3): raise ValueError(f'Index {i+1} out of range.')
                    correct_indices.append(i)
            except ValueError as e:
                err('correct', f'Must be "1,3" style. {e}')

    if len(preview.errors) == errors_before:
        preview.rows.append(ParsedQuestion(
            test_title=test_title, question_text=question_text,
            question_type=q_type, language=language, difficulty=difficulty,
            options=non_empty, correct_indices=correct_indices, row_number=excel_row,
        ))


@dataclass
class ImportResult:
    tests_created: int = 0
    questions_created: int = 0
    options_created: int = 0
    errors: list = field(default_factory=list)

    @property
    def success(self):
        return not self.errors


def commit_import(preview: ImportPreview) -> ImportResult:
    from django.db import transaction
    result = ImportResult()
    Test, Question, QuestionOption, QuestionType, DifficultyLevel = _get_models()

    try:
        with transaction.atomic():
            test_cache = {}
            for pq in preview.rows:
                if pq.test_title not in test_cache:
                    test, created = Test.objects.get_or_create(
                        title=pq.test_title,
                        defaults={'level': pq.difficulty},
                    )
                    if created:
                        result.tests_created += 1
                    test_cache[pq.test_title] = test

                question = Question.objects.create(
                    test=test_cache[pq.test_title],
                    text=pq.question_text,
                    question_type=pq.question_type,
                    language=pq.language,
                    difficulty=pq.difficulty,
                )
                result.questions_created += 1

                for order, text in enumerate(pq.options, start=1):
                    QuestionOption.objects.create(
                        question=question, text=text,
                        is_correct=(order - 1) in pq.correct_indices, order=order,
                    )
                    result.options_created += 1
    except Exception as exc:
        result.errors.append(str(exc))
    return result


def export_questions_to_excel(test_ids=None) -> bytes:
    Test, Question, QuestionOption, QuestionType, DifficultyLevel = _get_models()
    qs = Question.objects.select_related('test').prefetch_related('options')
    if test_ids:
        qs = qs.filter(test_id__in=test_ids)

    rows = []
    for q in qs:
        opts = list(q.options.order_by('order'))
        correct_nums = [str(i + 1) for i, o in enumerate(opts) if o.is_correct]
        rows.append({
            'test_title': q.test.title, 'question_text': q.text,
            'type': q.question_type, 'language': q.language,
            'option_1': opts[0].text if len(opts) > 0 else '',
            'option_2': opts[1].text if len(opts) > 1 else '',
            'option_3': opts[2].text if len(opts) > 2 else '',
            'option_4': opts[3].text if len(opts) > 3 else '',
            'correct': ','.join(correct_nums), 'difficulty': q.difficulty,
        })

    df = pd.DataFrame(rows, columns=ALL_COLUMNS) if rows else pd.DataFrame(columns=ALL_COLUMNS)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name=SHEET_NAME)
    output.seek(0)
    return output.read()