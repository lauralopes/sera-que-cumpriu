import {el,button,toast} from './dom';
import type {Commitment} from './types';
type Column={label:string;value:(r:Commitment)=>string;className?:string};
export const columns:Column[]=[
 {label:'ID',value:r=>r.id},{label:'Presidente',value:r=>r.president},{label:'Eleição',value:r=>String(r.election)},
 {label:'Período avaliado',value:r=>`${r.start} a ${r.end}${r.provisional?' · provisório':''}`},
 {label:'Tema',value:r=>r.theme},{label:'Promessa',value:r=>r.description,className:'promise'},
 {label:'Trecho original',value:r=>r.refs.map(x=>x.quote).join(' | '),className:'wide'},
 {label:'Página PDF',value:r=>r.refs.map(x=>String(x.page)).join(', ')},
 {label:'Meta',value:r=>r.target===null?'—':`${r.target.toLocaleString('pt-BR')} ${r.unit||''}`},
 {label:'Prazo',value:r=>r.deadline||'Não explícito'},{label:'Critério de conclusão',value:r=>r.criterion,className:'wide'},
 {label:'Estado',value:r=>r.status||'Pendente',className:'status-cell'},{label:'Resultado observado',value:r=>r.result||'Não pesquisado',className:'wide'},
 {label:'Avanço quantitativo',value:r=>r.quantitative_progress===null?'—':`${r.quantitative_progress}% · ${r.calculation||''}`},
 {label:'Justificativa',value:r=>r.justification||'—',className:'wide'},
 {label:'Fontes',value:r=>r.evidence.map(e=>`${e.institution}: ${e.url}`).join(' | '),className:'wide'},
 {label:'Confiança',value:r=>r.confidence||'—'},{label:'Data de corte',value:r=>r.cutoff||'—'},{label:'Revisão humana',value:r=>r.human_review?'Sim':'Não'}
];
const preferred=['ID','Tema','Promessa','Estado','Confiança','Fontes'];
columns.sort((a,b)=>{const ai=preferred.indexOf(a.label),bi=preferred.indexOf(b.label);return (ai<0?100:ai)-(bi<0?100:bi);});
export function grid(rows:Commitment[],detail:(r:Commitment)=>void){
 const wrapper=el('div',undefined,'grid-wrap'),table=el('table',undefined,'sheet');table.setAttribute('role','grid');table.setAttribute('aria-label','Compromissos de governo');
 let sorted=[...rows],sort=-1,ascending=true,anchor=[0,0],end=[0,0],hasSelection=false;
 const head=el('thead'),hr=el('tr');hr.append(el('th','# / Detalhe'));for(const [i,c] of columns.entries()){const th=el('th');th.append(button(c.label,()=>{ascending=sort===i?!ascending:true;sort=i;sorted.sort((a,b)=>c.value(a).localeCompare(c.value(b),'pt-BR',{numeric:true})*(ascending?1:-1));paint();},'sort'));hr.append(th);}head.append(hr);table.append(head);
 const body=el('tbody');table.append(body);wrapper.append(table);
 function selection(){for(const cell of body.querySelectorAll<HTMLTableCellElement>('td[data-row]')){const r=Number(cell.dataset.row),c=Number(cell.dataset.col);const selected=hasSelection&&r>=Math.min(anchor[0],end[0])&&r<=Math.max(anchor[0],end[0])&&c>=Math.min(anchor[1],end[1])&&c<=Math.max(anchor[1],end[1]);cell.classList.toggle('selected',selected);cell.setAttribute('aria-selected',String(selected));}}
 function choose(r:number,c:number,shift=false){if(!shift)anchor=[r,c];end=[r,c];hasSelection=true;selection();}
 function tsv(){const values=[];for(let r=Math.min(anchor[0],end[0]);r<=Math.max(anchor[0],end[0]);r++)values.push(columns.slice(Math.min(anchor[1],end[1]),Math.max(anchor[1],end[1])+1).map(c=>c.value(sorted[r]).replace(/\t|\r?\n/g,' ')).join('\t'));return values.join('\n');}
 function paint(){body.replaceChildren();for(const [ri,r] of sorted.entries()){const tr=el('tr');const index=el('th');index.append(el('small',String(ri+1)),button('Abrir',()=>detail(r),'text-button'));tr.append(index);for(const [ci,c] of columns.entries()){const value=c.value(r),td=el('td',value,c.className);td.tabIndex=0;td.title=value;td.dataset.row=String(ri);td.dataset.col=String(ci);td.onpointerdown=e=>{choose(ri,ci,e.shiftKey);};td.onpointerenter=e=>{if(e.buttons===1){end=[ri,ci];selection();}};td.onkeydown=e=>{let dr=0,dc=0;if(e.key==='ArrowDown')dr=1;if(e.key==='ArrowUp')dr=-1;if(e.key==='ArrowRight')dc=1;if(e.key==='ArrowLeft')dc=-1;if(dr||dc){e.preventDefault();const nr=Math.max(0,Math.min(sorted.length-1,ri+dr)),nc=Math.max(0,Math.min(columns.length-1,ci+dc));choose(nr,nc,e.shiftKey);body.querySelector<HTMLElement>(`td[data-row="${nr}"][data-col="${nc}"]`)?.focus();}if(e.key==='Enter')detail(r);if(e.key==='Escape'){hasSelection=false;selection();}};tr.append(td);}body.append(tr);}selection();}
 table.addEventListener('copy',e=>{if(hasSelection){e.preventDefault();e.clipboardData?.setData('text/plain',tsv());toast('Células copiadas');}});
 paint();if(!rows.length){const empty=el('div','Nenhum compromisso neste filtro. A ausência de itens não indica ausência de promessas.','empty');wrapper.append(empty);}
 return wrapper;
}
