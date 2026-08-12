html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI Hotboard</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0a0a0f;color:#e0e0e0;font-family:Arial,sans-serif}
.header{background:linear-gradient(135deg,#1a1a2e,#16213e);padding:20px 32px;border-bottom:1px solid #2a2a4a}
.header h1{font-size:22px;color:#ffd700}
.header .sub{font-size:12px;color:#888;margin-top:4px}
.container{max-width:1200px;margin:0 auto;padding:20px 24px}
.tabs{display:flex;margin-bottom:24px;border-bottom:2px solid #2a2a4a}
.tab{padding:12px 28px;cursor:pointer;font-size:14px;color:#888;border-bottom:2px solid transparent;margin-bottom:-2px}
.tab.active{color:#ffd700;border-bottom-color:#ffd700}
.topic-card{background:#141428;border:1px solid #2a2a4a;border-radius:10px;padding:20px;margin-bottom:16px}
.topic-header{display:flex;align-items:center;gap:14px;margin-bottom:12px}
.rank{font-size:30px;font-weight:900;color:#ffd700;min-width:44px}
.rank.small{font-size:22px;color:#aaa}
.topic-info{flex:1}
.topic-keyword{font-size:18px;font-weight:700;color:#fff}
.topic-summary{font-size:13px;color:#aaa;line-height:1.6;margin-bottom:12px;padding:10px;background:#0d0d20;border-radius:6px;border-left:3px solid #ffd700}
.sources-title{font-size:11px;color:#666;margin-bottom:6px;letter-spacing:1px}
.sources{display:flex;flex-wrap:wrap;gap:6px}
.source-pill{display:inline-flex;align-items:center;gap:4px;padding:4px 10px;background:#1a1a35;border:1px solid #333;border-radius:16px;font-size:11px;color:#ccc;text-decoration:none}
.source-pill:hover{background:#2a2a55;border-color:#ffd700;color:#ffd700}
.source-pill .dot{width:5px;height:5px;border-radius:50%;background:#ffd700}
.video-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:12px;margin-top:12px}
.video-card{background:#0d0d20;border:1px solid #2a2a4a;border-radius:8px;overflow:hidden;text-decoration:none;color:inherit;display:block}
.video-card:hover{border-color:#fb7299;transform:translateY(-1px)}
.video-cover{position:relative;width:100%;padding-top:56%;background:#1a1a35;overflow:hidden}
.video-cover img{position:absolute;top:0;left:0;width:100%;height:100%;object-fit:cover}
.video-play{position:absolute;bottom:4px;right:4px;background:rgba(0,0,0,.8);color:#fff;font-size:10px;padding:2px 5px;border-radius:3px}
.video-info{padding:10px}
.video-title{font-size:12px;line-height:1.4;margin-bottom:4px;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;color:#ddd}
.video-meta{display:flex;justify-content:space-between;font-size:10px;color:#777}
.bv{font-family:monospace;font-size:9px;color:#555}
.loading{text-align:center;padding:30px;color:#666}
.spinner{width:28px;height:28px;border:3px solid #333;border-top-color:#ffd700;border-radius:50%;animation:s .8s linear infinite;margin:0 auto 10px}
@keyframes s{to{transform:rotate(360deg)}}
.empty{text-align:center;padding:40px;color:#555}
.badge{display:inline-flex;gap:3px;background:#ffd70022;color:#ffd700;font-size:10px;padding:2px 7px;border-radius:8px;margin-left:8px}
.section-divider{display:flex;align-items:center;gap:10px;margin:16px 0 8px}
.section-divider .line{flex:1;height:1px;background:#2a2a4a}
.section-divider span{font-size:11px;color:#555}
.stats-bar{display:flex;gap:16px;margin-bottom:16px}
.stat{background:#141428;border:1px solid #2a2a4a;border-radius:8px;padding:10px 16px}
.stat .val{font-size:22px;font-weight:700;color:#ffd700}
.stat .lbl{font-size:10px;color:#666;margin-top:2px}
</style>
</head>
<body>
<div class="header"><h1>AI Hotboard</h1><div class="sub" id="t">Loading...</div></div>
<div class="container">
<div class="tabs"><div class="tab active" onclick="s(0)">Hot Topics</div><div class="tab" onclick="s(1)">Bilibili 48h</div></div>
<div id="c"></div>
</div>
<script>
var D=null,B={};
async function L(){
try{
var r=await fetch("data/dashboard.json");
D=await r.json();
document.getElementById("t").textContent="Updated: "+new Date(D.generated_at).toLocaleString("zh-CN")+" | 48h items: "+D.total_recent_items+" | Topics: "+D.hot_topics.length;
s(0)
}catch(e){
document.getElementById("t").textContent="Error: "+e.message;
document.getElementById("c").innerHTML="<div class=empty><h3>Data Load Failed</h3><p>Run: python build_dashboard.py</p><p>"+e.message+"</p></div>"
}
}
function s(n){
document.querySelectorAll(".tab").forEach(function(t,i){t.classList.toggle("active",i===n)});
if(n===0)r0();else r1()
}
function r0(){
if(!D||!D.hot_topics){document.getElementById("c").innerHTML="<div class=empty>No data yet. Run build_dashboard.py first.</div>";return}
var h="";
h+="<div class=stats-bar><div class=stat><div class=val>"+D.hot_topics.length+"</div><div class=lbl>Topics</div></div><div class=stat><div class=val>"+D.total_recent_items+"</div><div class=lbl>48h Items</div></div></div>";
D.hot_topics.forEach(function(t){
h+="<div class=topic-card>";
h+="<div class=topic-header><div class='rank"+(t.rank>3?" small":"")+"'>#"+t.rank+"</div><div class=topic-info><div class=topic-keyword>"+t.keyword+"<span class=badge>"+t.resonance+" sources</span></div></div></div>";
h+="<div class=topic-summary>"+t.summary+"</div>";
h+="<div class=sources-title>SOURCES</div><div class=sources>";
t.sources.forEach(function(s){
h+="<a href='"+s.url+"' target=_blank class=source-pill title='"+s.title+"'><span class=dot></span>"+s.name.substring(0,45)+"</a>";
});
h+="</div></div>";
});
document.getElementById("c").innerHTML=h;
}
async function r1(){
if(!D||!D.hot_topics){document.getElementById("c").innerHTML="<div class=empty>No data</div>";return}
var h="<div class=stats-bar><div class=stat><div class=val>"+D.hot_topics.length+"</div><div class=lbl>Scanning</div></div></div>";
D.hot_topics.forEach(function(t,i){
h+="<div class=topic-card>";
h+="<div class=topic-header><div class='rank"+(t.rank>3?" small":"")+"'>#"+t.rank+"</div><div class=topic-info><div class=topic-keyword>"+t.keyword+"<span class=badge>"+t.resonance+" sources</span></div></div></div>";
h+="<div class=section-divider><div class=line></div><span>BILIBILI 48H TOP10</span><div class=line></div></div>";
h+="<div class=loading id=bl"+i+"><div class=spinner></div>Searching...</div>";
h+="<div class=video-grid id=bv"+i+"></div></div>";
});
document.getElementById("c").innerHTML=h;
D.hot_topics.forEach(function(t,i){f(t.search_query,i)});
}
async function f(k,i){
var le=document.getElementById("bl"+i);
var ve=document.getElementById("bv"+i);
if(B[k]){rv(ve,le,B[k]);return}
try{
var u="https://api.bilibili.com/x/web-interface/search/type?search_type=video&order=pubdate&duration=2&page=1&keyword="+encodeURIComponent(k);
var r=await fetch(u,{headers:{Referer:"https://www.bilibili.com"}});
var d=await r.json();
if(d.code===0&&d.data&&d.data.result){
var cut=Date.now()-48*60*60*1000;
var v=d.data.result.filter(function(x){return x.pubdate*1000>cut}).sort(function(a,b){return b.play-a.play}).slice(0,10);
B[k]=v;
rv(ve,le,v);
}else{
if(le)le.innerHTML="<div class=empty>No videos found</div>";
}
}catch(e){
if(le)le.innerHTML="<div class=empty>Bilibili API error: "+e.message+"</div>";
}
}
function rv(ve,le,v){
if(le)le.style.display="none";
if(!v||v.length===0){ve.innerHTML="<div class=empty>No 48h videos</div>";return}
ve.innerHTML=v.map(function(x){
var ps=x.play>10000?Math.floor(x.play/10000)+"w":x.play;
return "<a href='https://www.bilibili.com/video/"+x.bvid+"' target=_blank class=video-card><div class=video-cover><img src='"+x.pic.replace("http:","https:")+"' loading=lazy onerror=\"this.style.display='none'\"><div class=video-play>"+ps+" plays</div></div><div class=video-info><div class=video-title>"+x.title+"</div><div class=video-meta><span>"+x.author+"</span><span class=bv>"+x.bvid+"</span></div></div></a>";
}).join("");
}
L();
</script>
</body>
</html>"""

with open("C:/Users/qiyanxi/Bitto/default/ai-hotboard/dashboard.html", "w", encoding="utf-8") as f:
    f.write(html)
print("dashboard.html written (utf-8, no BOM)")
