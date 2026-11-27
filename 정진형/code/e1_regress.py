"""③ 기온→전력 반응: 충북본부 일 전력(한전 원격검침) ~ 청주 ERA5-Land 기온, 2022-2024 6~9월.
식별: 연×월 고정효과 + 요일 + 공휴일(+여름휴가주간) 안에서 일별 기온 변동만 사용."""
import re, json, datetime as dt
import numpy as np
D='data/'
def rows(f,pat):
    out={}
    for l in open(D+f,encoding='utf-8'):
        m=re.match(pat,l)
        if m: out[int(m.group(1))]=[[float(v) for v in x.split(',')] for x in l.split(':',1)[1].strip().split(';') if x]
    return out
E=rows('e1_kepco_chungbuk_summer.txt',r'(\d{4}):')
T=rows('e1_era5_cheongju_summer.txt',r'E\|(\d{4}):')
HOL={'2022-06-01','2022-06-06','2022-08-15','2022-09-09','2022-09-10','2022-09-11','2022-09-12',
     '2023-06-06','2023-08-15','2023-09-28','2023-09-29','2023-09-30',
     '2024-06-06','2024-08-15','2024-09-16','2024-09-17','2024-09-18'}
rec=[]
for y in (2022,2023,2024):
    d0=dt.date(y,6,1)
    for i,(e,t) in enumerate(zip(E[y],T[y])):
        d=d0+dt.timedelta(i); k=d.isoformat()
        vac = (dt.date(y,7,25)<=d<=dt.date(y,8,9))
        rec.append(dict(date=k,y=y,m=d.month,dow=d.weekday(),hol=k in HOL,vac=vac,
            E=e[0],E18=e[1],Emax=e[2],Tm=t[0],Tx=t[1],T15=t[2],T18=t[3]))
def ols(yv,xcols,rec,ycol):
    X=[];Y=[]
    ym=sorted({(r['y'],r['m']) for r in rec})
    for r in rec:
        row=[r[c] for c in xcols]
        row+=[1.0 if (r['y'],r['m'])==g else 0.0 for g in ym]
        row+=[1.0 if r['dow']==w else 0.0 for w in range(1,7)]
        row+=[1.0 if r['hol'] else 0.0]
        X.append(row);Y.append(r[ycol])
    X=np.array(X);Y=np.array(Y)
    b,*_=np.linalg.lstsq(X,Y,rcond=None)
    res=Y-X@b; n,k=X.shape; s2=res@res/(n-k)
    cov=s2*np.linalg.pinv(X.T@X)
    # HC1 robust
    XtXi=np.linalg.pinv(X.T@X); meat=(X*res[:,None]).T@(X*res[:,None])
    covr=XtXi@meat@XtXi*n/(n-k)
    r2=1-res@res/((Y-Y.mean())@(Y-Y.mean()))
    return b[:len(xcols)],np.sqrt(np.diag(covr))[:len(xcols)],r2,n
out={}
for name,ycol,tcol,extra in [('day_Tmean','E','Tm',[]),('day_Tmean_vac','E','Tm',['vac']),
                             ('h18_T18','E18','T18',['vac']),('hmax_Tmax','Emax','Tx',['vac'])]:
    for r in rec: r['vac']=float(r['vac'])
    sub=[r for r in rec]
    b,se,r2,n=ols(None,[tcol]+extra,sub,ycol)
    out[name]=dict(beta=float(round(b[0],1)),se=float(round(se[0],1)),r2=float(round(r2,3)),n=n,unit='MWh/°C' if ycol=='E' else 'MWh/h/°C')
    print(name,out[name])
# 연도별(원격검침 호수 변화 확인)
for y in (2022,2023,2024):
    sub=[r for r in rec if r['y']==y]
    b,se,r2,n=ols(None,['Tm','vac'],sub,'E')
    out[f'day_Tmean_{y}']=dict(beta=float(round(b[0],1)),se=float(round(se[0],1)),r2=float(round(r2,3)),n=n)
    print(y,out[f'day_Tmean_{y}'])
# 평균 여름 일전력, 평균기온
out['mean_E']=float(round(np.mean([r['E'] for r in rec]),0)); out['mean_Tm']=float(round(np.mean([r['Tm'] for r in rec]),2))
out['mean_E18']=float(round(np.mean([r['E18'] for r in rec]),0))
json.dump(out,open(D+'e1_temp_power.json','w'),ensure_ascii=False,indent=1)

# ---- 서울(서울+남서울본부) 교차확인 ----
ES=rows('e1_kepco_seoul_summer.txt',r'(\d{4}):')
TS=rows('e1_era5_seoul_summer.txt',r'S\|(\d{4}):')
recS=[]
for y in (2022,2023,2024):
    d0=dt.date(y,6,1)
    for i,(e,t) in enumerate(zip(ES[y],TS[y])):
        d=d0+dt.timedelta(i); k=d.isoformat()
        recS.append(dict(y=y,m=d.month,dow=d.weekday(),hol=k in HOL,vac=float(dt.date(y,7,25)<=d<=dt.date(y,8,9)),E=e[0],E18=e[1],Tm=t[0],T18=t[1]))
for y in (2022,2023,2024,None):
    sub=[r for r in recS if y is None or r['y']==y]
    b,se,r2,n=ols(None,['Tm','vac'],sub,'E')
    b2,se2,_,_=ols(None,['T18','vac'],sub,'E18')
    key=f'seoul_day_Tmean_{y or "all"}'
    out[key]=dict(beta=float(round(b[0],1)),se=float(round(se[0],1)),r2=float(round(r2,3)),n=n,beta18=float(round(b2[0],1)),se18=float(round(se2[0],1)))
    print(key,out[key])
json.dump(out,open(D+'e1_temp_power.json','w'),ensure_ascii=False,indent=1)
