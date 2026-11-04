/* Local WebGL mesh review. Positions retain the uploaded mesh coordinate system. */
class MeshViewer {
  constructor(canvas, axes, onSelect) {
    this.canvas = canvas; this.axes = axes; this.onSelect = onSelect;
    this.gl = canvas.getContext('webgl', {antialias:true, preserveDrawingBuffer:true});
    if (!this.gl) throw new Error("WebGL is unavailable in this browser.");
    const gl = this.gl;
    const shader = (type, source) => {
      const s = gl.createShader(type); gl.shaderSource(s, source); gl.compileShader(s);
      if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(s));
      return s;
    };
    this.program = gl.createProgram();
    gl.attachShader(this.program, shader(gl.VERTEX_SHADER, `
      attribute vec3 position; attribute vec3 normal;
      uniform mat3 rotation; uniform vec2 pan; uniform vec2 scale;
      varying float light;
      void main() { vec3 p=rotation*position; gl_Position=vec4(p.xy*scale+pan,p.z*0.2,1.0);
        light=0.48+0.52*abs(dot(normalize(rotation*normal),normalize(vec3(0.3,0.5,1.0)))); }`));
    gl.attachShader(this.program, shader(gl.FRAGMENT_SHADER, `
      precision mediump float; uniform vec3 color; uniform bool picking; uniform float opacity; varying float light;
      void main(){gl_FragColor=vec4(color*(picking?1.0:light),opacity);}`));
    gl.linkProgram(this.program);
    if (!gl.getProgramParameter(this.program, gl.LINK_STATUS)) throw new Error("Could not initialize the mesh renderer.");
    this.uniforms = Object.fromEntries(['rotation','pan','scale','color','picking','opacity'].map(k=>[k,gl.getUniformLocation(this.program,k)]));
    this.attributes = ['position','normal'].map(k=>gl.getAttribLocation(this.program,k));
    this.parts = []; this.selected = []; this.isolate = false; this.reset();
    this.resize = new ResizeObserver(()=>this.draw()); this.resize.observe(canvas);
    canvas.addEventListener('contextmenu', e=>e.preventDefault());
    canvas.addEventListener('pointerdown', e=>{
      this.drag={x:e.clientX,y:e.clientY,startX:e.clientX,startY:e.clientY,pan:e.button===2||e.shiftKey};
      canvas.setPointerCapture(e.pointerId);
    });
    canvas.addEventListener('pointermove', e=>{
      if (!this.drag) return;
      const dx=e.clientX-this.drag.x, dy=e.clientY-this.drag.y;
      if(this.drag.pan){this.pan[0]+=dx/canvas.clientWidth*2;this.pan[1]-=dy/canvas.clientHeight*2;}
      else {this.yaw+=dx*0.008;this.pitch+=dy*0.008;}
      this.drag.x=e.clientX; this.drag.y=e.clientY; this.draw();
    });
    canvas.addEventListener('pointerup',e=>{
      if(this.drag && Math.hypot(e.clientX-this.drag.startX,e.clientY-this.drag.startY)<5 && !this.drag.pan) this.pick(e);
      this.drag=null;
    });
    canvas.addEventListener('pointercancel',()=>{this.drag=null;});
    canvas.addEventListener('wheel',e=>{e.preventDefault();this.zoom=Math.max(.15,Math.min(20,this.zoom*Math.exp(-e.deltaY*.001)));this.draw();},{passive:false});
  }
  reset(){this.yaw=-.5;this.pitch=.5;this.zoom=1;this.pan=[0,0];if(this.parts)this.draw();}
  rotation(){
    const c=Math.cos(this.yaw),s=Math.sin(this.yaw),a=Math.cos(this.pitch),b=Math.sin(this.pitch);
    return new Float32Array([c,b*s,-a*s, 0,a,b, s,-b*c,a*c]);
  }
  setData(data){
    const gl=this.gl; for(const part of this.parts)gl.deleteBuffer(part.buffer);
    this.data=data;this.groups=data.groups;this.volume_groups=data.volume_groups||[];this.parts=[];this.selected=[];this.isolate=false;
    const b=data.bounds,center=b.slice(0,3).map((x,i)=>(x+b[i+3])/2),span=Math.max(...center.map((_,i)=>b[i+3]-b[i]))||1;
    const buckets=new Map();
    for(const tri of data.triangles){
      const key=tri.tags.join(',')+'|'+(tri.volume_tags||[]).join(','); if(!buckets.has(key))buckets.set(key,{tags:tri.tags,volume_tags:tri.volume_tags||[],values:[]});
      const points=tri.nodes.map(i=>data.nodes[i].map((x,j)=>(x-center[j])/span*1.5));
      const a=points[1].map((x,i)=>x-points[0][i]),c=points[2].map((x,i)=>x-points[0][i]);
      const normal=[a[1]*c[2]-a[2]*c[1],a[2]*c[0]-a[0]*c[2],a[0]*c[1]-a[1]*c[0]];
      const length=Math.hypot(...normal)||1;
      for(const p of points)buckets.get(key).values.push(...p,...normal.map(x=>x/length));
    }
    for(const [index,part] of [...buckets.values()].entries()){
      const buffer=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,buffer);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array(part.values),gl.STATIC_DRAW);
      this.parts.push({buffer,count:part.values.length/6,tags:part.tags,volume_tags:part.volume_tags,id:index+1});
    }
    this.reset();
  }
  select(regions){this.selected=regions.flatMap(r=>r.tags.map(tag=>r.dim===3?'volume:'+tag:tag));this.draw();}
  isSelected(part){return part.tags.some(t=>this.selected.includes(t))||part.volume_tags.some(t=>this.selected.includes('volume:'+t));}
  color(tag){const colors=[[.27,.53,.78],[.82,.48,.25],[.29,.66,.52],[.64,.46,.76],[.76,.65,.27],[.28,.65,.72],[.77,.43,.55]];return colors[Math.max(0,this.groups.findIndex(g=>g.tags.includes(tag)))%colors.length];}
  draw(picking=false){
    if(!this.gl)return;const gl=this.gl,canvas=this.canvas;
    const ratio=Math.min(devicePixelRatio||1,2),w=Math.max(1,Math.round(canvas.clientWidth*ratio)),h=Math.max(1,Math.round(canvas.clientHeight*ratio));
    if(canvas.width!==w||canvas.height!==h){canvas.width=w;canvas.height=h;}
    gl.viewport(0,0,w,h);gl.depthMask(true);gl.clearColor(...(picking?[0,0,0,1]:[.958,.967,.98,1]));gl.clear(gl.COLOR_BUFFER_BIT|gl.DEPTH_BUFFER_BIT);
    gl.enable(gl.DEPTH_TEST);gl.disable(gl.CULL_FACE);gl.disable(gl.DITHER);gl.useProgram(this.program);
    const rotation=this.rotation();gl.uniformMatrix3fv(this.uniforms.rotation,false,rotation);
    gl.uniform2fv(this.uniforms.pan,this.pan);gl.uniform2f(this.uniforms.scale,this.zoom*h/w,this.zoom);gl.uniform1i(this.uniforms.picking,picking);
    const ordered=picking?this.parts:[...this.parts].sort((a,b)=>Number(this.isSelected(a))-Number(this.isSelected(b)));
    for(const part of ordered){
      const selected=this.isSelected(part);if(this.isolate&&this.selected.length&&!selected)continue;
      const translucent=!picking&&this.selected.length&&!selected;
      if(translucent){gl.enable(gl.BLEND);gl.blendFunc(gl.SRC_ALPHA,gl.ONE_MINUS_SRC_ALPHA);gl.depthMask(false);}
      else{gl.disable(gl.BLEND);gl.depthMask(true);}
      gl.uniform1f(this.uniforms.opacity,translucent ? 0.12 : 1);
      gl.bindBuffer(gl.ARRAY_BUFFER,part.buffer);
      this.attributes.forEach((a,i)=>{gl.enableVertexAttribArray(a);gl.vertexAttribPointer(a,3,gl.FLOAT,false,24,i*12);});
      const color=picking?[(part.id&255)/255,((part.id>>8)&255)/255,0]:selected?[1,.58,.16]:this.selected.length?[.69,.74,.8]:part.tags.length?this.color(part.tags[0]):[.72,.75,.78];
      gl.uniform3fv(this.uniforms.color,color);gl.drawArrays(gl.TRIANGLES,0,part.count);
    }
    if(!picking)this.drawAxes(rotation);
  }
  drawAxes(r){
    this.axes.replaceChildren();
    for(let i=0;i<3;i++){
      const x=47+r[i*3]*30,y=47-r[i*3+1]*30;
      const line=document.createElementNS('http://www.w3.org/2000/svg','line');
      for(const[k,v]of Object.entries({x1:47,y1:47,x2:x,y2:y,stroke:['#be4444','#318359','#3c68b3'][i],'stroke-width':2}))line.setAttribute(k,v);
      const label=document.createElementNS('http://www.w3.org/2000/svg','text');label.setAttribute('x',x+3);label.setAttribute('y',y+3);label.textContent=['x','y','z'][i];
      this.axes.append(line,label);
    }
  }
  pick(event){
    this.draw(true);const gl=this.gl,rect=this.canvas.getBoundingClientRect(),pixel=new Uint8Array(4);
    const x=Math.floor((event.clientX-rect.left)/rect.width*this.canvas.width),y=Math.floor((rect.bottom-event.clientY)/rect.height*this.canvas.height);
    gl.readPixels(x,y,1,1,gl.RGBA,gl.UNSIGNED_BYTE,pixel);this.draw();
    const part=this.parts.find(p=>p.id===pixel[0]+256*pixel[1]);
    if(part){const groups=this.pickDimension===3?this.volume_groups:this.groups,tags=this.pickDimension===3?part.volume_tags:part.tags;this.onSelect(groups.filter(g=>g.tags.some(t=>tags.includes(t))).map(g=>({name:g.name,dim:g.dim,tags:g.tags})));}
  }
}
window.MeshViewer=MeshViewer;
