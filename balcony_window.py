"""Four-column balcony glazing, user elevation 4600 x 2300 mm.
Nominal widths 700/1600/1600/700 fit the existing 4560 mm CAD opening.
Plan +Y is outdoors. Both end casements hinge on the outer jambs.
"""
import math

def build_balcony_window(api):
    box,rect,tube=api['box'],api['rect'],api['tube']
    x0,x1,y,z0,z1=1.0,5.56,10.11,.03,2.33
    w=x1-x0;side=w*700/4600;mid=w*1600/4600
    cuts=[x0,x0+side,x0+side+mid,x1-side,x1];f=.05;depth=.06
    def panel(name,a,b,c,d,material='window_frame'):
        return rect(name,a,b,y-depth/2,y+depth/2,c,d,material,'Windows','balcony',.002)
    for a,b in [(x0,x0+f),(x1-f,x1)]:panel('阳台四列外框立柱',a,b,z0,z1)
    for a,b in [(z0,z0+f),(z1-f,z1)]:panel('阳台四列外框横梁',x0,x1,a,b)
    for x in cuts[1:-1]:panel('阳台四列竖梃',x-f/2,x+f/2,z0+f,z1-f)
    split=z0+1.0
    for a,b in [(cuts[0]+f,cuts[1]-f/2),(cuts[3]+f/2,cuts[4]-f)]:
        panel('阳台边列上下分格横梃',a,b,split-f/2,split+f/2)
    for name,a,b,c,d,nominal in [
        ('F1中央固定玻璃',cuts[1]+f/2,cuts[2]-f/2,z0+f,z1-f,1600),
        ('F2中央固定玻璃',cuts[2]+f/2,cuts[3]-f/2,z0+f,z1-f,1600),
        ('F3左下固定玻璃',x0+f,cuts[1]-f/2,z0+f,split-f/2,700),
        ('F4右下固定玻璃',cuts[3]+f/2,x1-f,z0+f,split-f/2,700)]:
        o=rect('阳台'+name,a,b,y-.008,y+.008,c,d,'glass','Windows','balcony',0)
        o['nominal_column_mm']=nominal;o['window_type']='fixed'
        if name.startswith(('F1','F2')):o['glass_note']='Reference image: 8mm + 8mm; build-up unspecified'
    # Sashes displayed open 35 degrees; interior is Y < 10.11.
    for label,a,b,side_sign in [('A1左',x0+f,cuts[1]-f/2,1),('A2右',cuts[3]+f/2,x1-f,-1)]:
        hinge=a if side_sign==1 else b;span=b-a;angle=math.radians(35)*side_sign
        bottom,top=split+f/2+.006,z1-f-.006
        def p(u,v,z):
            dx=side_sign*u
            return (hinge+dx*math.cos(angle)-v*math.sin(angle),y+dx*math.sin(angle)+v*math.cos(angle),z)
        def part(suffix,u,v,z,sz,ma):
            o=box('阳台'+label+'外开扇'+suffix,p(u,v,z),sz,ma,'Windows','balcony',.002,rot=angle)
            o['window_type']='outward_casement';o['opening_degrees']=35;o['nominal_column_mm']=700
            return o
        for u in (f/2,span-f/2):part('立框',u,0,(bottom+top)/2,(f,depth,top-bottom),'window_frame')
        for z in (bottom+f/2,top-f/2):part('横框',span/2,0,z,(span-f*2,depth,f),'window_frame')
        part('玻璃',span/2,0,(bottom+top)/2,(span-f*2,.016,top-bottom-f*2),'glass')
        tube('阳台'+label+'外开扇把手',[p(span-f/2,-.05,1.45),p(span-f/2,-.05,1.61)],.009,'black','Windows','balcony')
        for z in (bottom+.18,top-.18):
            box('阳台'+label+'外开铰链',(hinge,y,z),(.025,.08,.10),'window_frame','Windows','balcony',.003)
    # Close the remaining head space to the existing ceiling, without changing the opening width.
    rect('阳台窗顶收口',x0,x1,9.99,10.23,z1,2.72,'wall','WallsUpper','balcony',.002)
