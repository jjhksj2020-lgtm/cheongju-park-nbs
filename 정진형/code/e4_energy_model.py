"""공원 조성 → 주변 냉방전력·피크·탄소 저감 알고리즘 (①~⑤ 연결)
① ΔLST(d) = A(a)·exp(-d/L(a))            size_model.json  (D1 전국 107곳 + D2 547곳)
② ΔTa = k · ΔLST                         e2_lst_to_air.json (S-DoT 1,002센서 × Landsat 4일)
③ ΔE/인/일 = β · ΔTa                     e1_temp_power.json (한전 충북 시간별 × ERA5-Land, 2022-24 여름)
④ Σ 고리별 인구(GHS-POP 2025) × ΔE × 122일(6~9월)
⑤ × 0.4173 tCO2eq/MWh (2023 국가 전력 배출계수)
"""
import json, math, csv, re
D='data/'
SM=json.load(open(D+'size_model.json')); K=json.load(open(D+'e2_lst_to_air.json')); E=json.load(open(D+'e1_temp_power.json'))
parks={p[0]:p for p in json.load(open(D+'parks40_geom.json'))}
Amax,a0=SM['A']['Amax'],SM['A']['a0']; L0,b=SM['L']['L0'],SM['L']['b']
POP_CB=(1581382+1578419+1576313)/3            # 충북 주민등록인구 2022~24 평균
beta=E['day_Tmean_vac']['beta']*1000/POP_CB   # kWh/인/°C/일
beta_se=E['day_Tmean_vac']['se']*1000/POP_CB
gam=E['h18_T18']['beta']*1e6/POP_CB           # W/인/°C (18시)
DAYS=122; EF=0.4173
bands=[(0,50),(50,100),(100,150),(150,200),(200,300),(300,500)]
rows=[]
for l in open(D+'e4_rings_pop_raw.txt',encoding='utf-8'):
    if not l.startswith('W|'): continue
    for rec in l[2:].strip().split(';'):
        if not rec: continue
        i,pp,aa=rec.split(':'); i=int(i)
        pp=[float(x)/100 for x in pp.split(',')]   # 원값/100 = 인구
        rows.append((i,pp[0],pp[1:]))
def ring_mean(A,L,d0,d1):  # 고리 평균 exp 감쇠
    return A*L/(d1-d0)*(math.exp(-d0/L)-math.exp(-d1/L))
def run(k_day,k_18,beta_=beta):
    out=[]
    for i,pin,pr in rows:
        p=parks[i]; a=p[2]/1e4
        A=Amax*(1-math.exp(-a/a0)); L=L0*a**b
        dl=[ring_mean(A,L,*bd) for bd in bands]
        e=sum(pp*k_day*d*beta_*DAYS for pp,d in zip(pr,dl))           # kWh/여름 (음수=감소)
        pk=sum(pp*k_18*d*gam for pp,d in zip(pr,dl))/1000              # kW
        out.append(dict(id=i,name=p[1],cur=p[4],area_m2=p[2],a_ha=round(a,3),A=round(A,3),L=round(L,1),
            pop0_300=round(sum(pr[:5])),pop0_500=round(sum(pr)),
            dLST_0_50=round(dl[0],3),dTa_0_50=round(dl[0]*k_day,3),
            kWh=round(-e),kW=round(-pk,1),tCO2=round(-e/1000*EF,2),
            kWh_per_ha=round(-e/a) ))
    return out
base=run(K['adopted']['k_day'],K['adopted']['k_18'])
up=run(K['adopted']['k_day_upper'],K['adopted']['k_18_upper'])
for r,u in zip(base,up): r['kWh_hi']=u['kWh']; r['kW_hi']=u['kW']; r['tCO2_hi']=u['tCO2']
base.sort(key=lambda r:-r['kWh'])
with open(D+'e4_park_energy.csv','w',newline='',encoding='utf-8-sig') as f:
    w=csv.DictWriter(f,fieldnames=list(base[0].keys())); w.writeheader(); w.writerows(base)
tot={k:round(sum(r[k] for r in base),2) for k in ['kWh','kWh_hi','kW','kW_hi','tCO2','tCO2_hi','pop0_300']}
summary=dict(params=dict(beta_kWh_per_person_C_day=round(beta,4),beta_se=round(beta_se,4),gamma_W_per_person_C_18h=round(gam,2),
    k_day=K['adopted']['k_day'],k_day_upper=K['adopted']['k_day_upper'],k_18=K['adopted']['k_18'],k_18_upper=K['adopted']['k_18_upper'],
    days=DAYS,EF_tCO2_per_MWh=EF,pop_chungbuk=round(POP_CB)),total=tot,n=len(base))
json.dump(summary,open(D+'e4_summary.json','w'),ensure_ascii=False,indent=1)
print(json.dumps(summary,ensure_ascii=False,indent=1))
print(f"{'공원':10}{'현황':6}{'면적㎡':>8}{'A°C':>7}{'L m':>6}{'인구300':>8}{'kWh':>8}{'kWh상한':>8}{'kW':>6}{'tCO2':>7}")
for r in base: print(f"{r['name']:10}{r['cur']:6}{r['area_m2']:>8.0f}{r['A']:>7}{r['L']:>6}{r['pop0_300']:>8}{r['kWh']:>8}{r['kWh_hi']:>8}{r['kW']:>6}{r['tCO2']:>7}")

# ---- 일반화 표: 원형 공원, 주변 인구밀도 1만 명/km² 균일 가정 ----
print('\n[일반화] 면적별 (주변 1만명/km², 원형)')
gen=[]
for a in [0.05,0.1,0.25,0.5,1,2,4,10]:
    r=math.sqrt(a*1e4/math.pi); A=Amax*(1-math.exp(-a/a0)); L=L0*a**b
    res={}
    for tag,kd,k18 in [('base',K['adopted']['k_day'],K['adopted']['k_18']),('hi',K['adopted']['k_day_upper'],K['adopted']['k_18_upper'])]:
        e=pk=0
        for d0,d1 in bands:
            pop=0.01*math.pi*((r+d1)**2-(r+d0)**2); dl=ring_mean(A,L,d0,d1)
            e+=pop*kd*dl*beta*DAYS; pk+=pop*k18*dl*gam/1000
        res[tag]=(-e,-pk)
    gen.append(dict(a_ha=a,A=round(A,3),L=round(L,1),kWh=round(res['base'][0]),kWh_hi=round(res['hi'][0]),kW=round(res['base'][1],2),tCO2=round(res['base'][0]/1000*EF,2),tCO2_hi=round(res['hi'][0]/1000*EF,2)))
    print(gen[-1])
summary['generic_10k_per_km2']=gen
summary['check_seoul']=dict(beta_2024=round(E['seoul_day_Tmean_2024']['beta']*1000/9331860,3),note='서울+남서울본부 2024 / 서울 주민등록 933만 (원격검침 커버리지 ~91%라 하한)')
json.dump(summary,open(D+'e4_summary.json','w'),ensure_ascii=False,indent=1)
