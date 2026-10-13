import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go


# =========================================================
# НАЛАШТУВАННЯ СТОРІНКИ
# =========================================================

st.set_page_config(
    page_title="Фінансово-економічна стійкість ТОВ «СОЛЮТЕХ»",
    page_icon="📊",
    layout="wide"
)

st.title("Фінансово-економічна стійкість ТОВ «СОЛЮТЕХ»")

st.caption(
    "CVP-аналіз, факторний аналіз, сценарне моделювання "
    "та сценарна проєкція на 2026–2030 роки"
)


# =========================================================
# ДОПОМІЖНІ ФУНКЦІЇ
# =========================================================

def calculate_cvp(D, ZV, PV):
    """
    Розрахунок основних показників CVP-аналізу.

    D  - чистий дохід від реалізації
    ZV - змінні витрати
    PV - постійні витрати
    """

    if D <= 0:
        return None

    MD = D - ZV
    q = ZV / D
    Kmd = MD / D
    EBIT = MD - PV

    if Kmd > 0:
        TB = PV / Kmd
        ZFS = D - TB
        ZFS_pct = (ZFS / D) * 100
    else:
        TB = np.nan
        ZFS = np.nan
        ZFS_pct = np.nan

    return {
        "Дохід": D,
        "Змінні витрати": ZV,
        "Частка ЗВ": q * 100,
        "Постійні витрати": PV,
        "Маржинальний дохід": MD,
        "Кмд": Kmd * 100,
        "EBIT": EBIT,
        "Точка беззбитковості": TB,
        "ЗФС": ZFS,
        "ЗФС, %": ZFS_pct
    }


def financial_zone(ebit, zfs):
    """
    Визначення положення підприємства
    відносно точки беззбитковості.
    """

    if pd.isna(ebit) or pd.isna(zfs):
        return "Неможливо визначити"

    if abs(ebit) < 0.01:
        return "Точка беззбитковості"

    if ebit > 0 and zfs > 0:
        return "Прибуткова зона"

    return "Збиткова зона"


def format_ua(value, decimals=2):
    """
    Форматування числа для звичайного тексту:
    32044.94 -> 32 044,94
    """

    if pd.isna(value):
        return "—"

    text = f"{value:,.{decimals}f}"
    text = text.replace(",", " ")
    text = text.replace(".", ",")
    return text


def latex_number(value, decimals=2):
    """
    Форматування числа для LaTeX:
    32044.94 -> 32\\,044{,}94
    """

    if pd.isna(value):
        return "-"

    text = f"{value:,.{decimals}f}"

    integer_part, decimal_part = text.split(".")

    integer_part = integer_part.replace(",", r"\,")

    return rf"{integer_part}{{,}}{decimal_part}"


# =========================================================
# ВИХІДНІ ДАНІ
# =========================================================

historical_data = pd.DataFrame({
    "Рік": [2024, 2025],
    "Дохід": [
        28137.20,
        79654.10
    ],
    "Змінні витрати": [
        15884.80,
        76408.10
    ],
    "Постійні витрати": [
        2640.60,
        2323.90
    ]
})


# =========================================================
# РОЗРАХУНОК ФАКТИЧНИХ ПОКАЗНИКІВ
# =========================================================

history_results = []

for _, row in historical_data.iterrows():

    result = calculate_cvp(
        row["Дохід"],
        row["Змінні витрати"],
        row["Постійні витрати"]
    )

    result["Рік"] = int(row["Рік"])
    result["Зона"] = financial_zone(
        result["EBIT"],
        result["ЗФС"]
    )

    history_results.append(result)


history = pd.DataFrame(history_results)

history = history[
    [
        "Рік",
        "Дохід",
        "Змінні витрати",
        "Частка ЗВ",
        "Постійні витрати",
        "Маржинальний дохід",
        "Кмд",
        "EBIT",
        "Точка беззбитковості",
        "ЗФС",
        "ЗФС, %",
        "Зона"
    ]
]


r2024 = history[history["Рік"] == 2024].iloc[0]
r2025 = history[history["Рік"] == 2025].iloc[0]


# =========================================================
# ВКЛАДКИ
# =========================================================

tab1, tab2, tab3, tab4 = st.tabs(
    [
        "Фактичні показники",
        "Факторний аналіз",
        "Сценарний аналіз",
        "Проєкція на 5 років"
    ]
)


# =========================================================
# TAB 1 — ФАКТИЧНІ ПОКАЗНИКИ
# =========================================================

with tab1:

    st.header("CVP-аналіз за 2024–2025 роки")

    st.write(
        "Для оцінювання фінансово-економічної стійкості "
        "використовується система показників CVP-аналізу."
    )

    st.markdown("**Маржинальний дохід:**")

    st.latex(
        r"\mathrm{МД} = \mathrm{Д} - \mathrm{ЗВ}"
    )

    st.markdown("**Коефіцієнт маржинального доходу:**")

    st.latex(
        r"\mathrm{Кмд} = "
        r"\frac{\mathrm{МД}}{\mathrm{Д}}"
    )

    st.markdown("**Операційний результат:**")

    st.latex(
        r"EBIT = "
        r"\mathrm{Д} - \mathrm{ЗВ} - \mathrm{ПВ}"
    )

    st.markdown("**Точка беззбитковості:**")

    st.latex(
        r"\mathrm{ТБ} = "
        r"\frac{\mathrm{ПВ}}{\mathrm{Кмд}}"
    )

    st.markdown("**Абсолютний запас фінансової стійкості:**")

    st.latex(
        r"\mathrm{ЗФС} = "
        r"\mathrm{Д} - \mathrm{ТБ}"
    )

    st.markdown("**Відносний запас фінансової стійкості:**")

    st.latex(
        r"\mathrm{ЗФС}_{\%} = "
        r"\frac{\mathrm{ЗФС}}{\mathrm{Д}} "
        r"\times 100\%"
    )

    st.divider()

    st.subheader("Результати розрахунків")

    display_history = history.copy()

    numeric_columns = [
        "Дохід",
        "Змінні витрати",
        "Частка ЗВ",
        "Постійні витрати",
        "Маржинальний дохід",
        "Кмд",
        "EBIT",
        "Точка беззбитковості",
        "ЗФС",
        "ЗФС, %"
    ]

    display_history[numeric_columns] = (
        display_history[numeric_columns].round(2)
    )

    st.dataframe(
        display_history,
        use_container_width=True,
        hide_index=True
    )

    st.subheader("Ключові показники")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Кмд 2024",
        f"{format_ua(r2024['Кмд'])} %"
    )

    col2.metric(
        "Кмд 2025",
        f"{format_ua(r2025['Кмд'])} %",
        f"{format_ua(r2025['Кмд'] - r2024['Кмд'])} в. п."
    )

    col3.metric(
        "ЗФС 2024",
        f"{format_ua(r2024['ЗФС, %'])} %"
    )

    col4.metric(
        "ЗФС 2025",
        f"{format_ua(r2025['ЗФС, %'])} %",
        f"{format_ua(r2025['ЗФС, %'] - r2024['ЗФС, %'])} в. п."
    )

    # -----------------------------------------------------
    # ГРАФІК ДОХОДУ ТА ТОЧКИ БЕЗЗБИТКОВОСТІ
    # -----------------------------------------------------

    st.subheader("Дохід і точка беззбитковості")

    break_even_chart = history[
        ["Рік", "Дохід", "Точка беззбитковості"]
    ].melt(
        id_vars="Рік",
        var_name="Показник",
        value_name="тис. грн"
    )

    fig = px.bar(
        break_even_chart,
        x="Рік",
        y="тис. грн",
        barmode="group",
        color="Показник"
    )

    fig.update_layout(
        xaxis=dict(
            tickmode="array",
            tickvals=[2024, 2025]
        ),
        legend_title_text="",
        yaxis_title="тис. грн",
        xaxis_title=""
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    # -----------------------------------------------------
    # ГРАФІК КМД ТА ЗФС
    # -----------------------------------------------------

    st.subheader(
        "Динаміка коефіцієнта маржинального доходу "
        "та запасу фінансової стійкості"
    )

    percentage_chart = history[
        ["Рік", "Кмд", "ЗФС, %"]
    ].melt(
        id_vars="Рік",
        var_name="Показник",
        value_name="Значення, %"
    )

    fig2 = px.line(
        percentage_chart,
        x="Рік",
        y="Значення, %",
        color="Показник",
        markers=True
    )

    fig2.update_layout(
        xaxis=dict(
            tickmode="array",
            tickvals=[2024, 2025]
        ),
        legend_title_text="",
        xaxis_title="",
        yaxis_title="%"
    )

    st.plotly_chart(
        fig2,
        use_container_width=True
    )


# =========================================================
# TAB 2 — ФАКТОРНИЙ АНАЛІЗ
# =========================================================

with tab2:

    st.header(
        "Факторний аналіз методом ланцюгових підстановок"
    )

    st.write(
        "Метою факторного аналізу є визначення кількісного "
        "впливу зміни доходу, коефіцієнта маржинального "
        "доходу та постійних витрат на зміну EBIT."
    )

    st.markdown("**Факторна модель:**")

    st.latex(
        r"EBIT = "
        r"\mathrm{Д}\times\mathrm{Кмд}"
        r"-\mathrm{ПВ}"
    )

    D0 = r2024["Дохід"]
    K0 = r2024["Кмд"] / 100
    PV0 = r2024["Постійні витрати"]

    D1 = r2025["Дохід"]
    K1 = r2025["Кмд"] / 100
    PV1 = r2025["Постійні витрати"]

    EBIT0 = D0 * K0 - PV0

    EBIT_D = D1 * K0 - PV0

    EBIT_DK = D1 * K1 - PV0

    EBIT1 = D1 * K1 - PV1

    impact_D = EBIT_D - EBIT0
    impact_K = EBIT_DK - EBIT_D
    impact_PV = EBIT1 - EBIT_DK

    total_change = EBIT1 - EBIT0

    st.divider()

    # -----------------------------------------------------
    # ЕТАП 1
    # -----------------------------------------------------

    st.subheader("1. Базовий результат 2024 року")

    st.latex(
        rf"EBIT_{{2024}} = "
        rf"{latex_number(D0)}"
        rf"\times"
        rf"{K0:.6f}"
        rf"-"
        rf"{latex_number(PV0)}"
        rf"="
        rf"{latex_number(EBIT0)}"
        rf"\ \text{{тис. грн}}"
    )

    # -----------------------------------------------------
    # ЕТАП 2
    # -----------------------------------------------------

    st.subheader("2. Вплив зміни чистого доходу")

    st.write(
        "На першому етапі до моделі підставляється "
        "дохід 2025 року, тоді як коефіцієнт "
        "маржинального доходу та постійні витрати "
        "залишаються на рівні 2024 року."
    )

    st.latex(
        rf"EBIT_{{Д}} = "
        rf"{latex_number(D1)}"
        rf"\times"
        rf"{K0:.6f}"
        rf"-"
        rf"{latex_number(PV0)}"
        rf"="
        rf"{latex_number(EBIT_D)}"
        rf"\ \text{{тис. грн}}"
    )

    st.latex(
        rf"\Delta EBIT_{{Д}} = "
        rf"{latex_number(EBIT_D)}"
        rf"-"
        rf"{latex_number(EBIT0)}"
        rf"="
        rf"{latex_number(impact_D)}"
        rf"\ \text{{тис. грн}}"
    )

    # -----------------------------------------------------
    # ЕТАП 3
    # -----------------------------------------------------

    st.subheader(
        "3. Вплив зміни коефіцієнта маржинального доходу"
    )

    st.write(
        "На другому етапі до вже зміненого доходу "
        "підставляється фактичний коефіцієнт "
        "маржинального доходу 2025 року."
    )

    st.latex(
        rf"EBIT_{{Д,\ Кмд}} = "
        rf"{latex_number(D1)}"
        rf"\times"
        rf"{K1:.6f}"
        rf"-"
        rf"{latex_number(PV0)}"
        rf"="
        rf"{latex_number(EBIT_DK)}"
        rf"\ \text{{тис. грн}}"
    )

    st.latex(
        rf"\Delta EBIT_{{Кмд}} = "
        rf"{latex_number(EBIT_DK)}"
        rf"-"
        rf"{latex_number(EBIT_D)}"
        rf"="
        rf"{latex_number(impact_K)}"
        rf"\ \text{{тис. грн}}"
    )

    # -----------------------------------------------------
    # ЕТАП 4
    # -----------------------------------------------------

    st.subheader("4. Вплив зміни постійних витрат")

    st.write(
        "На заключному етапі постійні витрати "
        "замінюються фактичним значенням 2025 року."
    )

    st.latex(
        rf"EBIT_{{2025}} = "
        rf"{latex_number(D1)}"
        rf"\times"
        rf"{K1:.6f}"
        rf"-"
        rf"{latex_number(PV1)}"
        rf"="
        rf"{latex_number(EBIT1)}"
        rf"\ \text{{тис. грн}}"
    )

    st.latex(
        rf"\Delta EBIT_{{ПВ}} = "
        rf"{latex_number(EBIT1)}"
        rf"-"
        rf"{latex_number(EBIT_DK)}"
        rf"="
        rf"{latex_number(impact_PV)}"
        rf"\ \text{{тис. грн}}"
    )

    # -----------------------------------------------------
    # ПЕРЕВІРКА
    # -----------------------------------------------------

    st.subheader("5. Перевірка факторного розкладання")

    st.latex(
        rf"\Delta EBIT = "
        rf"{latex_number(impact_D)}"
        rf"{'+' if impact_K >= 0 else ''}"
        rf"{latex_number(impact_K)}"
        rf"{'+' if impact_PV >= 0 else ''}"
        rf"{latex_number(impact_PV)}"
        rf"="
        rf"{latex_number(total_change)}"
        rf"\ \text{{тис. грн}}"
    )

    st.latex(
        rf"EBIT_{{2025}}-EBIT_{{2024}} = "
        rf"{latex_number(EBIT1)}"
        rf"-"
        rf"{latex_number(EBIT0)}"
        rf"="
        rf"{latex_number(total_change)}"
        rf"\ \text{{тис. грн}}"
    )

    st.success(
        "Сума факторних впливів відповідає загальній "
        "зміні EBIT."
    )

    factor_df = pd.DataFrame({
        "Чинник": [
            "Зміна чистого доходу",
            "Зміна Кмд",
            "Зміна постійних витрат",
            "Загальна зміна EBIT"
        ],
        "Вплив, тис. грн": [
            impact_D,
            impact_K,
            impact_PV,
            total_change
        ]
    })

    st.subheader("Результати факторного аналізу")

    st.dataframe(
        factor_df.round(2),
        use_container_width=True,
        hide_index=True
    )

    # -----------------------------------------------------
    # WATERFALL
    # -----------------------------------------------------

    st.subheader("Факторне розкладання зміни EBIT")

    fig_factor = go.Figure(
        go.Waterfall(
            orientation="v",
            measure=[
                "absolute",
                "relative",
                "relative",
                "relative",
                "total"
            ],
            x=[
                "EBIT 2024",
                "Зміна доходу",
                "Зміна Кмд",
                "Зміна ПВ",
                "EBIT 2025"
            ],
            y=[
                EBIT0,
                impact_D,
                impact_K,
                impact_PV,
                0
            ],
            text=[
                format_ua(EBIT0),
                f"{'+' if impact_D > 0 else ''}{format_ua(impact_D)}",
                f"{'+' if impact_K > 0 else ''}{format_ua(impact_K)}",
                f"{'+' if impact_PV > 0 else ''}{format_ua(impact_PV)}",
                format_ua(EBIT1)
            ],
            textposition="outside"
        )
    )

    fig_factor.update_layout(
        yaxis_title="тис. грн",
        xaxis_title="",
        showlegend=False
    )

    st.plotly_chart(
        fig_factor,
        use_container_width=True
    )

    st.info(
        "Зростання доходу мало позитивний вплив на EBIT, "
        "однак цей ефект був повністю перекритий "
        "зниженням коефіцієнта маржинального доходу."
    )


# =========================================================
# TAB 3 — СЦЕНАРНИЙ АНАЛІЗ
# =========================================================

with tab3:

    st.header("Сценарний аналіз")

    st.write(
        "Базою для сценарного аналізу є фактичні "
        "показники 2025 року. Користувач може змінювати "
        "дохід, частку змінних витрат та постійні витрати."
    )

    st.markdown("**Сценарний чистий дохід:**")

    st.latex(
        r"\mathrm{Д}_{s}="
        r"\mathrm{Д}_{0}"
        r"\times"
        r"\left(1+g_{\mathrm{Д}}\right)"
    )

    st.markdown("**Сценарна частка змінних витрат:**")

    st.latex(
        r"q_{s}=q_{0}+\Delta q"
    )

    st.markdown("**Сценарні постійні витрати:**")

    st.latex(
        r"\mathrm{ПВ}_{s}="
        r"\mathrm{ПВ}_{0}"
        r"\times"
        r"\left(1+g_{\mathrm{ПВ}}\right)"
    )

    st.divider()

    left, middle, right = st.columns(3)

    with left:
        income_change = st.slider(
            "Зміна чистого доходу, %",
            min_value=-50.0,
            max_value=50.0,
            value=0.0,
            step=1.0
        )

    with middle:
        q_change_pp = st.slider(
            "Зміна частки змінних витрат, в. п.",
            min_value=-3.0,
            max_value=3.0,
            value=0.0,
            step=0.1
        )

    with right:
        fixed_change = st.slider(
            "Зміна постійних витрат, %",
            min_value=-50.0,
            max_value=50.0,
            value=0.0,
            step=1.0
        )

    D_s = r2025["Дохід"] * (
        1 + income_change / 100
    )

    q_base = r2025["Частка ЗВ"] / 100

    q_s = q_base + q_change_pp / 100

    PV_s = r2025["Постійні витрати"] * (
        1 + fixed_change / 100
    )

    if q_s <= 0:

        st.error(
            "Частка змінних витрат не може бути "
            "меншою або дорівнювати 0 %."
        )

    elif q_s >= 1:

        st.error(
            "Частка змінних витрат не може дорівнювати "
            "або перевищувати 100 %."
        )

    elif D_s <= 0:

        st.error(
            "Чистий дохід повинен бути більшим за нуль."
        )

    else:

        ZV_s = D_s * q_s

        scenario = calculate_cvp(
            D_s,
            ZV_s,
            PV_s
        )

        zone = financial_zone(
            scenario["EBIT"],
            scenario["ЗФС"]
        )

        st.subheader("Розрахунок сценарних показників")

        st.markdown("**Коефіцієнт маржинального доходу:**")

        st.latex(
            rf"\mathrm{{Кмд}}_s="
            rf"1-{q_s:.6f}"
            rf"="
            rf"{scenario['Кмд']:.2f}\%"
        )

        st.markdown("**Маржинальний дохід:**")

        st.latex(
            rf"\mathrm{{МД}}_s="
            rf"{latex_number(D_s)}"
            rf"\times"
            rf"{1-q_s:.6f}"
            rf"="
            rf"{latex_number(scenario['Маржинальний дохід'])}"
            rf"\ \text{{тис. грн}}"
        )

        st.markdown("**Операційний результат:**")

        st.latex(
            rf"EBIT_s="
            rf"{latex_number(scenario['Маржинальний дохід'])}"
            rf"-"
            rf"{latex_number(PV_s)}"
            rf"="
            rf"{latex_number(scenario['EBIT'])}"
            rf"\ \text{{тис. грн}}"
        )

        st.markdown("**Точка беззбитковості:**")

        st.latex(
            rf"\mathrm{{ТБ}}_s="
            rf"\frac{{{latex_number(PV_s)}}}"
            rf"{{{1-q_s:.6f}}}"
            rf"="
            rf"{latex_number(scenario['Точка беззбитковості'])}"
            rf"\ \text{{тис. грн}}"
        )

        st.markdown("**Запас фінансової стійкості:**")

        st.latex(
            rf"\mathrm{{ЗФС}}_s="
            rf"{latex_number(D_s)}"
            rf"-"
            rf"{latex_number(scenario['Точка беззбитковості'])}"
            rf"="
            rf"{latex_number(scenario['ЗФС'])}"
            rf"\ \text{{тис. грн}}"
        )

        st.latex(
            rf"\mathrm{{ЗФС}}_{{s,\%}}="
            rf"{scenario['ЗФС, %']:.2f}\%"
        )

        st.divider()

        st.subheader("Результат сценарію")

        c1, c2, c3, c4 = st.columns(4)

        c1.metric(
            "EBIT",
            f"{format_ua(scenario['EBIT'])} тис. грн"
        )

        c2.metric(
            "Точка беззбитковості",
            f"{format_ua(scenario['Точка беззбитковості'])} тис. грн"
        )

        c3.metric(
            "ЗФС",
            f"{format_ua(scenario['ЗФС, %'])} %"
        )

        c4.metric(
            "Фінансовий стан",
            zone
        )

        comparison = pd.DataFrame({
            "Показник": [
                "Дохід",
                "EBIT",
                "Точка беззбитковості",
                "ЗФС"
            ],
            "Базовий 2025": [
                r2025["Дохід"],
                r2025["EBIT"],
                r2025["Точка беззбитковості"],
                r2025["ЗФС"]
            ],
            "Сценарій": [
                scenario["Дохід"],
                scenario["EBIT"],
                scenario["Точка беззбитковості"],
                scenario["ЗФС"]
            ]
        })

        comparison_long = comparison.melt(
            id_vars="Показник",
            var_name="Варіант",
            value_name="тис. грн"
        )

        st.subheader(
            "Порівняння базового та сценарного станів"
        )

        fig_scenario = px.bar(
            comparison_long,
            x="Показник",
            y="тис. грн",
            color="Варіант",
            barmode="group"
        )

        fig_scenario.update_layout(
            legend_title_text="",
            xaxis_title="",
            yaxis_title="тис. грн"
        )

        st.plotly_chart(
            fig_scenario,
            use_container_width=True
        )

        result_table = pd.DataFrame({
            "Показник": [
                "Дохід",
                "Змінні витрати",
                "Частка ЗВ, %",
                "Кмд, %",
                "Постійні витрати",
                "Маржинальний дохід",
                "EBIT",
                "Точка беззбитковості",
                "ЗФС",
                "ЗФС, %"
            ],
            "Базовий стан": [
                r2025["Дохід"],
                r2025["Змінні витрати"],
                r2025["Частка ЗВ"],
                r2025["Кмд"],
                r2025["Постійні витрати"],
                r2025["Маржинальний дохід"],
                r2025["EBIT"],
                r2025["Точка беззбитковості"],
                r2025["ЗФС"],
                r2025["ЗФС, %"]
            ],
            "Сценарій": [
                scenario["Дохід"],
                scenario["Змінні витрати"],
                scenario["Частка ЗВ"],
                scenario["Кмд"],
                scenario["Постійні витрати"],
                scenario["Маржинальний дохід"],
                scenario["EBIT"],
                scenario["Точка беззбитковості"],
                scenario["ЗФС"],
                scenario["ЗФС, %"]
            ]
        })

        st.dataframe(
            result_table.round(2),
            use_container_width=True,
            hide_index=True
        )


# =========================================================
# TAB 4 — СЦЕНАРНА ПРОЄКЦІЯ 2026–2030
# =========================================================

with tab4:

    st.header(
        "Сценарна проєкція фінансово-економічної "
        "стійкості на 2026–2030 роки"
    )

    st.info(
        "Цей блок є сценарною проєкцією, а не "
        "статистичним прогнозом часових рядів. "
        "Базою є фактичні показники 2025 року."
    )

    st.write(
        "Для кожного наступного року задається "
        "очікуваний темп зміни доходу, щорічна зміна "
        "частки змінних витрат та темп зміни "
        "постійних витрат."
    )

    st.markdown("**Проєкція доходу:**")

    st.latex(
        r"\mathrm{Д}_{t}="
        r"\mathrm{Д}_{t-1}"
        r"\times"
        r"\left(1+g_{\mathrm{Д}}\right)"
    )

    st.markdown("**Проєкція змінної витратомісткості:**")

    st.latex(
        r"q_t=q_{t-1}+\Delta q"
    )

    st.markdown("**Проєкція постійних витрат:**")

    st.latex(
        r"\mathrm{ПВ}_{t}="
        r"\mathrm{ПВ}_{t-1}"
        r"\times"
        r"\left(1+g_{\mathrm{ПВ}}\right)"
    )

    st.divider()

    fc1, fc2, fc3 = st.columns(3)

    with fc1:
        revenue_growth = st.slider(
            "Щорічна зміна доходу, %",
            min_value=-20.0,
            max_value=30.0,
            value=5.0,
            step=0.5
        )

    with fc2:
        q_annual_change = st.slider(
            "Щорічна зміна частки ЗВ, в. п.",
            min_value=-2.0,
            max_value=2.0,
            value=-0.2,
            step=0.1
        )

    with fc3:
        pv_growth = st.slider(
            "Щорічна зміна постійних витрат, %",
            min_value=-10.0,
            max_value=20.0,
            value=3.0,
            step=0.5
        )

    projection = []

    D = r2025["Дохід"]
    q = r2025["Частка ЗВ"] / 100
    PV = r2025["Постійні витрати"]

    base_result = calculate_cvp(
        D,
        D * q,
        PV
    )

    projection.append({
        "Рік": 2025,
        **base_result
    })

    for year in range(2026, 2031):

        D = D * (
            1 + revenue_growth / 100
        )

        q = q + q_annual_change / 100

        PV = PV * (
            1 + pv_growth / 100
        )

        q = max(
            0.001,
            min(q, 0.999)
        )

        ZV = D * q

        result = calculate_cvp(
            D,
            ZV,
            PV
        )

        projection.append({
            "Рік": year,
            **result
        })


    forecast = pd.DataFrame(projection)

    forecast["Зона"] = forecast.apply(
        lambda x: financial_zone(
            x["EBIT"],
            x["ЗФС"]
        ),
        axis=1
    )

    forecast_display = forecast[
        [
            "Рік",
            "Дохід",
            "Змінні витрати",
            "Частка ЗВ",
            "Кмд",
            "Постійні витрати",
            "EBIT",
            "Точка беззбитковості",
            "ЗФС",
            "ЗФС, %",
            "Зона"
        ]
    ].copy()

    st.subheader("Результати проєкції")

    st.dataframe(
        forecast_display.round(2),
        use_container_width=True,
        hide_index=True
    )

    # -----------------------------------------------------
    # ГРАФІК 1
    # -----------------------------------------------------

    st.subheader(
        "Динаміка доходу та точки беззбитковості"
    )

    forecast_long = forecast[
        [
            "Рік",
            "Дохід",
            "Точка беззбитковості"
        ]
    ].melt(
        id_vars="Рік",
        var_name="Показник",
        value_name="тис. грн"
    )

    fig_forecast = px.line(
        forecast_long,
        x="Рік",
        y="тис. грн",
        color="Показник",
        markers=True
    )

    fig_forecast.update_layout(
        legend_title_text="",
        xaxis_title="",
        yaxis_title="тис. грн"
    )

    st.plotly_chart(
        fig_forecast,
        use_container_width=True
    )

    # -----------------------------------------------------
    # ГРАФІК 2
    # -----------------------------------------------------

    st.subheader("Динаміка EBIT")

    fig_ebit = px.bar(
        forecast,
        x="Рік",
        y="EBIT"
    )

    fig_ebit.update_layout(
        xaxis_title="",
        yaxis_title="EBIT, тис. грн"
    )

    st.plotly_chart(
        fig_ebit,
        use_container_width=True
    )

    # -----------------------------------------------------
    # ГРАФІК 3
    # -----------------------------------------------------

    st.subheader(
        "Динаміка запасу фінансової стійкості"
    )

    fig_zfs = px.line(
        forecast,
        x="Рік",
        y="ЗФС, %",
        markers=True
    )

    fig_zfs.update_layout(
        xaxis_title="",
        yaxis_title="ЗФС, %"
    )

    st.plotly_chart(
        fig_zfs,
        use_container_width=True
    )

    # -----------------------------------------------------
    # ГРАФІК 4
    # -----------------------------------------------------

    st.subheader(
        "Динаміка коефіцієнта маржинального доходу"
    )

    fig_kmd = px.line(
        forecast,
        x="Рік",
        y="Кмд",
        markers=True
    )

    fig_kmd.update_layout(
        xaxis_title="",
        yaxis_title="Кмд, %"
    )

    st.plotly_chart(
        fig_kmd,
        use_container_width=True
    )

    # -----------------------------------------------------
    # ГРАФІК 5 — EBIT ТА ТОЧКА БЕЗЗБИТКОВОСТІ
    # -----------------------------------------------------

    st.subheader(
        "Співвідношення доходу і критичного рівня діяльності"
    )

    fig_area = go.Figure()

    fig_area.add_trace(
        go.Scatter(
            x=forecast["Рік"],
            y=forecast["Дохід"],
            mode="lines+markers",
            name="Дохід"
        )
    )

    fig_area.add_trace(
        go.Scatter(
            x=forecast["Рік"],
            y=forecast["Точка беззбитковості"],
            mode="lines+markers",
            name="Точка беззбитковості"
        )
    )

    fig_area.update_layout(
        xaxis_title="",
        yaxis_title="тис. грн",
        legend_title_text=""
    )

    st.plotly_chart(
        fig_area,
        use_container_width=True
    )

    # -----------------------------------------------------
    # ЕКСПОРТ CSV
    # -----------------------------------------------------

    csv = forecast_display.to_csv(
        index=False
    ).encode("utf-8-sig")

    st.download_button(
        label="Завантажити результати проєкції CSV",
        data=csv,
        file_name="solutech_projection_2026_2030.csv",
        mime="text/csv"
    )


# =========================================================
# МЕТОДИЧНІ ПРИПУЩЕННЯ
# =========================================================

with st.expander(
    "Методичні припущення та обмеження моделі"
):

    st.write(
        "Для агрегованого CVP-аналізу собівартість "
        "реалізації використовується як змінна складова "
        "витрат, а інші операційні витрати — як "
        "умовно-постійна складова."
    )

    st.write(
        "Точка беззбитковості визначається у вартісному "
        "вираженні."
    )

    st.write(
        "Зміна частки змінних витрат у сценарному "
        "аналізі задається у відсоткових пунктах."
    )

    st.write(
        "Сценарна проєкція на 2026–2030 роки не є "
        "статистичним прогнозом часових рядів. "
        "Вона показує можливу траєкторію показників "
        "за заданих користувачем припущень."
    )

    st.write(
        "За наявності більшого масиву історичних даних "
        "інструментарій може бути розширений методами "
        "регресійного аналізу та прогнозування часових рядів."
    )
