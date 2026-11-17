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

# 2. Візуалізація: світле полотно, контрастні підписи, єдиний масштаб
# Явний стиль Plotly використовується незалежно від теми Streamlit.
INK, GRID = '#172B42', '#D9E1EA'
POS, NEG = '#006D77', '#AE2638'
COLORS = {'S0':'#536779','S1':'#006D77','S2':'#285CA8','S3':'#17653D','S4':'#AE2638','USER':'#7043A0'}
SHORT = {'S0':'Базовий','S1':'Маржинальність','S2':'Операційні витрати','S3':'Комплексний','S4':'Стресовий','USER':'Власний'}
PLOT_CONFIG = {'displaylogo': False, 'responsive': True, 'toImageButtonOptions': {'format':'png','scale':3}}

def fmt(v,n=2):
    if pd.isna(v): return 'н/д'
    return f'{v:,.{n}f}'.replace(',','\u202f').replace('.',',').replace('-','−')

def signed(v,n=2):
    return ('+' if v>0 else '')+fmt(v,n)

def cell_text_color(value, limit):
    # Обираємо колір тексту за відносною яскравістю фактичної заливки.
    if not np.isfinite(value): return INK
    t=min(abs(value)/limit,1.0)
    end=(158,32,53) if value<0 else (0,109,119)
    rgb=[(255*(1-t)+v*t)/255 for v in end]
    linear=[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in rgb]
    lum=sum(c*v for c,v in zip((.2126,.7152,.0722),linear))
    return '#101820' if (lum+.05)/(.0085+.05) >= 1.05/(lum+.05) else '#FFFFFF'

def theme(fig,title,xtitle='',ytitle='',height=420,left=90,bottom=100):
    fig.update_layout(template='plotly_white',title=dict(text=title,x=.02,xanchor='left',font=dict(size=21,color=INK)),
        height=height, autosize=True,font=dict(family='Arial, sans-serif',size=15,color=INK),
        margin=dict(l=left,r=65,t=78,b=bottom),legend=dict(orientation='h',y=-.21,x=0,font=dict(size=14,color=INK),bgcolor='rgba(255,255,255,0)'),
        hoverlabel=dict(bgcolor='white',font=dict(size=14,color=INK)),paper_bgcolor='#FFFFFF',plot_bgcolor='#FFFFFF',
        separators=', ',uniformtext=dict(minsize=13,mode='show'))
    fig.update_xaxes(title_text=xtitle,gridcolor=GRID,zerolinecolor=INK,automargin=True,tickfont=dict(size=14,color=INK),title_font=dict(size=15,color=INK),fixedrange=False)
    fig.update_yaxes(title_text=ytitle,gridcolor=GRID,zerolinecolor=INK,automargin=True,tickfont=dict(size=14,color=INK),title_font=dict(size=15,color=INK),fixedrange=False)
    return fig

def chart(st,fig,key):
    st.plotly_chart(fig,use_container_width=True,theme=None,config=PLOT_CONFIG,key=key)

def scenario_labels(codes):
    return [f'{c} · {SHORT.get(c,c)}' for c in codes]

def bar_compare(t,col,title,unit):
    codes=t['Код'].tolist(); labels=scenario_labels(codes); vals=t[col].to_numpy(float)
    fig=go.Figure(go.Bar(x=vals,y=labels,orientation='h',marker=dict(color=[NEG if np.isfinite(v) and v<0 else COLORS.get(c,POS) for c,v in zip(codes,vals)],line=dict(color='white',width=1)),
        text=[fmt(v)+(' %' if unit=='%' else '') if np.isfinite(v) else '' for v in vals],textposition='outside',textfont=dict(size=16,color=INK),cliponaxis=False,
        customdata=t['Сценарій'],hovertemplate='%{customdata}<br>%{x:,.2f} '+unit+'<extra></extra>'))
    finite=vals[np.isfinite(vals)]; lo=min(0,float(finite.min())) if len(finite) else 0; hi=max(0,float(finite.max())) if len(finite) else 1; span=max(hi-lo,1)
    fig.update_xaxes(range=[lo-.25*span,hi+.28*span],zeroline=False)
    fig.update_yaxes(autorange='reversed',categoryorder='array',categoryarray=labels,showgrid=False,ticks='outside',ticklen=5)
    fig.add_vline(x=0,line_color=INK,line_width=1.6)
    if len(vals) and np.isfinite(vals[0]) and vals[0]!=0:
        fig.add_vline(x=vals[0],line_color='#536779',line_dash='dash',line_width=1.5)
        fig.add_annotation(x=vals[0],y=1.025,yref='paper',text='База 2025',showarrow=False,xanchor='center',yanchor='bottom',bgcolor='white')
    for lab,v in zip(labels,vals):
        if not np.isfinite(v): fig.add_annotation(x=0,y=lab,text='Не визначається',showarrow=False,xanchor='left',xshift=8)
    return theme(fig,title,unit,height=max(370,72*len(labels)+130),left=185,bottom=65)

def revenue_bep_chart(t,label='Код',title='Дохід і точка беззбитковості'):
    labels=scenario_labels(t[label].tolist()) if label=='Код' else t[label].astype(str).tolist()
    fig=go.Figure()
    for col,color in [('Дохід','#285CA8'),('Точка беззбитковості','#AE2638')]:
        vals=t[col].to_numpy(float)/1000
        fig.add_bar(x=vals,y=labels,orientation='h',name=col,marker_color=color,
            text=[fmt(v,2) if np.isfinite(v) else '' for v in vals],textposition='outside',textfont=dict(size=14,color=INK),cliponaxis=False,
            customdata=t[col],hovertemplate='%{y}<br>%{customdata:,.2f} тис. грн<extra>%{fullData.name}</extra>')
    vals=np.concatenate([t['Дохід'].to_numpy(float),t['Точка беззбитковості'].to_numpy(float)])/1000
    hi=max(np.nanmax(vals),1); fig.update_layout(barmode='group',bargap=.28,bargroupgap=.13)
    fig.update_xaxes(range=[0,hi*1.25]); fig.update_yaxes(autorange='reversed',showgrid=False,categoryorder='array',categoryarray=labels,ticks='outside',ticklen=5)
    for lab,v in zip(labels,t['Точка беззбитковості']):
        if not np.isfinite(v): fig.add_annotation(x=0,y=lab,text='ТБ не визначається',showarrow=False,xanchor='left',yshift=-14,bgcolor='white')
    return theme(fig,title,'Млн грн',height=max(345,86*len(labels)+145),left=185 if label=='Код' else 90,bottom=105)

def waterfall_chart(values,start_label,end_label,title):
    labels=[f'{start_label}<br>EBIT','Зміна<br>доходу','Зміна<br>маржинальності','Зміна<br>постійних витрат',f'{end_label}<br>EBIT']
    fig=go.Figure(go.Waterfall(x=labels,measure=['absolute','relative','relative','relative','total'],y=values[:4]+[0],
        text=[fmt(values[0])]+[signed(v) for v in values[1:4]]+[fmt(values[4])],textposition='outside',textfont=dict(size=15,color=INK),cliponaxis=False,
        connector=dict(line=dict(color='#536779',dash='dot',width=2)),increasing=dict(marker=dict(color=POS)),decreasing=dict(marker=dict(color=NEG)),totals=dict(marker=dict(color='#285CA8')),
        hovertemplate='%{x}<br>%{y:,.2f} тис. грн<extra></extra>'))
    ends=np.r_[0,np.cumsum(values[:4]),values[-1]]; span=max(ends.max()-ends.min(),1)
    fig.update_yaxes(range=[ends.min()-.13*span,ends.max()+.20*span]); fig.update_xaxes(showgrid=False)
    fig.add_hline(y=0,line_color=INK,line_width=1.3)
    return theme(fig,title,ytitle='Тис. грн',height=500,bottom=85)

def break_even_chart(row):
    # Графік прибутку замість двох майже паралельних ліній доходу й витрат.
    D,PV,k=row['Дохід'],row['Постійні витрати'],row['Кмд']/100
    tb=row['Точка беззбитковості']; xmax=max(D,tb if np.isfinite(tb) else 0)*1.20
    x=np.linspace(0,xmax,251); y=x*k-PV
    fig=go.Figure()
    fig.add_scatter(x=x/1000,y=np.minimum(y,0),mode='lines',line=dict(width=0),fill='tozeroy',fillcolor='rgba(174,38,56,.14)',name='Збиткова зона',hoverinfo='skip')
    fig.add_scatter(x=x/1000,y=np.maximum(y,0),mode='lines',line=dict(width=0),fill='tozeroy',fillcolor='rgba(0,109,119,.15)',name='Прибуткова зона',hoverinfo='skip')
    fig.add_scatter(x=x/1000,y=y,mode='lines',line=dict(color=INK,width=3.5),name='Операційний результат',hovertemplate='Дохід: %{x:.2f} млн грн<br>EBIT: %{y:,.2f} тис. грн<extra></extra>')
    fig.add_hline(y=0,line_color=INK,line_width=1.5,line_dash='dash')
    if np.isfinite(tb):
        fig.add_scatter(x=[tb/1000],y=[0],mode='markers',name='Беззбитковість',marker=dict(size=13,color='white',symbol='diamond',line=dict(color=NEG,width=3)))
        fig.add_annotation(x=tb/1000,y=0,text=f'ТБ: {fmt(tb/1000)} млн',showarrow=True,arrowhead=2,ax=-65,ay=46,bgcolor='white',bordercolor=GRID,borderpad=5)
    fig.add_scatter(x=[D/1000],y=[row['EBIT']],mode='markers',name='Сценарний результат',marker=dict(size=15,color=POS if row['EBIT']>=0 else NEG,line=dict(color='white',width=2)))
    fig.add_vline(x=D/1000,line_dash='dot',line_color='#536779',line_width=1.5)
    fig.add_annotation(x=D/1000,y=row['EBIT'],text=f'Дохід: {fmt(D/1000)} млн<br>EBIT: {fmt(row["EBIT"])} тис.',showarrow=True,arrowhead=2,ax=-80,ay=-55,bgcolor='white',bordercolor=GRID,borderpad=6)
    ymin=min(float(y.min()),0); ymax=max(float(y.max()),0); span=max(ymax-ymin,1)
    fig.update_yaxes(range=[ymin-.10*span,ymax+.23*span]); fig.update_xaxes(range=[0,xmax/1000*1.04]); fig.update_layout(showlegend=False)
    return theme(fig,'Операційний результат залежно від доходу','Чистий дохід, млн грн','EBIT, тис. грн',520,bottom=70)

def heatmap_chart(f,d,q):
    # Комірки є точними розрахунками в центрах, не інтерпольованими прогнозами.
    dx=np.linspace(min(-30,d-5),max(30,d+5),9); qx=np.linspace(min(-1.5,q-.4),max(2.5,q+.4),9)
    grid=sensitivity_grid(f,dx,qx); z=grid.to_numpy(); lim=max(float(np.nanmax(np.abs(z))),1)
    fig=go.Figure(go.Heatmap(x=dx,y=qx,z=z,zmin=-lim,zmax=lim,colorscale=[[0,'#9E2035'],[.5,'#FFFFFF'],[1,'#006D77']],xgap=2,ygap=2,
        colorbar=dict(title=dict(text='EBIT<br>тис. грн',font=dict(size=14,color=INK)),tickfont=dict(size=13,color=INK),thickness=18,len=.84),
        hovertemplate='Δ доходу: %{x:.1f}%<br>Δ частки ЗВ: %{y:.2f} в. п.<br>EBIT: %{z:,.2f} тис. грн<extra></extra>'))
    for i, yy in enumerate(qx):
        for j, xx in enumerate(dx):
            v=z[i,j]
            if np.isfinite(v):
                near=abs(xx-d)<abs(dx[1]-dx[0])*.25 and abs(yy-q)<abs(qx[1]-qx[0])*.25
                fig.add_annotation(x=xx,y=yy,text=fmt(v,0),showarrow=False,yshift=-15 if near else 0,font=dict(size=13,color=cell_text_color(v,lim)))
    dense=np.linspace(dx.min(),dx.max(),300); boundary=100*(1-Q0-PV0*(1+f/100)/(D0*(1+dense/100)))
    mask=(boundary>=qx.min())&(boundary<=qx.max())
    fig.add_trace(go.Scatter(x=dense[mask],y=boundary[mask],mode='lines',name='Межа EBIT = 0',line=dict(color='white',width=6),showlegend=False,hoverinfo='skip'))
    fig.add_trace(go.Scatter(x=dense[mask],y=boundary[mask],mode='lines',name='Межа EBIT = 0',line=dict(color=INK,width=2.8,dash='dash')))
    fig.add_trace(go.Scatter(x=[d],y=[q],mode='markers',name='Обраний сценарій',marker=dict(symbol='star',size=22,color='#F7CD49',line=dict(color=INK,width=2)),customdata=[calculate_scenario(d,q,f)['EBIT']],hovertemplate='Обраний сценарій<br>EBIT: %{customdata:,.2f} тис. грн<extra></extra>'))
    fig.update_xaxes(tickmode='array',tickvals=dx,ticktext=[signed(v,1)+'%' for v in dx],showgrid=False,zeroline=False)
    fig.update_yaxes(tickmode='array',tickvals=qx,ticktext=[signed(v,2) for v in qx],showgrid=False,zeroline=False)
    fig=theme(fig,f'Чутливість EBIT · зміна ПВ {signed(f,1)} %','Зміна доходу від бази, %','Зміна частки ЗВ, в. п.',690,left=95,bottom=120)
    # Експорт зберігає первісну щільну матрицю для дослідження.
    return fig,sensitivity_grid(f,np.linspace(dx.min(),dx.max(),161),np.linspace(qx.min(),qx.max(),151))

def projection_chart(p,col,title,unit):
    # Матриця років: не приховує збіг траєкторій при нульових щорічних змінах.
    years=list(range(2025,2031)); codes=list(dict.fromkeys(p['Код'])); labels=scenario_labels(codes)
    z=p.pivot(index='Код',columns='Рік',values=col).reindex(index=codes,columns=years).to_numpy(float)
    valid=z[np.isfinite(z)]; lim=max(float(np.max(np.abs(valid))) if len(valid) else 1,1)
    fig=go.Figure(go.Heatmap(x=list(range(len(years))),y=list(range(len(labels))),z=z,zmin=-lim,zmax=lim,
        colorscale=[[0,'#9E2035'],[.5,'#FFFFFF'],[1,'#006D77']],xgap=4,ygap=4,showscale=True,
        colorbar=dict(title=dict(text=unit,font=dict(size=14,color=INK)),tickfont=dict(size=13,color=INK),thickness=17),
        customdata=[[[lab,year] for year in years] for lab in labels],hovertemplate='%{customdata[0]}<br>%{customdata[1]}<br>%{z:,.2f} '+unit+'<extra></extra>'))
    for i,lab in enumerate(labels):
        for j,year in enumerate(years):
            v=z[i,j]; color=cell_text_color(v,lim)
            fig.add_annotation(x=j,y=i,text=fmt(v,1 if unit=='Тис. грн' else 2),showarrow=False,font=dict(size=15,color=color))
    fig.update_xaxes(type='linear',tickmode='array',tickvals=list(range(len(years))),ticktext=[str(y) for y in years],range=[-.5,len(years)-.5],showgrid=False,zeroline=False,side='top')
    fig.update_yaxes(type='linear',tickmode='array',tickvals=list(range(len(labels))),ticktext=labels,range=[len(labels)-.5,-.5],showgrid=False,zeroline=False)
    fig.add_vline(x=.5,line_color=INK,line_width=2,line_dash='dash')
    return theme(fig,title,'','',height=max(355,64*len(labels)+155),left=185,bottom=55)

def history_percent_chart(history):
    fig=go.Figure()
    for col,label,color in [('Кмд','Коефіцієнт маржинального доходу',POS),('ЗФС, %','Запас фінансової стійкості','#285CA8')]:
        fig.add_bar(x=history['Рік'].astype(str),y=history[col],name=label,marker_color=color,text=[fmt(v)+' %' for v in history[col]],textposition='outside',textfont=dict(size=16,color=INK),cliponaxis=False)
    fig.update_layout(barmode='group',bargap=.36); fig.update_yaxes(range=[0,95]); fig.update_xaxes(showgrid=False)
    return theme(fig,'Маржинальність і запас стійкості',ytitle='%',height=440)

def benchmark_chart(benchmark):
    t=benchmark.iloc[[2,3]]; fig=go.Figure()
    for col,color in [('СОЛЮТЕХ, 2025','#285CA8'),('К2, середнє (10 підприємств)','#006D77')]:
        fig.add_bar(x=t[col],y=['Валова рентабельність','Чиста рентабельність'],orientation='h',name=col,marker_color=color,text=[fmt(v)+' %' for v in t[col]],textposition='outside',textfont=dict(size=15,color=INK),cliponaxis=False)
    fig.update_layout(barmode='group',bargap=.30); fig.update_xaxes(range=[0,16.5]); fig.update_yaxes(autorange='reversed',showgrid=False,ticks='outside',ticklen=5)
    return theme(fig,'Прибутковість: СОЛЮТЕХ і кластер К2','%',height=350,left=190,bottom=105)

def csv_bytes(df,index=False): return df.to_csv(index=index,float_format='%.8f').encode('utf-8-sig')

# 3. Інтерфейс: збережено чотири вихідні напрями, додано окремий аналіз чутливості

def main():
    import streamlit as st
    st.set_page_config(page_title='СОЛЮТЕХ | Економічна стійкість',page_icon='📊',layout='wide')
    st.title('Економічна стійкість ТОВ «СОЛЮТЕХ»')
    st.caption('Графіки: контрастна палітра, прямі підписи, однакові одиниці вимірювання. PNG можна зберегти кнопкою камери.')
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
        chart(st,revenue_bep_chart(history,'Рік','Чистий дохід і точка беззбитковості за роками'),'history_bep')
        chart(st,history_percent_chart(history),'history_pct')
        st.download_button('Фактичні показники CSV',csv_bytes(history),'history_2024_2025.csv','text/csv')
        with st.expander('Зв’язок із кластерним аналізом (3.1)',expanded=True):
            benchmark=pd.DataFrame({'Показник':['Коефіцієнт автономії','Абсолютна ліквідність','Валова рентабельність, %','Чиста рентабельність, %','Оборотність активів'],
                'СОЛЮТЕХ, 2025':[.351,.194,4.08,.99,3.128],'К2, середнє (10 підприємств)':[.273,.308,12.79,3.80,3.460]})
            chart(st,benchmark_chart(benchmark),'benchmark_profitability')
            st.dataframe(benchmark,hide_index=True,use_container_width=True)
            st.caption('Джерело: таблиця 3.3 кластерного аналізу. Значення округлені як у дисертації. Порівняльні орієнтири, не нормативи.')
            st.write('Найбільше відставання — за валовою та чистою рентабельністю. Тому S1 спрямовано на маржинальність, S2 — на операційні витрати, S3 — на їх поєднання зі зростанням доходу. CVP не прогнозує ліквідність, автономію або кластерну належність.')
    with t2:
        st.header('Факторний аналіз методом ланцюгових підстановок')
        pairs=[('2024 → 2025',calculate_cvp(*HISTORICAL[2024]),base,'2024','2025'),('S0 → S3',base,calculate_scenario(10,-.5,-5),'S0','S3'),('S0 → поточний',base,current,'S0',code)]
        if code in ('S0','S3'): pairs=pairs[:2]
        for label,start,end,l0,l1 in pairs:
            with st.expander(label,expanded=(label=='S0 → S3')):
                vals=factor_bridge(start,end)
                chart(st,waterfall_chart(vals,l0,l1,f'Факторне розкладання: {label}'),f'factor_{label}')
                factors=pd.DataFrame({'Чинник':['Зміна доходу','Зміна Кмд','Зміна ПВ','Загальна зміна EBIT'],'Вплив, тис. грн':vals[1:4]+[vals[-1]-vals[0]]})
                st.dataframe(factors.round(2),hide_index=True,use_container_width=True)
                st.download_button('Завантажити розклад CSV',csv_bytes(factors),f'factor_{l0}_{l1}.csv','text/csv',key=f'factor_dl_{label}')
        st.caption('Порядок: дохід → Кмд → ПВ. Спільний ефект зміни доходу й Кмд віднесено до другого фактора.')
    with t3:
        st.header('Порівняння погоджених сценаріїв S0–S4')
        st.caption('S1–S3 — управлінські заходи з 3.2; S0 — база; S4 — стрес-тест. USER — додатковий експеримент.')
        st.dataframe(compare[['Код','Сценарій','ΔД, %','ΔЗВ, в. п.','ΔПВ, %']].round(2),hide_index=True,use_container_width=True)
        chart(st,bar_compare(compare,'EBIT','Операційний результат за сценаріями','Тис. грн'),'scenario_ebit')
        st.caption('Пунктир — результат базового 2025 року. Від’ємний EBIT означає операційний збиток за CVP.')
        chart(st,bar_compare(compare,'ЗФС, %','Запас фінансової стійкості за сценаріями','%'),'scenario_safety')
        st.caption('Від’ємний запас означає, що сценарний дохід нижчий за точку беззбитковості.')
        chart(st,revenue_bep_chart(compare),'scenario_bep')
        st.dataframe(compare[['Код','Сценарій','Дохід','Маржинальний дохід','Кмд','EBIT','Точка беззбитковості','ЗФС, %','Резерв ЗВ, в. п.','Зона']].round(2),hide_index=True,use_container_width=True)
        st.download_button('Повні результати сценаріїв CSV',csv_bytes(compare),'scenarios.csv','text/csv')
        st.subheader('Детальний результат обраного варіанта')
        st.caption('Замість двох майже паралельних ліній показано EBIT залежно від доходу. Перетин нульової лінії — точка беззбитковості.')
        chart(st,break_even_chart(current),'current_bep')
        detail=pd.DataFrame({'Показник':list(current),'База 2025':[base[k] for k in current],'Сценарій':list(current.values())})
        for col in ['База 2025','Сценарій']: detail[col]=detail[col].map(lambda v:fmt(v) if isinstance(v,(int,float,np.number)) else str(v))
        st.dataframe(detail,hide_index=True,use_container_width=True)
        st.download_button('Обраний сценарій CSV',csv_bytes(pd.DataFrame([{'Код':code,**current}])),'current.csv','text/csv')
    with t4:
        st.header('Двофакторний аналіз чутливості')
        st.write('На карті змінюються дохід і частка змінних витрат. Постійні витрати зафіксовано на рівні обраного сценарію.')
        fig,grid=heatmap_chart(f,d,q)
        chart(st,fig,'heatmap')
        st.markdown(f'**Обраний сценарій {code}: EBIT = {fmt(current["EBIT"])} тис. грн.**')
        st.caption('Бірюзова зона — додатний результат, червона — збиток; темний пунктир — точна межа беззбитковості. Числа в комірках — EBIT у тис. грн для значень на осях (округлено до цілих). Зірка — обраний сценарій; її точне значення доступне при наведенні.')
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
                for col,title,unit in [('EBIT','Операційний результат за сценаріями','Тис. грн'),('ЗФС, %','Запас фінансової стійкості','%')]:
                    chart(st,projection_chart(p,col,title,unit),f'proj_{col}')
                display_code=st.selectbox('Деталізація доходу та точки беззбитковості',p['Код'].unique().tolist(),index=list(p['Код'].unique()).index(code) if code in p['Код'].unique() else 0)
                g=p[p['Код']==display_code]
                chart(st,revenue_bep_chart(g,'Рік',f'{display_code} · Дохід і точка беззбитковості за роками'),'proj_bep')
                st.caption('Матриці вище показують значення для кожного року. За нульових щорічних змін параметри 2026–2030 рр. однакові; це припущення, а не тенденція.')
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
