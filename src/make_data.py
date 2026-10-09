import csv, json, re, sys
TD = sys.argv[1]; OUT = sys.argv[2]

def norm(s): return re.sub(r'\s+', ' ', s.replace('Chueung', 'Cheung')).strip()

def days(s):
    s = s.lower()
    if 'daily' in s: return ['wd', 'sat', 'sun']
    if 'mondays to saturdays' in s: return ['wd', 'sat']
    if 'mondays to friday' in s: return ['wd']
    if 'saturdays,' in s or 'saturdays sundays' in s: return ['sat', 'sun']
    if s.startswith('saturday'): return ['sat']
    if s.startswith('sunday'): return ['sun']
    raise ValueError(s)

def mins(t):
    t = t.strip().lower().replace('noon', 'p.m.')
    m = re.match(r'(\d+)(?:[:.](\d+))?(?::\d+)?\s*([ap])\.?m', t)
    if not m: raise ValueError('time: ' + repr(t))
    h, mi, ap = int(m[1]), int(m[2] or 0), m[3]
    h = h % 12 + (12 if ap == 'p' else 0)
    v = h * 60 + mi
    return v + 1440 if v < 180 else v   # after-midnight sailings sort to the end

def rem(r):
    r = (r or '').strip()
    if not r: return ''
    return ','.join(str(int(float(x))) for x in r.split(','))

def read(f):
    return list(csv.reader(open(f'{TD}/{f}.csv', encoding='utf-8-sig')))

def timetable(f, mixed=False):
    rows = read(f)[1:]
    dirs = {}
    for r in rows:
        if f == 'tm_tc_slw_to':
            sd, bound, frm, t, rk = r[0], norm(r[1]), norm(r[2]), r[3], r[4]
            d, leg = f'Towards {bound}', f'from {frm}'
        else:
            d, sd, t, rk = norm(r[0]), r[1], r[2], r[3]
            leg = d if mixed else ''
            if mixed: d = 'All sailings'
        for dc in days(sd):
            dirs.setdefault(d, {}).setdefault(dc, set()).add((mins(t), rem(rk), leg))
    out = {}
    for d, byday in dirs.items():
        out[d] = {dc: [list(x) for x in sorted(v)] for dc, v in byday.items()}
    return out

DAYSHORT = {'wd': 'Mon–Fri', 'sat': 'Sat', 'sun': 'Sun & holidays'}
def daylabel(s):
    s = s.lower()
    if 'daily' in s: return ''
    if 'saturdays,' in s or 'saturdays sundays' in s: return 'Sat, Sun & hols'
    if 'sunday' in s: return 'Sun & hols'
    if 'saturdays' in s and 'mondays' not in s: return 'Sat'
    if 'school' in s: return 'School days'
    if 'mondays to saturdays' in s: return 'Mon–Sat'
    return 'Mon–Fri'

def fares(f):
    rows = read(f + '_fare')
    h = [c.strip() for c in rows[0]]
    ix = lambda n: next((i for i, c in enumerate(h) if c.startswith(n)), None)
    ip, ir, id_, it, iff, im = ix('Passenger'), ix('Route'), ix('Service Date'), ix('Ferry Type'), ix('Fare (HK'), ix('Remark')
    out, seen = [], set()
    for r in rows[1:]:
        if not r or not r[ip].strip(): continue
        p = r[ip]
        if 'dult' not in p or 'hild' in p: continue
        if not (p.strip().startswith('Single') or p.strip() == 'Adult'): continue
        v = r[iff].strip().replace('$', '')
        if v in ('', 'N/A'): continue
        bits = []
        if ir is not None: bits.append(norm(r[ir]))
        if it is not None and r[it].strip(): bits.append(norm(r[it]))
        pm = re.search(r'\((.*?)\)', p)
        if pm: bits.append(pm[1])
        if id_ is not None and daylabel(r[id_]): bits.append(daylabel(r[id_]))
        if im is not None and im < len(r) and r[im].strip() and f.startswith(('mawan',)): bits.append('note ' + rem(r[im]))
        label = ' · '.join(bits) or 'Adult single'
        try: v = ('%.1f' % float(v)).rstrip('0').rstrip('.') if float(v) != int(float(v)) else str(int(float(v)))
        except ValueError: pass
        key = (label, v)
        if key in seen: continue
        seen.add(key); out.append([label, v])
    return out

SUN_REM = {'1': 'Ordinary ferry (slower)'}
R = []
def add(id, group, name, op='', info='', f=None, mixed=False, remnotes=None, freq=None, fare=None):
    R.append(dict(id=id, group=group, name=name, op=op, info=info,
                  dirs=timetable(f, mixed) if f else {}, fares=fares(f) if f and not fare else (fare or []),
                  remnotes=remnotes or {}, freq=freq))

H, I, L = 'Harbour crossings', 'Outlying islands', 'Lantau, Ma Wan & west'
band = lambda *a: [list(x) for x in a]
STAR_CTR_WD = band(('06:30–07:25', '10–12'), ('07:25–09:55', '6'), ('09:55–20:40', '6–8'), ('20:40–23:30', '10–12'))
STAR_CTR_WE = band(('06:30–07:25', '10–12'), ('07:25–22:40', '6–8'), ('22:40–23:30', '10–12'))
STAR_TST_WD = band(('06:30–07:15', '10–12'), ('07:15–09:45', '6'), ('09:45–20:30', '6–8'), ('20:30–23:30', '10–12'))
STAR_TST_WE = band(('06:30–07:15', '10–12'), ('07:15–22:30', '6–8'), ('22:30–23:30', '10–12'))
WC_MS = band(('07:30–07:52', '11'), ('07:52–09:12', '8'), ('09:12–16:48', '12'), ('16:48–18:24', '8'), ('18:24–20:00', '12'), ('20:00–22:20', '10–14'), ('22:20–23:00', '20'))
TW_MS = band(('07:20–07:30', '10'), ('07:30–07:41', '11'), ('07:41–09:00', '8'), ('09:00–16:36', '12'), ('16:36–18:12', '8'), ('18:12–19:36', '12'), ('19:36–22:30', '10–14'), ('22:30–22:50', '20'))
WC_SUN = band(('07:40–23:00', '12–20'))
TW_SUN = band(('07:30–22:50', '12–20'))
def sf(a, b, wd, sat, sun): return {a: {'wd': wd, 'sat': sat, 'sun': sun}, b: None}
add('star-central', H, 'Central ⇄ Tsim Sha Tsui', 'Star Ferry', 'Central Pier 7 ⇄ Star Ferry Pier, Salisbury Road. About 9 min. No fixed timetable: ferries leave on the frequencies below.',
    freq={'Central → Tsim Sha Tsui': {'wd': STAR_CTR_WD, 'sat': STAR_CTR_WE, 'sun': STAR_CTR_WE},
          'Tsim Sha Tsui → Central': {'wd': STAR_TST_WD, 'sat': STAR_TST_WE, 'sun': STAR_TST_WE}},
    fare=[['Upper deck · Mon–Fri', '5'], ['Lower deck · Mon–Fri', '4'], ['Upper deck · Sat, Sun & hols', '6.5'], ['Lower deck · Sat, Sun & hols', '5.6'], ['Child / 65+ · Mon–Fri (upper / lower)', '2.9 / 2.8'], ['Child / 65+ · weekend (upper / lower)', '3.9 / 3.7']])
add('star-wanchai', H, 'Wan Chai ⇄ Tsim Sha Tsui', 'Star Ferry', 'Wan Chai Pier, Hung Hing Road ⇄ Star Ferry Pier. About 8 min. Frequency in minutes; no fixed timetable.',
    freq={'Wan Chai → Tsim Sha Tsui': {'wd': WC_MS, 'sat': WC_MS, 'sun': WC_SUN},
          'Tsim Sha Tsui → Wan Chai': {'wd': TW_MS, 'sat': TW_MS, 'sun': TW_SUN}},
    fare=[['Adult · Mon–Fri', '5'], ['Adult · Sat, Sun & hols', '6.5'], ['Child / 65+ · Mon–Fri', '2.9'], ['Child / 65+ · weekend', '3.9']])
add('np-hh', H, 'North Point ⇄ Hung Hom', 'Sun Ferry', 'North Point (West) Pier ⇄ Hung Hom (North) Pier, Wa Shun St. About 8 min.', 'np_hh', remnotes={})
add('np-kc', H, 'North Point ⇄ Kowloon City', 'Sun Ferry', 'North Point (West) Pier ⇄ Kowloon City Pier, San Ma Tau St. About 14 min.', 'np_klnc')
add('np-kt', H, 'North Point ⇄ Kwun Tong ⇄ Kai Tak', 'Fortune Ferry', 'North Point (East) Pier ⇄ Kwun Tong Pier ⇄ Kai Tak Runway Park Pier. North Point–Kwun Tong about 12 min; the whole run about 24 min. Kai Tak calls run Sat, Sun & holidays only.', 'np_ktak')
add('swh-kt', H, 'Sai Wan Ho ⇄ Kwun Tong', 'Coral Sea Ferry', 'Sai Wan Ho Pier ⇄ Kwun Tong Pier. About 15 min.', 'swh_kt')
add('swh-skt', H, 'Sai Wan Ho ⇄ Sam Ka Tsuen', 'Coral Sea Ferry', 'Sai Wan Ho Pier ⇄ Sam Ka Tsuen (Yau Tong).', 'swh_skt')
add('c-hh', H, 'Central ⇄ Hung Hom', 'Fortune Ferry', 'Central Pier 8 (Western Berth) ⇄ Hung Hom (South) Pier. About 16 min.', 'c_hh')
add('cc', I, 'Central ⇄ Cheung Chau', 'Sun Ferry', 'Central Pier 6. Fast ferry about 35–40 min; ordinary ferries are slower and marked.', 'central_cc', remnotes=SUN_REM)
add('mw', I, 'Central ⇄ Mui Wo', 'Sun Ferry', 'Central Pier 6. Fast ferry about 35–40 min; ordinary ferries are slower and marked.', 'central_mw', remnotes=SUN_REM)
add('pc', I, 'Central ⇄ Peng Chau', 'HKKF', 'Includes the Peng Chau ⇄ Hei Ling Chau legs. Timetable effective 1 Apr 2026.', 'central_pc')
add('ysw', I, 'Central ⇄ Yung Shue Wan (Lamma)', 'HKKF', '', 'central_ysw')
add('skw', I, 'Central ⇄ Sok Kwu Wan (Lamma)', 'HKKF', '', 'central_skw')
add('inter', I, 'Peng Chau · Mui Wo · Chi Ma Wan · Cheung Chau', 'Sun Ferry', 'Inter-island service, daily. Each row shows the leg.', 'pc_mw_cmw_cc', mixed=True)
add('abd-ysw', I, 'Aberdeen ⇄ Yung Shue Wan (via Pak Kok Tsuen)', '', '', 'abd_ysw')
add('abd-skw', I, 'Aberdeen ⇄ Sok Kwu Wan (via Mo Tat)', '', '', 'abd_skw')
add('db', L, 'Central ⇄ Discovery Bay', '', '', 'central_db')
add('db-mw', L, 'Discovery Bay ⇄ Mui Wo', 'Peng Chau Kaito', 'Kaito (small ferry). Weekday service is school days only.', 'db_mw')
add('db-pc', L, 'Discovery Bay ⇄ Peng Chau / Trappist', '', '', 'db_pc_tm')
add('mawan-c', L, 'Ma Wan ⇄ Central', '', '', 'mawan_c')
add('mawan-tw', L, 'Ma Wan ⇄ Tsuen Wan', '', '', 'mawan_tw')
add('tm-to', L, 'Tuen Mun · Tung Chung · Sha Lo Wan · Tai O', 'Fortune Ferry', 'Each row shows where the sailing starts. Weekday timetable is school-day based; check holidays.', 'tm_tc_slw_to')

# ---- Kaito (small licensed ferries): hand-keyed from the Transport Department's kaito service details page ----
K = 'Kaito (small ferries)'
def T(txt):
    out = []
    for h, m, ap in re.findall(r'(\d{1,2})[.:](\d{2})\s*([ap])\.?m', txt):
        out.append(mins(f'{h}:{m} {ap}.m.'))
    if 'noon' in txt: out.append(720)
    return sorted(out)
def fmt_t(m): return '%02d:%02d' % (m // 60, m % 60)
def kd(**byday):
    return {dc: [list(e) for e in sorted(v)] for dc, v in byday.items() if v}
def L(times, leg='', rk=''): return [[m, rk, leg] for m in T(times)]
def kaito(id, name, op, info, dirs, fares, remnotes=None, daynotes=None, freq=None):
    R.append(dict(id=id, group=K, name=name, op=op, info=info, dirs=dirs, fares=fares,
                  remnotes=remnotes or {}, freq=freq, daynotes=daynotes or {}))

kaito('k-tl-swh', 'Sai Wan Ho ⇄ Tung Lung Chau', 'Blue Sea Ferry', 'From Shau Kei Wan Typhoon Shelter Landing No. 10 to Tung Lung Chau Public Pier. Weekends and public holidays only, except the first two days of Lunar New Year. Hotline 2337 6568.',
    {'Sai Wan Ho → Tung Lung Chau': kd(sat=L('9.00 a.m. 9.45 a.m. 10.30 a.m. 11.15 a.m. 12.00 noon 12.45 p.m. 1.30 p.m. 3.15 p.m. 4.45 p.m.'), sun=L('9.00 a.m. 9.45 a.m. 10.30 a.m. 11.15 a.m. 12.00 noon 12.45 p.m. 1.30 p.m. 3.15 p.m. 4.45 p.m.')),
     'Tung Lung Chau → Sai Wan Ho': kd(sat=L('9.45 a.m. 10.30 a.m. 11.15 a.m. 12.00 noon 12.45 p.m. 2.30 p.m. 4.00 p.m. 4.45 p.m. 5.30 p.m.'), sun=L('9.45 a.m. 10.30 a.m. 11.15 a.m. 12.00 noon 12.45 p.m. 2.30 p.m. 4.00 p.m. 4.45 p.m. 5.30 p.m.'))},
    [['Adult · round trip', '60'], ['Child 5–12 · round trip', '40'], ['65+ / disabled · single', '30'], ['Tung Lung Chau → Sai Wan Ho · single', '30']],
    daynotes={'wd': 'No service Monday to Friday.'})
kaito('k-tl-skt', 'Sam Ka Tsuen ⇄ Tung Lung Chau', 'Coral Sea Shipping', 'Sam Ka Tsuen Ferry Pier (Yau Tong) to Tung Lung Chau Public Pier. Weekends and public holidays only. Buy the return ticket with the outward ticket. Hotline 2368 8885.',
    {'Sam Ka Tsuen → Tung Lung Chau': kd(sat=L('8.20 a.m. 9.25 a.m. 10.40 a.m. 11.50 a.m. 1.20 p.m. 2.35 p.m. 3.45 p.m. 4.55 p.m.'), sun=L('8.20 a.m. 9.25 a.m. 10.40 a.m. 11.50 a.m. 1.20 p.m. 2.35 p.m. 3.45 p.m. 4.55 p.m.')),
     'Tung Lung Chau → Sam Ka Tsuen': kd(sat=L('8.50 a.m. 10.00 a.m. 11.10 a.m. 12.25 p.m. 2.00 p.m. 3.10 p.m. 4.20 p.m. 5.40 p.m.'), sun=L('8.50 a.m. 10.00 a.m. 11.10 a.m. 12.25 p.m. 2.00 p.m. 3.10 p.m. 4.20 p.m. 5.40 p.m.'))},
    [['Adult · single', '22.5'], ['Bicycle / animal', '20']],
    daynotes={'wd': 'No service Monday to Friday.'})
kaito('k-potoi', 'Aberdeen / Stanley ⇄ Po Toi', 'Tsui Wah Ferry', 'Aberdeen Tsui Wah Ferry Pier and Stanley Blake Pier to Po Toi Public Pier. Runs on only some days (see below). Hotline 2272 2022.',
    {'To Po Toi': kd(
        wd=L('10.00 a.m.', 'from Aberdeen') + L('10.30 a.m.', 'from Stanley'),
        sat=L('10.00 a.m. 3.00 p.m.', 'from Aberdeen') + L('10.30 a.m. 1.20 p.m.', 'from Stanley'),
        sun=L('8.15 a.m.', 'from Aberdeen') + L('10.00 a.m. 11.30 a.m. 3.30 p.m. 5.00 p.m.', 'from Stanley')),
     'From Po Toi': kd(
        wd=L('3.30 p.m.', 'return'),
        sat=L('12.40 p.m.', 'to Stanley') + L('2.00 p.m. 4.00 p.m.', 'to Aberdeen via Stanley'),
        sun=L('9.15 a.m. 10.45 a.m. 3.00 p.m. 4.30 p.m.', 'to Stanley') + L('6.00 p.m.', 'to Aberdeen via Stanley'))},
    [['Tue, Thu & Sat · non-resident', '30'], ['Sun & holidays · non-resident', '30']],
    daynotes={'wd': 'Tuesdays and Thursdays only. No service Mon, Wed, Fri.', 'sat': 'Saturdays except public holidays.'})
kaito('k-tapmun', 'Tap Mun ⇄ Wong Shek', 'Tsui Wah Ferry', 'Tap Mun to Wong Shek Pier (Sai Kung). Sailings marked 1 are run by the Ma Liu Shui service and call at Ko Lau Wan and Chek Keng. Hotline 2272 2022.',
    {'Tap Mun → Wong Shek': kd(wd=L('7:45 am 11:45 am 1:45 pm 3:45 pm 6:00 pm') + L('10:00 am 4:20 pm', '', '1'), sat=L('8:00 am 9:00 am 11:00 am 12:00 noon 1:05 pm 2:00 pm 3:05 pm 4:05 pm 5:05 pm 6:05 pm') + L('10:00 am 4:20 pm', '', '1'),
                                   sun=L('8:00 am 9:00 am 11:00 am 12:00 noon 1:05 pm 2:00 pm 3:05 pm 4:05 pm 5:05 pm 6:05 pm') + L('10:00 am 4:20 pm', '', '1')),
     'Wong Shek → Tap Mun': kd(wd=L('8:30 am 12:30 pm 2:30 pm 4:30 pm 6:30 pm') + L('10:35 am 4:55 pm', '', '1'), sat=L('8:30 am 9:30 am 11:30 am 12:30 pm 1:30 pm 2:35 pm 3:35 pm 4:35 pm 5:35 pm 6:35 pm') + L('10:35 am 4:55 pm', '', '1'),
                                   sun=L('8:30 am 9:30 am 11:30 am 12:30 pm 1:30 pm 2:35 pm 3:35 pm 4:35 pm 5:35 pm 6:35 pm') + L('10:35 am 4:55 pm', '', '1'))},
    [['Mon–Fri', '11'], ['Sat, Sun & holidays', '16']], remnotes={'1': 'via Ko Lau Wan & Chek Keng'})
run_wd = [[510, '', 'Ma Liu Shui 08:30 → Sham Chung 09:00 → Lai Chi Chong 09:15 → Tap Mun 10:00 → Ko Lau Wan 10:05 → Chek Keng 10:20 → Wong Shek 10:35'],
          [645, '', 'Back: Chek Keng 10:45 → Ko Lau Wan 11:00 → Tap Mun 11:10 → Lai Chi Chong 11:40 → Sham Chung 11:55 → Ma Liu Shui 12:25'],
          [900, '', 'Ma Liu Shui 15:00 → Sham Chung 15:30 → Lai Chi Chong 15:45 → Tap Mun 16:20 → Ko Lau Wan 16:25 → Chek Keng 16:40 → Wong Shek 16:55'],
          [1025, '', 'Back: Chek Keng 17:05 → Ko Lau Wan 17:20 → Tap Mun 17:30 → Lai Chi Chong 18:00 → Sham Chung 18:15 → Ma Liu Shui 18:45']]
run_we = sorted(run_wd[:2] + [[750, '', 'Ma Liu Shui 12:30 → Sham Chung 13:00 → Lai Chi Chong 13:15 → Tap Mun 13:45'],
                                [855, '', 'Back: Lai Chi Chong 14:15 → Sham Chung 14:30 → Ma Liu Shui 15:00 (Tap Mun departure not shown in the source)']] + run_wd[2:])
kaito('k-mls-tapmun', 'Ma Liu Shui ⇄ Tap Mun', 'Tsui Wah Ferry', 'From Ma Liu Shui Ferry Pier (Science Park Rd, near University station) up Tolo Harbour to Tap Mun and Wong Shek. Each row is a whole run with its stops. Hotline 2272 2022.',
    {'Runs': {'wd': run_wd, 'sat': run_we, 'sun': run_we}}, [['Mon–Fri', '20'], ['Sat, Sun & holidays', '30']])
kaito('k-tpc', 'Ma Liu Shui ⇄ Tung Ping Chau', 'Tsui Wah Ferry', 'Ma Liu Shui Ferry Pier to Tung Ping Chau Public Pier. Weekends and public holidays only. Saturday return times are 15:30 and 17:15 as listed by the Transport Department; confirm on 2272 2022. Return tickets are valid for one round trip.',
    {'Ma Liu Shui → Tung Ping Chau': kd(sat=L('9.00 a.m.'), sun=L('9.00 a.m.')), 'Tung Ping Chau → Ma Liu Shui': kd(sat=L('3.30 p.m. 5.15 p.m.'), sun=L('5.15 p.m.'))},
    [['Adult / child · round trip', '100'], ['65+ / disabled · single', '50']], daynotes={'wd': 'No service Monday to Friday.'})
kaito('k-sk-kausai', 'Sai Kung ⇄ Kau Sai / High Island', 'Tsui Wah Ferry', 'Sai Kung Public Pier via Kau Sai Village to Leung Shuen Wan (High Island). Weekends and public holidays. Each outbound run calls at Kau Sai 30 min after leaving Sai Kung and High Island 30 min after that. Return sailings are not clear in the published table; call 2272 2022.',
    {'Outbound runs': {dc: [[m, '', f'Kau Sai {fmt_t(m + 30)} → High Island {fmt_t(m + 60)}'] for m in (570, 690, 870, 990)] for dc in ('sat', 'sun')}},
    [['Adult / child · maximum per single trip', '65']], daynotes={'wd': 'No service Monday to Friday.'})
kaito('k-tko-swh', 'Tseung Kwan O (South) ⇄ Sai Wan Ho', 'Yun Lee Marine', 'Tseung Kwan O (South) Landing to Shau Kei Wan Typhoon Shelter Landing No. 10. Weekends and public holidays only. Hotline 2771 7742.',
    {'Sai Wan Ho → Tseung Kwan O': kd(sat=L('9.30 am 10.40 am 11.30 am 1.15 pm 2.15 pm 3.25 pm 4.15 pm 5.15 pm 6.15 pm'), sun=L('9.30 am 10.40 am 11.30 am 1.15 pm 2.15 pm 3.25 pm 4.15 pm 5.15 pm 6.15 pm')),
     'Tseung Kwan O → Sai Wan Ho': kd(sat=L('10.00 am 11.05 am 11.55 am 1.45 pm 2.45 pm 3.50 pm 4.45 pm 5.45 pm 6.45 pm'), sun=L('10.00 am 11.05 am 11.55 am 1.45 pm 2.45 pm 3.50 pm 4.45 pm 5.45 pm 6.45 pm'))},
    [['Adult · maximum single', '16.8'], ['Child / 65+ · single', '8.5']], daynotes={'wd': 'No service Monday to Friday.'})
kaito('k-abd-alc', 'Aberdeen ⇄ Ap Lei Chau', 'Eastern Ferry', 'About 4 min. Two Aberdeen piers. Hotline 2873 0310. Octopus users get a HK$0.50 discount when interchanging with the MTR within 90 minutes.',
    {}, [['Adult', '3'], ['Child', '1.5']],
    freq={'Aberdeen Promenade pier': {dc: [['From Aberdeen 07:10–22:45', '5–8'], ['From Ap Lei Chau 07:00–22:50', '5–8']] for dc in ('wd', 'sat', 'sun')},
          'Fish Market pier': {dc: [['From Aberdeen 06:10–23:50', '5–8'], ['From Ap Lei Chau 06:00–23:45', '5–8']] for dc in ('wd', 'sat', 'sun')}})
kaito('k-mls-lcw', 'Ma Liu Shui ⇄ Lai Chi Wo', 'Best Sonic', 'About 90 min. Weekdays run on demand only; phone 2555 9269 first. Extra sailings may run if busy.',
    {'Ma Liu Shui → Lai Chi Wo': kd(sat=L('9:00 a.m.'), sun=L('9:00 a.m.')), 'Lai Chi Wo → Ma Liu Shui': kd(sat=L('3:30 p.m.'), sun=L('3:30 p.m.'))},
    [['Single', '45']], daynotes={'wd': 'Weekdays: on demand only.'})
kaito('k-mls-kato', 'Ma Liu Shui ⇄ Kat O / Ap Chau', 'Best Sonic', 'Weekends and public holidays. Hotline 2555 9269.',
    {'All sailings': kd(sat=L('9.00 a.m.', 'from Ma Liu Shui') + L('10.45 a.m. 3.30 p.m.', 'from Kat O') + L('12.30 p.m.', 'from Ap Chau'), sun=L('9.00 a.m.', 'from Ma Liu Shui') + L('10.45 a.m. 3.30 p.m.', 'from Kat O') + L('12.30 p.m.', 'from Ap Chau'))},
    [['Single', '45']], daynotes={'wd': 'No service Monday to Friday.'})
sk = lambda m, t: [m, '', t]
stk = [sk(510, 'Lai Chi Wo 09:00 → Kat O 09:15 → Ap Chau 09:30 → back at Sha Tau Kok about 09:45'), sk(630, 'Ap Chau 11:00 → Kat O 11:15 → Lai Chi Wo 11:30 → back about 11:55'),
       sk(750, 'Lai Chi Wo 13:00 → Kat O 13:15 → Ap Chau 13:30 → back about 13:45'), sk(915, 'Ap Chau 15:45 → Kat O 16:00 → Lai Chi Wo 16:15 → back about 16:40'), sk(1020, 'Kat O, arriving about 17:20')]
kaito('k-stk', 'Sha Tau Kok ⇄ Lai Chi Wo / Ap Chau / Kat O', 'Best Sonic', 'Departures from Sha Tau Kok Public Pier, each with its stops. You need a Sha Tau Kok Closed Area Permit to travel back to Sha Tau Kok. Extra sailings may run if busy. Hotline 2555 9269.',
    {'Runs': {dc: stk for dc in ('wd', 'sat', 'sun')}}, [['Single', '40']], daynotes={'wd': 'Daily except Tuesdays (public holidays run).'})
kaito('k-tsh', 'Tai Shui Hang ⇄ Lai Chi Wo / Kat O / Ap Chau', 'Best Sonic', 'Tuesdays only (not public holidays). The published table is hard to read, so only the confirmed departure is listed. Phone 2555 9269 for the rest.',
    {'Tai Shui Hang → Lai Chi Wo': kd(wd=L('9:00 am', 'from Tai Shui Hang'))}, [['Whole trip from Tai Shui Hang', '80'], ['Whole trip from Lai Chi Wo / Kat O / Ap Chau', '60']],
    daynotes={'wd': 'Tuesdays only. No other weekday service.', 'sat': 'No service.', 'sun': 'No service.'})

# ---- "Going to..." destinations. mins = crossing time; approx = my estimate, not from the source data ----
def leg(r, origin, out, back, mins, approx=False, outLeg=None):
    return dict(r=r, origin=origin, out=out, back=back, mins=mins, approx=approx, outLeg=outLeg)
D = [
 dict(id='to-cheungchau', name='Cheung Chau', legs=[leg('cc', 'Central', 'Central to Cheung Chau', 'Cheung Chau to Central', 40)]),
 dict(id='to-muiwo', name='Mui Wo', legs=[leg('mw', 'Central', 'Central to Mui Wo', 'Mui Wo to Central', 40)]),
 dict(id='to-pengchau', name='Peng Chau', legs=[leg('pc', 'Central', 'Central to Peng Chau', 'Peng Chau to Central', 40, True)]),
 dict(id='to-yungshuewan', name='Yung Shue Wan (Lamma)', legs=[leg('ysw', 'Central', 'Central to Yung Shue Wan', 'Yung Shue Wan to Central', 30, True), leg('abd-ysw', 'Aberdeen', 'Aberdeen to Yung Shue Wan', 'Yung Shue Wan to Aberdeen', 25, True)]),
 dict(id='to-sokkwuwan', name='Sok Kwu Wan (Lamma)', legs=[leg('skw', 'Central', 'Central to Sok Kwu Wan', 'Sok Kwu Wan to Central', 40, True), leg('abd-skw', 'Aberdeen', 'Aberdeen to Sok Kwu Wan', 'Sok Kwu Wan to Aberdeen', 30, True)]),
 dict(id='to-discoverybay', name='Discovery Bay', legs=[leg('db', 'Central', 'Central to Discovery Bay', 'Discovery Bay to Central', 30, True)]),
 dict(id='to-hunghom', name='Hung Hom', legs=[leg('c-hh', 'Central', 'Central to Hung Hom', 'Hung Hom to Central', 16), leg('np-hh', 'North Point', 'North Point to Hung Hom', 'Hung Hom to North Point', 8)]),
 dict(id='to-kowlooncity', name='Kowloon City', legs=[leg('np-kc', 'North Point', 'North Point to Kowloon City', 'Kowloon City to North Point', 14)]),
 dict(id='to-kwuntong', name='Kwun Tong', legs=[leg('np-kt', 'North Point', 'North Point to Kwun Tong', 'Kwun Tong to North Point', 12), leg('swh-kt', 'Sai Wan Ho', 'Sai Wan Ho to Kwun Tong', 'Kwun Tong to Sai Wan Ho', 15)]),
 dict(id='to-tunglung', name='Tung Lung Chau', legs=[leg('k-tl-swh', 'Sai Wan Ho', 'Sai Wan Ho → Tung Lung Chau', 'Tung Lung Chau → Sai Wan Ho', 25, True), leg('k-tl-skt', 'Sam Ka Tsuen', 'Sam Ka Tsuen → Tung Lung Chau', 'Tung Lung Chau → Sam Ka Tsuen', 25, True)]),
 dict(id='to-potoi', name='Po Toi', legs=[leg('k-potoi', 'Aberdeen', 'To Po Toi', 'From Po Toi', 60, True, 'from Aberdeen'), leg('k-potoi', 'Stanley', 'To Po Toi', 'From Po Toi', 45, True, 'from Stanley')]),
 dict(id='to-tapmun', name='Tap Mun', legs=[leg('k-tapmun', 'Wong Shek', 'Wong Shek → Tap Mun', 'Tap Mun → Wong Shek', 35, True)]),
]
ids = {r['id']: r for r in R}
for d in D:
    for l in d['legs']:
        assert l['out'] in ids[l['r']]['dirs'] and l['back'] in ids[l['r']]['dirs'], (d['id'], l)

# ---- Piers: names from the Transport Department's service details; coordinates from OpenStreetMap (a = approximate pin) ----
P = {
 'central-2': ('Central Pier 2', 22.28835, 114.15660), 'central-3': ('Central Pier 3', 22.28751, 114.15736), 'central-4': ('Central Pier 4', 22.28779, 114.15841),
 'central-5': ('Central Pier 5', 22.28769, 114.15939), 'central-6': ('Central Pier 6', 22.28736, 114.16028), 'central-7': ('Central Pier 7 (Star Ferry)', 22.28704, 114.16119),
 'central-8': ('Central Pier 8', 22.28667, 114.16206), 'tst': ('Tsim Sha Tsui Star Ferry Pier', 22.29354, 114.16799), 'wanchai': ('Wan Chai Ferry Pier', 22.28209, 114.17580),
 'np-west': ('North Point (West) Ferry Pier', 22.29315, 114.20202), 'np-east': ('North Point (East) Ferry Pier', 22.29414, 114.20087),
 'hh-north': ('Hung Hom (North) Ferry Pier', 22.30112, 114.19025), 'hh-south': ('Hung Hom (South) Ferry Pier', 22.30051, 114.18927),
 'kowloon-city': ('Kowloon City Ferry Pier', 22.31784, 114.19431), 'kaitak': ('Kai Tak Runway Park Pier', 22.30983, 114.21327), 'kwuntong': ('Kwun Tong Ferry Pier', 22.30637, 114.22165),
 'swh': ('Sai Wan Ho Ferry Pier', 22.28636, 114.22410), 'skt': ('Sam Ka Tsuen Ferry Pier', 22.29077, 114.23649), 'shaukeiwan': ('Shau Kei Wan Typhoon Shelter Landing 10', 22.28468, 114.22530),
 'aberdeen': ('Aberdeen Promenade pier', 22.24733, 114.15422, 1), 'stanley': ('Blake Pier, Stanley', 22.21742, 114.21014), 'potoi': ('Po Toi Public Pier', 22.16504, 114.25311), 'alc': ('Ap Lei Chau pier', 22.24416, 114.15429, 1),
 'cheungchau': ('Cheung Chau Ferry Pier', 22.20858, 114.02834), 'muiwo': ('Mui Wo Ferry Pier', 22.26512, 114.00231), 'pengchau': ('Peng Chau Ferry Pier', 22.28448, 114.03714), 'chimawan': ('Chi Ma Wan Pier', 22.23954, 113.99989),
 'ysw': ('Yung Shue Wan Ferry Pier', 22.22633, 114.10880), 'skw': ('Sok Kwu Wan Pier', 22.20628, 114.13123), 'pakkok': ('Pak Kok Tsuen Pier', 22.23650, 114.10998), 'motat': ('Mo Tat Wan', 22.20878, 114.14420, 1),
 'db': ('Discovery Bay Pier', 22.29702, 114.01796), 'dbn': ('Discovery Bay North Pier', 22.30636, 114.01715), 'nimshuewan': ('Nim Shue Wan (Discovery Bay)', 22.29260, 114.02083, 1), 'trappist': ('Trappist Monastery Pier', 22.28189, 114.02284),
 'mawan': ('Park Island Ferry Pier, Ma Wan', 22.35288, 114.06441), 'tsuenwan': ('Tsuen Wan Ferry Pier', 22.36668, 114.11070), 'tuenmun': ('Tuen Mun Ferry Pier', 22.37163, 113.96598),
 'tungchung': ('Tung Chung Development Pier', 22.29432, 113.94038), 'shalowan': ('Sha Lo Wan Pier', 22.29333, 113.90410), 'taio': ('Tai O Promenade landing steps', 22.25248, 113.86095),
 'mls': ('Ma Liu Shui Ferry Pier', 22.41718, 114.21441), 'tapmun': ('Tap Mun Pier', 22.47034, 114.35860), 'wongshek': ('Wong Shek Pier', 22.43564, 114.33735), 'tunglung': ('Tung Lung Chau Public Pier', 22.25462, 114.28897),
 'tungpingchau': ('Tung Ping Chau Public Pier', 22.54478, 114.43320), 'skwan': ('Sai Kung Public Pier', 22.38118, 114.27583), 'kausai': ('Kau Sai Village Pier', 22.34231, 114.32060), 'highisland': ('Leung Shuen Wan (High Island) Pier', 22.35049, 114.35292),
 'lcw': ('Lai Chi Wo landing steps', 22.52964, 114.26333), 'kato': ('Kat O Pier', 22.55009, 114.28995), 'apchau': ('Ap Chau Public Pier', 22.55042, 114.26976), 'stk': ('Sha Tau Kok Public Pier', 22.54248, 114.22672),
 'tko': ('Tseung Kwan O (South) Landing',), 'taishuihang': ('Tai Shui Hang (Ma On Shan, Area 77)',),
}
PIERS = {k: dict(n=v[0], la=v[1] if len(v) > 1 else None, lo=v[2] if len(v) > 1 else None, a=1 if len(v) > 3 else 0) for k, v in P.items()}
RP = {'star-central': ['central-7', 'tst'], 'star-wanchai': ['wanchai', 'tst'], 'np-hh': ['np-west', 'hh-north'], 'np-kc': ['np-west', 'kowloon-city'], 'np-kt': ['np-east', 'kwuntong', 'kaitak'],
 'swh-kt': ['swh', 'kwuntong'], 'swh-skt': ['swh', 'skt'], 'c-hh': ['central-8', 'hh-south'], 'cc': ['central-5', 'cheungchau'], 'mw': ['central-6', 'muiwo'], 'pc': ['central-6', 'pengchau'],
 'ysw': ['central-4', 'ysw'], 'skw': ['central-4', 'skw'], 'inter': ['pengchau', 'muiwo', 'chimawan', 'cheungchau'], 'abd-ysw': ['aberdeen', 'pakkok', 'ysw'], 'abd-skw': ['aberdeen', 'motat', 'skw'],
 'db': ['central-3', 'db', 'dbn'], 'db-mw': ['nimshuewan', 'pengchau', 'muiwo'], 'db-pc': ['pengchau', 'nimshuewan', 'trappist'], 'mawan-c': ['central-2', 'mawan'], 'mawan-tw': ['mawan', 'tsuenwan'],
 'tm-to': ['tuenmun', 'tungchung', 'shalowan', 'taio'], 'k-tl-swh': ['shaukeiwan', 'tunglung'], 'k-tl-skt': ['skt', 'tunglung'], 'k-potoi': ['aberdeen', 'stanley', 'potoi'], 'k-tapmun': ['tapmun', 'wongshek'],
 'k-mls-tapmun': ['mls', 'tapmun', 'wongshek'], 'k-tpc': ['mls', 'tungpingchau'], 'k-sk-kausai': ['skwan', 'kausai', 'highisland'], 'k-tko-swh': ['tko', 'shaukeiwan'], 'k-abd-alc': ['aberdeen', 'alc'],
 'k-mls-lcw': ['mls', 'lcw'], 'k-mls-kato': ['mls', 'kato', 'apchau'], 'k-stk': ['stk', 'lcw', 'kato', 'apchau'], 'k-tsh': ['taishuihang', 'lcw', 'kato', 'apchau']}
for r in R: r['piers'] = RP.get(r['id'], [])

# ---- Search keywords: places people type that are not in a route's name ----
ALIAS = {'ysw': 'Lamma Island', 'skw': 'Lamma Island', 'abd-ysw': 'Lamma Island', 'abd-skw': 'Lamma Island',
 'cc': 'Cheung Chau Island', 'mw': 'Lantau Island Silvermine Bay', 'pc': 'Peng Chau Hei Ling Chau', 'inter': 'Lantau Island Chi Ma Wan',
 'db': 'Lantau Island DB', 'db-mw': 'Lantau Island DB', 'db-pc': 'Lantau Island DB Trappist', 'mawan-c': 'Ma Wan Lantau Island Park Island', 'mawan-tw': 'Ma Wan Lantau Island Park Island',
 'tm-to': 'Lantau Island Tai O Tung Chung Tuen Mun Sha Lo Wan', 'star-central': 'TST Kowloon Hong Kong Island', 'star-wanchai': 'TST Kowloon Hong Kong Island',
 'c-hh': 'Kowloon Hong Kong Island', 'np-hh': 'Kowloon Hong Kong Island', 'np-kc': 'Kowloon Hong Kong Island', 'np-kt': 'Kowloon Hong Kong Island',
 'k-tl-swh': 'Tung Lung Island', 'k-tl-skt': 'Tung Lung Island Yau Tong', 'k-potoi': 'Po Toi Island Stanley Aberdeen', 'k-tapmun': 'Grass Island Sai Kung Wong Shek',
 'k-mls-tapmun': 'Grass Island Tolo Harbour Sai Kung Wong Shek University', 'k-tpc': 'Ping Chau Tolo Harbour University', 'k-sk-kausai': 'Kau Sai Chau High Island', 'k-tko-swh': 'TKO',
 'k-mls-lcw': 'Tolo Harbour University', 'k-mls-kato': 'Tolo Harbour University', 'k-stk': 'Closed Area', 'k-abd-alc': 'Ap Lei Chau Southern'}
for r in R:
    r['tags'] = (ALIAS.get(r['id'], '') + (' kaito small ferry' if r['group'].startswith('Kaito') else '')).strip()

assert all(p in PIERS for ps in RP.values() for p in ps)
OVR = {'cc': dict(info='Central Pier 5. Fast ferry about 35–40 min; ordinary ferries are slower and marked.'),
       'mw': dict(info='Central Pier 6 (Eastern Berth). Fast ferry about 35–40 min; ordinary ferries are slower and marked.'),
       'pc': dict(info='Central Pier 6 (Western Berth). Includes the Peng Chau ⇄ Hei Ling Chau legs. Timetable effective 1 Apr 2026.'),
       'ysw': dict(info='Central Pier 4.'), 'skw': dict(info='Central Pier 4 to Sok Kwu Wan Pier No. 2.'),
       'abd-ysw': dict(op='Tsui Wah Ferry', info='From the Aberdeen Promenade pontoon, calling at Pak Kok Tsuen.'),
       'abd-skw': dict(op='Chuen Kee Ferry', info='From the Aberdeen Promenade pontoon, calling at Mo Tat.'),
       'db': dict(op='Discovery Bay Transportation', info='Central Pier 3. A few sailings go to Discovery Bay North.'),
       'db-pc': dict(op='Tsui Wah Ferry'), 'mawan-c': dict(op='Park Island Transport', info='Central Pier 2 ⇄ Park Island Pier, Ma Wan.'),
       'mawan-tw': dict(op='Park Island Transport', info='Park Island Pier, Ma Wan ⇄ Tsuen Wan Ferry Pier.')}
for r in R:
    r.update(OVR.get(r['id'], {}))
for d_ in D:
    pass
LEGPIER = {('cc', 'Central'): 'central-5', ('mw', 'Central'): 'central-6', ('pc', 'Central'): 'central-6', ('ysw', 'Central'): 'central-4', ('abd-ysw', 'Aberdeen'): 'aberdeen', ('skw', 'Central'): 'central-4',
           ('abd-skw', 'Aberdeen'): 'aberdeen', ('db', 'Central'): 'central-3', ('c-hh', 'Central'): 'central-8', ('np-hh', 'North Point'): 'np-west', ('np-kc', 'North Point'): 'np-west', ('np-kt', 'North Point'): 'np-east',
           ('swh-kt', 'Sai Wan Ho'): 'swh', ('k-tl-swh', 'Sai Wan Ho'): 'shaukeiwan', ('k-tl-skt', 'Sam Ka Tsuen'): 'skt', ('k-potoi', 'Aberdeen'): 'aberdeen', ('k-potoi', 'Stanley'): 'stanley', ('k-tapmun', 'Wong Shek'): 'wongshek'}
for d_ in D:
    for l_ in d_['legs']:
        l_['pier'] = LEGPIER.get((l_['r'], l_['origin']))
json.dump({'routes': R, 'dest': D, 'piers': PIERS}, open(OUT, 'w'), ensure_ascii=False, separators=(',', ':'))
print(len(R), 'routes', sum(len(r['dirs']) for r in R), 'dirs')
for r in R: print(r['id'], len(r['fares']), 'fares', [(d, {k: len(v) for k, v in dd.items()}) for d, dd in list(r['dirs'].items())[:1]])
