import fs from 'node:fs';
import {createHash} from 'node:crypto';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {build} from 'esbuild';
const root=path.dirname(fileURLToPath(import.meta.url));
const options=JSON.parse(fs.readFileSync(path.join(root,'kitchen-options.json'),'utf8'));
const modelUrls={};
for(const [width,option] of Object.entries(options)){
 const modelHash=createHash('sha256').update(fs.readFileSync(path.join(root,option.model))).digest('hex');
 if(JSON.parse(fs.readFileSync(path.join(root,option.navigation),'utf8')).model_sha256!==modelHash)throw new Error(`Navigation for ${width} mm is stale.`);
 modelUrls[width]=`./${option.model}?v=${modelHash.slice(0,12)}`;
}
await build({entryPoints:[path.join(root,'app.js')],outfile:path.join(root,'app.bundle.js'),bundle:true,minify:true,format:'iife',alias:{three:path.join(root,'three.module.min.js')},legalComments:'eof'});
const g=JSON.parse(fs.readFileSync(path.join(root,'current-geometry.json'),'utf8'));
const lines=g.lines.filter(l=>l.p.every(p=>p[0]>-100&&p[0]<10000&&p[1]>-300&&p[1]<10500)).map(l=>l.p);
const revision=name=>createHash('sha256').update(fs.readFileSync(path.join(root,name))).digest('hex').slice(0,12);
const html=fs.readFileSync(path.join(root,'template.html'),'utf8').replace('__CAD_DATA__',()=>JSON.stringify(lines)).replace('__MODEL_VARIANTS__',()=>JSON.stringify(modelUrls)).replace('__APP_REV__',revision('app.bundle.js'));
fs.writeFileSync(path.join(root,'index.html'),html);
console.log('Built index.html and app.bundle.js; three fridge variants are loaded on demand.');
