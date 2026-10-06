# Transcripción a Python de DarklordsValidator (Unit.cs, AbilityTable.cs, ParserUtils.cs, RulesEngine.cs): reglas 1-25.
# build.py arma con esto la tabla de Power; prueba_reglas\comparar.py compara el parche con el validador real.
import re, os, struct
TABLE = {1:"Leadership",2:"Chaos",3:"Morale",4:"Fear",5:"Siege",6:"Fortify",7:"Movement",8:"Strength",9:"Move Bonus",
10:"Gold",11:"Gold per City",12:"Engineer",13:"Fly",14:"Hits",15:"Speed",16:"Invisibility",17:"Group Movement",
18:"Group Hits",19:"Port",20:"Spell",21:"Production",22:"Summon Army",23:"View",24:"View (group)",25:"Bless",
26:"Poison",27:"Disease",28:"Assassin",29:"Reveal Map",30:"Missiles",31:"Medals",32:"Trample",33:"Curse",
34:"Teleport",35:"Summon Item",36:"xx",37:"Banding",38:"Acid",39:"Lightning",40:"Paralysis",41:"Warding",
42:"Acid (group)",43:"Lightning (group)",44:"Dragonslayer",45:"Demonslayer",46:"Deathslayer",47:"Humanslayer",
48:"bb",49:"Dwarfslayer",50:"Orcslayer",51:"Necromancy",52:"Warding (group)",53:"Necromancy",54:"Life Drain",
55:"Questing",56:"Mana Drain",57:"None"}
NOVALUE = {13,16,44,45,46,47,49,50,55,57}
def getname(c): return TABLE.get(c, f'Ability_{c}')

def legacy(bs):   # ReadLegacyString: Encoding.ASCII (byte > 0x7f -> '?'), corta en el primer nulo, solo 32..126
    s = ''.join(chr(c) if c < 0x80 else '?' for c in bs.split(b'\0')[0])
    return ''.join(ch for ch in s if 32 <= ord(ch) <= 126).strip()
def ntlen_str(b, off):   # ReadNullTerminatedLength + ReadLegacyString
    e = off
    while e < len(b) and b[e] != 0: e += 1
    return legacy(b[off:e])

def is_none_token(s):
    if s.strip() == '': return True
    t = s.strip().lower()
    return t in ('none', 'n/a', '-', '—', 'none +0', 'none+0')
NONE_RE = re.compile(r'\bnone\b|\bn\/a\b|\b-\b', re.ASCII)
def parse(raw):
    t = re.sub(r'\s+', ' ', raw.strip())
    if not t: return ('', 0, True)
    lower = t.lower()
    if is_none_token(lower) or NONE_RE.search(lower): return ('', 0, True)
    num = None
    m = re.search(r'([+-]?\d+)', t, re.ASCII)
    if m:
        v = int(m.group(1))
        if -2**31 <= v < 2**31: num = v
    bonus = num or 0
    ab = re.sub(r'[+-]?\d+', '', t, flags=re.ASCII).replace('+', '').strip()
    ab = re.sub(r'\s+', ' ', ab).lower()
    if not ab: return ('', 0, True) if num is None else ('', bonus, False)
    return (ab, bonus, False)
def normalizar(raw):
    ab, bonus, none = parse(raw or '')
    if none: return ''
    if not ab: return f'+{bonus}' if bonus else ''
    return f'{ab} +{bonus}' if bonus else ab

def unit(b, ship):
    u = {}
    u['Strength'], u['Move'], u['Hits'], u['Turns'], u['Upkeep'] = b[0x9a], b[0x9b], b[0x9c], b[0x9d], b[0x9e]
    mbs = [legacy(b[0xb2 + 9 * i:0xbb + 9 * i]) for i in range(4)]
    u['MoveBonuses'] = [m for m in mbs if m.strip() and m.lower() != 'none']
    cn = ntlen_str(b, 0xd6); cv = b[0xdf]
    u['CombatBonus'] = '' if (cn.strip() == '' or cn == 'none') else f'{cn} +{cv}'
    pc, pv = b[0xe6], b[0xe8]
    nm = getname(pc)
    u['Power'] = nm if pc in NOVALUE else ('' if pc == 0 or pv == 0 else f'{nm} +{pv}')
    u['Cost'], u['Setup'] = struct.unpack_from('<HH', b, 0xe2)
    u['IsAShip'] = ship
    return u

def power_value(p):
    if not p.strip(): return 0
    k = p.rfind('+')
    if 0 <= k < len(p) - 1:
        try: return int(p[k+1:].strip())
        except ValueError: return 0
    return 0

def validar(u):
    cb, pw = normalizar(u['CombatBonus']), normalizar(u['Power'])
    mbs = [m.lower() for m in u['MoveBonuses']]
    fly = 'fly' in mbs; land = 'landing' in mbs; carr = 'carrier' in mbs
    ship = u['IsAShip']; terr = not fly and not ship
    hp = pw.strip() != ''; hc = cb.strip() != ''; pv = power_value(pw)
    M, S, H, T, U, C, SE = u['Move'], u['Strength'], u['Hits'], u['Turns'], u['Upkeep'], u['Cost'], u['Setup']
    R = [
        terr and M > 25,                                                     # 1
        terr and hp and 'trample' in pw.lower() and M > 15,
        terr and hp and pw.lower().startswith('siege') and pv > 2 and M > 17,
        fly and M > 40,                                                      # 4
        fly and hp and pw.lower().startswith('trample') and M > 20,
        fly and hp and pw.lower().startswith('siege') and pv > 2 and M > 22,
        ship and M > 30,                                                     # 7
        ship and land and M > 12,
        fly and (S > 3 or H > 1) and (SE < 600 or U < 10 or T < 3),          # 9
        fly and (S > 6 or H > 2) and (SE < 800 or U < 15 or T < 4),
        fly and (S > 8 or H > 3) and (SE < 1000 or U < 20 or T < 5),
        terr and (S > 3 or H > 1) and (SE < 300 or U < 5 or T < 2),
        terr and (S > 6 or H > 2) and (SE < 400 or U < 10 or T < 3),
        terr and (S > 8 or H > 3) and (SE < 500 or U < 15 or T < 4),
        fly and (hp or hc) and (C < 600 or U < 10),
        fly and hp and hc and (C < 800 or U < 15),
        fly and pv > 4 and (C < 1000 or U < 20),
        terr and (hp or hc) and (C < 150 or U < 4),
        terr and hp and hc and (C < 300 or U < 8),
        terr and pv > 4 and (C < 500 or U < 12),
        ship and (hp or hc) and (C < 400 or U < 8),                          # 21
        ship and hp and hc and (C < 600 or U < 12),
        ship and pv > 4 and (C < 800 or U < 18),
        ship and land and (C < 1000 or U < 17),
        ship and carr and (C < 1200 or U < 34),                              # 25
    ]
    return [i + 1 for i, r in enumerate(R) if r]
