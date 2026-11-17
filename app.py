"""ТОВ «СОЛЮТЕХ» | CVP, сценарії S0–S4, факторний аналіз, проєкція.
Запуск: streamlit run app.py. Грошові показники — тис. грн.
"""
import numpy as np
import pandas as pd
import plotly.graph_objects as go

# 1. Вихідні дані та розрахункова модель (без округлення проміжних величин)
HISTORICAL = {2024: (28137.20, 15884.80, 2640.60),
              2025: (79654.10, 76408.10, 2323.90)}
D0, ZV0, PV0 = HISTORICAL[2025]
Q0 = ZV0 / D0
SCENARIOS = {
    'S0': ('Базовий', 0., 0., 0.),
    'S1': ('Підвищення маржинальності', 0., -0.5, 0.),
    'S2': ('Оптимізація операційних витрат', 0., 0., -10.),
    'S3': ('Комплексне підвищення економічної стійкості', 10., -0.5, -5.),
    'S4': ('Стресовий', -15., 0.5, 10.),
}
COLORS = {'S0':'#64748B','S1':'#147D85','S2':'#4676B5','S3':'#176B49','S4':'#B24444','USER':'#8055A5'}
POS, NEG, INK, GRID = '#147D85', '#B24444', '#24364B', '#E3E9EF'
MONEY = ['Дохід','Змінні витрати','Постійні витрати','Маржинальний дохід','EBIT','Точка беззбитковості','ЗФС','Зміна EBIT']
PERCENT = ['Частка ЗВ','Кмд','ЗФС, %','Операційна рентабельність']

def calculate_cvp(D, ZV, PV):
    """Зберігає назви показників початкового коду. За Кмд ≤ 0 ТБ не існує (окрім виродженого випадку нульових ПВ)."""
    if not np.isfinite([D,ZV,PV]).all() or D <= 0 or ZV < 0 or PV < 0:
        raise ValueError('Дохід має бути додатним, витрати — невід’ємними, параметри — скінченними.')
    MD = D - ZV
    q = ZV / D
    k = MD / D
    EBIT = MD - PV
    TB = PV / k if k > 1e-12 else np.nan
    ZFS = D - TB if np.isfinite(TB) else np.nan
    return {'Дохід':D, 'Змінні витрати':ZV, 'Частка ЗВ':100*q,
            'Постійні витрати':PV, 'Маржинальний дохід':MD, 'Кмд':100*k,
            'EBIT':EBIT, 'Точка беззбитковості':TB, 'ЗФС':ZFS,
            'ЗФС, %':100*ZFS/D, 'Резерв ЗВ, в. п.':100*(1-PV/D-q),
            'Операційна рентабельність':100*EBIT/D,
            'Зміна EBIT':EBIT-(D0-ZV0-PV0),
            'Зона':financial_zone(EBIT, 100*k)}

def financial_zone(ebit, k_pct):
    if abs(ebit) < 1e-8:
        return 'Беззбитковість'
    if k_pct <= 0:
        return 'Збиток: Кмд ≤ 0'
    return 'Прибуткова зона' if ebit > 0 else 'Збиткова зона'

def calculate_scenario(d=0., q_pp=0., f=0.):
    """d, f — зміна у %, q_pp — зміна у відсоткових пунктах до 2025 р."""
    D = D0*(1+d/100)
    q = Q0+q_pp/100
    PV = PV0*(1+f/100)
    if q < 0:
        raise ValueError('Частка змінних витрат не може бути від’ємною.')
    return calculate_cvp(D, D*q, PV)

def history_table():
    return pd.DataFrame([{'Рік':y,**calculate_cvp(*vals)} for y,vals in HISTORICAL.items()])

def scenario_table():
    return pd.DataFrame([{'Код':c,'Сценарій':name,'ΔД, %':d,'ΔЗВ, в. п.':q,'ΔПВ, %':f,
                          **calculate_scenario(d,q,f)} for c,(name,d,q,f) in SCENARIOS.items()])

def factor_bridge(start, end):
    """Ланцюгові підстановки: Д → Кмд → ПВ; взаємодія Д і Кмд належить другому чиннику."""
    d0,d1=start['Дохід'],end['Дохід']
    k0,k1=start['Кмд']/100,end['Кмд']/100
    p0,p1=start['Постійні витрати'],end['Постійні витрати']
    values=[start['EBIT'],(d1-d0)*k0,d1*(k1-k0),p0-p1,end['EBIT']]
    assert np.isclose(sum(values[:4]),values[4])
    return values

def sensitivity_grid(f, d_axis, q_axis):
    d_axis,q_axis=np.asarray(d_axis,float),np.asarray(q_axis,float)
    D=D0*(1+d_axis[None,:]/100)
    q=Q0+q_axis[:,None]/100
    PV=PV0*(1+f/100)
    z=np.where((D>0)&(q>=0)&(PV>=0),D*(1-q)-PV,np.nan)
    return pd.DataFrame(z,index=pd.Index(q_axis,name='ΔЗВ, в. п.'),columns=pd.Index(d_axis,name='ΔД, %'))

def projection(code, d, q_pp, f, growth=0., annual_q=0., annual_f=0.):
    """Одноразовий сценарний перехід у 2026 р.; з 2027 р. окремі щорічні припущення.
    Не обрізає q до 99,9%: при q ≥ 100% маржинальність недодатна; ТБ не визначається.
    """
    first=calculate_scenario(d,q_pp,f)
    rows=[{'Рік':2025,'Код':code,**calculate_cvp(D0,ZV0,PV0)}]
    D, q, PV=first['Дохід'],first['Частка ЗВ']/100,first['Постійні витрати']
    for year in range(2026,2031):
        if year>2026:
            D*=1+growth/100
            q+=annual_q/100
            PV*=1+annual_f/100
        if q<0:
            raise ValueError(f'{year}: від’ємна частка ЗВ. Змініть щорічні припущення.')
        rows.append({'Рік':year,'Код':code,**calculate_cvp(D,D*q,PV)})
    return pd.DataFrame(rows)

def self_test():
    t=scenario_table().set_index('Код')
    assert np.allclose(t['EBIT'],[922.1,1320.3705,1154.49,1800.99255,-135.719925])
    assert np.allclose(t['ЗФС, %'],100*t['ЗФС']/t['Дохід'])
    assert np.allclose(t['Резерв ЗВ, в. п.'],100*t['EBIT']/t['Дохід'])
    assert np.allclose(t['Точка беззбитковості']*t['Кмд']/100,t['Постійні витрати'])
    assert np.isclose(sensitivity_grid(-5,[10],[-.5]).iloc[0,0],t.loc['S3','EBIT'])
    factor_bridge(t.loc['S0'],t.loc['S3'])
    factor_bridge(calculate_cvp(*HISTORICAL[2024]),t.loc['S0'])
    for c,(_,d,q,f) in SCENARIOS.items():
        p=projection(c,d,q,f)
        assert np.isclose(p.loc[p['Рік']==2026,'EBIT'].iloc[0],t.loc[c,'EBIT'])
        assert np.allclose(p.loc[p['Рік']>=2026,'EBIT'],t.loc[c,'EBIT'])
    loss=calculate_scenario(0,5,0)
    assert loss['EBIT']<0 and np.isnan(loss['Точка беззбитковості'])
    assert np.isnan(projection('USER',0,5,0)['Точка беззбитковості'].iloc[-1])
    adverse=projection('USER',0,0,0,annual_q=2)
    assert adverse.iloc[-1]['Частка ЗВ']>100 and adverse.iloc[-1]['EBIT']<0
    assert np.isnan(adverse.iloc[-1]['ЗФС, %'])
    return t

# 2. Узгоджений візуальний стиль

def fmt(v,n=2):
    if pd.isna(v): return 'н/д'
    return f'{v:,.{n}f}'.replace(',',' ').replace('.',',').replace('-','−')

def theme(fig,title,xtitle='',ytitle='',height=420):
    fig.update_layout(template='plotly_white',title=dict(text=title,x=.015,font=dict(size=20)),
        height=height,font=dict(family='Arial',size=13,color=INK),
        margin=dict(l=65,r=40,t=70,b=80),legend=dict(orientation='h',y=-.19,x=0),
        hoverlabel=dict(font_size=13),paper_bgcolor='white',plot_bgcolor='white')
    fig.update_xaxes(title_text=xtitle,gridcolor=GRID,zerolinecolor=INK,automargin=True)
    fig.update_yaxes(title_text=ytitle,gridcolor=GRID,zerolinecolor=INK,automargin=True)
    return fig

def bar_compare(t, col, title, unit):
    codes=t['Код'].tolist(); vals=t[col].tolist()
    fig=go.Figure(go.Bar(x=vals,y=codes,orientation='h',marker_color=[COLORS.get(c,POS) for c in codes],
        text=[fmt(v) for v in vals],textposition='outside',cliponaxis=False,
        customdata=t['Сценарій'],hovertemplate='%{y} · %{customdata}<br>%{x:,.2f} '+unit+'<extra></extra>'))
    fig.update_yaxes(autorange='reversed'); fig.add_vline(x=0,line_color=INK,line_width=1)
    valid=[v for v in vals if np.isfinite(v)]
    if valid:
        span=max(max(valid)-min(valid),max(abs(v) for v in valid),1)
        fig.update_xaxes(range=[min(0,min(valid))-span*.20,max(0,max(valid))+span*.25])
    return theme(fig,title,unit,height=360)

def revenue_bep_chart(t, label='Код', title='Дохід і точка беззбитковості'):
    labels=t[label].astype(str).tolist(); fig=go.Figure()
    for (_,row),lab in zip(t.iterrows(),labels):
        if np.isfinite(row['Точка беззбитковості']):
            fig.add_trace(go.Scatter(x=[row['Точка беззбитковості'],row['Дохід']],y=[lab,lab],mode='lines',
                line=dict(color=POS if row['EBIT']>=0 else NEG,width=4),showlegend=False,hoverinfo='skip'))
    for col,color,symbol in [('Дохід','#24364B','circle'),('Точка беззбитковості','#B24444','diamond-open')]:
        fig.add_trace(go.Scatter(x=t[col],y=labels,name=col,mode='markers',marker=dict(color=color,symbol=symbol,size=12,line=dict(width=1.4)),hovertemplate='%{y}<br>%{x:,.2f} тис. грн<extra>%{fullData.name}</extra>'))
    fig.update_yaxes(autorange='reversed',categoryorder='array',categoryarray=labels)
    return theme(fig,title,'Тис. грн',height=365)

def waterfall_chart(values,start_label,end_label,title):
    fig=go.Figure(go.Waterfall(x=[start_label,'Дохід','Маржинальність','Постійні витрати',end_label],
        measure=['absolute','relative','relative','relative','total'],y=values[:4]+[0],
        text=[fmt(values[0])]+[('+' if v>0 else '')+fmt(v) for v in values[1:4]]+[fmt(values[4])],
        textposition='outside',cliponaxis=False,connector=dict(line=dict(color='#A2AEBB',dash='dot')),
        increasing=dict(marker=dict(color=POS)),decreasing=dict(marker=dict(color=NEG)),totals=dict(marker=dict(color='#4676B5'))))
    return theme(fig,title,ytitle='Тис. грн',height=460)

def break_even_chart(row):
    D,PV,q=row['Дохід'],row['Постійні витрати'],row['Частка ЗВ']/100
    tb=row['Точка беззбитковості']; xmax=max(D,tb if np.isfinite(tb) else 0)*1.12
    x=np.linspace(0,xmax,200); cost=PV+x*q
    fig=go.Figure([go.Scatter(x=x,y=x,name='Дохід',line=dict(color=POS,width=3)),
                   go.Scatter(x=x,y=cost,name='Сукупні витрати',line=dict(color=NEG,width=3))])
    if np.isfinite(tb):
        fig.add_trace(go.Scatter(x=[tb],y=[tb],mode='markers',name='Точка беззбитковості',marker=dict(size=13,color=INK,symbol='diamond')))
    fig.add_vline(x=D,line_dash='dot',line_color=INK,annotation_text='Сценарний дохід')
    return theme(fig,'Графік беззбитковості','Чистий дохід, тис. грн','Дохід / витрати, тис. грн',470)

def heatmap_chart(f,d,q):
    dx=np.linspace(min(-50,d-5),max(30,d+5),161); qx=np.linspace(min(-2,q-.4),max(3,q+.4),151)
    grid=sensitivity_grid(f,dx,qx); z=grid.to_numpy(); lim=max(float(np.nanmax(np.abs(z))),1)
    fig=go.Figure(go.Heatmap(x=dx,y=qx,z=z,zmin=-lim,zmax=lim,colorscale=[[0,'#A62B36'],[.5,'#F9FAFC'],[1,'#147D85']],
        colorbar=dict(title='Тис. грн'),hovertemplate='Δ доходу: %{x:.1f}%<br>Δ частки ЗВ: %{y:.2f} в. п.<br>EBIT: %{z:,.2f} тис. грн<extra></extra>'))
    boundary=100*(1-Q0-PV0*(1+f/100)/(D0*(1+dx/100)))
    mask=(boundary>=qx.min())&(boundary<=qx.max())
    fig.add_trace(go.Scatter(x=dx[mask],y=boundary[mask],mode='lines',name='EBIT = 0',line=dict(color=INK,width=3)))
    fig.add_trace(go.Scatter(x=[d],y=[q],mode='markers',name='Обраний сценарій',marker=dict(symbol='star',size=16,color='#F0BE41',line=dict(color=INK,width=1.5))))
    return theme(fig,f'Чутливість EBIT | Δ ПВ = {fmt(f,1)} %','Зміна доходу, %','Зміна частки ЗВ, в. п.',550),grid

def projection_chart(p,col,title,unit):
    fig=go.Figure()
    for c,g in p.groupby('Код',sort=False):
        fig.add_trace(go.Scatter(x=g['Рік'],y=g[col],mode='lines+markers',name=c,line=dict(color=COLORS.get(c,POS),width=3 if c=='S3' else 2,dash='dash' if c=='S4' else 'solid'),connectgaps=False,hovertemplate='%{x}<br>%{y:,.2f} '+unit+'<extra>'+c+'</extra>'))
    fig.update_xaxes(tickmode='array',tickvals=list(range(2025,2031)))
    fig.add_vline(x=2025.5,line_dash='dot',line_color='#94A3B8')
    if col in ['EBIT','ЗФС, %','Кмд']: fig.add_hline(y=0,line_color=INK,line_width=1)
    return theme(fig,title,'Рік',unit,435)

def csv_bytes(df,index=False): return df.to_csv(index=index,float_format='%.8f').encode('utf-8-sig')

# 3. Інтерфейс: збережено чотири вихідні напрями, додано окремий аналіз чутливості

def main():
    import streamlit as st
    st.set_page_config(page_title='СОЛЮТЕХ | Економічна стійкість',page_icon='📊',layout='wide')
    st.title('Економічна стійкість ТОВ «СОЛЮТЕХ»')
    st.caption('Фактичні показники 2024–2025 · сценарії S0–S4 · проєкція 2026–2030 · тис. грн')
    self_test()
    history=history_table(); table=scenario_table(); base=calculate_cvp(D0,ZV0,PV0)
    with st.sidebar:
        st.header('Сценарні параметри')
        selected=st.selectbox('Оберіть сценарій',list(SCENARIOS),index=3,format_func=lambda c:f'{c} — {SCENARIOS[c][0]}')
        _,d0,q0,f0=SCENARIOS[selected]
        manual=st.checkbox('Власні параметри',value=False)
        if manual:
            d=st.slider('Зміна чистого доходу, %',-70.,50.,d0,.5,key=f'd_{selected}')
            q=st.slider('Зміна частки ЗВ, в. п.',-5.,6.,q0,.1,key=f'q_{selected}')
            f=st.slider('Зміна ПВ, %',-50.,50.,f0,1.,key=f'f_{selected}')
        else: d,q,f=d0,q0,f0
        code='USER' if manual else selected
        st.caption(f'Базова частка ЗВ — {fmt(Q0*100,4)} %. Зміна −0,5 в. п. означає віднімання 0,5 відсоткового пункту.')
        st.divider(); st.markdown('**База 2025 року**')
        st.write(f'Дохід: {fmt(D0)} тис. грн'); st.write(f'ЗВ: {fmt(ZV0)} тис. грн'); st.write(f'ПВ: {fmt(PV0)} тис. грн')
    current=calculate_scenario(d,q,f)
    compare=table.copy()
    if manual:
        compare=pd.concat([compare,pd.DataFrame([{'Код':'USER','Сценарій':'Власний варіант','ΔД, %':d,'ΔЗВ, в. п.':q,'ΔПВ, %':f,**current}])],ignore_index=True)
    st.subheader(f'{code} · '+('Власний експеримент' if manual else SCENARIOS[selected][0]))
    c=st.columns(4)
    c[0].metric('EBIT, тис. грн',fmt(current['EBIT']),fmt(current['Зміна EBIT']))
    c[1].metric('Запас стійкості, %',fmt(current['ЗФС, %']),fmt(current['ЗФС, %']-base['ЗФС, %'])+' в. п.' if np.isfinite(current['ЗФС, %']) else None)
    c[2].metric('Точка беззбитковості, тис. грн',fmt(current['Точка беззбитковості']),fmt(current['Точка беззбитковості']-base['Точка беззбитковості']) if np.isfinite(current['Точка беззбитковості']) else None,delta_color='inverse')
    c[3].metric('Резерв частки ЗВ, в. п.',fmt(current['Резерв ЗВ, в. п.']))
    if current['Кмд']<=0: st.error('Кмд недодатний. За цих умов стандартна точка беззбитковості не визначається; результат не слід штучно коригувати.')
    elif current['EBIT']<-1e-8: st.warning('Збиткова зона за умовною CVP-моделлю.')
    elif current['EBIT']>1e-8: st.success('Прибуткова зона за умовною CVP-моделлю. Це не гарантія платоспроможності.')
    else: st.info('Межа беззбитковості.')
    t1,t2,t3,t4,t5=st.tabs(['Фактичні показники','Факторний аналіз','Сценарний аналіз','Аналіз чутливості','Проєкція 2026–2030'])
    with t1:
        st.header('CVP-аналіз за 2024–2025 роки')
        st.dataframe(history.round(2),hide_index=True,use_container_width=True)
        st.plotly_chart(revenue_bep_chart(history,'Рік','Чистий дохід і точка беззбитковості за роками'),use_container_width=True,key='history_bep')
        fig=go.Figure()
        for col,color in [('Кмд',POS),('ЗФС, %','#4676B5')]:
            fig.add_bar(x=history['Рік'].astype(str),y=history[col],name=col,marker_color=color,text=[fmt(v) for v in history[col]],textposition='outside',cliponaxis=False)
        fig.update_layout(barmode='group'); fig.update_yaxes(range=[0,90])
        st.plotly_chart(theme(fig,'Маржинальність та запас фінансової стійкості',ytitle='%'),use_container_width=True,key='history_pct')
        st.download_button('Фактичні показники CSV',csv_bytes(history),'history_2024_2025.csv','text/csv')
        with st.expander('Зв’язок із кластерним аналізом (3.1)',expanded=True):
            benchmark=pd.DataFrame({'Показник':['Коефіцієнт автономії','Абсолютна ліквідність','Валова рентабельність, %','Чиста рентабельність, %','Оборотність активів'],
                'СОЛЮТЕХ, 2025':[.351,.194,4.08,.99,3.128],'К2, середнє (10 підприємств)':[.273,.308,12.79,3.80,3.460]})
            st.dataframe(benchmark,hide_index=True,use_container_width=True)
            st.caption('Джерело: таблиця 3.3 кластерного аналізу. Значення округлені як у дисертації. Порівняльні орієнтири, не нормативи.')
            st.write('Найбільше відставання — за валовою та чистою рентабельністю. Тому S1 спрямовано на маржинальність, S2 — на операційні витрати, S3 — на їх поєднання зі зростанням доходу. CVP не прогнозує ліквідність, автономію або кластерну належність.')
    with t2:
        st.header('Факторний аналіз методом ланцюгових підстановок')
        pairs=[('2024 → 2025',calculate_cvp(*HISTORICAL[2024]),base,'2024','2025'),('S0 → S3',base,calculate_scenario(10,-.5,-5),'S0','S3'),('S0 → поточний',base,current,'S0',code)]
        for label,start,end,l0,l1 in pairs:
            with st.expander(label,expanded=(label=='S0 → S3')):
                vals=factor_bridge(start,end)
                st.plotly_chart(waterfall_chart(vals,l0,l1,f'Факторне розкладання: {label}'),use_container_width=True,key=f'factor_{label}')
                factors=pd.DataFrame({'Чинник':['Зміна доходу','Зміна Кмд','Зміна ПВ','Загальна зміна EBIT'],'Вплив, тис. грн':vals[1:4]+[vals[-1]-vals[0]]})
                st.dataframe(factors.round(2),hide_index=True,use_container_width=True)
                st.download_button('Завантажити розклад CSV',csv_bytes(factors),f'factor_{l0}_{l1}.csv','text/csv',key=f'factor_dl_{label}')
        st.caption('Порядок: дохід → Кмд → ПВ. Спільний ефект зміни доходу й Кмд віднесено до другого фактора.')
    with t3:
        st.header('Порівняння погоджених сценаріїв S0–S4')
        st.caption('S1–S3 — управлінські заходи з 3.2; S0 — база; S4 — стрес-тест. USER — додатковий експеримент.')
        st.dataframe(compare[['Код','Сценарій','ΔД, %','ΔЗВ, в. п.','ΔПВ, %']].round(2),hide_index=True,use_container_width=True)
        l,r=st.columns(2)
        with l: st.plotly_chart(bar_compare(compare,'EBIT','Операційний результат','Тис. грн'),use_container_width=True,key='scenario_ebit')
        with r: st.plotly_chart(bar_compare(compare,'ЗФС, %','Запас фінансової стійкості','%'),use_container_width=True,key='scenario_safety')
        st.plotly_chart(revenue_bep_chart(compare),use_container_width=True,key='scenario_bep')
        st.dataframe(compare[['Код','Сценарій','Дохід','Маржинальний дохід','Кмд','EBIT','Точка беззбитковості','ЗФС, %','Резерв ЗВ, в. п.','Зона']].round(2),hide_index=True,use_container_width=True)
        st.download_button('Повні результати сценаріїв CSV',csv_bytes(compare),'scenarios.csv','text/csv')
        st.subheader('Детальний результат обраного варіанта')
        st.plotly_chart(break_even_chart(current),use_container_width=True,key='current_bep')
        detail=pd.DataFrame({'Показник':list(current),'База 2025':[base[k] for k in current],'Сценарій':list(current.values())})
        for col in ['База 2025','Сценарій']: detail[col]=detail[col].map(lambda v:fmt(v) if isinstance(v,(int,float,np.number)) else str(v))
        st.dataframe(detail,hide_index=True,use_container_width=True)
        st.download_button('Обраний сценарій CSV',csv_bytes(pd.DataFrame([{'Код':code,**current}])),'current.csv','text/csv')
    with t4:
        st.header('Двофакторний аналіз чутливості')
        st.write('На карті змінюються дохід і частка змінних витрат. Постійні витрати зафіксовано на рівні обраного сценарію.')
        fig,grid=heatmap_chart(f,d,q)
        st.plotly_chart(fig,use_container_width=True,key='heatmap')
        st.caption('Бірюзова зона — додатний результат, червона — збиток; темна лінія — межа беззбитковості. Зірка — обраний сценарій.')
        stress=calculate_scenario(-10,-.5,-5)
        st.write(f'Перевірка S3: за доходу −10 % від бази, ΔЗВ −0,5 в. п. та ΔПВ −5 % EBIT = {fmt(stress["EBIT"])} тис. грн; ЗФС = {fmt(stress["ЗФС, %"])} %.')
        st.download_button('Матриця чутливості CSV',csv_bytes(grid,True),'sensitivity.csv','text/csv')
    with t5:
        st.header('Умовна сценарна проєкція на 2026–2030 роки')
        st.info('У 2026 році застосовуються одноразові сценарні зміни S0–S4 до 2025 року. З 2027 року діють окремі щорічні припущення. Це не статистичний прогноз і не фактичні дані 2026 року.')
        g1,g2,g3=st.columns(3)
        with g1: growth=st.slider('Щорічна зміна доходу з 2027 р., %',-20.,30.,0.,.5)
        with g2: annual_q=st.slider('Щорічна зміна частки ЗВ з 2027 р., в. п.',-2.,2.,0.,.1)
        with g3: annual_f=st.slider('Щорічна зміна ПВ з 2027 р., %',-20.,30.,0.,.5)
        st.caption('Нульові щорічні зміни означають утримання досягнутих у 2026 р. параметрів. Ненульові значення — додаткові припущення користувача, однакові для вибраних сценаріїв.')
        chosen=st.multiselect('Сценарії для порівняння',compare['Код'].tolist(),default=list(SCENARIOS))
        if chosen:
            frames=[]
            for _,row in compare[compare['Код'].isin(chosen)].iterrows():
                try: frames.append(projection(row['Код'],row['ΔД, %'],row['ΔЗВ, в. п.'],row['ΔПВ, %'],growth,annual_q,annual_f))
                except ValueError as exc: st.warning(f'{row["Код"]}: {exc}')
            if frames:
                p=pd.concat(frames,ignore_index=True)
                for col,title,unit in [('EBIT','Операційний результат за сценаріями','Тис. грн'),('ЗФС, %','Запас фінансової стійкості','%'),('Кмд','Коефіцієнт маржинального доходу','%')]:
                    st.plotly_chart(projection_chart(p,col,title,unit),use_container_width=True,key=f'proj_{col}')
                display_code=st.selectbox('Деталізація доходу та точки беззбитковості',p['Код'].unique().tolist(),index=list(p['Код'].unique()).index(code) if code in p['Код'].unique() else 0)
                g=p[p['Код']==display_code]; fig=go.Figure()
                for col,color,dash in [('Дохід',INK,'solid'),('Точка беззбитковості',NEG,'dot')]:
                    fig.add_trace(go.Scatter(x=g['Рік'],y=g[col],mode='lines+markers',name=col,line=dict(color=color,dash=dash,width=3),connectgaps=False,hovertemplate='%{x}<br>%{y:,.2f} тис. грн<extra>%{fullData.name}</extra>'))
                fig.update_xaxes(tickmode='array',tickvals=list(range(2025,2031))); fig.add_vline(x=2025.5,line_dash='dot',line_color='#94A3B8')
                st.plotly_chart(theme(fig,f'{display_code} | Дохід і точка беззбитковості','Рік','Тис. грн',445),use_container_width=True,key='proj_bep')
                if (p['Кмд']<=0).any(): st.warning('Для окремих років Кмд ≤ 0. ТБ і ЗФС не визначаються; пропуски на графіку залишено навмисно.')
                st.dataframe(p.round(2),hide_index=True,use_container_width=True)
                st.download_button('Проєкція 2026–2030 CSV',csv_bytes(p),'projection_2026_2030.csv','text/csv')
        else: st.info('Оберіть принаймні один сценарій.')
    with st.expander('Методика, формули й обмеження моделі'):
        st.markdown('**Припущення.** Собівартість реалізації є умовно-змінними витратами, інші операційні витрати — умовно-постійними. Коефіцієнти не округлюються під час розрахунків. EBIT тут означає умовний операційний результат CVP, а не чистий прибуток чи повний бухгалтерський EBIT. Сценарії не мають встановлених імовірностей. Ліквідність, автономія та кластерна належність без прогнозних балансових даних не визначаються.')
        st.latex(r'MD=D-ZV,\quad k=MD/D,\quad EBIT=MD-PV')
        st.latex(r'TB=PV/k,\quad ZFS= D-TB,\quad ZFS_{\%}=100(D-TB)/D')
        st.latex(r'R_q=100(1-PV/D-ZV/D)')
        st.caption('Резерв частки змінних витрат Rq — у відсоткових пунктах. Від’ємне значення означає необхідне зменшення частки ЗВ до межі беззбитковості.')

if __name__=='__main__':
    import sys
    if '--test' in sys.argv:
        print(self_test()[['EBIT','Точка беззбитковості','ЗФС, %','Резерв ЗВ, в. п.']].round(2).to_string())
    else:
        main()
