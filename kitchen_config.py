"""Kitchen run in metres; the three options keep the CAD run and shafts fixed."""
def layout(width_mm):
    if width_mm not in (600,700,800):raise ValueError('Choose 600, 700 or 800 mm')
    width=width_mm/1000
    robot_end=1.50-max(0,width-.70)
    fridge_start=robot_end+.01
    fridge_end=fridge_start+width
    pantry_start=fridge_end+.02
    return dict(width_mm=width_mm,robot_start=.86,robot_end=round(robot_end,3),
        robot_center=round((.86+robot_end)/2,3),fridge_start=round(fridge_start,3),
        fridge_end=round(fridge_end,3),pantry_start=round(pantry_start,3),pantry_end=2.46,
        robot_width_mm=round((robot_end-.86)*1000),pantry_width_mm=round((2.46-pantry_start)*1000))

def build_zone(api,k):
    rect,box,tube,cyl,cabinet=[api[n] for n in ('rect','box','tube','cyl','cabinet')]
    a,b,c=k['robot_start'],k['robot_end'],k['robot_center']
    rect('扫地机设备柜背板',3.94,3.97,a,b,.02,.85,'walnut','Storage','kitchen')
    for yy in (a,b-.02):rect('扫地机设备柜侧板',3.37,3.94,yy,yy+.02,.02,.85,'walnut','Storage','kitchen')
    rect('扫地机设备柜上隔板',3.37,3.94,a+.02,b-.02,.34,.36,'walnut','Storage','kitchen')
    for ya,yb in [(a+.02,c-.215),(c+.215,b-.02)]:
        rect('扫地机洞口侧封板',3.35,3.37,ya,yb,.02,.34,'walnut','Storage','kitchen')
    o=rect('扫地机设备柜检修门',3.35,3.37,a+.02,b-.02,.36,.84,'walnut','Storage','kitchen');o['front_panel']=True
    box('扫地机自动上下水基站',(3.70,c,.1445),(.450,.381,.249),'white','Appliances','kitchen',.018)
    cyl('扫地机器人归位',(3.48,c,.070),.165,.100,'white','Appliances','kitchen',48)
    rect('扫地机防水托盘',3.38,3.94,a+.035,b-.035,.016,.025,'steel','Appliances','kitchen')
    rect('窗侧钢台面',3.35,3.99,a,b,.85,.88,'steel','Furniture','kitchen')
    for name,pts,kind,r in [
        ('扫地机排水接入示意',[(3.92,c,.23),(3.92,c,.33),(3.88,.70,.33),(3.42,.70,.33),(3.42,.43,.33)],'drain',.012),
        ('扫地机冷水支管示意',[(3.92,c+.035,.20),(3.92,c+.035,.58),(3.48,.70,.58),(3.48,.43,.58)],'supply',.008)]:
        o=tube(name,pts,r,'blue' if kind=='supply' else 'white','Services','kitchen')
        o['service_kind']=kind;o['source']='Proposed branch route; verify on site'
    box('扫地机供水检修阀',(3.90,c+.035,.58),(.035,.055,.055),'blue','Appliances','kitchen')
    for title,z0,z1 in [('下区',.10,1.20),('上区',1.20,2.40)]:
        cabinet('冰箱旁窄高柜'+title,3.37,3.71,k['pantry_start'],k['pantry_end'],z1,'x-','walnut','kitchen',base=z0)
    # French-door style: upper paired doors and two full-width freezer drawers.
    lo,hi=k['fridge_start'],k['fridge_end'];mid=(lo+hi)/2
    body=rect('法式冰箱箱体',3.37,3.97,lo,hi,0,1.91,'fridge_white','Appliances','kitchen',.025)
    body['fridge_width_mm']=k['width_mm'];body['door_style']='French: upper pair + two drawers'
    for i,(y1,y2) in enumerate([(lo+.005,mid-.004),(mid+.004,hi-.005)]):
        rect('法式冰箱冷藏门',3.345,3.37,y1,y2,.805,1.895,'fridge_white','Appliances','kitchen',.008)
        yy=mid+(-.045 if i==0 else .045)
        tube('法式冰箱冷藏门把手',[(3.322,yy,.89),(3.322,yy,1.30)],.008,'steel','Appliances','kitchen')
    for z1,z2 in [(.04,.405),(.42,.785)]:
        rect('法式冰箱冷冻抽屉',3.341,3.37,lo+.005,hi-.005,z1,z2,'fridge_white','Appliances','kitchen',.008)
        tube('法式冰箱抽屉把手',[(3.317,lo+.09,z2-.045),(3.317,hi-.09,z2-.045)],.009,'steel','Appliances','kitchen')
