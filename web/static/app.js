const $=id=>document.getElementById(id);
const modelStages=['classifier','formulation','functionspace','material','boundary','solver'];
const storageKey='mcpsim-selection';
const settingsKey='mcpsim-model-settings';
let modelConfig=null;
let session=null,mesh=null,busy=false,editorKey=null,viewer=null,previewMeshId=null,meshRevision=0,selectedRegions=[];
let codegenRun=null,codegenSession=null,codegenTimer=null,codegenPreview=null,codegenError='',codegenRevision=0;
const contourChoices=new Map();
function settings(){return Object.fromEntries(modelStages.flatMap(stage=>['model','reasoning'].map(suffix=>[stage+'_'+suffix,$(stage+'-'+suffix).value])));}

function fillModels(input,profiles){input.replaceChildren();for(const p of profiles){const option=el('option','',p.label);option.value=p.id;input.append(option);}}
function fillReasoning(stage,profile,wanted){const input=$(stage+'-reasoning'),modes=profile.reasoning_options||[profile.reasoning];input.replaceChildren();for(const mode of modes){const label=mode==='enabled'?(profile.reasoning_max_tokens?`On · ${profile.reasoning_max_tokens} tokens`:"On"):{none:"Off",minimal:"Minimal",low:'Low',medium:'Medium',high:'High',xhigh:'Xhigh'}[mode];const option=el('option','',label);option.value=mode;input.append(option);}input.value=modes.includes(wanted)?wanted:profile.reasoning;input.disabled=busy||stage==='formulation';input.title=profile.id==='google/gemini-3-flash-preview'?"Gemini 3 Flash does not guarantee a full turn-off. Minimal is the minimum reasoning setting.":'';}
function applySettings(value={}){if(!modelConfig)return;for(const stage of modelStages){const input=$(stage+'-model'),profiles=stage==='formulation'?[modelConfig.formulation_profile]:modelConfig.model_profiles;const wanted=value?.[stage+'_model']||input.value;const selected=profiles.find(p=>p.id===wanted)||profiles.find(p=>p.id===modelConfig[stage+'_model'])||profiles[0];input.value=selected.id;fillReasoning(stage,selected,value?.[stage+'_reasoning']);}localStorage.setItem(settingsKey,JSON.stringify(settings()));}
function el(tag,cls,text){const n=document.createElement(tag);if(cls)n.className=cls;if(text!==undefined)n.textContent=text;return n;}
function error(value){$('error').textContent=value?.message||'';$('error').hidden=!value;}
async function request(path,data){const r=await fetch(path,data===undefined?{}:{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});const value=await r.json();if(!r.ok){const e=new Error(value.error||`Request failed ${r.status}`);e.sessionId=value.session_id;throw e;}return value;}
function setBusy(value,label){busy=value;const canChat=!session||['selection_review','expert_review','function_space_review','material_review','boundary_parameter_review','boundary_value_review','solver_review'].includes(session.stage)&&!session.can_continue;for(const id of ['send','message'])$(id).disabled=value||!canChat;for(const id of ['formulation-editor','expert-approved'])if($(id))$(id).disabled=value||session.stage!=='expert_review';$('new-chat').disabled=value;$('upload-mesh').disabled=value||Boolean(session);$('mesh-file').disabled=value||Boolean(session);$('mesh-unit').disabled=value||Boolean(mesh);for(const stage of modelStages){$(stage+'-model').disabled=value||stage==='formulation';$(stage+'-reasoning').disabled=value||stage==='formulation';}$('codegen-model').disabled=value;$('codegen-reasoning').disabled=value;document.querySelectorAll('[data-value-id],[data-dimensionless-id],[data-material-input],#solver-editor').forEach(input=>input.disabled=value);document.querySelectorAll('[data-unit-id]').forEach(input=>{const checkbox=input.parentElement.querySelector('[data-dimensionless-id]');input.disabled=value||!!checkbox?.checked;});$('pending').hidden=!value;if(label)$('pending-label').textContent=label;document.querySelectorAll('[data-action]').forEach(b=>b.disabled=value||b.dataset.available!=='true');$('use-boundary-region').disabled=value||!['boundary_parameter_review','boundary_value_review'].includes(session?.stage)||!selectedRegions.length;if($('use-material-region'))$('use-material-region').disabled=value||session?.stage!=='material_review'||!selectedRegions.some(r=>r.dim===3);}
function end(){const target={solver_review:'.solver-reply',boundary_value_review:'.boundary-value-reply',boundary_parameter_review:'.parameter-selection-reply',material_review:'.material-reply',function_space_review:'.functionspace-reply',expert_review:'.review-reply'}[session?.stage];const latest=target?Array.from(document.querySelectorAll(target)).at(-1):null;if(latest){latest.scrollIntoView({block:'start'});return;}$('conversation').scrollTop=$('conversation').scrollHeight;}

function button(label,available,action,cls=''){const b=el('button',cls,label);b.type='button';b.dataset.action='true';b.dataset.available=String(available);b.onclick=action;return b;}
function appendQuestion(target,response,available,valueLabels={},onChoose=null,english=false){target.append(el('p','question',response.question));const alternatives=response.options||[],recommended=response.question_type==='recommendation';if((response.question_type==='choice'||recommended)&&alternatives.length>=1){const options=el('div','options');for(const [index,option] of alternatives.entries()){const values=recommended?(option.values||[]).map(v=>(v.display_name||valueLabels[v.name]||v.name)+' = '+displayValue(v.value)+(v.unit?' '+v.unit:'')).join(' · '):'';const b=button(option.label,available,()=>{if(onChoose){onChoose(index);return;}$('message').value=option.label+': '+option.description+(values?'\n'+values:'');$('chat-form').requestSubmit();},'secondary');if(values)b.append(el('div','recommendation-values',values));b.append(el('small','',option.description));options.append(b);}target.append(options);if(recommended)target.append(el('p','muted',english?'Select a recommendation or enter other values in the conversation below.':"You can select a recommendation or enter another value in the chat window below."));}else if(!response.question_type&&alternatives.length){const notes=el('div','question-notes');for(const item of alternatives){const row=el('p');row.append(el('strong','',item.label),document.createTextNode(': '+item.description));notes.append(row);}target.append(notes);}}

function download(value,name){const url=URL.createObjectURL(new Blob([JSON.stringify(value,null,2)],{type:'application/json'}));const a=el('a');a.href=url;a.download=name+'.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
function user(text){const n=el('section','message user');n.append(el('div','role',"Me"),el('div','bubble',text));return n;}
function specView(spec){const n=el('details','spec-card'),p=spec.problem;n.append(el('summary','',"View selected specification details"));const summary=el('dl');for(const [label,value]of [['Type',p.type],['Unknowns',p.unknowns.join(', ')],['Linearity',p.linearity],['Time dependence',p.time_dependence],['History dependence',String(p.history_dependence)],['Dimension',String(p.dimension)],['Coupling',p.coupling.type]])summary.append(el('dt','',label),el('dd','',value));n.append(summary);
  const details=el('details','json');details.append(el('summary','',"Selected specification JSON"),el('pre','',JSON.stringify(spec,null,2)));n.append(details);return n;}
function selectionExplanation(response){return response.explanation||'Review the selection specification below.';}
function math(text){const target=el('div','equation');try{katex.render(text,target,{displayMode:true,throwOnError:true,trust:false,strict:'ignore'});}catch{target.textContent=text;target.classList.add('latex-fallback');}return target;}
function reviewExplanation(text){const n=el('div','selection-explanation');const pattern=/\\\[([\s\S]*?)\\\]|\\\(([\s\S]*?)\\\)|\$\$([\s\S]*?)\$\$|\$([^$\n]+)\$|`([^`\n]+)`/g;let start=0;for(const match of text.matchAll(pattern)){n.append(document.createTextNode(text.slice(start,match.index)));if(match[5]!==undefined)n.append(el('code','',match[5]));else{const display=match[1]!==undefined||match[3]!==undefined,target=el(display?'div':'span',display?'equation':'review-inline-math');try{katex.render(match[1]??match[2]??match[3]??match[4],target,{displayMode:display,throwOnError:true,trust:false,strict:'ignore'});}catch{target.textContent=match[0];target.classList.add('latex-fallback');}n.append(target);}start=match.index+match[0].length;}n.append(document.createTextNode(text.slice(start)));return n;}
function formulationView(value){const n=el('div','formulation');for(const [key,title]of [['weak_form','Weak Form'],['kinematics','Kinematics'],['constitutive','Constitutive']]){const section=el('section','equation-section');section.append(el('h3','',title));const part=value[key];if(part===null)section.append(el('p','muted','null'));else if(key==='weak_form')for(const form of part){const row=el('div','weak-form');row.append(el('h4','',form.field));for(const k of form.type==='linear'?['bilinear_form','linear_form']:['residual','jacobian'])row.append(math(form[k]));section.append(row);}else for(const equation of part)section.append(math(equation));n.append(section);}
  for(const key of ['constitutive_parameters','boundary_parameters','source_parameters']){const section=el('section','parameter-section');section.append(el('h3','',key));if(!value[key].length)section.append(el('p','muted','[]'));for(const p of value[key]){const row=el('div','parameter-row');row.append(el('code','',p.name),math(p.symbol));if(key==='boundary_parameters')row.append(el('small','boundary-kind',p.kind?({neumann:'Neumann',robin:'Robin'})[p.kind]:'Unclassified'));section.append(row);}n.append(section);}return n;}
function functionSpaceView(card){const n=el('div','space-card'),table=el('table','space-table'),head=el('tr');for(const title of ['Field','Value shape','Element family','Degree'])head.append(el('th','',title));const thead=el('thead');thead.append(head);table.append(thead);const body=el('tbody');for(const field of [...card.unknowns,...(card.state_variables||[])]){const row=el('tr');for(const value of [field.name,field.shape===null?'Unresolved':JSON.stringify(field.shape),field.function_space.family??'Unresolved',field.function_space.degree===null?'Unresolved':String(field.function_space.degree)])row.append(el('td','',value));body.append(row);}table.append(body);n.append(table);if(card.state_variables===null)n.append(el('p','muted','Internal state variables: unresolved'));else if(!card.state_variables.length)n.append(el('p','muted','No internal state variables'));const details=el('details','json');details.append(el('summary','','Function-space card JSON'),el('pre','',JSON.stringify(card,null,2)));n.append(details);return n;}
function materialView(card,fieldStatus={},editable=false,turnIndex=-1){
  const n=el('div','space-card'),table=el('table','space-table material-table'),head=el('tr'),counts={};
  for(const title of ['Parameter','Value','Unit','Material volumes','Decision'])head.append(el('th','',title));
  const thead=el('thead');thead.append(head);table.append(thead);const body=el('tbody');
  for(const parameter of card.constitutive_parameters){
    const binding=counts[parameter.name]||0;counts[parameter.name]=binding+1;
    const row=el('tr'),name=el('td','',parameter.name),symbol=session.formulation.constitutive_parameters.find(p=>p.name===parameter.name)?.symbol;
    if(symbol)name.append(math(symbol));
    const status=el('td','material-decision');
    for(const key of ['value','unit','regions']){const record=fieldStatus['constitutive_parameters.'+parameter.name+'.'+binding+'.'+key];status.append(el('div','',key+': '+(record?.status||(parameter[key]==null?'unresolved':'proposed'))));}
    row.append(name,el('td','',parameter.value==null?'Unresolved':JSON.stringify(parameter.value)),el('td','',parameter.unit==null?'Unresolved':parameter.unit||'Dimensionless'),el('td','',parameter.regions==null?'Unresolved':parameter.regions.map(r=>r.name+' · tag '+r.tags.join(', ')).join('\n')),status);
    if(editable){
      const editor=el('details','material-editor');editor.append(el('summary','','Edit / specify value and unit'));
      const value=el('input'),unit=el('input');value.dataset.materialInput='true';unit.dataset.materialInput='true';
      value.value=parameter.value==null?'':JSON.stringify(parameter.value);value.setAttribute('aria-label',parameter.name+' value');
      unit.value=parameter.unit??'';unit.setAttribute('aria-label',parameter.name+' unit');
      editor.append(el('label','','Numeric value or JSON array'),value,el('label','','Unit (blank means dimensionless)'),unit,button('Apply value and unit',true,()=>{
        try{const parsed=JSON.parse(value.value);if(parsed===null||typeof parsed==='string'||typeof parsed==='boolean')throw new Error('Enter a number or numeric JSON array.');
          action('/api/selection/update-materials',{material_turn_index:turnIndex,input:{parameter:parameter.name,binding,value:parsed,unit:unit.value.trim()}},'Applying your material input…');
        }catch(e){error(e);}
      },'update-material-value'));status.append(editor);
    }
    body.append(row);
  }
  table.append(body);n.append(table);const details=el('details','json');details.append(el('summary','','Material parameter card JSON'),el('pre','',JSON.stringify(card,null,2)));n.append(details);return n;
}

function renderFieldStatuses(target){
  const groups=session?.field_status;if(!groups||!Object.keys(groups).length)return;
  const details=el('details','field-origins');details.append(el('summary','','Field origins and decisions'));
  for(const [stage,fields]of Object.entries(groups)){
    const section=el('details');section.append(el('summary','',stage));const table=el('table','space-table'),head=el('tr');
    for(const title of ['Field','Source','Decision'])head.append(el('th','',title));table.append(head);
    for(const [path,record]of Object.entries(fields)){const row=el('tr');row.append(el('td','',path),el('td','',record.source),el('td','',record.status));if(record.evidence)row.title=record.evidence;table.append(row);}
    section.append(table);details.append(section);
  }target.append(details);
}
function accept(value){if(codegenSession!==value.id){codegenRun=null;codegenPreview=null;codegenError='';}session=value;mesh=value.mesh;applySettings(value.settings);localStorage.setItem(storageKey,value.id);render();syncCodegen(true);if(mesh&&previewMeshId!==mesh.id)loadMeshPreview();}


function displayValue(value){return Array.isArray(value)?'['+value.map(displayValue).join(', ')+']':typeof value==='number'?String(Number(value.toPrecision(7))):String(value);}


function parameterAssessmentView(assessment){
  const wrap=el('div','space-card');
  const useLabel=item=>item.requirement===null?'Unresolved':({needed:'Use',not_needed:'Do not use'})[item.requirement];
  const regionCell=item=>{
    const cell=el('td');
    for(const region of item.regions||[])cell.append(button(region.name,true,()=>selectRegions([region]),'secondary'),el('small','','dim '+region.dim+' · tag '+region.tags.join(', ')));
    if(!item.regions?.length)cell.textContent=item.requirement==='not_needed'?'Not applicable':'Unresolved regions';
    return cell;
  };
  for(const [key,title]of [['boundary_parameters','Boundary parameters'],['source_parameters','Volume source parameters']]){
    wrap.append(el('h3','',title));
    if(!assessment[key]?.length){wrap.append(el('p','muted','No candidates'));continue;}
    const table=el('table','space-table'),thead=el('thead'),head=el('tr');
    for(const title of ['Parameter','Use in this problem','Application regions','Reason'])head.append(el('th','',title));
    thead.append(head);table.append(thead);const body=el('tbody');
    for(const item of assessment[key]){
      const row=el('tr'),name=el('td','',item.name);
      const definition=session.formulation[key].find(p=>p.name===item.name);
      if(definition?.symbol)name.append(math(definition.symbol));
      if(key==='boundary_parameters')name.append(el('small','boundary-kind',definition?.kind?({neumann:'Neumann',robin:'Robin'})[definition.kind]:'Unclassified'));
      row.append(name,el('td',item.requirement===null?'draft-pending':'',useLabel(item)),regionCell(item),el('td','',item.reason));body.append(row);
    }
    table.append(body);wrap.append(table);
  }
  wrap.append(el('h3','','Dirichlet conditions'));
  if(assessment.dirichlet_conditions){
    const table=el('table','space-table'),thead=el('thead'),head=el('tr');
    for(const title of ['Field and components','Use in this problem','Application regions','Reason'])head.append(el('th','',title));
    thead.append(head);table.append(thead);const body=el('tbody');
    for(const item of assessment.dirichlet_conditions){
      const components=item.components===null?'Unresolved components':item.components.length?'Components '+item.components.join(', '):'Whole field';
      const row=el('tr');row.append(el('td','',item.field+' · '+components),el('td',item.requirement===null?'draft-pending':'',useLabel(item)),regionCell(item),el('td','',item.reason));body.append(row);
    }
    table.append(body);wrap.append(table);
  }else wrap.append(el('p','notice','This older assessment needs a review that includes Dirichlet conditions.'));
  const details=el('details','json');details.append(el('summary','','Condition assessment JSON'),el('pre','',JSON.stringify(assessment,null,2)));wrap.append(details);return wrap;
}
function renderParameterSelection(messages){
  if(!session)return;
  const turns=session.boundary_parameter_turns||[],stage=session.stage;
  if(session.material_card&&['complete','boundary_review','solver_review'].includes(stage)&&!session.can_continue){
    const section=el('section','notice');section.append(el('p','','Review condition use and application regions from the request and tagged mesh.'),button(turns.length?'Review condition requirements':'Start boundary and source assessment',true,()=>action('/api/selection/start-boundary-parameter-selection',{},'Assessing condition requirements…'),'start-boundary-parameter-selection'));messages.append(section);
  }
  for(const [index,turn]of turns.entries()){
    if(turn.message)messages.append(user(turn.message));
    const n=el('section','message assistant parameter-selection-reply'),r=turn.response;
    const available=stage==='boundary_parameter_review'&&!session.can_continue&&index===turns.length-1;
    const resolved=r.determination==='determined';
    n.append(el('div','role',turn.origin==='recommendation_choice'?'Selected recommendation':'Condition assessment · '+turn.served_model),reviewExplanation(r.explanation));
    n.append(el('p','condition-determination '+(resolved?'muted':'draft-pending'),resolved?'Specification complete'+(available?' · Awaiting your approval':''):'Specification incomplete'));
    if(r.recommendations?.length){
      const proposals=el('section','parameter-recommendations');proposals.append(el('h3','','Recommended condition combinations'),el('p','muted','Select a proposal or describe your own conditions in the chat. Selecting a proposal does not approve it.'));
      for(const [proposalIndex,proposal]of r.recommendations.entries()){
        const card=el('section','parameter-recommendation');card.append(el('h4','',proposal.label),reviewExplanation(proposal.description));
        const items=el('ul');
        for(const [key,label]of [['boundary_parameters','Boundary'],['source_parameters','Volume source']]){
          const needed=proposal.assessment[key].filter(p=>p.requirement==='needed');
          for(const item of needed)items.append(el('li','',item.name+' → '+(item.regions||[]).map(region=>region.name).join(', ')));
          if(!needed.length)items.append(el('li','',label+' parameters: not used'));
        }
        for(const item of proposal.assessment.dirichlet_conditions||[])if(item.requirement==='needed')items.append(el('li','', 'Dirichlet: '+item.field+' · '+(item.components?.length?'Components '+item.components.join(', '):item.components===null?'Unresolved components':'Whole field')+' → '+(item.regions||[]).map(r=>r.name).join(', ')));
        if(proposal.assessment.dirichlet_conditions&&!proposal.assessment.dirichlet_conditions.some(item=>item.requirement==='needed'))items.append(el('li','','Dirichlet: not used'));
        card.append(items);const details=el('details');details.append(el('summary','','Parameter and region details'),parameterAssessmentView(proposal.assessment));card.append(details);
        card.append(button('Select this combination',available&&!!proposal.assessment.dirichlet_conditions,()=>action('/api/selection/choose-boundary-parameter-combination',{boundary_parameter_turn_index:index,recommendation_index:proposalIndex},'Applying the selected proposal…'),'choose-boundary-parameter-combination'));proposals.append(card);
      }
      n.append(proposals);
    }
    n.append(el('h3','','Current assessment'),parameterAssessmentView(r.assessment));
    if(r.question)n.append(el('p','question',r.question));
    if(!r.assessment.dirichlet_conditions||r.recommendations===undefined)n.append(button('Request recommendations',available,()=>{$('message').value='Review the required boundary, source, and Dirichlet conditions and propose one or two suitable combinations.';$('chat-form').requestSubmit();},'secondary request-boundary-recommendations'));
    n.append(button('Specify conditions',available,()=>{$('message').placeholder='Describe the unresolved condition use, application regions, or field components.';$('message').focus();},'secondary custom-boundary-parameters'));
    n.append(button('Approve conditions and enter values',available&&resolved,()=>action('/api/selection/confirm-boundary-parameter-selection',{boundary_parameter_turn_index:index},'Saving the approved conditions…'),'confirm-boundary-parameter-selection'));messages.append(n);
  }
  if(session.boundary_parameter_assessment){const n=el('section','confirmed');n.append(el('h2','',session.boundary_parameter_assessment.dirichlet_conditions?'✓ Boundary, source, and Dirichlet conditions approved':'Older assessment needs a Dirichlet review'),el('p','','Condition use and application settings were explicitly approved.'),button('Save assessment JSON',true,()=>download(session.boundary_parameter_assessment,'boundary_source_parameter_assessment'),'secondary'));messages.append(n);}
}

function unitConversionNotes(notes=[]){const n=el('details','json');n.append(el('summary','',"Mesh length unit conversion ("+notes.length+" items)"));for(const note of notes)n.append(el('p','', (note.option_index!==undefined?"Recommended "+(note.option_index+1)+' · ':'')+(note.name||((session?.boundary_value_requirements||[]).find(row=>row.id===note.id)?boundaryValueLabel(session.boundary_value_requirements.find(row=>row.id===note.id)):note.id))+': '+displayValue(note.source_value)+' '+note.source_unit+' = '+displayValue(note.value)+' '+note.unit));return n;}
function authoringUnitNotice(converted=false){return el('p','muted',"Length unit basis: "+(mesh?.summary.coordinate_unit||"Unconfirmed")+(converted?" · The values and units below are display values converted to this length basis.":''));}
function boundaryValueLabel(row){return row.name||(row.field+' · '+(row.components.length?"Component "+row.components.join(', '):"Total section"));}
function boundaryValuesView(draft,rows,editable,index){
  const wrap=el('div','space-card'),table=el('table','space-table boundary-values-table'),thead=el('thead'),head=el('tr');
  const markDirty=()=>{wrap.dataset.dirty='true';const confirm=wrap.closest('.boundary-value-reply')?.querySelector('.confirm-boundary-values');if(confirm){confirm.dataset.available='false';confirm.disabled=true;}};
  for(const title of ["Conditions · physical quantities","Applied region","Value","Unit"])head.append(el('th','',title));thead.append(head);table.append(thead);
  const body=el('tbody'),inputs=[];
  for(const row of rows){
    const item=draft.find(v=>v.id===row.id)||{value:null,unit:null},tr=el('tr'),name=el('td','',boundaryValueLabel(row)),region=el('td');
    name.append(el('small','',({boundary_parameters:"Boundary parameters",source_parameters:"Volume sources",dirichlet_conditions:'Dirichlet'})[row.scope]));
    if(row.kind)name.append(el('small','boundary-kind',({neumann:'Neumann',robin:'Robin'})[row.kind]));
    region.append(button(row.region.name,true,()=>selectRegions([row.region]),'secondary'),el('small','','tag '+row.region.tags.join(', ')));
    const valueCell=el('td'),unitCell=el('td');
    if(editable){
      const value=el('input'),unit=el('input'),dimensionless=el('input'),label=el('label','dimensionless');
      value.type='text';value.value=item.value===null?'':JSON.stringify(item.value);value.placeholder=row.shape?.length?"JSON array":"Number or JSON array";value.dataset.valueId=row.id;value.setAttribute('aria-label',boundaryValueLabel(row)+' '+row.region.name+" value");
      unit.type='text';unit.value=item.unit||'';unit.placeholder="Unit";unit.dataset.unitId=row.id;unit.setAttribute('aria-label',boundaryValueLabel(row)+' '+row.region.name+" unit");
      dimensionless.type='checkbox';dimensionless.checked=item.unit==='';dimensionless.dataset.dimensionlessId=row.id;unit.disabled=dimensionless.checked;
      value.oninput=markDirty;unit.oninput=markDirty;dimensionless.onchange=()=>{unit.disabled=dimensionless.checked;if(dimensionless.checked)unit.value='';markDirty();};label.append(dimensionless,document.createTextNode("Dimensionless"));
      valueCell.append(value);unitCell.append(unit,label);inputs.push({id:row.id,value,unit,dimensionless});
    }else{valueCell.textContent=item.value===null?"Undecided":JSON.stringify(item.value);unitCell.textContent=item.unit===null?"Undecided":item.unit||"Dimensionless";}
    tr.append(name,region,valueCell,unitCell);body.append(tr);
  }
  table.append(body);wrap.append(table);
  if(!rows.length)wrap.append(el('p','muted',"No value to enter"));
  if(editable)wrap.append(button("Apply input value",true,()=>{try{
    const values=inputs.map(item=>{let value=null;const text=item.value.value.trim();if(text){try{value=JSON.parse(text);}catch{throw new Error("Please enter the value as a number or JSON array.");}if(value===null||typeof value==='boolean'||typeof value==='string')throw new Error("Please enter the value as a number or JSON array.");}
      return {id:item.id,value,unit:item.dimensionless.checked?'':item.unit.value.trim()||null};});
    action('/api/selection/update-boundary-values',{boundary_value_turn_index:index,draft:values},"Applying the entered value and unit…");
  }catch(e){error(e);}},'update-boundary-values'));
  if(editable)wrap.append(el('p','muted',"After editing the table, press Apply input value. The applied contents will be reviewed and then finalized."));
  return wrap;
}
function renderBoundaryValues(messages){
  if(!session)return;const turns=session.boundary_value_turns||[],rows=session.boundary_value_requirements||[];
  if(['complete','solver_review'].includes(session.stage)&&session.boundary_parameter_assessment?.dirichlet_conditions){
    messages.append(button(session.boundary_value_card?"Review value · unit again":"Start entering value · unit",true,()=>action('/api/selection/start-boundary-values',{},"Checking the values and units needed for the confirmed conditions…"),'start-boundary-values'));
  }
  for(const [index,turn]of turns.entries()){
    if(turn.message)messages.append(user(turn.message));const n=el('section','message assistant boundary-value-reply'),r=turn.response;
    const available=session.stage==='boundary_value_review'&&!session.can_continue&&index===turns.length-1;
    const complete=!r.question&&r.draft.every(v=>v.value!==null&&v.unit!==null);
    n.append(el('div','role',turn.origin==='value_input'?"Enter value · unit":"Boundary · source · Dirichlet value · "+(turn.served_model||"Review")),reviewExplanation(r.explanation),authoringUnitNotice(!!turn.unit_normalizations?.length));
    if(r.question)appendQuestion(n,r.question,available,Object.fromEntries(rows.map(row=>[row.id,boundaryValueLabel(row)+' ('+row.region.name+')'])));
    n.append(boundaryValuesView(r.draft,rows,available,index));
    if(turn.unit_normalizations?.length)n.append(unitConversionNotes(turn.unit_normalizations));
    n.append(button("Finalize value · unit",available&&complete,()=>action('/api/selection/confirm-boundary-values',{boundary_value_turn_index:index},"Saving the checked values and units…"),'confirm-boundary-values'));
    if(available)n.append(button("Review conditions · region again",true,()=>action('/api/selection/start-boundary-parameter-selection',{},"Rechecking the condition judgment, including Dirichlet…"),'secondary review-boundary-requirements'));
    messages.append(n);
  }
  if(session.boundary_value_card){const n=el('section','confirmed');n.append(el('h2','',"✓ Boundary · source · Dirichlet value confirmed"),button("Save condition · value card JSON",true,()=>download(session.boundary_value_card,'boundary_source_dirichlet_card'),'secondary'));const details=el('details','json');details.append(el('summary','',"Confirmed card JSON"),el('pre','',JSON.stringify(session.boundary_value_card,null,2)));n.append(details);messages.append(n);}
}


function solverView(card){
  const wrap=el('div','solver-card'),solver=card.solver;
  function part(title,item){const section=el('section');section.append(el('h3','',title));const list=el('dl');for(const [key,value]of Object.entries(item)){if(key==='linear_solver')continue;if(key==='options'){if(value.length)list.append(el('dt','',"Additional PETSc options"),el('dd','',value.map(o=>o.name+' = '+o.value).join('\n')));continue;}list.append(el('dt','',key),el('dd','',value===null?"Default / none":String(value)));}section.append(list);wrap.append(section);}
  if(solver.linear)part("Linear solver",solver.linear);
  if(solver.nonlinear){part("Nonlinear solver",solver.nonlinear);part("Internal linear solver",solver.nonlinear.linear_solver);}
  return wrap;
}
function solverEnvironmentView(value){
  const wrap=el('details','solver-environment');wrap.append(el('summary','',"Execution environment support info · PETSc "+value.petsc_version));
  wrap.append(el('p','muted','DOLFINx '+value.dolfinx_version+' · '+value.scalar_type+" · Check MPI "+value.probe_mpi_size+" items · Actual analysis MPI count "+(value.execution_mpi_size??"Unspecified")));
  wrap.append(el('p','notice',"Type creation, initialization, and cleanup were checked. The decomposition package verified the settings on a small serial CPU matrix. Suitability for the actual problem matrix and parallel execution will be verified at the code execution stage."));
  for(const [key,title]of [['ksp_types','KSP'],['pc_types','PC'],['snes_types','SNES'],['line_search_types',"Line search"],['factor_solvers',"Decomposition package"],['external_packages',"Verified external packages"]]){const row=el('p');row.append(el('strong','',title+' ('+(value[key]||[]).length+'): '),document.createTextNode((value[key]||[]).join(', ')||"None"));wrap.append(row);}
  if(value.factor_support){const detail=el('details','json');detail.append(el('summary','',"Verification results by decomposition method and matrix format"),el('pre','',JSON.stringify(value.factor_support,null,2)));wrap.append(detail);}
  return wrap;
}
function renderSolver(messages){
  if(!session)return;
  const turns=session.solver_turns||[];
  if(session.solver_environment?.petsc_version)messages.append(solverEnvironmentView(session.solver_environment));
  for(const [index,turn]of turns.entries()){
    if(turn.message)messages.append(user(turn.message));
    const n=el('section','message assistant solver-reply'),r=turn.response;
    const available=session.stage==='solver_review'&&!session.can_continue&&index===turns.length-1;
    const payload={solver_turn_index:index};
    n.append(el('div','role',"Solver settings · "+(turn.served_model||"Review")));
    if(r.explanation)n.append(reviewExplanation(r.explanation));
    for(const [j,item]of (r.recommendations||[]).entries()){
      const proposal=el('section','solver-recommendation');proposal.append(el('h3','',item.label),reviewExplanation(item.description),solverView(item.card),button("Select this solver configuration",available,()=>action('/api/selection/choose-solver',{...payload,recommendation_index:j},"Applying the selected solver configuration…"),'choose-solver'));n.append(proposal);
    }
    if(r.proposed_card){
      n.append(solverView(r.proposed_card));
      if(available){
        const details=el('details','json');details.append(el('summary','',"Edit solver card JSON directly"));
        const editor=el('textarea','solver-editor');editor.id='solver-editor';editor.setAttribute('aria-label',"Solver card JSON");editor.rows=18;editor.spellcheck=false;editor.value=JSON.stringify(r.proposed_card,null,2);const original=editor.value;
        const confirm=button("Finalize solver settings",true,()=>action('/api/selection/confirm-solver',payload,"Finalizing the reviewed solver settings…"),'confirm-solver');
        editor.oninput=()=>{confirm.dataset.available=String(editor.value===original);confirm.disabled=busy||editor.value!==original;};
        const apply=button("Apply solver JSON edits",true,()=>{try{action('/api/selection/update-solver',{...payload,card:JSON.parse(editor.value)},"Checking solver settings…");}catch(e){error(new Error("Please check the solver JSON format."));}},'update-solver');
        details.append(editor,apply,el('p','muted',"Please apply the edited JSON and then finalize it."));n.append(details,confirm);
      }
    }else if(r.question)appendQuestion(n,r,available);
    if(available)n.append(button("Recheck and recommend execution environment",true,()=>action('/api/selection/refresh-solver',payload,"Rechecking the installation environment and recommending a solver…"),'secondary refresh-solver'));
    messages.append(n);
  }
  if(session.solver_card){const n=el('section','confirmed');n.append(el('h2','',"✓ Solver settings confirmed"),solverView(session.solver_card),button("Save solver card JSON",true,()=>download(session.solver_card,'solver_card'),'secondary'));messages.append(n);}
  if(session.stage==='complete'&&session.boundary_value_card&&!session.can_continue)messages.append(button(session.solver_card?"Review solver settings again":"Start solver settings",true,()=>action('/api/selection/start-solver',{},"Recommending a solver based on the execution environment and confirmed cards…"),'start-solver'));
}

function initCodegenConfig(config){
  let saved={};try{saved=JSON.parse(localStorage.getItem('mcpsim-codegen-settings'))||{};}catch{}
  const input=$('codegen-model');fillModels(input,config.model_profiles);
  input.value=config.model_profiles.some(p=>p.id===saved.model)?saved.model:config.default_model;
  const save=()=>localStorage.setItem('mcpsim-codegen-settings',JSON.stringify({model:input.value,reasoning:$('codegen-reasoning').value}));
  const sync=wanted=>{const selected=config.model_profiles.find(p=>p.id===input.value);fillReasoning('codegen',selected,wanted);save();};
  input.onchange=()=>sync();$('codegen-reasoning').onchange=save;sync(saved.reasoning);
}
async function syncCodegen(force=false){
  if(!session||codegenSession===session.id&&!force)return;
  clearTimeout(codegenTimer);const id=session.id,revision=++codegenRevision;codegenSession=id;codegenPreview=null;codegenError='';
  try{const result=await request('/api/codegen/latest/'+id);if(session?.id!==id||revision!==codegenRevision)return;codegenRun=result.run;paintCodegen();scheduleCodegen();}
  catch(e){if(session?.id===id&&revision===codegenRevision){codegenError=e.message;paintCodegen();}}
}
function scheduleCodegen(){clearTimeout(codegenTimer);if(codegenRun&&(['queued','running'].includes(codegenRun.status)||codegenRun.contour_task?.status==='running'))codegenTimer=setTimeout(pollCodegen,2000);}
async function pollCodegen(){
  const run=codegenRun;if(!run||run.session_id!==session?.id)return;
  try{const result=await request('/api/codegen/run/'+run.session_id+'/'+run.id);if(session?.id!==run.session_id||codegenRun?.id!==run.id)return;codegenRun=result.run;codegenError='';paintCodegen();scheduleCodegen();}
  catch(e){codegenError=e.message;paintCodegen();}
}
async function codegenAction(action){
  if(busy||!session)return;setBusy(true,action==='preview'?"Separating the approved specification into step-by-step cards…":"Preparing for coding and analysis execution…");
  codegenError='';
  try{const result=await request('/api/codegen/'+action,{session_id:session.id,run_id:codegenRun?.id,
    model:$('codegen-model').value,reasoning:$('codegen-reasoning').value});
    if(action==='preview')codegenPreview=result;else{codegenRun=result.run;codegenPreview=null;scheduleCodegen();}
  }catch(e){codegenError=e.message;}
  finally{setBusy(false);paintCodegen();$('codegen-section')?.scrollIntoView({block:'start'});}
}
function paintCodegen(){const existing=$('codegen-section');if(existing){const openKeys=Array.from(existing.querySelectorAll('details[open]')).map(n=>n.dataset.viewKey||n.querySelector('summary')?.textContent);const oldPreview=existing.querySelector('.artifact-preview');const wrap=el('div');renderCodegen(wrap);for(const node of wrap.querySelectorAll('details'))if(openKeys.includes(node.dataset.viewKey||node.querySelector('summary')?.textContent))node.open=true;if(oldPreview&&!oldPreview.hidden){const preview=wrap.querySelector('.artifact-preview');if(preview){preview.textContent=oldPreview.textContent;preview.hidden=false;preview.scrollTop=oldPreview.scrollTop;}}existing.replaceWith(...wrap.childNodes);setBusy(busy);}else if(session?.solver_card||codegenRun){renderCodegen($('messages'));setBusy(busy);}}
function renderContours(section,run){
  if(!run.contours&&!run.can_render_contours&&!run.contour_task)return;
  const wrap=el('section','contour-panel');wrap.append(el('h3','',"Unknown field contour"));
  const task=run.contour_task,manifest=run.contours,working=task?.status==='running'||manifest?.status==='rendering';
  if(manifest?.source==='saved_code_replay')wrap.append(el('p','muted',"Contour generated by rerunning the saved analysis code."));
  if(working)wrap.append(el('p','muted',"Generating unknown field results and contour PNGs…"));
  if(task?.error)wrap.append(el('p','codegen-error',task.error));
  if(manifest?.error)wrap.append(el('p','codegen-error',manifest.error));
  const fields=(manifest?.fields||[]).filter(f=>f.images?.length);
  for(const field of manifest?.fields||[])if(field.error)wrap.append(el('p','codegen-error',field.name+': '+field.error));
  if(fields.length){
    const chosen=contourChoices.get(run.id)||{field:fields[0].name,mode:fields[0].shape.length?'magnitude':'value'};
    const tools=el('div','contour-tools'),fieldSelect=el('select'),modeSelect=el('select');fieldSelect.id='contour-field';modeSelect.id='contour-mode';fieldSelect.setAttribute('aria-label',"Unknown field to display");modeSelect.setAttribute('aria-label',"Value/component to display");
    for(const field of fields){const option=el('option','',field.name);option.value=field.name;fieldSelect.append(option);}fieldSelect.value=fields.some(f=>f.name===chosen.field)?chosen.field:fields[0].name;
    const image=el('img','contour-image'),range=el('p','muted'),save=el('a','contour-download',"Save PNG");save.setAttribute('download','');
    function update(){const field=fields.find(f=>f.name===fieldSelect.value),previous=modeSelect.value||chosen.mode;modeSelect.replaceChildren();for(const item of field.images){const label=item.mode==='magnitude'?"Magnitude":item.mode==='value'?"Value":"Component "+item.mode.replace('component_','');const option=el('option','',label);option.value=item.mode;modeSelect.append(option);}modeSelect.value=field.images.some(i=>i.mode===previous)?previous:field.images[0].mode;show();}
    function show(){const field=fields.find(f=>f.name===fieldSelect.value),item=field.images.find(i=>i.mode===modeSelect.value);contourChoices.set(run.id,{field:field.name,mode:item.mode});const path=item.path.split('/').map(encodeURIComponent).join('/');image.src='/api/codegen/image/'+run.session_id+'/'+run.id+'/'+path;image.alt=field.name+' '+item.label+" contour";save.href='/api/codegen/artifact/'+run.session_id+'/'+run.id+'/'+path;range.textContent="Minimum "+displayValue(item.min)+" · Maximum "+displayValue(item.max)+(field.unit?' '+field.unit:" · Numerical units in the analysis code");}
    fieldSelect.onchange=update;modeSelect.onchange=show;tools.append(fieldSelect,modeSelect,save);wrap.append(tools,image,range,el('p','muted',"Cool to warm · Final analysis values displayed on the original shape. Numerical value units are not converted automatically."));update();
  }
  if(run.can_render_contours&&!working){
    const saved=(manifest?.fields||[]).some(f=>f.files?.length);
    wrap.append(button(fields.length?"Regenerate contour":"Generate contour",true,()=>codegenAction('contours'),'secondary generate-contours'));
    if(!saved)wrap.append(el('p','muted',"The previous run re-executes the saved analysis code to store unknown field values and generate contours."));
  }
  section.append(wrap);
}
function renderCodegen(messages){
  if(!session||!session.solver_card&&!codegenRun&&!codegenError)return;
  const section=el('section','codegen-section');section.id='codegen-section';section.append(el('h2','',"KG-based coding and analysis"));
  section.append(el('p','muted',"Write and execute mesh → function space → weak form → boundary conditions → solve in order using the confirmed card. API retrieval uses k=3 and one hop per Procedure item. Runtime errors may trigger up to five correction attempts per stage."));
  const active=codegenRun&&(['queued','running'].includes(codegenRun.status)||codegenRun.contour_task?.status==='running'),ready=session.stage==='complete'&&!!session.solver_card&&!session.can_continue;
  section.append(button("5-step card preview",ready&&!active,()=>codegenAction('preview'),'secondary preview-codegen'),button("Run coding and analysis",ready&&!active,()=>codegenAction('start'),'start-codegen'));
  if(codegenError)section.append(el('p','codegen-error',codegenError));
  if(codegenPreview){const details=el('details','codegen-preview');details.open=true;details.append(el('summary','',"Step-by-step JSON cards to pass"));for(const [stage,card]of Object.entries(codegenPreview.cards)){const part=el('details','json');part.append(el('summary','',stage),el('pre','',JSON.stringify(card,null,2)));details.append(part);}details.append(button("Save full card JSON",true,()=>download(codegenPreview.cards,'codegen_cards'),'secondary'));section.append(details);}
  if(codegenRun){
    const run=codegenRun,labels={queued:"Queued",running:"Running",succeeded:"Code generation and solve completed",failed:"Run failed",cancelled:"Cancelled",interrupted:"Monitoring interrupted"};
    section.append(el('h3','codegen-status',labels[run.status]||run.status),el('p','',run.message));
    const retrieval=run.settings?.retrieval;
    if(retrieval)section.append(el('p','muted','Retrieval: k='+retrieval.top_k+' · '+retrieval.hops+' hop'));
    if(run.stale)section.append(el('p','notice',"This run is at a time different from the current specification. The cards and results below correspond to the approved specification at the time the run started."));
    const table=el('table','space-table'),head=el('tr');for(const title of ["Step","Status","Attempt","KG node / edge"])head.append(el('th','',title));table.append(head);
    const names={mesh:"Mesh",function_space:"Function space",weak_form:"Weak form",boundary_conditions:"Boundary conditions",solve:"Solve"},statuses={pending:"Queued",retrieving:"Graph retrieval",generating:"Generating code",executing:"Executing code",passed:"Passed",failed:"Failed"};
    for(const stage of run.stages){const row=el('tr',stage.status);for(const value of [names[stage.name],statuses[stage.status]||stage.status,stage.status==='pending'?'—':String(stage.attempt+1),stage.node_count===undefined?'—':stage.node_count+' / '+stage.edge_count])row.append(el('td','',value));table.append(row);}section.append(table);
    if(['queued','running'].includes(run.status))section.append(button("Stop execution",true,()=>codegenAction('cancel'),'secondary cancel-codegen'));
    section.append(button("Refresh execution status",true,()=>syncCodegen(true),'secondary refresh-codegen'));
    if(run.error){const details=el('details','json');details.open=true;details.append(el('summary','',"Error log"),el('pre','',run.error));section.append(details);}
    if(run.status==='succeeded')section.append(el('p','muted',"The final solve code has finished running. Please review execution success separately from physical validity and mesh convergence verification."));
    renderContours(section,run);
    const files=el('details','codegen-files');files.dataset.viewKey='artifacts';files.append(el('summary','',"Card, generated code, search history, execution file ("+run.artifacts.length+')'));
    const preview=el('pre','artifact-preview');preview.hidden=true;
    for(const item of run.artifacts){const row=el('div','artifact-row'),a=el('a','',item.path);a.href='/api/codegen/artifact/'+run.session_id+'/'+run.id+'/'+item.path.split('/').map(encodeURIComponent).join('/');a.setAttribute('download','');row.append(a,el('small','',Math.ceil(item.size/1024)+' KB'));
      if(/\.(py|json|txt|log)$/.test(item.path)&&item.size<2*1024*1024)row.append(button("View",true,async()=>{try{const response=await fetch(a.href);if(!response.ok)throw new Error("Failed to load the file.");preview.textContent=(await response.text()).slice(-40000);preview.hidden=false;}catch(e){codegenError=e.message;paintCodegen();}},'secondary artifact-view'));
      files.append(row);
    }files.append(preview);section.append(files);
  }
  messages.append(section);
}

async function recover(e){if(e.sessionId||session?.id)try{accept(await request('/api/selection/session/'+(e.sessionId||session.id)));}catch{}error(e);}
async function action(path,payload={},label="Preparing a response…"){if(busy)return;error(null);setBusy(true,label);try{accept(await request(path,{session_id:session.id,settings:settings(),material_selection:selectedRegions.filter(r=>r.dim===3),boundary_selection:selectedRegions,...payload}));}catch(e){await recover(e);}finally{setBusy(false);end();}}
function renderAuthoringStatus(){
  const target=$('authoring-status'),state=session?.authoring_status;
  target.hidden=!state;if(!state)return;
  const stages={selection:"Physics model",formulation:"Formulation",function_space:"Function space",material:"Material parameters",boundary_parameters:"Conditions and regions",boundary_values:"Values and units",solver:"Solver settings"};
  const labels={needs_input:"More information needed",ready_for_review:"Awaiting specification review",approved:"Approved",processing:"Processing"};
  target.dataset.state=state.status;
  target.textContent=(stages[state.stage]||"Physical specification")+' · '+(session.can_continue?"Retry processing required":labels[state.status]||"Checking");
}
function render(){const messages=$('messages');
  renderAuthoringStatus();
  const currentEditor=$('formulation-editor');let edited=currentEditor?.value;
  const approval=$('expert-approved')?.checked||false;
  messages.replaceChildren();$('welcome').hidden=Boolean(session?.turns.length);
  if(mesh)$('mesh-info').textContent=`${mesh.summary.filename} · dimension ${mesh.summary.dimension} · ${mesh.summary.cells.toLocaleString()} volume elements`;
  for(const [index,turn]of(session?.turns||[]).entries()){
    messages.append(user(turn.message));const n=el('section','message assistant');n.append(el('div','role',"Selected specification · "+turn.served_model));const r=turn.response;const available=session.stage==='selection_review'&&!session.can_continue&&index===session.turns.length-1;
    if(r.kind==='question'){appendQuestion(n,r,available,{},r.fixed_target?choice_index=>action('/api/selection/choose',{turn_index:index,choice_index},"Applying the selected item…"):null);}
    else{n.append(el('p','selection-explanation',selectionExplanation(r)));if(turn.library_match)n.append(el('p','library-match','Existing library formulation: '+turn.library_match));if(r.kind==='registration_request')n.append(el('p','notice',"Request to register a new model: "+r.reason));n.append(specView(r.spec));n.append(button(r.kind==='registration_request'?"Request new registration with this specification":"Confirm selected specification",available,()=>action('/api/selection/confirm',{turn_index:index},"Looking up the library and, if needed, generating a formulation draft with the selected model…"),'confirm-selection'));}
    messages.append(n);
  }
  if(session?.confirmed_selection){const n=el('section','confirmed');n.append(el('h2','',"✓ Selected specification confirmed"));n.append(button("Save selected JSON",true,()=>download(session.confirmed_selection,'problem_selection'),'secondary'));messages.append(n);}
  if(session?.can_continue){messages.append(button("Retry failed step",true,()=>action('/api/selection/continue',{},"Re-running the saved step…")));}
  if(session?.lookup){const notice=session.lookup.status==='ready'?"Imported the matching library formulation as is.":"No formulation matching the selected specification was found, so a new draft is needed.";messages.append(el('p','notice',notice));}
  const reviewTurns=session?.review_turns||[];
  if(reviewTurns.length&&session.generation?.formulation){const initial=el('details','review-version');initial.append(el('summary','',"View initial formulation draft"),formulationView(session.generation.formulation));messages.append(initial);}
  for(const turn of reviewTurns){messages.append(user(turn.message));const reply=el('section','message assistant review-reply');reply.append(el('div','role',"Formulation review · "+turn.served_model),reviewExplanation(turn.explanation));if(turn.formulation!==null){const version=el('details','review-version');version.append(el('summary','',"View the revised formulation in this response"),formulationView(turn.formulation));reply.append(version);}messages.append(reply);}
  if(session?.stage==='revise_formulation'&&session.review_message)messages.append(user(session.review_message));
  if(['expert_review','revise_formulation'].includes(session?.stage)){
    const current=session.stage==='revise_formulation'?session.review_input:session.formulation;
    const latest=reviewTurns.at(-1)||session.generation;
    const n=el('section','expert');n.append(el('h2','',(latest?.served_model||"Formulation")+" draft · Expert review"));n.append(el('p','muted',"You can point out errors or ask questions in the chat window. You can also edit the JSON below directly, and only the approved content will be saved to the library."));
    const key=session.id+':'+JSON.stringify(session.generation)+':'+reviewTurns.length;const changed=editorKey!==key;if(changed){editorKey=key;edited=JSON.stringify(current,null,2);}
    const editor=el('textarea');editor.id='formulation-editor';editor.value=edited||JSON.stringify(current,null,2);editor.spellcheck=false;editor.rows=15;n.append(editor);
    const preview=el('div');preview.id='formulation-preview';preview.append(formulationView(current));
    n.append(button("Preview revised JSON",true,()=>{try{preview.replaceChildren(formulationView(JSON.parse(editor.value)));error(null);}catch(e){error(new Error("Please check the format and items in the revised JSON."));}},'secondary'));
    const label=el('label','approval');const checkbox=el('input');checkbox.type='checkbox';checkbox.id='expert-approved';checkbox.checked=!changed&&approval;label.append(checkbox,document.createTextNode("As an expert, I have reviewed the equations and parameters."));n.append(label);
    n.append(button("Approve reviewed formulation and save to library",session.stage==='expert_review'&&!session.can_continue,()=>{try{if(!checkbox.checked)throw new Error("Please check the expert review confirmation.");action('/api/selection/approve',{expert_approved:true,formulation:JSON.parse(editor.value),review_turn_index:reviewTurns.length},"Saving the approved formulation…");}catch(e){error(e);}},'approve-formulation'));n.append(preview);messages.append(n);
  }
  if(session?.formulation&&!['selection_review','generate_formulation','expert_review','revise_formulation'].includes(session.stage)){
    const n=el('section','confirmed');n.append(el('h2','',"✓ Formulation confirmed"));
    const files=session.saved_files||session.lookup;n.append(el('p','muted',files.file||files.formulation_file));n.append(button("Save specification and formulation JSON",true,()=>download({...session.confirmed_selection,formulation:session.formulation},'formulation'),'secondary'));const details=el('details','review-version');details.append(el('summary','',"View confirmed formulation"),formulationView(session.formulation));n.append(details);if(session.stage==='complete'&&!session.functionspace_card)n.append(button("Start function space setup",true,()=>action('/api/selection/start-functionspace',{},"Proposing a function space that matches the confirmed formulation…"),'start-functionspace'));messages.append(n);
  }
  const spaceTurns=session?.functionspace_turns||[];
  for(const [index,turn]of spaceTurns.entries()){if(turn.message)messages.append(user(turn.message));const n=el('section','message assistant functionspace-reply');n.append(el('div','role','Function spaces · '+turn.served_model));const r=turn.response,available=session.stage==='function_space_review'&&!session.can_continue&&index===spaceTurns.length-1;if(r.proposed_card){n.append(reviewExplanation(r.explanation),functionSpaceView(r.proposed_card));n.append(button('Approve function spaces',available,()=>action('/api/selection/confirm-functionspace',{functionspace_turn_index:index},'Saving the reviewed function-space specification…'),'confirm-functionspace'));}else{if(r.draft_card)n.append(reviewExplanation(r.explanation),functionSpaceView(r.draft_card));if(r.requires_formulation_review)n.append(el('p','notice','The approved formulation needs review before these spaces can be approved.'));appendQuestion(n,r,available);}messages.append(n);}
  if(session?.functionspace_card){const n=el('section','confirmed');n.append(el('h2','',"✓ Function space specification confirmed"),button("Save function space card JSON",true,()=>download(session.functionspace_card,'functionspace_card'),'secondary'),functionSpaceView(session.functionspace_card));if(session.stage==='complete'&&!session.material_card)n.append(button("Start material parameter setup",true,()=>action('/api/selection/start-materials',{},"Checking the material values and volume regions needed for the formulation…"),'start-materials'));messages.append(n);}
  const materialTurns=session?.material_turns||[];
  for(const [index,turn]of materialTurns.entries()){if(turn.message)messages.append(user(turn.message));const n=el('section','message assistant material-reply');n.append(el('div','role','Material parameters · '+turn.served_model),authoringUnitNotice(!!turn.unit_normalizations?.length));const r=turn.response,available=session.stage==='material_review'&&!session.can_continue&&index===materialTurns.length-1;if(r.proposed_card){n.append(reviewExplanation(r.explanation),materialView(r.proposed_card,turn.field_status,available,index),button('Approve material parameters',available,()=>action('/api/selection/confirm-materials',{material_turn_index:index},'Saving the reviewed material values, units, and volumes…'),'confirm-materials'));}else{if(r.draft_card)n.append(materialView(r.draft_card,turn.field_status,available,index));appendQuestion(n,r,available,{},r.ambiguity_index!==undefined?option_index=>action('/api/selection/choose-material',{material_turn_index:index,option_index},'Applying the selected material candidate…'):null,true);}if(turn.unit_normalizations?.length)n.append(unitConversionNotes(turn.unit_normalizations));messages.append(n);}
  if(session?.material_card){const n=el('section','confirmed');n.append(el('h2','','✓ Material parameters approved'),button('Download material card JSON',true,()=>download(session.material_card,'material_card'),'secondary'),materialView(session.material_card,session.field_status?.material));messages.append(n);}
  renderParameterSelection(messages);renderBoundaryValues(messages);renderSolver(messages);renderCodegen(messages);renderFieldStatuses(messages);
  const stage=session?.stage;
  if(viewer)viewer.pickDimension=['material_parameters','material_review'].includes(stage)?3:2;
  $('status').textContent=!session?"Waiting for request":({solver_review:"Solver review",solver_parameters:"Checking runtime and recommending solvers",boundary_values:"Checking values and units",boundary_value_review:"Value and unit review",boundary_parameter_selection:"Assessing condition requirements",boundary_parameter_review:"Condition requirement review",material_review:"Material parameter review",material_parameters:"Checking material values",function_space_review:"Function space review",function_space:"Proposing function spaces",expert_review:"Expert review",revise_formulation:"Awaiting formulation revision",generate_formulation:"Generating formulation"})[stage]||(session.solver_card?"Confirm solver setup":session.boundary_value_card?"Confirm boundary, source, and Dirichlet values":session.boundary_parameter_assessment?"Confirm required parameter judgment":session.material_card?"Waiting for required parameter judgment":stage==='complete'?"Specification confirmed":"Check selected specification");
  $('step-selection').className=session?.confirmed_selection?'done':'active';
  $('step-lookup').className=session?.lookup?'done':'';
  $('step-review').className=['expert_review','revise_formulation'].includes(stage)?'active':session?.formulation?'done':'';
  $('step-functionspace').className=session?.functionspace_card?'done':['function_space','function_space_review'].includes(stage)?'active':'';
  $('step-material').className=session?.material_card?'done':['material_parameters','material_review'].includes(stage)?'active':'';
  $('step-boundary').className=session?.boundary_parameter_assessment?.dirichlet_conditions?'done':['boundary_parameter_selection','boundary_parameter_review'].includes(stage)?'active':'';
  $('step-boundary-values').className=session?.boundary_value_card?'done':['boundary_values','boundary_value_review'].includes(stage)?'active':'';
  $('step-solver').className=session?.solver_card?'done':['solver_parameters','solver_review'].includes(stage)?'active':'';
  $('message').placeholder=stage==='solver_review'?"Ask about the recommended solver or request other settings.":stage==='boundary_value_review'?"Enter values in the table or tell us the values and units in chat.":stage==='boundary_parameter_review'?"Tell us the types of required conditions and their application regions.":stage==='material_review'?"Tell us the material values, units, and the volume region to apply them to.":stage==='function_space_review'?"Tell us the element family and order to use for each field.":stage==='expert_review'?"Enter questions or revision comments about the formulation.":"Please describe the physical problem you want to analyze.";
  $('composer-note').textContent=(stage==='solver_review'?"Select the recommended configuration and then review and confirm it. You can specify other settings in chat or by JSON.":session?.solver_card?"Solver setup has also been confirmed.":stage==='boundary_value_review'?"Enter the values and units for the required items, review them, and then make the final confirmation.":session?.boundary_value_card?"Finished confirming the boundary, source, and Dirichlet values.":stage==='boundary_parameter_review'?"We review whether they are needed and the application regions. You can select surfaces or volumes to use in chat.":session?.boundary_parameter_assessment?"Finished confirming the required parameter judgment.":session?.material_card?"You can start determining the required boundary and source parameters.":stage==='material_review'?"Set the values, units, and volume regions for the material parameters.":stage==='function_space_review'?"Check the geometry, element family, and order for each field.":stage==='expert_review'?"Review the formulation and enter questions or revision comments.":"Confirm the specification based on the user's request.")+" · Enter to send / Shift+Enter for line break";
  setBusy(busy);end();
}
async function loadConfig(){
  const config=await request('/api/selection/config');modelConfig=config;
  for(const stage of modelStages)fillModels($(stage+'-model'),stage==='formulation'?[config.formulation_profile]:config.model_profiles);
  applySettings(config);
  initCodegenConfig(config);
}
$('chat-form').onsubmit=async event=>{
  event.preventDefault();const message=$('message').value.trim();if(!message||busy)return;error(null);
  const stage=session?.stage;
  try{
    const payload={session_id:session?.id||null,mesh_id:mesh?.id,message,settings:settings()};
    if(stage==='boundary_parameter_review')payload.boundary_parameter_turn_index=(session.boundary_parameter_turns||[]).length-1;
    if(stage==='solver_review')payload.solver_turn_index=(session.solver_turns||[]).length-1;
    if(stage==='boundary_value_review')payload.boundary_value_turn_index=(session.boundary_value_turns||[]).length-1;
    if(stage==='material_review'){payload.material_turn_index=(session.material_turns||[]).length-1;payload.material_selection=selectedRegions.filter(r=>r.dim===3);}
    if(stage==='function_space_review')payload.functionspace_turn_index=(session.functionspace_turns||[]).length-1;
    if(stage==='expert_review'){try{payload.formulation=JSON.parse($('formulation-editor').value);}catch{throw new Error("Please check the current formulation JSON and send feedback.");}payload.review_turn_index=(session.review_turns||[]).length;}
    const modelStage={solver_review:'solver',boundary_value_review:'boundary',boundary_parameter_review:'boundary',material_review:'material',function_space_review:'functionspace',expert_review:'formulation'}[stage]||'classifier';
    setBusy(true,settings()[modelStage+'_model']+"is reviewing the input…");
    accept(await request('/api/selection/chat',payload));$('message').value='';
  }catch(e){await recover(e);}finally{setBusy(false);end();}
};
$('message').onkeydown=event=>{if(event.key==='Enter'&&!event.shiftKey&&!event.isComposing){event.preventDefault();$('chat-form').requestSubmit();}};
$('new-chat').onclick=()=>{if(busy)return;clearTimeout(codegenTimer);codegenRevision++;codegenSession=null;codegenRun=null;codegenPreview=null;codegenError='';session=null;mesh=null;editorKey=null;previewMeshId=null;selectedRegions=[];meshRevision++;localStorage.removeItem(storageKey);$('message').value='';$('mesh-file').value='';$('mesh-unit').value='';$('mesh-display').hidden=true;$('mesh-info').textContent="Please load the .msh file first.";error(null);render();};
$('upload-mesh').onclick=async()=>{const file=$('mesh-file').files[0];if(!file||busy){error(new Error("Please select a .msh file."));return;}error(null);setBusy(true,"Reading the mesh geometry and boundary surfaces…");try{if(file.size>40*1024*1024)throw new Error("The mesh file must be within 40 MB.");const content=await new Promise((resolve,reject)=>{const r=new FileReader();r.onload=()=>resolve(String(r.result).split(',')[1]);r.onerror=reject;r.readAsDataURL(file);});mesh=await request('/api/mesh',{filename:file.name,content,coordinate_unit:$('mesh-unit').value});render();await loadMeshPreview();}catch(e){error(e);}finally{setBusy(false);}};
function coordinates(values){return values.map(value=>Number(value).toPrecision(4)).join(', ');}
function selectRegions(regions){selectedRegions=regions;viewer?.select(regions);for(const button of document.querySelectorAll('#mesh-groups button,#volume-groups button'))button.setAttribute('aria-pressed',String(regions.some(r=>r.dim===Number(button.dataset.dim)&&r.tags.includes(Number(button.dataset.tag)))));const selected=regions.map(r=>(r.dim===3?mesh.summary.volume_groups||[]:mesh.summary.boundary_groups).find(g=>g.tags.some(tag=>r.tags.includes(tag)))).filter(Boolean);$('selected-region').textContent=selected.length?selected.map(g=>`${g.name} · dim ${g.dim} · tag ${g.tags.join(', ')} · ${g.elements} ${g.dim===3?"volume":"boundary"} elements${(g.dim===3?g.volume_si:g.area_si)!=null?' · '+Number(g.dim===3?g.volume_si:g.area_si).toPrecision(5)+(g.dim===3?' m³':' m²'):''}\nRange: (${coordinates(g.bounds.slice(0,3))}) ~ (${coordinates(g.bounds.slice(3))})\nCenter: (${coordinates(g.centroid)})`).join('\n\n'):"If you select a region, you can check its dimension, tag, and geometry information.";setBusy(busy);}
function renderVolumeGroups(data){mesh.summary.volume_groups=data.volume_groups||[];if(viewer)viewer.pickDimension=['material_parameters','material_review'].includes(session?.stage)?3:2;const target=$('volume-groups');target.replaceChildren();for(const group of mesh.summary.volume_groups){const b=el('button','mesh-group',group.name+' · dim 3 · tag '+group.tags.join(', '));b.type='button';b.dataset.tag=group.tags[0];b.dataset.dim=3;b.style.borderLeftColor='#597ca7';b.setAttribute('aria-pressed','false');b.append(el('small','',group.elements.toLocaleString()+" volume elements"));b.onclick=()=>selectRegions([{name:group.name,dim:3,tags:group.tags}]);target.append(b);}if(!mesh.summary.volume_groups.length)target.append(el('p','muted',"There is no volume Physical Group."));}
async function loadMeshPreview(){const id=mesh?.id,revision=++meshRevision;if(!id)return;try{const data=await request('/api/mesh/'+id);if(revision!==meshRevision||mesh?.id!==id)return;$('mesh-display').hidden=false;if(!viewer)viewer=new MeshViewer($('mesh-canvas'),$('mesh-axes'),selectRegions);viewer.setData(data);previewMeshId=id;$('isolate-mesh').checked=false;renderVolumeGroups(data);mesh.summary.boundary_groups=data.groups;selectRegions([]);$('mesh-unit').value=mesh.summary.coordinate_unit||'';const s=mesh.summary,metadata=$('mesh-metadata');metadata.replaceChildren();for(const [label,value]of [["Dimension",String(s.dimension)+'D'],["Nodes",s.nodes.toLocaleString()],["Volume elements",s.cells.toLocaleString()],["Boundary groups",String(data.groups.length)],["Coordinate unit",s.coordinate_unit||"Unconfirmed"],["x range",coordinates([s.bounds[0],s.bounds[3]])],["y range",coordinates([s.bounds[1],s.bounds[4]])],["z range",coordinates([s.bounds[2],s.bounds[5]])]])metadata.append(el('dt','',label),el('dd','',value));const groups=$('mesh-groups');groups.replaceChildren();for(const g of data.groups){const b=el('button','mesh-group',g.name+' · tag '+g.tags.join(', '));b.type='button';b.dataset.tag=g.tags[0];b.dataset.dim=2;b.setAttribute('aria-pressed','false');b.style.borderLeftColor='rgb('+viewer.color(g.tags[0]).map(c=>Math.round(c*255)).join(',')+')';b.append(el('small','',g.elements.toLocaleString()+" boundary elements"));b.onclick=()=>selectRegions([{name:g.name,dim:g.dim,tags:g.tags}]);groups.append(b);}if(!data.groups.length)groups.append(el('p','muted',"There is no tagged outer boundary group."));}catch(e){error(e);}}
$('use-boundary-region').onclick=()=>{if(!selectedRegions.length||!['boundary_parameter_review','boundary_value_review'].includes(session?.stage))return;const text=selectedRegions.map(r=>r.name+' (dim '+r.dim+', tag '+r.tags.join(', ')+')').join(', ');$('message').value=($('message').value.trim()?$('message').value.trim()+'\n':'')+"Region to apply: "+text+'. ';$('message').focus();};
$('reset-view').onclick=()=>viewer?.reset();$('clear-region').onclick=()=>selectRegions([]);$('isolate-mesh').onchange=()=>{if(viewer){viewer.isolate=$('isolate-mesh').checked;viewer.draw();}};
$('use-material-region').onclick=()=>{const regions=selectedRegions.filter(r=>r.dim===3);if(!regions.length||session?.stage!=='material_review')return;const text=regions.map(r=>r.name+' (dim 3, tag '+r.tags.join(', ')+')').join(', ');$('message').value=($('message').value.trim()?$('message').value.trim()+'\n':'')+"Material application region: "+text+'. ';$('message').focus();};
for(const stage of modelStages){$(stage+'-model').onchange=()=>{applySettings({...settings(),[stage+'_reasoning']:null});setBusy(busy);};$(stage+'-reasoning').onchange=()=>{applySettings(settings());setBusy(busy);};}
async function init(){try{let savedSettings=null;try{savedSettings=JSON.parse(localStorage.getItem(settingsKey));}catch{}await loadConfig();applySettings(savedSettings);if(matchMedia('(max-width:800px)').matches)$('model-settings').open=false;const saved=localStorage.getItem(storageKey);if(saved)try{accept(await request('/api/selection/session/'+saved));}catch{localStorage.removeItem(storageKey);}render();}catch(e){error(e);}}init();
