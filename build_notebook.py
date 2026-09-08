"""Создаёт Notebook по экзаменационной задаче №3 в формате решения преподавателя."""
from pathlib import Path
import nbformat as nbf

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "notebooks" / "task_03_ai_pricing.ipynb"
nb = nbf.v4.new_notebook()
cells = []

cells.append(nbf.v4.new_markdown_cell("""# Экзаменационная задача №3
## Выбор ценовой стратегии для AI-сервиса по созданию контента

**Проект:** «AI-Копирайтер»

В работе последовательно рассматриваются четыре стратегии: **Freemium, подписка, динамическое и персонализированное ценообразование**. Формат решения соответствует структуре задания: вопрос → расчёт → таблица → вывод."""))

cells.append(nbf.v4.new_code_cell("""from pathlib import Path
import json
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from IPython.display import display

repo_root = Path.cwd().resolve()
if repo_root.name == "notebooks":
    repo_root = repo_root.parent
elif not (repo_root / "data").exists() and (repo_root.parent / "data").exists():
    repo_root = repo_root.parent
sys.path.insert(0, str(repo_root))

from utils.calculations import arpu, ltv, ltv_cac, user_bases, annual_profit, npv, sensitivity_npv

cfg = json.loads((repo_root / "data" / "task_03_ai_pricing_config.json").read_text(encoding="utf-8"))
figures_dir = repo_root / "reports" / "figures"
figures_dir.mkdir(parents=True, exist_ok=True)
pd.set_option("display.float_format", lambda x: f"{x:,.2f}".replace(",", " ").replace(".", ","))
print(f"Проект: {cfg['project_name']}")
print(f"Период расчёта: {cfg['horizon_years']} года; ставка дисконтирования: {cfg['annual_discount_rate']:.0%}")"""))

cells.append(nbf.v4.new_markdown_cell("""## Исходные данные задачи

Рынок AI-сервиса в России оценивается в 500 000 потенциальных пользователей. Конкурентный диапазон составляет 500–5 000 руб. в месяц. Затраты на разработку равны 15 млн руб., ежемесячное поддержание и облачные услуги требуют 2 млн руб. Начальная база составляет 1 000 пользователей."""))

cells.append(nbf.v4.new_code_cell("""source_table = pd.DataFrame([
    ["Потенциальный рынок", "500 000 пользователей"],
    ["Рост рынка", "25% в год"],
    ["Разработка", "15 000 000 руб."],
    ["Поддержание", "2 000 000 руб./мес."],
    ["Начальная база", "1 000 пользователей"],
    ["Ставка дисконтирования", "12% годовых"],
    ["Горизонт", "3 года"],
], columns=["Показатель", "Значение"])
display(source_table)

strategy_input = pd.DataFrame([
    [name, values["price_rub_month"], values["conversion"], values["churn"]]
    for name, values in cfg["strategies"].items()
], columns=["Стратегия", "Цена, руб./мес.", "Конверсия", "Churn"])
display(strategy_input)

cac_table = pd.DataFrame(list(cfg["cac_channels_rub"].items()), columns=["Канал привлечения", "CAC, руб."])
display(cac_table)"""))

cells.append(nbf.v4.new_markdown_cell("""# Часть 1. Расчёт ключевых метрик

## Вопрос 1. Рассчитать ARPU для каждой стратегии

**Формула:**

$$ARPU = Цена \\times Конверсия.$$

ARPU показывает ожидаемый средний месячный доход на одного пользователя с учётом доли пользователей, которые переходят на платный вариант."""))

cells.append(nbf.v4.new_code_cell("""arpu_table = pd.DataFrame([
    [name, values["price_rub_month"], values["conversion"], arpu(values["price_rub_month"], values["conversion"])]
    for name, values in cfg["strategies"].items()
], columns=["Стратегия", "Цена, руб./мес.", "Конверсия", "ARPU, руб./мес."])
display(arpu_table)
best_arpu = arpu_table.loc[arpu_table["ARPU, руб./мес."].idxmax()]
print(f"Ответ на вопрос 1: максимальный ARPU имеет стратегия «{best_arpu['Стратегия']}» — {best_arpu['ARPU, руб./мес.']:.0f} руб./мес.")"""))

cells.append(nbf.v4.new_markdown_cell("""## Вопрос 2. Рассчитать LTV для каждой стратегии

**Формула:**

$$LTV = \\frac{ARPU}{Churn}.$$

Средний срок жизни клиента определяется как $1 / Churn$. Чем ниже churn, тем дольше сохраняется клиент и тем выше его LTV при прочих равных условиях."""))

cells.append(nbf.v4.new_code_cell("""ltv_table = pd.DataFrame([
    [name, arpu(values["price_rub_month"], values["conversion"]), values["churn"], 1 / values["churn"], ltv(arpu(values["price_rub_month"], values["conversion"]), values["churn"])]
    for name, values in cfg["strategies"].items()
], columns=["Стратегия", "ARPU, руб./мес.", "Churn", "Срок жизни, мес.", "LTV, руб."])
display(ltv_table)
best_ltv = ltv_table.loc[ltv_table["LTV, руб."].idxmax()]
print(f"Ответ на вопрос 2: максимальный LTV имеет стратегия «{best_ltv['Стратегия']}» — {best_ltv['LTV, руб.']:.0f} руб.")"""))

cells.append(nbf.v4.new_markdown_cell("""## Вопрос 3. Рассчитать LTV/CAC для каналов привлечения

**Формула:**

$$LTV/CAC = \\frac{LTV}{CAC}.$$

Расчёт выполнен отдельно для рекламы, контент-маркетинга и вирального роста."""))

cells.append(nbf.v4.new_code_cell("""ltv_cac_rows = []
for name, values in cfg["strategies"].items():
    strategy_ltv = ltv(arpu(values["price_rub_month"], values["conversion"]), values["churn"])
    ltv_cac_rows.append([name, strategy_ltv] + [ltv_cac(strategy_ltv, cac) for cac in cfg["cac_channels_rub"].values()])
ltv_cac_table = pd.DataFrame(ltv_cac_rows, columns=["Стратегия", "LTV, руб.", "Реклама", "Контент-маркетинг", "Виральный рост"])
for col in ["Реклама", "Контент-маркетинг", "Виральный рост"]:
    ltv_cac_table[col] = ltv_cac_table[col].map(lambda x: f"{x:.2f}x".replace(".", ","))
display(ltv_cac_table)
ltv_cac_wide = ltv_cac_table.set_index("Стратегия")[["Реклама", "Контент-маркетинг", "Виральный рост"]].T
ltv_cac_wide.index.name = "Канал привлечения"
display(ltv_cac_wide)
numeric_ltv_cac = pd.DataFrame(ltv_cac_rows, columns=["Стратегия", "LTV, руб.", "Реклама", "Контент-маркетинг", "Виральный рост"])
best_channel = numeric_ltv_cac[["Реклама", "Контент-маркетинг", "Виральный рост"]].max().idxmax()
best_channel_value = numeric_ltv_cac[best_channel].max()
best_channel_strategy = numeric_ltv_cac.loc[numeric_ltv_cac[best_channel].idxmax(), "Стратегия"]
print(f"Ответ на вопрос 3: максимальное LTV/CAC даёт канал «{best_channel}» для стратегии «{best_channel_strategy}» — {best_channel_value:.2f}x.")"""))

cells.append(nbf.v4.new_markdown_cell("""# Часть 2. Оценка эффективности

## Вопрос 4. Рассчитать прогнозную прибыль за 3 года

Модель роста базы пользователей задаётся условием:

| Год | Прирост | База пользователей |
|---:|---:|---:|
| 0 | — | 1 000 |
| 1 | 100% | 2 000 |
| 2 | 50% | 3 000 |
| 3 | 20% | 3 600 |

Для годового прогноза используется CAC контент-маркетинга — 800 руб. Формула прибыли:

$$П_t = ARPU \\times N_t \\times 12 - 2\\,000\\,000 \\times 12 - CAC \\times \\Delta N_t.$$

Затраты на разработку относятся к нулевому году и отдельно учитываются в NPV."""))

cells.append(nbf.v4.new_code_cell("""bases = user_bases(cfg["initial_users"], cfg["growth_rates"])
base_cac = cfg["cac_channels_rub"]["Контент-маркетинг"]
profit_rows = []
for name, values in cfg["strategies"].items():
    strategy_arpu = arpu(values["price_rub_month"], values["conversion"])
    previous = bases[0]
    for year in range(1, len(bases)):
        current = bases[year]
        revenue = strategy_arpu * current * 12
        maintenance = cfg["monthly_maintenance_cost_rub"] * 12
        acquisition = (current - previous) * base_cac
        profit = revenue - maintenance - acquisition
        profit_rows.append([name, year, current, current - previous, revenue, maintenance, acquisition, profit])
        previous = current
profit_table = pd.DataFrame(profit_rows, columns=["Стратегия", "Год", "База", "Новые пользователи", "Доход, руб.", "Поддержание, руб.", "CAC, руб.", "Прибыль, руб."])
display(profit_table)
profit_summary = profit_table.groupby("Стратегия")["Прибыль, руб."].sum().sort_values(ascending=False)
best_profit_strategy = profit_summary.index[0]
positive_profit = profit_summary[profit_summary >= 0]
profit_conclusion = (f"положительную суммарную прибыль имеют: {', '.join(positive_profit.index)}"
                     if len(positive_profit) else "ни одна стратегия не имеет положительной суммарной прибыли")
print(f"Ответ на вопрос 4: лучший результат по суммарной прибыли показывает «{best_profit_strategy}» ({profit_summary.iloc[0]:,.0f} руб.); {profit_conclusion}.")"""))

cells.append(nbf.v4.new_markdown_cell("""## Вопрос 5. Рассчитать NPV за 3 года

**Формула:**

$$NPV = \\sum_{t=0}^{3} \\frac{CF_t}{(1+0{,}12)^t}.$$

В нулевом году отражаются затраты на разработку 15 млн руб. Далее дисконтируются годовые денежные потоки."""))

cells.append(nbf.v4.new_code_cell("""npv_rows = []
for name, values in cfg["strategies"].items():
    strategy_arpu = arpu(values["price_rub_month"], values["conversion"])
    cash_flows = [-cfg["development_cost_rub"]]
    previous = bases[0]
    for year in range(1, len(bases)):
        current = bases[year]
        cash_flows.append(annual_profit(current, current - previous, strategy_arpu, cfg["monthly_maintenance_cost_rub"], base_cac))
        previous = current
    value = npv(cash_flows, cfg["annual_discount_rate"])
    npv_rows.append([name, *cash_flows, value, value / 1e6])
npv_table = pd.DataFrame(npv_rows, columns=["Стратегия", "Денежный поток, год 0, руб.", "Денежный поток, год 1, руб.", "Денежный поток, год 2, руб.", "Денежный поток, год 3, руб.", "NPV, руб.", "NPV, млн руб."])
display(npv_table)

# Отдельное сопоставление с числовыми результатами, приведёнными
# в разделе «Решение для преподавателя» учебных материалов.
teacher_npv = pd.DataFrame(list(cfg["teacher_solution_reference"]["teacher_npv_mln_rub"].items()), columns=["Стратегия", "NPV по решению преподавателя, млн руб."])
npv_comparison = npv_table[["Стратегия", "NPV, млн руб."]].merge(teacher_npv, on="Стратегия", how="left")
print("Сравнение расчёта Notebook с решением преподавателя из учебных материалов:")
display(npv_comparison)
print("Примечание: столбец «NPV по решению преподавателя» содержит значения, приведённые в учебном решении; столбец «NPV, млн руб.» — результат текущей воспроизводимой модели.")
best_npv = npv_table.loc[npv_table["NPV, млн руб."].idxmax()]
positive_npv = npv_table.loc[npv_table["NPV, млн руб."] >= 0, "Стратегия"].tolist()
npv_conclusion = f"положительный NPV имеют: {', '.join(positive_npv)}" if positive_npv else "положительного NPV нет ни у одной стратегии"
print(f"Ответ на вопрос 5: лучший NPV имеет «{best_npv['Стратегия']}» — {best_npv['NPV, млн руб.']:.2f} млн руб.; {npv_conclusion}.")"""))

cells.append(nbf.v4.new_markdown_cell("""# Часть 3. Анализ чувствительности

## Вопрос 6. Изменить конверсию, Churn и CAC на ±30%

Для удобства сравнения сценарии расположены строками, а стратегии — столбцами. Значения показаны в млн руб. При изменении конверсии изменяется ARPU. При изменении CAC меняются затраты на новых пользователей. При изменении Churn применяется отдельное годовое приближение удержания: доход масштабируется пропорционально изменению доли удержанных клиентов. Базовый сценарий при этом совпадает с основной моделью."""))

cells.append(nbf.v4.new_code_cell("""scenario_definitions = [
    ("Базовый сценарий", {}),
    ("Конверсия +30%", {"conversion_multiplier": 1.3}),
    ("Конверсия -30%", {"conversion_multiplier": 0.7}),
    ("Churn +30%", {"churn_multiplier": 1.3}),
    ("Churn -30%", {"churn_multiplier": 0.7}),
    ("CAC +30%", {"cac_multiplier": 1.3}),
    ("CAC -30%", {"cac_multiplier": 0.7}),
]
sensitivity_wide = []
for label, kwargs in scenario_definitions:
    row = {"Сценарий": label}
    for name, values in cfg["strategies"].items():
        row[name] = sensitivity_npv(values, bases, cfg["growth_rates"], cfg["monthly_maintenance_cost_rub"], base_cac, cfg["development_cost_rub"], cfg["annual_discount_rate"], **kwargs) / 1e6
    sensitivity_wide.append(row)
sensitivity_wide_table = pd.DataFrame(sensitivity_wide)
display(sensitivity_wide_table)
subscription_sensitivity = sensitivity_wide_table[["Сценарий", "Подписка"]].copy()
subscription_sensitivity["Отклонение от базового, млн руб."] = subscription_sensitivity["Подписка"] - subscription_sensitivity.loc[subscription_sensitivity["Сценарий"] == "Базовый сценарий", "Подписка"].iloc[0]
display(subscription_sensitivity)
best_by_scenario = sensitivity_wide_table.set_index("Сценарий").idxmax(axis=1)
best_counts = best_by_scenario.value_counts()
overall_sensitivity_winner = best_counts.index[0]
print(f"Ответ на вопрос 6: лучший NPV чаще всего показывает «{overall_sensitivity_winner}» ({best_counts.iloc[0]} из {len(best_by_scenario)} сценариев).")"""))

cells.append(nbf.v4.new_markdown_cell("""## Вопрос 7. Определить наиболее устойчивую стратегию

Устойчивость оценивается по размаху NPV между минимальным и максимальным сценарием. Чем меньше размах, тем слабее чувствительность к изменению параметров."""))

cells.append(nbf.v4.new_code_cell("""sensitivity_long = sensitivity_wide_table.melt(id_vars="Сценарий", var_name="Стратегия", value_name="NPV, млн руб.")
stability = sensitivity_long.groupby("Стратегия")["NPV, млн руб."].agg(["min", "max"])
stability["Размах NPV, млн руб."] = stability["max"] - stability["min"]
stability = stability.sort_values("Размах NPV, млн руб.").reset_index()
display(stability)
most_stable = stability.iloc[0]
selected_stability = stability.loc[stability["Стратегия"] == best_npv["Стратегия"]].iloc[0]
print(f"Ответ на вопрос 7: по абсолютному размаху наиболее стабильна «{most_stable['Стратегия']}» — {most_stable['Размах NPV, млн руб.']:.2f} млн руб.")
print(f"Для выбранной стратегии «{best_npv['Стратегия']}» размах NPV составляет {selected_stability['Размах NPV, млн руб.']:.2f} млн руб.; именно её чувствительность дополнительно показана в таблице сценариев.")"""))

cells.append(nbf.v4.new_code_cell("""fig, ax = plt.subplots(figsize=(10, 5.5))
npv_plot = npv_table.sort_values("NPV, млн руб.")
ax.bar(npv_plot["Стратегия"], npv_plot["NPV, млн руб."], color=["#7A8B99", "#3F6B7A", "#A6B8B0", "#6F8F72"])
ax.axhline(0, color="#333333", linewidth=1)
ax.set_title("NPV ценовых стратегий")
ax.set_ylabel("NPV, млн руб.")
ax.tick_params(axis="x", rotation=15)
fig.tight_layout()
fig.savefig(figures_dir / "task_03_npv_by_strategy.png", dpi=160, bbox_inches="tight")
plt.show()

fig, ax = plt.subplots(figsize=(10, 5.5))
for strategy in cfg["strategies"]:
    subset = sensitivity_long[sensitivity_long["Стратегия"] == strategy]
    ax.plot(subset["Сценарий"], subset["NPV, млн руб."], marker="o", linewidth=1.6, label=strategy)
ax.axhline(0, color="#333333", linewidth=1)
ax.set_title("Чувствительность NPV к изменению параметров")
ax.set_ylabel("NPV, млн руб.")
ax.tick_params(axis="x", rotation=35)
ax.legend()
fig.tight_layout()
fig.savefig(figures_dir / "task_03_sensitivity.png", dpi=160, bbox_inches="tight")
plt.show()

fig, ax = plt.subplots(figsize=(10, 5.5))
ltv_plot = ltv_table.set_index("Стратегия")["LTV, руб."]
ltv_plot.plot(kind="bar", ax=ax, color="#536878")
ax.set_title("LTV ценовых стратегий")
ax.set_ylabel("LTV, руб.")
ax.tick_params(axis="x", rotation=15)
fig.tight_layout()
fig.savefig(figures_dir / "task_03_ltv.png", dpi=160, bbox_inches="tight")
plt.show()"""))

cells.append(nbf.v4.new_markdown_cell("""# Часть 4. Стратегические рекомендации

## Вопрос 8. Выбрать оптимальную ценовую стратегию

Рекомендация определяется по рассчитанным метрикам: сначала сравнивается NPV, затем ARPU, LTV и LTV/CAC. Если финансовые результаты отрицательны у всех стратегий, выбирается вариант с максимальным NPV и дополнительно проверяются его ARPU, LTV и устойчивость."""))

cells.append(nbf.v4.new_code_cell("""selection_rows = []
for name, values in cfg["strategies"].items():
    strategy_arpu = arpu(values["price_rub_month"], values["conversion"])
    strategy_ltv = ltv(strategy_arpu, values["churn"])
    strategy_npv = npv_table.loc[npv_table["Стратегия"] == name, "NPV, млн руб."].iloc[0]
    strategy_ratio = strategy_ltv / base_cac
    selection_rows.append([name, strategy_arpu, strategy_ltv, strategy_ratio, strategy_npv])
selection_table = pd.DataFrame(selection_rows, columns=["Стратегия", "ARPU, руб./мес.", "LTV, руб.", "LTV/CAC: контент", "NPV, млн руб."])
selection_table["Решение"] = np.where(selection_table["Стратегия"] == best_npv["Стратегия"], "Рекомендуется", "Альтернативный вариант")
display(selection_table)
selected_metrics = selection_table.loc[selection_table["Стратегия"] == best_npv["Стратегия"]].iloc[0]
print(f"Ответ на вопрос 8: по текущим исходным данным выбирается стратегия «{best_npv['Стратегия']}» с максимальным NPV {best_npv['NPV, млн руб.']:.2f} млн руб.")
print(f"Её ARPU = {selected_metrics['ARPU, руб./мес.']:.2f} руб./мес., LTV = {selected_metrics['LTV, руб.']:.2f} руб., LTV/CAC = {selected_metrics['LTV/CAC: контент']:.2f}x.")"""))

cells.append(nbf.v4.new_markdown_cell("""## Вопрос 9. Разработать план внедрения выбранной стратегии

| Период | План действий |
|---|---|
| Год 1. Выход на рынок | Запуск выбранной стратегии с 14-дневным пробным периодом; контент-маркетинг; интеграции с Tilda и WordPress. |
| Год 2. Рост | Реферальная программа; функции для отдельных ниш; автоматизация воронки продаж. |
| Год 3. Зрелость | Снижение churn через улучшение продукта; сегментные тарифы; аналитические продукты. |"""))

cells.append(nbf.v4.new_code_cell("""monitoring_table = pd.DataFrame([
    ["Churn Rate", "< 5%", "Ежемесячно"],
    ["LTV/CAC", "> 3x", "Ежеквартально"],
    ["MRR", "Рост 20% в месяц", "Ежемесячно"],
    ["Конверсия", "> 20%", "Ежемесячно"],
    ["NRR", "> 120%", "Ежеквартально"],
], columns=["Метрика", "Целевое значение", "Частота мониторинга"])
display(monitoring_table)
print(f"Ответ на вопрос 9: дорожная карта начинается со стратегии «{best_npv['Стратегия']}», далее используются пробный период, контент-маркетинг, реферальные механизмы и сегментация.")"""))

cells.append(nbf.v4.new_markdown_cell("""## Вопрос 10. Проанализировать риски и меры митигации

| Риск | Вероятность | Мера снижения |
|---|---|---|
| Рост churn | Средняя | Регулярный сбор обратной связи и улучшение продукта. |
| Снижение конверсии | Средняя | A/B-тестирование пробного периода и тарифов. |
| Рост CAC | Высокая | Диверсификация каналов, контент-маркетинг и реферальная программа. |
| Усиление конкуренции | Высокая | Развитие AI-модели и уникальных функций. |
| Регуляторные ограничения | Низкая | Юридическая проверка использования AI и контента. |"""))

cells.append(nbf.v4.new_markdown_cell("""# Итоговый вывод

Текст итогового вывода формируется по значениям таблиц в последней расчётной ячейке. Это позволяет автоматически обновлять выбранную стратегию, показатели и формулировку при изменении исходных данных.

NPV в Notebook рассчитывается прозрачно с учётом всех исходных затрат. Значения NPV из решения преподавателя выводятся отдельно для сопоставления."""))

cells.append(nbf.v4.new_code_cell("""print("Итоговый вывод")
print(f"Основная рекомендация: стратегия «{best_npv['Стратегия']}».")
print(f"Критерий выбора: максимальный рассчитанный NPV = {best_npv['NPV, млн руб.']:.2f} млн руб.")
teacher_selected_npv = teacher_npv.loc[teacher_npv["Стратегия"] == best_npv["Стратегия"], "NPV по решению преподавателя, млн руб."]
if len(teacher_selected_npv):
    print(f"NPV по решению преподавателя для этой стратегии = {teacher_selected_npv.iloc[0]:.2f} млн руб.")
    print("Сравнение: первое значение рассчитано текущей моделью Notebook, второе взято из решения преподавателя.")
print(f"ARPU выбранной стратегии: {selected_metrics['ARPU, руб./мес.']:.2f} руб./мес.; LTV: {selected_metrics['LTV, руб.']:.2f} руб.; LTV/CAC: {selected_metrics['LTV/CAC: контент']:.2f}x.")
print(f"Наиболее устойчивая стратегия по размаху NPV: «{most_stable['Стратегия']}».")"""))

cells.append(nbf.v4.new_markdown_cell("""## Источник

Задание и параметры взяты из учебных материалов курса «Экономика информатизации», экзаменационная задача «Выбор ценовой стратегии для AI-сервиса по созданию контента»."""))

nb["cells"] = cells
nb["metadata"] = {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}, "language_info": {"name": "python", "version": "3"}}
OUT.write_text(nbf.writes(nb), encoding="utf-8")
print(f"Notebook created: {OUT}")
