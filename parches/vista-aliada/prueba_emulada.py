# Prueba del código parcheado real (emulado) sobre el estado de una partida guardada.
# Uso: python prueba_emulada.py <DarklordAV.exe> <partida.SAV> <dirección hex de la rutina "turn">
#   ej.: python prueba_emulada.py dist\vista-aliada\DarklordAV.exe C:\Warlords3\SAVES\hide01.SAV 6b0190
#   (la dirección la imprime build.py en la línea "caves"; requiere pefile y unicorn)
import pefile, struct, sys
from unicorn import *
from unicorn.x86_const import *
EXE=sys.argv[1]; SAV=sys.argv[2]
pe=pefile.PE(EXE); img=pe.get_memory_mapped_image()
b=open(SAV,'rb').read()
mu=Uc(UC_ARCH_X86,UC_MODE_32)
mu.mem_map(0x400000,(len(img)+0xfff)&~0xfff); mu.mem_write(0x400000,img)
STK=0x10000000; mu.mem_map(STK,0x100000); mu.mem_map(0xdead0000,0x1000)
off=0x6d
for va,n in ((0x503e00,0x12),(0x503e58,0x32000),(0x535ed0,0xa96),(0x536b30,0x2d894)):
    mu.mem_write(va,b[off:off+n]); off+=n
opt=mu.mem_read(0x53c38e,1)[0]; mu.mem_write(0x53c38e,bytes([opt|0x80]))
W,H=struct.unpack('<hh',mu.mem_read(0x503e00,4)); sh=mu.mem_read(0x503e06,1)[0]
TURN=int(sys.argv[3],16)
def tiles():
    m=mu.mem_read(0x503e58,0x32000)
    return {(x,y):(m[((y*10)<<sh)+x*10+4],m[((y*10)<<sh)+x*10+5]) for y in range(H) for x in range(W)}
def know(t,p): return {k for k,(e,s) in t.items() if e>>p&1}
def own(t,p): return {k for k,(e,s) in t.items() if e>>p&1 and not s>>p&1}
def call(addr,args,stop,regs={}):
    sp=STK+0x80000
    for a in reversed(args): sp-=4; mu.mem_write(sp,struct.pack('<i',a))
    sp-=4; mu.mem_write(sp,struct.pack('<I',0xdead0000))
    mu.reg_write(UC_X86_REG_ESP,sp)
    for r,v in regs.items(): mu.reg_write(r,v)
    mu.emu_start(addr,stop,count=50_000_000)
def diplo(a,c,v):
    mu.mem_write(0x55ee4c+a*56+c,bytes([v])); mu.mem_write(0x55ee4c+c*56+a,bytes([v]))
def show(tag):
    t=tiles(); print(f'{tag:34}', [len(know(t,p)) for p in range(4)], 'prestadas', [len(know(t,p)-own(t,p)) for p in range(4)]); return t
ok=True
def check(c,msg):
    global ok; print('   ', 'OK ' if c else 'FALLA', msg); ok&=c
t0=show('inicial (2 y 3 aliados)')
own2_0=know(t0,2); own3_0=know(t0,3); k0=know(t0,0)
call(TURN,[2],0x442470); t1=show('turno de 2')
check(know(t1,2)==own2_0|own3_0,'2 conoce lo suyo + lo de 3')
check(own(t1,2)==own2_0,'lo propio de 2 no cambió')
call(0x441b30,[40,50,3,3],0xdead0000); t2=show('3 revela (40,50) r3')
rv=know(t2,3)-own3_0
check(rv<=know(t2,2) and rv<=own(t2,3),'lo nuevo de 3 es propio de 3 y llega a 2')
# 2 revela por sí mismo una casilla que tenía prestada
pres=sorted(know(t2,2)-own(t2,2)); px,py=pres[len(pres)//2]
call(0x441b30,[px,py,0,2],0xdead0000); t3=show(f'2 revela ({px},{py}) r0 (prestada)')
check((px,py) in own(t3,2),'esa casilla pasa a ser propia de 2')
diplo(2,3,2)
call(TURN,[2],0x442470); t4=show('guerra 2-3, turno de 2')
check(know(t4,2)==own2_0|{(px,py)},'2 vuelve a lo propio (+ la casilla que vio él)')
check(know(t4,3)==know(t2,3),'3 sin cambios hasta su turno')
check(know(t4,0)==k0,'control: 0 sin cambios')
call(TURN,[3],0x442470); t5=show('turno de 3')
check(know(t5,3)==own3_0|rv,'3 queda con lo propio')
call(0x441b30,[px,py,1,3],0xdead0000); t6=show('3 revela de nuevo (enemigo)')
check(not (know(t6,3)-own3_0-rv) - know(t6,3) and know(t6,2)==know(t4,2),'2 no recibe nada de su enemigo')
# rectángulo: 0x41fab0(p, x, y, w, h) para p=2 sobre zona prestada con alianza
diplo(2,3,0); call(TURN,[2],0x442470); t7=show('alianza de nuevo, turno de 2')
pres=sorted(know(t7,2)-own(t7,2)); rx,ry=pres[0]
call(0x41fab0,[2,rx,ry,2,2],0x41fbf6); t8=show(f'rectángulo de 2 en ({rx},{ry}) 2x2')
check((rx,ry) in own(t8,2),'casilla del rectángulo pasa a ser propia')
# inicio de partida: el bucle de 0x4418df..0x441989 con bl=0 borra explorado y prestado
mu.reg_write(UC_X86_REG_ESP,STK+0x80000); mu.reg_write(UC_X86_REG_EBX,0)
mu.mem_write(STK+0x80000,bytes(32))
mu.emu_start(0x4418df,0x441989,count=50_000_000); t9=show('inicio de partida')
check(all(e==0 and s==0 for e,s in t9.values()),'todo en 0')
print('RESULTADO:', 'TODO OK' if ok else 'HAY FALLAS')
