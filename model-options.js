export const MASTER_LAYOUTS={
 current:{label:'当前方案',offsetMm:0,note:'主卧双开门保持当前 CAD 位置。'},
 inset:{label:'门内移 · 储藏门齐平',offsetMm:670,note:'主卧门板向内移 670 mm，与储藏室门板正面齐平；入口浅柜改为过道侧 480 × 310 mm 浅柜，柜门内退 378 mm 至 x=6260 mm，与两侧门板齐平，背墙和侧墙做凹位收口。'}
};
export function modelChoice(width=700,layout='current'){
 width=Number(width);if(![600,700,800].includes(width))width=700;
 if(!Object.hasOwn(MASTER_LAYOUTS,layout))layout='current';
 const suffix=layout==='inset'?`-inset-${width}`:(width===700?'':`-${width}`);
 return {width,layout,key:`${layout}-${width}`,model:`home-model${suffix}.glb`,navigation:`navigation${suffix}.json`};
}
