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

st.title("Оцінювання фінансово-економічної стійкості ТОВ «СОЛЮТЕХ»")

st.caption(
    "CVP-аналіз, факторний аналіз, сценарне моделювання "
    "та п'ятирічна сценарна проєкція"
)


# =========================================================
# ФУНКЦІЇ
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
    """Визначення положення підприємства відносно точки беззбитковості."""

    if np.isnan(ebit) or np.isnan(zfs):
        return "Неможливо визначити"

    if abs(ebit) < 0.01:
        return "Точка беззбитковості"

    if ebit > 0 and zfs > 0:
        return "Прибуткова зона"

    return "Збиткова зона"


def format_value(value):
    if pd.isna(value):
        return "—"
    return f"{value:,.2f}".replace(",", " ").replace(".", ",")


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
# РОЗРАХУНОК ІСТОРИЧНИХ ПОКАЗНИКІВ
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


# =========================================================
# ВКЛАДКИ
# =========================================================

tab1, tab2, tab3, tab4 = st.tabs(
    [
        "Фактичні показники",
        "Факторний аналіз",
        "Сценарний аналіз",
        "Прогноз на 5 років"
    ]
)


# =========================================================
# TAB 1 — ФАКТИЧНІ ПОКАЗНИКИ
# =========================================================

with tab1:

    st.header("CVP-аналіз за 2024–2025 роки")

    st.markdown(
        """
        Для розрахунку використовується система:

        \[
        МД = Д - ЗВ
        \]

        \[
        Кмд = \\frac{МД}{Д}
        \]

        \[
        EBIT = Д - ЗВ - ПВ
        \]

        \[
        ТБ = \\frac{ПВ}{Кмд}
        \]

        \[
        ЗФС = Д - ТБ
        \]

        \[
        ЗФС\\% = \\frac{ЗФС}{Д} \\times 100
        \]
        """
    )

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

    # -----------------------------------------------------
    # Ключові зміни
    # -----------------------------------------------------

    r2024 = history[history["Рік"] == 2024].iloc[0]
    r2025 = history[history["Рік"] == 2025].iloc[0]

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Кмд 2024",
        f"{r2024['Кмд']:.2f} %"
    )

    col2.metric(
        "Кмд 2025",
        f"{r2025['Кмд']:.2f} %",
        f"{r2025['Кмд'] - r2024['Кмд']:.2f} в.п."
    )

    col3.metric(
        "ЗФС 2024",
        f"{r2024['ЗФС, %']:.2f} %"
    )

    col4.metric(
        "ЗФС 2025",
        f"{r2025['ЗФС, %']:.2f} %",
        f"{r2025['ЗФС, %'] - r2024['ЗФС, %']:.2f} в.п."
    )

    # -----------------------------------------------------
    # Графік 1
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
        color="Показник",
        text_auto=".2s"
    )

    fig.update_layout(
        xaxis=dict(
            tickmode="array",
            tickvals=[2024, 2025]
        ),
        legend_title_text=""
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    # -----------------------------------------------------
    # Графік 2
    # -----------------------------------------------------

    st.subheader("Зміна маржинальності та запасу стійкості")

    percentage_chart = history[
        ["Рік", "Кмд", "ЗФС, %"]
    ].melt(
        id_vars="Рік",
        var_name="Показник",
        value_name="%"
    )

    fig2 = px.line(
        percentage_chart,
        x="Рік",
        y="%",
        color="Показник",
        markers=True
    )

    fig2.update_layout(
        xaxis=dict(
            tickmode="array",
            tickvals=[2024, 2025]
        ),
        legend_title_text=""
    )

    st.plotly_chart(
        fig2,
        use_container_width=True
    )


# =========================================================
# TAB 2 — ФАКТОРНИЙ АНАЛІЗ
# =========================================================

with tab2:

    st.header("Факторний аналіз методом ланцюгових підстановок")

    D0 = r2024["Дохід"]
    K0 = r2024["Кмд"] / 100
    PV0 = r2024["Постійні витрати"]

    D1 = r2025["Дохід"]
    K1 = r2025["Кмд"] / 100
    PV1 = r2025["Постійні витрати"]

    # Базове значення
    EBIT0 = D0 * K0 - PV0

    # Підстановка доходу 2025
    EBIT_D = D1 * K0 - PV0

    # Підстановка Кмд 2025
    EBIT_DK = D1 * K1 - PV0

    # Підстановка ПВ 2025
    EBIT1 = D1 * K1 - PV1

    impact_D = EBIT_D - EBIT0
    impact_K = EBIT_DK - EBIT_D
    impact_PV = EBIT1 - EBIT_DK

    total_change = EBIT1 - EBIT0

    factor_df = pd.DataFrame({
        "Чинник": [
            "Зміна доходу",
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

    st.dataframe(
        factor_df.round(2),
        use_container_width=True,
        hide_index=True
    )

    st.markdown(
        f"""
        **Вплив збільшення доходу**

        \[
        \Delta EBIT_Д =
        {EBIT_D:.2f} -
        {EBIT0:.2f}
        =
        {impact_D:.2f}
        \]

        **Вплив зміни коефіцієнта маржинального доходу**

        \[
        \Delta EBIT_{{Кмд}} =
        {EBIT_DK:.2f} -
        {EBIT_D:.2f}
        =
        {impact_K:.2f}
        \]

        **Вплив зміни постійних витрат**

        \[
        \Delta EBIT_{{ПВ}} =
        {EBIT1:.2f} -
        {EBIT_DK:.2f}
        =
        {impact_PV:.2f}
        \]
        """
    )

    # -----------------------------------------------------
    # Waterfall
    # -----------------------------------------------------

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
                "Дохід",
                "Кмд",
                "Постійні витрати",
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
                f"{EBIT0:.1f}",
                f"{impact_D:+.1f}",
                f"{impact_K:+.1f}",
                f"{impact_PV:+.1f}",
                f"{EBIT1:.1f}"
            ],
            textposition="outside"
        )
    )

    fig_factor.update_layout(
        title="Факторне розкладання зміни EBIT",
        yaxis_title="тис. грн",
        showlegend=False
    )

    st.plotly_chart(
        fig_factor,
        use_container_width=True
    )

    st.info(
        "Позитивний вплив збільшення доходу був перекритий "
        "зниженням коефіцієнта маржинального доходу."
    )


# =========================================================
# TAB 3 — СЦЕНАРНИЙ АНАЛІЗ
# =========================================================

with tab3:

    st.header("Сценарний аналіз")

    st.write(
        "Базою є фактичні показники 2025 року. "
        "Змініть параметри та оцініть реакцію моделі."
    )

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
            "Зміна частки змінних витрат, в.п.",
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

    # -----------------------------------------------------
    # Нові параметри
    # -----------------------------------------------------

    D_s = r2025["Дохід"] * (
        1 + income_change / 100
    )

    q_base = r2025["Частка ЗВ"] / 100

    q_s = q_base + q_change_pp / 100

    PV_s = r2025["Постійні витрати"] * (
        1 + fixed_change / 100
    )

    if q_s <= 0 or q_s >= 1:

        st.error(
            "Частка змінних витрат повинна бути "
            "більшою за 0 % та меншою за 100 %."
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

        st.subheader("Результат сценарію")

        c1, c2, c3, c4 = st.columns(4)

        c1.metric(
            "EBIT",
            f"{scenario['EBIT']:,.2f} тис. грн"
        )

        c2.metric(
            "Точка беззбитковості",
            f"{scenario['Точка беззбитковості']:,.2f} тис. грн"
        )

        c3.metric(
            "ЗФС",
            f"{scenario['ЗФС, %']:.2f} %"
        )

        c4.metric(
            "Стан",
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

        fig_scenario = px.bar(
            comparison_long,
            x="Показник",
            y="тис. грн",
            color="Варіант",
            barmode="group"
        )

        fig_scenario.update_layout(
            legend_title_text=""
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
# TAB 4 — 5-РІЧНА СЦЕНАРНА ПРОЄКЦІЯ
# =========================================================

with tab4:

    st.header("Сценарна проєкція на 2026–2030 роки")

    st.warning(
        "Цей блок є сценарною проєкцією, а не статистичним прогнозом. "
        "Для побудови надійної часової прогнозної моделі двох "
        "повних років спостережень недостатньо."
    )

    st.write(
        "Прогноз формується від базових показників 2025 року. "
        "Для кожного наступного року задаються темп зростання доходу, "
        "щорічна зміна частки змінних витрат та темп зміни "
        "постійних витрат."
    )

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
            "Щорічна зміна частки ЗВ, в.п.",
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

    # -----------------------------------------------------
    # Формування прогнозу
    # -----------------------------------------------------

    projection = []

    D = r2025["Дохід"]
    q = r2025["Частка ЗВ"] / 100
    PV = r2025["Постійні витрати"]

    # Додаємо базовий 2025 рік
    projection.append({
        "Рік": 2025,
        **calculate_cvp(
            D,
            D * q,
            PV
        )
    })

    for year in range(2026, 2031):

        D = D * (
            1 + revenue_growth / 100
        )

        q = q + q_annual_change / 100

        PV = PV * (
            1 + pv_growth / 100
        )

        # Обмеження економічно допустимого діапазону
        q = max(0.001, min(q, 0.999))

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

    # -----------------------------------------------------
    # Таблиця прогнозу
    # -----------------------------------------------------

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

    st.dataframe(
        forecast_display.round(2),
        use_container_width=True,
        hide_index=True
    )

    # -----------------------------------------------------
    # ПРОГНОЗНИЙ ГРАФІК 1
    # -----------------------------------------------------

    st.subheader("Дохід та точка беззбитковості")

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
        legend_title_text=""
    )

    st.plotly_chart(
        fig_forecast,
        use_container_width=True
    )

    # -----------------------------------------------------
    # ПРОГНОЗНИЙ ГРАФІК 2
    # -----------------------------------------------------

    st.subheader("Прогноз EBIT")

    fig_ebit = px.bar(
        forecast,
        x="Рік",
        y="EBIT",
        text_auto=".2s"
    )

    fig_ebit.update_layout(
        yaxis_title="EBIT, тис. грн"
    )

    st.plotly_chart(
        fig_ebit,
        use_container_width=True
    )

    # -----------------------------------------------------
    # ПРОГНОЗНИЙ ГРАФІК 3
    # -----------------------------------------------------

    st.subheader("Динаміка запасу фінансової стійкості")

    fig_zfs = px.line(
        forecast,
        x="Рік",
        y="ЗФС, %",
        markers=True
    )

    fig_zfs.update_layout(
        yaxis_title="ЗФС, %"
    )

    st.plotly_chart(
        fig_zfs,
        use_container_width=True
    )

    # -----------------------------------------------------
    # ПРОГНОЗНИЙ ГРАФІК 4
    # -----------------------------------------------------

    st.subheader("Динаміка коефіцієнта маржинального доходу")

    fig_kmd = px.line(
        forecast,
        x="Рік",
        y="Кмд",
        markers=True
    )

    fig_kmd.update_layout(
        yaxis_title="Кмд, %"
    )

    st.plotly_chart(
        fig_kmd,
        use_container_width=True
    )

    # -----------------------------------------------------
    # ЗАВАНТАЖЕННЯ РЕЗУЛЬТАТУ
    # -----------------------------------------------------

    csv = forecast_display.to_csv(
        index=False
    ).encode("utf-8-sig")

    st.download_button(
        label="Завантажити результати прогнозу CSV",
        data=csv,
        file_name="solutech_forecast_2026_2030.csv",
        mime="text/csv"
    )


# =========================================================
# МЕТОДИЧНІ ПРИМІТКИ
# =========================================================

with st.expander("Методичні припущення моделі"):

    st.markdown(
        """
        1. Для агрегованого CVP-аналізу собівартість реалізації
        розглядається як змінна складова витрат.

        2. Інші операційні витрати використовуються як
        умовно-постійна складова.

        3. Точка беззбитковості розраховується у вартісному
        вираженні.

        4. Сценарна зміна частки змінних витрат задається
        у відсоткових пунктах.

        5. П'ятирічний блок є сценарною проєкцією, а не
        статистичним прогнозом часових рядів.

        6. За появи більшого масиву історичних даних модель
        може бути доповнена регресійним або часовим
        прогнозуванням.
        """
    )