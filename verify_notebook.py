from pathlib import Path
import json
import nbformat

root = Path(__file__).resolve().parent
nb_path = root / 'notebooks' / 'task_03_ai_pricing.ipynb'
nb = nbformat.read(nb_path, as_version=4)
errors = []
for i, cell in enumerate(nb.cells):
    for output in cell.get('outputs', []):
        if output.output_type == 'error':
            errors.append((i, output.ename, output.evalue))
if errors:
    raise SystemExit(f'Notebook errors: {errors}')
required = ['ARPU', 'LTV', 'LTV/CAC', 'NPV', 'Чувствительность', 'Подписка', 'Вопрос 10']
source = '\n'.join(cell.source for cell in nb.cells)
missing = [item for item in required if item not in source]
if missing:
    raise SystemExit(f'Missing sections: {missing}')
figures = list((root / 'reports' / 'figures').glob('task_03_*.png'))
if len(figures) < 3 or any(path.stat().st_size == 0 for path in figures):
    raise SystemExit('Expected at least three non-empty figures')
print('PASS: notebook contains no execution errors')
print(f'PASS: {len(figures)} figures exist and are non-empty')
print('PASS: required metrics and questions are present')

# Extract plain text outputs for a compact audit.
for cell in nb.cells:
    for output in cell.get('outputs', []):
        if output.output_type == 'stream' and 'text' in output:
            text = ''.join(output['text'])
            if 'Примечание:' in text:
                print(text)
