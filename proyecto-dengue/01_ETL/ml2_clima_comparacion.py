# -*- coding: utf-8 -*-
"""
Modelado avanzado: dengue + clima, comparacion de modelos, walk-forward y por departamento.
Resolucion MENSUAL (para integrar clima de NASA POWER). Complementa ml_dengue_spark.py.
Salidas en 02_datos_procesados/: ml2_metricas.json, ml2_pred_nacional_2024.csv, ml2_serie_mensual.csv
"""
import os, json, numpy as np, pandas as pd
from datetime import date, timedelta
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
import warnings; warnings.filterwarnings("ignore")

BASE=os.environ.get("PROJ_BASE","."); OUT=os.path.join(BASE,"02_datos_procesados")
DEPS=["PIURA","LIMA","LORETO","LA LIBERTAD","ICA"]

def wk_to_month(a,w):
    try: d=date(int(a),1,1)+timedelta(weeks=int(w)-1); return d.month
    except: return min(12,max(1,int((int(w)-1)/4.345)+1))

# 1. Dengue mensual (nacional y por depto)
print("Cargando fact_dengue...")
fact=pd.read_csv(os.path.join(OUT,"fact_dengue.csv"),usecols=["ano","semana","departamento","casos"])
fact["mes"]=[wk_to_month(a,w) for a,w in zip(fact["ano"],fact["semana"])]
fact["aniomes"]=fact["ano"].astype(int)*100+fact["mes"]
nac=fact.groupby("aniomes")["casos"].sum().rename("casos").reset_index()

# 2. Clima
cl=pd.read_csv(os.path.join(OUT,"clima_mensual.csv"))
cl["aniomes"]=cl["aniomes"].astype(int)
# pesos por depto = participacion de casos (entre los 5)
w=fact[fact.departamento.isin(DEPS)].groupby("departamento")["casos"].sum()
w=w/w.sum()
clp=cl.pivot_table(index="aniomes",columns="departamento",values=["t2m","rh2m","prec"])
nac_cl=pd.DataFrame(index=clp.index)
for var in ["t2m","rh2m","prec"]:
    nac_cl[var]=sum(clp[(var,d)]*w[d] for d in DEPS)
nac_cl=nac_cl.reset_index()

df=nac.merge(nac_cl,on="aniomes").sort_values("aniomes").reset_index(drop=True)
df["ano"]=df["aniomes"]//100; df["mes"]=df["aniomes"]%100
df["sin"]=np.sin(2*np.pi*df["mes"]/12); df["cos"]=np.cos(2*np.pi*df["mes"]/12)
for L in [1,2,3,12]: df[f"lag{L}"]=df["casos"].shift(L)
for L in [1,2]:
    df[f"prec_l{L}"]=df["prec"].shift(L); df[f"t2m_l{L}"]=df["t2m"].shift(L); df[f"rh_l{L}"]=df["rh2m"].shift(L)
df=df.dropna().reset_index(drop=True)
df.to_csv(os.path.join(OUT,"ml2_serie_mensual.csv"),index=False)

F_BASE=["sin","cos","lag1","lag2","lag3","lag12"]
F_CLIMA=F_BASE+["t2m","rh2m","prec","prec_l1","prec_l2","t2m_l1","rh_l1"]

def metrics(y,p): 
    return {"R2":round(r2_score(y,p),3),"RMSE":round(mean_squared_error(y,p)**0.5,1),"MAE":round(mean_absolute_error(y,p),1)}

# 3. Out-of-time: train<=2023, test 2024
tr=df[df.ano<=2023]; te=df[df.ano==2024]
res={}
res["Persistencia (lag-1)"]=metrics(te["casos"],te["lag1"])
res["Naive estacional (lag-12)"]=metrics(te["casos"],te["lag12"])
rf_b=RandomForestRegressor(n_estimators=400,max_depth=8,random_state=42).fit(tr[F_BASE],np.log1p(tr["casos"]))
res["Random Forest (sin clima)"]=metrics(te["casos"],np.expm1(rf_b.predict(te[F_BASE])))
rf_c=RandomForestRegressor(n_estimators=400,max_depth=8,random_state=42).fit(tr[F_CLIMA],np.log1p(tr["casos"]))
pred_rfc=np.expm1(rf_c.predict(te[F_CLIMA]))
res["Random Forest (con clima)"]=metrics(te["casos"],pred_rfc)
gb_b=GradientBoostingRegressor(n_estimators=400,max_depth=3,learning_rate=0.05,random_state=42).fit(tr[F_BASE],np.log1p(tr["casos"]))
res["Gradient Boosting (sin clima)"]=metrics(te["casos"],np.expm1(gb_b.predict(te[F_BASE])))
gb=GradientBoostingRegressor(n_estimators=400,max_depth=3,learning_rate=0.05,random_state=42).fit(tr[F_CLIMA],np.log1p(tr["casos"]))
pred_gb=np.expm1(gb.predict(te[F_CLIMA]))
res["Gradient Boosting (con clima)"]=metrics(te["casos"],pred_gb)

# SARIMA y SARIMAX (con clima) via statsmodels
from statsmodels.tsa.statespace.sarimax import SARIMAX
ynac=df.set_index("aniomes")["casos"]
try:
    s=SARIMAX(np.log1p(tr["casos"].values),order=(1,0,1),seasonal_order=(1,1,0,12)).fit(disp=False)
    fc=np.expm1(s.forecast(len(te))); res["SARIMA (sin clima)"]=metrics(te["casos"].values,fc)
except Exception as e: res["SARIMA (sin clima)"]={"error":str(e)[:40]}
try:
    ex=["t2m","rh2m","prec","prec_l1","prec_l2"]
    sx=SARIMAX(np.log1p(tr["casos"].values),exog=tr[ex].values,order=(1,0,1),seasonal_order=(1,1,0,12)).fit(disp=False)
    fcx=np.expm1(sx.forecast(len(te),exog=te[ex].values)); res["SARIMAX (con clima)"]=metrics(te["casos"].values,fcx)
except Exception as e: res["SARIMAX (con clima)"]={"error":str(e)[:40]}

# importancia clima
imp=dict(zip(F_CLIMA,[round(float(x),3) for x in rf_c.feature_importances_]))

# 4. Walk-forward one-step (2019-2024)
def walkfwd(feats):
    ys,ps=[],[]
    idx=df.index[df.ano>=2019]
    for i in idx:
        trn=df.iloc[:i]
        if len(trn)<24: continue
        m=RandomForestRegressor(n_estimators=200,max_depth=8,random_state=42).fit(trn[feats],np.log1p(trn["casos"]))
        ps.append(float(np.expm1(m.predict(df.iloc[[i]][feats]))[0])); ys.append(float(df.iloc[i]["casos"]))
    return metrics(np.array(ys),np.array(ps))
wf={"RF sin clima":walkfwd(F_BASE),"RF con clima":walkfwd(F_CLIMA)}

# 5. Por departamento (out-of-time 2024, RF con clima)
depres={}
for d in DEPS:
    dd=fact[fact.departamento==d].groupby("aniomes")["casos"].sum().rename("casos").reset_index()
    dc=cl[cl.departamento==d][["aniomes","t2m","rh2m","prec"]]
    m=dd.merge(dc,on="aniomes").sort_values("aniomes").reset_index(drop=True)
    m["ano"]=m["aniomes"]//100; m["mes"]=m["aniomes"]%100
    m["sin"]=np.sin(2*np.pi*m["mes"]/12); m["cos"]=np.cos(2*np.pi*m["mes"]/12)
    for L in [1,2,3,12]: m[f"lag{L}"]=m["casos"].shift(L)
    m["prec_l1"]=m["prec"].shift(1); m["t2m_l1"]=m["t2m"].shift(1)
    m=m.dropna().reset_index(drop=True)
    ff=F_BASE+["t2m","rh2m","prec","prec_l1","t2m_l1"]
    tr2=m[m.ano<=2023]; te2=m[m.ano==2024]
    if len(te2)<6 or len(tr2)<24: continue
    mo=RandomForestRegressor(n_estimators=300,max_depth=8,random_state=42).fit(tr2[ff],np.log1p(tr2["casos"]))
    depres[d]=metrics(te2["casos"],np.expm1(mo.predict(te2[ff])))

# guardar predicciones nacionales 2024 para grafico
pd.DataFrame({"mes":te["mes"].values,"casos_real":te["casos"].astype(int).values,
    "rf_sin_clima":np.expm1(rf_b.predict(te[F_BASE])).round().astype(int),
    "gbt_con_clima":pred_gb.round().astype(int),
    "persistencia":te["lag1"].astype(int).values}).to_csv(os.path.join(OUT,"ml2_pred_nacional_2024.csv"),index=False)

allm={"resolucion":"mensual","periodo":"2000-2024","test":"2024 (out-of-time)",
    "comparacion_2024":res,"walk_forward_2019_2024":wf,"por_departamento_2024":depres,
    "importancia_rf_clima":imp,"departamentos_clima":DEPS}
json.dump(allm,open(os.path.join(OUT,"ml2_metricas.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=2)
print(json.dumps(allm,ensure_ascii=False,indent=2))
print("ML2 OK")
