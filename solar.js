// NOAA fractional-year solar position, geometric (no refraction).
// https://www.gml.noaa.gov/grad/solcalc/solareqns.PDF
export const SITE = Object.freeze({latitude:30.27,longitude:120.15,timezone:8,floor:6,floorHeight:3,clearHeight:2.72,southAzimuth:180});
export const TIMES = Object.freeze({morning:{hour:8,label:'早晨',time:'08:00'},noon:{hour:12,label:'正午',time:'12:00'},evening:{hour:17,label:'傍晚',time:'17:00'}});
const rad=Math.PI/180,clamp=(x,a,b)=>Math.max(a,Math.min(b,x));
export function solarPosition(date,hour,site=SITE){
 const d=new Date(`${date}T00:00:00Z`);
 if(!/^\d{4}-\d{2}-\d{2}$/.test(date)||!Number.isFinite(d.getTime())||d.toISOString().slice(0,10)!==date||!Number.isFinite(hour)||hour<0||hour>=24)throw new RangeError('Invalid solar date or time');
 const year=d.getUTCFullYear(),start=Date.UTC(year,0,1),days=(Date.UTC(year+1,0,1)-start)/86400000;
 const day=(d.getTime()-start)/86400000+1,gamma=2*Math.PI/days*(day-1+(hour-12)/24);
 const eq=229.18*(.000075+.001868*Math.cos(gamma)-.032077*Math.sin(gamma)-.014615*Math.cos(2*gamma)-.040849*Math.sin(2*gamma));
 const dec=.006918-.399912*Math.cos(gamma)+.070257*Math.sin(gamma)-.006758*Math.cos(2*gamma)+.000907*Math.sin(2*gamma)-.002697*Math.cos(3*gamma)+.00148*Math.sin(3*gamma);
 const ha=(hour*60+eq+4*site.longitude-60*site.timezone)/4*rad-Math.PI,lat=site.latitude*rad;
 const altitude=Math.asin(clamp(Math.sin(lat)*Math.sin(dec)+Math.cos(lat)*Math.cos(dec)*Math.cos(ha),-1,1));
 const azimuth=(Math.atan2(Math.sin(ha),Math.cos(ha)*Math.sin(lat)-Math.tan(dec)*Math.cos(lat))+Math.PI+2*Math.PI)%(2*Math.PI);
 // Plan +X east / +Y south -> Three +X east / -Z south. Rotate only when surveyed.
 const az=azimuth-(site.southAzimuth-180)*rad;
 return {altitude:altitude/rad,azimuth:azimuth/rad,direction:[Math.sin(az)*Math.cos(altitude),Math.sin(altitude),Math.cos(az)*Math.cos(altitude)]};
}
export function daylight(date,period,site=SITE){
 if(!TIMES[period])throw new RangeError('Unknown daylight preset');
 const sun=solarPosition(date,TIMES[period].hour,site);
 const height=Math.max(0,Math.sin(sun.altitude*rad));
 // Artistic clear-sky exposure, NOT a lux / irradiance calculation. Below horizon: no direct sun.
 return {...sun,direct:sun.altitude>0?3.8*Math.pow(height,.38):0,sky:.035+.68*clamp((sun.altitude+6)/45,0,1),warmth:clamp((18-sun.altitude)/18,0,1),groundY:-(site.floor-1)*site.floorHeight-.2};
}
