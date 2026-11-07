export const MASTER_LAYOUTS={
 current:{label:'当前方案',offsetMm:0,note:'主卧双开门保持当前 CAD 位置。'},
 inset:{label:'门内移 · 储藏门齐平',offsetMm:670,note:'主卧门向内移 670 mm，与储藏室门齐平；中间为同平面的完整实墙，无朝过道的柜门。'}
};
export function modelChoice(width=700,layout='current'){
 width=Number(width);if(![600,700,800].includes(width))width=700;
 if(!Object.hasOwn(MASTER_LAYOUTS,layout))layout='current';
 const suffix=layout==='inset'?`-inset-${width}`:(width===700?'':`-${width}`);
 return {width,layout,key:`${layout}-${width}`,model:`home-model${suffix}.glb`,navigation:`navigation${suffix}.json`};
}
