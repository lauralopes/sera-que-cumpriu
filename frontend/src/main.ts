import './style.css';
import {el,button,select,api,toast} from './dom';
import {states,type Commitment,type Plan,type Summary} from './types';
import {grid} from './grid';
import {detailPanel} from './detail';
import {summaryView,researchView,methodologyView} from './views';
const app=document.querySelector<HTMLDivElement>('#app')!;
let plans:Plan[]=[],rows:Commitment[]=[],summaries:Summary[]=[],plan='',q='',theme='',status='',confidence='',active='Compromissos',selected:string|null=null;
let timer:number|undefined;
const header=el('header'),brand=el('div');brand.append(el('h1','O governo cumpriu o plano?'),el('p','Planos de governo, execução e evidências.'));const actions=el('div',undefined,'header-actions');actions.append(button('Metodologia',()=>{active='Metodologia';render();},'text-button'),button('Exportar CSV',()=>download('csv')),button('Exportar XLSX',()=>download('xlsx'),'primary'));header.append(brand,actions);const tabs=el('nav',undefined,'election-tabs');tabs.setAttribute('aria-label','Filtro por governo e eleição');const notice=el('div',undefined,'notice');const content=el('main');const nav=el('nav',undefined,'bottom-nav');nav.setAttribute('aria-label','Visões da auditoria');app.append(header,tabs,notice,content,nav);
function query(){const p=new URLSearchParams();if(plan)p.set('plan',plan);if(q)p.set('q',q);if(theme)p.set('theme',theme);if(status)p.set('status',status);if(confidence)p.set('confidence',confidence);return p.toString();}
function download(format:string){location.href=`/api/export?format=${format}&${query()}`;}
async function load(){[plans,rows,summaries]=await Promise.all([api<Plan[]>('/api/plans'),api<Commitment[]>('/api/commitments'),api<Summary[]>('/api/summary')]);await render();}
function filtered(){return rows.filter(r=>(!plan||r.plan_id===plan)&&(!theme||r.theme===theme)&&(!status||(r.status||'Pendente')===status)&&(!confidence||r.confidence===confidence)&&(!q||JSON.stringify(r).toLocaleLowerCase('pt-BR').includes(q.toLocaleLowerCase('pt-BR'))));}
async function render(){
 tabs.replaceChildren();tabs.append(button('Todos os planos',()=>{plan='';selected=null;render();},plan===''?'active':''));for(const p of plans)tabs.append(button(`${p.president==='Jair Bolsonaro'?'Bolsonaro':p.president==='Dilma Rousseff'?'Dilma':'Lula'} ${p.election}`,()=>{plan=p.id;selected=null;render();},plan===p.id?'active':''));
 notice.textContent='Pesquisa em andamento · extração parcial · avaliações iniciais por Codex, sem revisão humana';nav.replaceChildren();for(const name of ['Compromissos','Resumo por plano','Pesquisa','Metodologia'])nav.append(button(name,()=>{active=name;render();},active===name?'active':''));
 content.replaceChildren();
 if(active==='Resumo por plano'){content.append(summaryView(summaries));return;}
 if(active==='Pesquisa'){try{content.append(await researchView());}catch(e){toast(String(e));}return;}
 if(active==='Metodologia'){content.append(await methodologyView());return;}
 const toolbar=el('div',undefined,'toolbar');const search=el('input');search.type='search';search.placeholder='Buscar promessas, temas ou evidências';search.setAttribute('aria-label','Busca textual');search.value=q;search.oninput=()=>{q=search.value;clearTimeout(timer);timer=window.setTimeout(renderTable,180);};toolbar.append(search,select('Filtrar tema',['Todos os temas',...[...new Set(rows.map(r=>r.theme))].sort()],theme,v=>{theme=v;renderTable();}),select('Filtrar estado',['Todos os estados','Pendente',...states],status,v=>{status=v;renderTable();}),select('Filtrar confiança',['Todas as confianças','Alta','Média','Baixa'],confidence,v=>{confidence=v;renderTable();}),button('Limpar filtros',()=>{plan='';q='';theme='';status='';confidence='';render();}));content.append(toolbar);
 const workspace=el('div',undefined,'workspace'),tableRegion=el('section',undefined,'table-region');const counter=el('div',undefined,'counter');content.append(counter,workspace);workspace.append(tableRegion);
 function renderTable(){const result=filtered();counter.textContent=`${result.length} compromissos cadastrados neste filtro · clique em Abrir para consultar fontes · Shift + clique seleciona intervalo · Ctrl/Cmd + C copia`;tableRegion.replaceChildren(grid(result,r=>{selected=r.id;renderTable();}));workspace.querySelector('.detail')?.remove();const r=rows.find(x=>x.id===selected);workspace.classList.toggle('with-detail',Boolean(r));if(r)workspace.append(detailPanel(r,()=>{selected=null;renderTable();},load));}
 renderTable();
}
load().catch(e=>{content.append(el('p',`Não foi possível carregar o banco: ${e}`,'error'));});
