from flask import Flask, render_template_string, request, redirect, url_for, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import os, uuid, json

app = Flask(__name__)
app.secret_key = "yousi-local-secret"
app.config["MAX_CONTENT_LENGTH"] = 300 * 1024 * 1024

BASE = os.path.dirname(os.path.abspath(__file__))
VIDEO_DIR = os.path.join(BASE, "static", "videos")
UPLOAD_DIR = os.path.join(BASE, "static", "uploads")
DATA_FILE = os.path.join(BASE, "yousi_data.json")
os.makedirs(VIDEO_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED = (".mp4", ".webm", ".mov", ".m4v")
IMAGE_ALLOWED = (".jpg", ".jpeg", ".png", ".webp")
MEDIA_ALLOWED = ALLOWED + IMAGE_ALLOWED

def load_data():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {
            "profile": {"name": "YOUSI User", "username": "yousi_user",
                        "bio": "Welcome to my YOUSI profile ✨", "avatar": ""},
            "likes": [], "favorites": [], "videos": {}, "comments": {}, "views": {}, "following": [],
            "settings": {"private": False, "notifications": True}
        }

data = load_data()
data.setdefault("comments", {})
data.setdefault("views", {})
data.setdefault("following", [])
data.setdefault("wallet", {
    "balance": 0.0,
    "total_earned": 0.0,
    "coins": 0
})

def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def video_list():
    files = [f for f in os.listdir(VIDEO_DIR)
             if f.lower().endswith(MEDIA_ALLOWED)]
    return sorted(files, reverse=True)

def profile():
    return data["profile"]

PAGE = r"""
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,viewport-fit=cover">
<title>YOUSI</title>
<style>
*{box-sizing:border-box;-webkit-tap-highlight-color:transparent}
html,body{margin:0;background:#000;color:#fff;font-family:Arial,sans-serif}
body{overscroll-behavior:none}a{color:inherit;text-decoration:none}
button{color:inherit;border:0;cursor:pointer;font:inherit}
header{height:58px;position:fixed;z-index:10;top:0;left:0;right:0;background:#080808;display:flex;align-items:center;justify-content:space-between;padding:0 12px}
.logo{font-size:23px;font-weight:900;color:#ff3158;letter-spacing:-1px}
.tabs{display:flex;align-items:center;justify-content:space-around;gap:0;height:58px;flex:1;min-width:0;margin:0 7px}
.tabs a{height:58px;display:flex;align-items:center;justify-content:center;flex:1;min-width:0;position:relative;font-size:12px;font-weight:800;color:#aaa;white-space:nowrap}
.tabs a.active{color:#fff}
.tabs a.active:after{content:"";height:3px;background:#ff3158;border-radius:4px;position:absolute;bottom:5px;left:8px;right:8px}
.search{width:30px;flex:0 0 30px;height:58px;display:flex;align-items:center;justify-content:center;position:relative;color:#fff}
.search svg{width:22px;height:22px;stroke:currentColor;fill:none;stroke-width:2.2;stroke-linecap:round}
.search.active:after{content:"";height:3px;background:#ff3158;border-radius:4px;position:absolute;bottom:5px;left:2px;right:2px}
.feed{padding-top:58px;padding-bottom:62px}
.video-card{-webkit-touch-callout:none;user-select:none;touch-action:pan-y;height:calc(100dvh - 120px);min-height:400px;position:relative;background:#111;overflow:hidden;scroll-snap-align:start}
.feed-video{width:100%;height:100%;object-fit:cover}
.feed-image{width:100%;height:100%;object-fit:contain;background:#080808}
.play-mark{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);font-size:65px;color:#fff9;display:none;pointer-events:none;text-shadow:0 2px 10px #000}
.side{position:absolute;right:10px;bottom:75px;display:flex;flex-direction:column;align-items:center;gap:18px;z-index:3}
.action{background:transparent;display:flex;flex-direction:column;align-items:center;gap:4px;font-size:11px;text-shadow:0 1px 4px #000}
.action svg{width:29px;height:29px;stroke:white;fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}
.action.liked svg{fill:#ff3158;stroke:#ff3158}
.info{position:absolute;bottom:18px;left:13px;right:70px;z-index:3;text-shadow:0 1px 5px #000}
.info b{font-size:15px}.info p{font-size:13px;margin:6px 0}
.bottom{height:62px;position:fixed;bottom:0;left:0;right:0;background:#080808;display:flex;justify-content:space-around;align-items:center;z-index:10;border-top:1px solid #222}
.bottom a{display:flex;flex-direction:column;align-items:center;gap:3px;font-size:10px;color:#aaa;min-width:48px}
.bottom svg{width:23px;height:23px;stroke:currentColor;fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}
.bottom a.active{color:#fff}
.plus{width:39px;height:27px;background:#ff3158;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:27px}
.empty{text-align:center;padding:110px 15px;color:#ddd}
.page{padding:78px 16px 85px;max-width:600px;margin:auto}
.primary{background:#ff3158;color:white;border-radius:8px;padding:11px 18px;font-weight:bold}
.secondary{background:#252525;color:white;border-radius:8px;padding:10px 15px}
.field{width:100%;background:#171717;color:white;border:1px solid #444;border-radius:8px;padding:13px;margin:7px 0 16px}
.avatar{width:90px;height:90px;border-radius:50%;object-fit:cover;background:#333;border:2px solid #ff3158}
.stats{display:flex;justify-content:center;gap:28px;margin:22px 0;text-align:center}
.stats b{display:block;font-size:19px}.stats span{font-size:12px;color:#aaa}
.video-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:3px;margin-top:20px}
.video-grid video{width:100%;height:150px;object-fit:cover;background:#222}
.row{display:flex;align-items:center;gap:14px;padding:15px 0;border-bottom:1px solid #292929}
.row .right{margin-left:auto;color:#aaa}
.sound-head{display:flex;align-items:center;gap:15px;margin:25px 0}
.sound-art{width:105px;height:105px;border-radius:12px;background:linear-gradient(135deg,#ff3158,#39203c);display:grid;place-items:center;font-size:40px}
.creator{display:flex;align-items:center;gap:10px;margin:15px 0}
.creator img{width:43px;height:43px;border-radius:50%;object-fit:cover;background:#333}
.sheet-backdrop{position:fixed;inset:0;background:#0008;z-index:50;display:none}
.sheet{position:absolute;left:0;right:0;bottom:0;background:#202020;border-radius:20px 20px 0 0;padding:17px 13px calc(20px + env(safe-area-inset-bottom));max-height:78dvh;overflow:auto;animation:rise .22s ease}
@keyframes rise{from{transform:translateY(100%)}to{transform:translateY(0)}}
.sheet-title{text-align:center;font-weight:bold;margin:0 0 17px}
.friend-strip{display:flex;gap:17px;overflow-x:auto;padding:8px 3px 18px;margin-bottom:13px;border-bottom:1px solid #393939}
.friend-shortcut{min-width:65px;text-align:center;font-size:11px;color:#ddd}
.friend-avatar{width:52px;height:52px;margin:0 auto 7px;border-radius:50%;display:grid;place-items:center;background:linear-gradient(135deg,#ff3158,#7045a5);font-size:19px;font-weight:800;border:2px solid #555}
.friend-add{background:#333;color:#fff;border:2px dashed #aaa;font-size:25px}
.friend-shortcut a{color:#ddd}

.menu-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:18px 8px}
.menu-item{background:transparent;display:flex;flex-direction:column;align-items:center;gap:7px;font-size:11px;color:#eee}
.menu-icon{width:52px;height:52px;border-radius:50%;background:#363636;display:grid;place-items:center}
.menu-icon svg{width:24px;height:24px;stroke:white;fill:none;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round}
.menu-icon.brand{font-weight:900;font-size:22px}.menu-icon.brand svg{width:30px;height:30px;stroke:none;fill:currentColor}.menu-icon.brand{background:#292929}
.speed-options{display:flex;gap:9px;justify-content:center;margin-top:18px}
.speed-options button{background:#383838;padding:9px 13px;border-radius:20px}
.camera{display:none;position:fixed;inset:0;background:#000;z-index:30}
#cameraView{width:100%;height:100%;object-fit:cover}
.cam-top{position:absolute;top:15px;left:15px;right:15px;display:flex;justify-content:space-between}
.cam-top button,.cam-icon{background:#333b;border:1px solid #fff6;border-radius:50%;width:44px;height:44px}
.cam-bottom{position:absolute;bottom:20px;left:0;right:0;display:flex;flex-direction:column;align-items:center;gap:15px}
.filters{display:flex;gap:12px;overflow-x:auto;width:100%;padding:8px}
.filter{background:#222;color:white;border-radius:18px;padding:9px 12px;white-space:nowrap}
.filter.selected{background:#ff3158}
.camera-buttons{display:flex;justify-content:space-around;align-items:center;width:100%}
.record{width:72px;height:72px;border:5px solid white;border-radius:50%;background:#ff3158}
.record.recording{border-radius:15px;background:white;width:55px;height:55px}
#gallery{display:none}
#splash{position:fixed;inset:0;background:#050505;z-index:100;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:24px;animation:fadeout .5s ease 1.7s forwards}
.splash-logo{font-size:48px;font-weight:900;color:#ff3158}
.dots{display:flex;gap:10px}.dots i{width:10px;height:10px;border-radius:50%;background:#ff3158;animation:bounce .65s infinite alternate}
.dots i:nth-child(2){animation-delay:.2s}
@keyframes bounce{to{transform:translateY(-12px);opacity:.4}}
@keyframes fadeout{to{opacity:0;visibility:hidden;pointer-events:none}}
@media(max-width:370px){.tabs{gap:8px}.tabs a{font-size:11px}.logo{font-size:20px}}
 .shop-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}
.product-card{background:#171717;border:1px solid #303030;border-radius:12px;padding:12px;min-width:0}
.product-picture{height:115px;border-radius:9px;background:linear-gradient(135deg,#30303a,#171717);display:grid;place-items:center;font-size:58px}
.product-card h3{font-size:15px;margin:12px 0 5px}
.product-card p{font-size:12px;color:#aaa;min-height:28px}
.cart-box{background:#171717;border:1px solid #444;border-radius:12px;padding:15px;margin-top:20px}
.cart-line{display:flex;justify-content:space-between;gap:10px;padding:10px 0;border-bottom:1px solid #333}
@media(max-width:370px){.tabs{gap:6px}.tabs a{font-size:10px}.logo{font-size:18px}}

.live-screen{position:fixed;inset:0;background:#050505;z-index:80;color:white}
#livePreview{width:100%;height:100%;object-fit:cover;position:absolute;inset:0}
.live-shade{position:absolute;inset:0;background:linear-gradient(#0008,transparent 30%,transparent 55%,#000c)}
.live-top{position:absolute;top:18px;left:16px;right:16px;display:flex;justify-content:space-between;align-items:center}
.live-top button{width:44px;height:44px;border:1px solid #ffffff66;border-radius:50%;background:#222b;color:white;font-size:22px}
.live-panel{position:absolute;bottom:25px;left:16px;right:16px}
.live-title{width:100%;box-sizing:border-box;padding:14px;border:1px solid #ffffff55;border-radius:12px;background:#222b;color:white;font-size:16px;margin-bottom:14px}
.live-options{display:flex;gap:10px;margin-bottom:15px}
.live-options button{flex:1;padding:12px 5px;border:1px solid #ffffff55;border-radius:12px;background:#222b;color:white}
.live-start{width:100%;padding:16px;border:0;border-radius:30px;background:#ff3158;color:white;font-size:18px;font-weight:bold}
#liveStatus{text-align:center;font-size:12px;color:white;margin-top:12px}


.inbox-page{padding:75px 15px 85px;background:#080808;min-height:100vh}
.inbox-head{display:flex;justify-content:space-between;align-items:center}
.inbox-tabs{display:flex;gap:24px;border-bottom:1px solid #333;margin:18px 0}
.inbox-tabs button{background:none;color:#aaa;padding:12px 0}
.inbox-tabs button.active{color:white;border-bottom:3px solid #ff3158}
.inbox-person{display:flex;align-items:center;gap:12px;padding:13px 0;border-bottom:1px solid #292929;width:100%;text-align:left;background:none}
.inbox-avatar{width:49px;height:49px;border-radius:50%;display:grid;place-items:center;background:linear-gradient(135deg,#ff3158,#7045a5);font-weight:bold;font-size:19px;flex-shrink:0}
.inbox-info{flex:1;min-width:0}.inbox-info b{display:block}.inbox-info small{color:#aaa}
.inbox-chat{display:none;position:fixed;inset:0;background:#090909;z-index:60;padding:15px;padding-top:25px}
.inbox-chat-top{display:flex;align-items:center;gap:12px;border-bottom:1px solid #333;padding-bottom:14px}
.inbox-chat-messages{height:65vh;overflow:auto;padding:15px 0}
.inbox-bubble{background:#292929;border-radius:17px;padding:11px 14px;margin:9px 0;max-width:80%;width:max-content}
.inbox-bubble.mine{background:#d92c58;margin-left:auto}
.inbox-compose{position:absolute;bottom:20px;left:12px;right:12px;display:flex;gap:8px}
.inbox-compose input{flex:1;min-width:0;background:#252525;border:0;border-radius:24px;padding:13px;color:white}
.inbox-compose button{background:#ff3158;border-radius:22px;padding:0 18px}


.camera{overflow:hidden;color:white;background:#000}
#cameraView{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;transition:filter .2s,transform .2s}
.cam-top{z-index:4;align-items:center;gap:8px}
.cam-top button{color:white;background:#222b;font-size:19px}
.cam-top .music-control{width:auto;padding:0 13px;border-radius:22px;font-size:13px}
.cam-side{position:absolute;z-index:4;right:10px;top:90px;display:flex;flex-direction:column;gap:13px}
.cam-side button{width:47px;height:47px;border:0;border-radius:50%;background:#222b;color:white;font-size:21px;display:flex;flex-direction:column;align-items:center;justify-content:center}
.cam-side small,.cam-icon small{font-size:10px}
.cam-bottom{z-index:4;bottom:12px;gap:12px;padding:0 8px}
.cam-modes{display:flex;justify-content:center;gap:18px;width:100%}
.cam-mode{background:transparent;color:#ddd;border:0;padding:8px 3px;font-weight:bold}
.cam-mode.selected{color:white;border-bottom:3px solid #ff3158}
.camera-buttons{justify-content:space-evenly}
.camera-buttons .cam-icon{display:flex;flex-direction:column;align-items:center;justify-content:center;color:white}
.record{width:76px;height:76px;border:5px solid white;background:#ff3158;box-shadow:0 0 0 4px #ffffff55}
.record.recording{width:55px;height:55px;border-radius:14px;background:white}
#camHint{font-size:11px;color:white}
#gallery{display:none}
\n
.camera{overflow:hidden;color:#fff;background:#000}
#cameraView{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}
.cam-top{z-index:5;align-items:center;gap:9px}
.cam-top button{color:white;background:#222b;border:1px solid #ffffff55}
.cam-top .music-control{width:auto;padding:0 15px;border-radius:24px;font-size:13px}
.cam-side{position:absolute;z-index:5;right:12px;top:90px;display:flex;flex-direction:column;gap:13px}
.cam-side button{width:48px;height:48px;border:0;border-radius:50%;background:#2229;color:white;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:1px}
.cam-side button span{font-size:22px}
.cam-side small{font-size:10px}
.cam-bottom{z-index:5;bottom:12px;gap:12px;padding:0 8px}
.cam-modes{display:flex;justify-content:center;align-items:center;gap:20px;width:100%}
.cam-mode{background:transparent;color:#ddd;border:0;padding:9px 4px;font-size:13px;font-weight:800}
.cam-mode.selected{color:white;border-bottom:3px solid #ff3158}
.camera-buttons{justify-content:space-evenly;align-items:center}
.camera-buttons .cam-icon{width:50px;height:50px;border:0;background:transparent;color:white;font-size:23px;display:flex;flex-direction:column;align-items:center;justify-content:center}
.cam-icon small{font-size:10px}
.record{flex:none;width:78px;height:78px;min-width:78px;min-height:78px;border:5px solid white;border-radius:50%;background:#ff3158;box-shadow:0 0 0 4px #ffffff55}
.record.recording{width:58px;height:58px;min-width:58px;min-height:58px;border-radius:15px;background:white}
#camHint{color:white;font-size:11px}
#gallery{display:none}
.post-editor{display:none;position:fixed;inset:0;z-index:60;background:#111;color:white;overflow-y:auto;padding:16px;flex-direction:column;gap:14px}
.editor-head{display:flex;align-items:center;justify-content:space-between;padding:8px 0}
.editor-head button{background:#333;color:white;border:0;border-radius:20px;padding:9px 15px}
.post-preview{height:250px;display:flex;justify-content:center;align-items:center;background:#080808;border-radius:12px;overflow:hidden}
.post-preview img,.post-preview video{height:100%;max-width:100%;object-fit:contain}
#postCaption{width:100%;height:105px;resize:vertical;background:#252525;border:1px solid #444;border-radius:10px;color:white;padding:13px;font:15px Arial}
.editor-options{background:#202020;border-radius:12px;padding:12px}
.editor-options>div{display:flex;align-items:center;gap:10px;padding:12px 3px;border-bottom:1px solid #444}
.editor-options>div:last-child{border:0}
.editor-options span{font-size:14px;font-weight:600}
.editor-options small{margin-left:auto;color:#aaa;font-size:11px}
.editor-options select{margin-left:auto;background:#333;color:white;border:0;padding:8px;border-radius:8px}
.editor-options input{margin-left:auto;accent-color:#ff3158}
.publish-post{width:100%;padding:15px;border:0;border-radius:9px;background:#ff3158;color:white;font-weight:800;font-size:16px}

</style>
</head>
<body>

<div id="splash">
<script>
try {
  if (sessionStorage.getItem('yousi_splash_seen') === '1') {
    document.getElementById('splash').remove();
  } else {
    sessionStorage.setItem('yousi_splash_seen', '1');
  }
} catch(e) {}

let liveStream = null;
let liveFacing = 'environment';

async function openLiveCamera(){
  const preview = document.getElementById('livePreview');
  if(!preview) return;
  try{
    liveStream = await navigator.mediaDevices.getUserMedia({
      video:{facingMode:liveFacing},
      audio:true
    });
    preview.srcObject = liveStream;
    await preview.play();
    document.getElementById('liveStatus').textContent =
      'Camera ready. You are in preview mode.';
  }catch(err){
    document.getElementById('liveStatus').textContent =
      'Camera permission denied. Allow camera and microphone access.';
  }
}

function stopLiveCamera(){
  if(liveStream){
    liveStream.getTracks().forEach(track=>track.stop());
    liveStream=null;
  }
}

async function switchLiveCamera(){
  liveFacing = liveFacing === 'environment' ? 'user' : 'environment';
  stopLiveCamera();
  await openLiveCamera();
}

function closeLive(){
  stopLiveCamera();
  location.href='/';
}

function startLocalLive(){
  const title = document.getElementById('liveTitle').value.trim();
  const status = document.getElementById('liveStatus');
  if(!liveStream){
    status.textContent='Please allow camera and microphone first.';
    return;
  }
  status.textContent = title
    ? 'Preview ready: ' + title + '. Streaming server is not connected yet.'
    : 'Preview ready. Streaming server is not connected yet.';
}

if(document.getElementById('livePreview')){
  openLiveCamera();
}


function showInboxTab(which){
 const messages=document.getElementById('inboxMessages');
 const requests=document.getElementById('inboxRequests');
 if(!messages||!requests)return;
 messages.style.display=which==='messages'?'block':'none';
 requests.style.display=which==='requests'?'block':'none';
 document.getElementById('tabMessages').classList.toggle('active',which==='messages');
 document.getElementById('tabRequests').classList.toggle('active',which==='requests');
}
function openInboxChat(name,initial){
 document.getElementById('chatName').textContent=name;
 document.getElementById('chatAvatar').textContent=initial;
 document.getElementById('inboxChat').style.display='block';
}
function closeInboxChat(){document.getElementById('inboxChat').style.display='none';}
function sendInboxMessage(){
 const input=document.getElementById('chatInput');
 const value=input.value.trim(); if(!value)return;
 const bubble=document.createElement('div');
 bubble.className='inbox-bubble mine';
 bubble.textContent=value;
 document.getElementById('chatMessages').appendChild(bubble);
 input.value='';
 document.getElementById('chatMessages').scrollTop=999999;
}

</script>
<div class="splash-logo">✦ YOUSI</div><div class="dots"><i></i><i></i></div></div>

<header>
<a class="logo" href="/">✦ YOUSI</a>
<nav class="tabs">
<a href="/" class="{{ 'active' if tab=='For You' else '' }}">For You</a>
<a href="/following" class="{{ 'active' if tab=='Following' else '' }}">Following</a>
<a href="/live" class="{{ 'active' if tab=='LIVE' else '' }}">LIVE</a>
<a href="/shop" class="{{ 'active' if tab=='Shop' else '' }}">Shop</a>
</nav>
<a class="search {{ 'active' if tab=='Search' else '' }}" href="/search" aria-label="Search">
<svg viewBox="0 0 24 24"><circle cx="10.8" cy="10.8" r="6.8"/><path d="m16 16 5 5"/></svg>
</a>
</header>

{% if page == 'feed' %}
<div class="feed" id="feed">
{% for v in videos %}
<div class="video-card" data-video="{{ v }}">
{% if v.rsplit('.',1)[-1].lower() in ['jpg','jpeg','png','webp'] %}
<img class="feed-image" src="{{ url_for('static',filename='videos/'+v) }}" alt="YOUSI photo">
{% else %}
<video class="feed-video" src="{{ url_for('static',filename='videos/'+v) }}" autoplay playsinline loop controls preload="metadata"></video>
{% endif %}
<div class="play-mark">▶</div>
<div class="side">
<button class="action {{ 'liked' if v in liked else '' }}" onclick="toggleLike('{{ v }}',this)">
<svg viewBox="0 0 24 24"><path d="M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.7l-1.1-1.1a5.5 5.5 0 0 0-7.8 7.8l1.1 1.1L12 21l7.8-7.5 1.1-1.1a5.5 5.5 0 0 0-.1-7.8z"/></svg><small>{{ '1' if v in liked else '0' }}</small>
</button>
<a class="action" href="/comment/{{ v }}"><svg viewBox="0 0 24 24"><path d="M21 11.5a8.5 8.5 0 0 1-8.5 8.5 8 8 0 0 1-4-.9L3 21l1.9-5.5a8 8 0 0 1-.9-4A8.5 8.5 0 0 1 12.5 3h.5a8.5 8.5 0 0 1 8 8z"/></svg><small>{{ comments_data.get(v, [])|length }} comments</small></a>
<button class="action" onclick="openShare('{{ v }}')"><svg viewBox="0 0 24 24"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><path d="m8.6 10.7 6.8-4.4M8.6 13.3l6.8 4.4"/></svg><small>Share</small></button>
<a class="action" href="/sound/{{ v }}"><svg viewBox="0 0 24 24"><path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/></svg><small>Sound</small></a>
</div>
<div class="info"><b>@{{ username }}</b><p>{{ metadata.get(v,{}).get('caption','Welcome to YOUSI ✨') }}</p><small>{{ views_data.get(v, 0) }} views</small></div>
</div>
{% endfor %}
{% if not videos %}<div class="empty">Welcome to YOUSI ✨<p>Upload your first video using +</p></div>{% endif %}
</div>
{% elif page == 'profile' %}
<div class="page">
<div style="text-align:center">
{% if avatar %}<img class="avatar" src="{{ url_for('static',filename='uploads/'+avatar) }}">{% else %}<div class="avatar" style="display:inline-grid;place-items:center;font-size:35px">👤</div>{% endif %}
<h2>{{ display_name }}</h2><p style="color:#aaa">@{{ username }}</p><p>{{ bio }}</p>
<div class="stats"><div><b>{{ videos|length }}</b><span>Videos</span></div><div><b>0</b><span>Following</span></div><div><b>0</b><span>Followers</span></div><div><b>{{ liked|length }}</b><span>Likes</span></div></div>
<a class="secondary" href="/wallet">💰 My Wallet</a>
<a class="secondary" href="/edit-profile">Edit Profile</a>
<a class="secondary" href="/settings">⚙ Settings</a>
<button class="secondary" onclick="shareProfile()">Share Profile</button>
</div>
<h3>Videos</h3><div class="video-grid">{% for v in videos %}<a href="/?video={{ v }}"><video src="{{ url_for('static',filename='videos/'+v) }}" muted></video></a>{% endfor %}</div>
</div>
{% elif page == 'wallet' %}
<div class="page">
<h2>💰 My Wallet</h2>
<div class="row"><span>Available Balance</span><b>Rs. {{ wallet.balance }}</b></div>
<div class="row"><span>Total Earnings</span><b>Rs. {{ wallet.total_earned }}</b></div>
<div class="row"><span>YOUSI Coins</span><b>{{ wallet.coins }}</b></div>
<div class="row"><span>Withdraw</span><b>Coming Soon</b></div>
<p style="color:#aaa;margin-top:20px">This is a demo wallet. Real payments will be enabled after payment setup.</p>
<a class="secondary" href="/profile">Back to Profile</a>
</div>
{% elif page == 'edit' %}
<div class="page"><h2>Edit Profile</h2>
<form method="post" enctype="multipart/form-data">
<label>Profile Picture</label><input class="field" type="file" name="avatar" accept="image/*">
<label>Name</label><input class="field" name="name" value="{{ display_name }}" maxlength="40">
<label>Username</label><input class="field" name="username" value="{{ username }}" maxlength="25">
<label>Bio</label><textarea class="field" name="bio" rows="4" maxlength="150">{{ bio }}</textarea>
<button class="primary">Save Profile</button>
</form></div>
{% elif page == 'settings' %}
<div class="page"><h2>Settings</h2>
<a class="row" href="/edit-profile">Account <span class="right">›</span></a>
<div class="row">Private Account <span class="right"><input type="checkbox" id="private" {{ 'checked' if settings.private else '' }} onchange="saveSetting('private',this.checked)"></span></div>
<div class="row">Notifications <span class="right"><input type="checkbox" id="notifications" {{ 'checked' if settings.notifications else '' }} onchange="saveSetting('notifications',this.checked)"></span></div>
<div class="row">Privacy and Safety <span class="right">›</span></div>
<div class="row">About YOUSI <span class="right">Local prototype</span></div>
</div>
{% elif page == 'comments' %}
<div class="page">
<h2>Comments</h2>
<div class="row"><a href="/">‹ Back to YOUSI</a><span class="right">{{ results|length }} comments</span></div>
{% if metadata.get(sound_file, {}).get('allow_comments', True) %}
<form method="post" action="/comment/{{ sound_file }}">
<input class="field" name="comment" maxlength="500" required placeholder="Add a comment...">
<button class="primary" type="submit">Post comment</button>
</form>
{% else %}<p>Comments are turned off for this post.</p>{% endif %}
{% for c in results|reverse %}<div class="row"><b>@{{ c.user }}</b><span>{{ c.text }}</span></div>{% endfor %}
{% if not results %}<p style="color:#aaa">Be the first to comment.</p>{% endif %}
</div>
{% elif page == 'sound' %}
<div class="page">
<h2>Sound</h2>
<div class="sound-head"><div class="sound-art">♫</div><div><h3>{{ sound_name }}</h3><p style="color:#aaa">Original sound</p><p style="color:#aaa">Used in {{ sound_videos|length }} video(s)</p></div></div>
<div class="creator">
{% if avatar %}<img src="{{ url_for('static',filename='uploads/'+avatar) }}">{% else %}<img src="">{% endif %}
<div><b>{{ display_name }}</b><div style="color:#aaa;font-size:12px">@{{ username }} · Sound creator</div></div>
</div>
<a class="primary" href="/?camera=1&sound={{ sound_file }}">＋ Use This Sound</a>
<h3 style="margin-top:30px">Videos using this sound</h3>
<div class="video-grid">{% for v in sound_videos %}<a href="/?video={{ v }}"><video src="{{ url_for('static',filename='videos/'+v) }}" muted></video></a>{% endfor %}</div>
<button class="secondary" onclick="copyText(location.href)">Copy Sound Link</button>
</div>
{% elif page == 'search' %}
<div class="page">
<h2>Search YOUSI</h2>
<form method="get" action="/search">
<input class="field" name="q" value="{{ query }}" placeholder="Search videos, users or hashtags...">
<button class="primary" type="submit">Search</button>
</form>
{% if query %}
<h3>Search results for: {{ query }}</h3>
{% if profile_match %}
<div class="row"><span>👤</span><b>{{ display_name }}</b><span>@{{ username }}</span></div>
{% endif %}
<div class="video-grid">
{% for v in results %}
<a href="/?video={{ v }}"><video src="{{ url_for('static',filename='videos/'+v) }}" muted playsinline></video></a>
{% endfor %}
</div>
{% if not results and not profile_match %}
<p style="color:#aaa;text-align:center;padding:25px">No results found. Try another search.</p>
{% endif %}
{% else %}
<h3>Trending searches</h3>
<a class="row" href="/search?q=%23YOUSI">#YOUSI <span class="right">›</span></a>
<a class="row" href="/search?q=%23Video">#Video <span class="right">›</span></a>
<a class="row" href="/search?q=%23Pakistan">#Pakistan <span class="right">›</span></a>
<h3>Popular videos</h3>
<div class="video-grid">
{% for v in videos %}
<a href="/?video={{ v }}"><video src="{{ url_for('static',filename='videos/'+v) }}" muted playsinline></video></a>
{% endfor %}
</div>
{% endif %}
</div>

{% elif page == 'inbox' %}
<div class="inbox-page">
 <div class="inbox-head"><h2>Inbox</h2><span>✉️</span></div>
 <div class="inbox-tabs">
  <button id="tabMessages" class="active" onclick="showInboxTab('messages')">Messages</button>
  <button id="tabRequests" onclick="showInboxTab('requests')">Message Requests</button>
 </div>
 <div id="inboxMessages">
  <button class="inbox-person" onclick="openInboxChat('YOUSI Friend','Y')">
   <span class="inbox-avatar">Y</span><span class="inbox-info"><b>YOUSI Friend</b><small>Start a conversation</small></span><span>›</span>
  </button>
  <button class="inbox-person" onclick="openInboxChat('New Friend','N')">
   <span class="inbox-avatar">N</span><span class="inbox-info"><b>New Friend</b><small>Say hello 👋</small></span><span>›</span>
  </button>
  <p style="color:#888;text-align:center;margin-top:30px;font-size:12px">یہ مقامی ڈیمو چیٹ ہے۔ حقیقی پیغامات کے لیے صارف اکاؤنٹس اور آن لائن سرور درکار ہوگا۔</p>
 </div>
 <div id="inboxRequests" style="display:none">
  <p style="color:#aaa;text-align:center;padding:30px 5px">ابھی کوئی Message Request نہیں ہے۔</p>
 </div>
</div>
<div class="inbox-chat" id="inboxChat">
 <div class="inbox-chat-top">
  <button onclick="closeInboxChat()" style="background:none;font-size:25px">‹</button>
  <span class="inbox-avatar" id="chatAvatar">Y</span>
  <b id="chatName">Friend</b>
 </div>
 <div class="inbox-chat-messages" id="chatMessages">
  <p style="color:#888;text-align:center;font-size:12px">Conversation شروع کریں</p>
 </div>
 <div class="inbox-compose">
  <input id="chatInput" placeholder="Write a message..." onkeydown="if(event.key==='Enter')sendInboxMessage()">
  <button onclick="sendInboxMessage()">Send</button>
 </div>
</div>

{% elif page == 'shop' %}
<div class="page">
<h2>🛍 YOUSI Shop</h2>
<p style="color:#aaa">Discover products and add them to your cart.</p>
<input class="field" id="shopSearch" placeholder="Search products..." oninput="filterProducts()">
<div style="display:flex;justify-content:space-between;align-items:center;margin:15px 0">
<h3>Products</h3>
<button class="primary" onclick="showCart()">🛒 Cart (<span id="cartCount">0</span>)</button>
</div>
<div class="shop-grid" id="productGrid">
{% for p in products %}
<div class="product-card" data-name="{{ p.name|lower }}">
<div class="product-picture">{{ p.emoji }}</div>
<h3>{{ p.name }}</h3>
<p>{{ p.description }}</p>
<b>Rs {{ p.price }}</b>
<button class="primary" style="width:100%;margin-top:12px" onclick='addToCart({{ p.name|tojson }},{{ p.price|tojson }})'>Add to Cart</button>
</div>
{% endfor %}
</div>
<div id="cartBox" class="cart-box" style="display:none">
<h3>Your Cart</h3>
<div id="cartItems"></div>
<h3 id="cartTotal"></h3>
<button class="secondary" onclick="showCart()">Continue Shopping</button>
<button class="secondary" onclick="clearCart()">Clear Cart</button>
</div>
<p style="color:#888;font-size:12px;margin-top:25px">Demo shop: sample products only. Online ordering and payments are not connected yet.</p>
</div>
{% elif page == 'live' %}
<div class="live-screen">
  <video id="livePreview" autoplay muted playsinline></video>
  <div class="live-shade"></div>
  <div class="live-top">
    <button onclick="closeLive()">×</button>
    <button onclick="switchLiveCamera()">↻</button>
  </div>
  <div class="live-panel">
    <input id="liveTitle" class="live-title" placeholder="Write your LIVE title...">
    <div class="live-options">
      <button onclick="switchLiveCamera()">↻ Switch Camera</button>
      <button onclick="document.getElementById('liveTitle').focus()">✎ Add Title</button>
    </div>
    <button class="live-start" onclick="startLocalLive()">Go LIVE</button>
    <p id="liveStatus">Starting camera...</p>
  </div>
</div>
<div class="page"><h2>{{ heading }}</h2><p>{{ message }}</p><a class="primary" href="/">Back to Home</a></div>
{% endif %}

<div class="bottom">
<a class="{{ 'active' if page=='feed' else '' }}" href="/"><svg viewBox="0 0 24 24"><path d="m3 10 9-7 9 7v10a1 1 0 0 1-1 1h-6v-7h-4v7H4a1 1 0 0 1-1-1z"/></svg>Home</a>
<a href="/following"><svg viewBox="0 0 24 24"><circle cx="9" cy="8" r="4"/><path d="M2 21v-2a7 7 0 0 1 14 0v2m3-13a4 4 0 0 1 0 8"/></svg>Friends</a>
<a href="#" onclick="openCamera(event)"><span class="plus">+</span>Upload</a>
<a href="/inbox"><svg viewBox="0 0 24 24"><path d="M4 4h16v16H4zM4 13h4l2 3h4l2-3h4"/></svg>Inbox</a>
<a class="{{ 'active' if page=='profile' else '' }}" href="/profile"><svg viewBox="0 0 24 24"><circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/></svg>Profile</a>
</div>

<div class="sheet-backdrop" id="menuBackdrop" onclick="if(event.target===this)closeMenu()">
<div class="sheet">
<p class="sheet-title">Video Options</p>
<div class="friend-strip">
 <div class="friend-shortcut"><a href="/following"><div class="friend-avatar friend-add">+</div>Find Friends</a></div>
 <div class="friend-shortcut"><div class="friend-avatar">Y</div>YOUSI</div>
 <div class="friend-shortcut"><div class="friend-avatar">S</div>Share</div>
 <div class="friend-shortcut"><div class="friend-avatar">M</div>Message</div>
</div>

<div class="menu-grid">
<button class="menu-item" onclick="menuAction('delete')"><span class="menu-icon"><svg viewBox="0 0 24 24"><path d="M3 6h18M8 6V4h8v2m3 0-1 14H6L5 6m4 4v6m6-6v6"/></svg></span>Delete</button>
<button class="menu-item" onclick="menuAction('copy')"><span class="menu-icon"><svg viewBox="0 0 24 24"><rect x="8" y="8" width="13" height="13" rx="2"/><path d="M16 8V5a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h3"/></svg></span>Copy Link</button>
<button class="menu-item" onclick="menuAction('download')"><span class="menu-icon"><svg viewBox="0 0 24 24"><path d="M12 3v12m-5-5 5 5 5-5M4 20h16"/></svg></span>Download</button>
<button class="menu-item" onclick="menuAction('favorite')"><span class="menu-icon"><svg viewBox="0 0 24 24"><path d="m12 3 2.8 5.7 6.2.9-4.5 4.4 1.1 6.2-5.6-3-5.6 3 1.1-6.2L3 9.6l6.2-.9z"/></svg></span>Add to Favorites</button>
<button class="menu-item" onclick="menuAction('whatsapp')"><span class="menu-icon brand" style="color:#25d366"><svg viewBox="0 0 24 24"><path d="M12 2a9.8 9.8 0 0 0-8.5 14.7L2 22l5.5-1.4A10 10 0 1 0 12 2zm0 18a8 8 0 0 1-4.1-1.1l-.4-.2-3.2.8.9-3.1-.3-.5A8 8 0 1 1 12 20zm4.4-5.9c-.2-.1-1.4-.7-1.6-.8-.2-.1-.4-.1-.5.1l-.7.8c-.1.2-.3.2-.5.1a6.5 6.5 0 0 1-3.2-2.8c-.2-.3.2-.3.6-1 .1-.2 0-.4 0-.5l-.7-1.7c-.2-.4-.4-.4-.5-.4h-.5c-.2 0-.5.1-.7.3-.2.2-.9.9-.9 2.1s.9 2.4 1 2.5c.1.2 1.8 2.8 4.4 3.8 1.6.7 2.2.7 3 .6.5-.1 1.4-.6 1.6-1.2.2-.6.2-1.1.1-1.2-.1-.1-.3-.2-.5-.3z"/></svg></span>WhatsApp</button>
<button class="menu-item" onclick="menuAction('facebook')"><span class="menu-icon brand" style="color:#1877f2"><svg viewBox="0 0 24 24"><path d="M24 12a12 12 0 1 0-13.9 11.9v-8.4H7.1V12h3V9.3c0-3 1.8-4.7 4.5-4.7 1.3 0 2.6.2 2.6.2v2.9h-1.5c-1.5 0-2 .9-2 1.9V12H17l-.5 3.5h-2.8v8.4A12 12 0 0 0 24 12z"/></svg></span>Facebook</button>
<button class="menu-item" onclick="menuAction('messenger')"><span class="menu-icon brand" style="color:#168aff"><svg viewBox="0 0 24 24"><path d="M12 2C6.2 2 1.5 6.2 1.5 11.4c0 2.8 1.4 5.3 3.7 7l-.6 3.5 3.8-2.1c1.1.3 2.3.5 3.6.5 5.8 0 10.5-4.2 10.5-9.4S17.8 2 12 2z"/><path d="m13.4 5.8-6 7h4l-.8 5.4 6-7h-4z" fill="#fff"/></svg></span>Messenger</button>
<button class="menu-item" onclick="menuAction('share')"><span class="menu-icon"><svg viewBox="0 0 24 24"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><path d="m8.6 10.7 6.8-4.4M8.6 13.3l6.8 4.4"/></svg></span>Share</button>
<button class="menu-item" onclick="menuAction('speed')"><span class="menu-icon"><svg viewBox="0 0 24 24"><path d="M12 3a9 9 0 1 0 9 9M12 7v5l4 2"/></svg></span>Playback Speed</button>
<button class="menu-item" onclick="menuAction('notinterested')"><span class="menu-icon"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="m5.5 5.5 13 13"/></svg></span>Not Interested</button>
<button class="menu-item" onclick="menuAction('report')"><span class="menu-icon"><svg viewBox="0 0 24 24"><path d="M4 21V5m0 0c7-5 9 5 16 0v11c-7 5-9-5-16 0"/></svg></span>Report</button>
<button class="menu-item" onclick="menuAction('sound')"><span class="menu-icon"><svg viewBox="0 0 24 24"><path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/></svg></span>View Sound</button>
</div>
<div id="speedOptions" class="speed-options" style="display:none">
<button onclick="setSpeed(.5)">0.5x</button><button onclick="setSpeed(1)">1x</button><button onclick="setSpeed(1.5)">1.5x</button><button onclick="setSpeed(2)">2x</button>
</div>
</div></div>

<div class="camera" id="camera">
<video id="cameraView" autoplay muted playsinline></video>
<div class="cam-top">
<button onclick="closeCamera()" title="Close">✕</button>
<button class="music-control" onclick="cameraMusic()">♫ Add sound</button>
<button onclick="toggleFlash()">⚡</button>
<button onclick="toggleTimer()">◷</button>
</div>
<div class="cam-side">
<button onclick="switchCamera()"><span>⟳</span><small>Flip</small></button>
<button onclick="changeSpeed()"><span>⏩</span><small id="speedLabel">Speed 1x</small></button>
<button onclick="toggleBeauty()"><span>✧</span><small>Beauty</small></button>
<button onclick="showCameraFilters()"><span>◉</span><small>Filters</small></button>
<button onclick="cameraEffects()"><span>✦</span><small>Effects</small></button>
<button onclick="changeZoom()"><span>＋</span><small id="zoomLabel">Zoom 1x</small></button>
</div>
<div class="cam-bottom">
<div class="filters" id="cameraFilters">
<button class="filter selected" onclick="setFilter('none',this)">Normal</button>
<button class="filter" onclick="setFilter('contrast(1.3) saturate(1.5)',this)">Vivid</button>
<button class="filter" onclick="setFilter('grayscale(1)',this)">B&W</button>
<button class="filter" onclick="setFilter('sepia(.65)',this)">Warm</button>
<button class="filter" onclick="setFilter('brightness(1.2) saturate(.8)',this)">Soft</button>
</div>
<div class="cam-modes">
<button class="cam-mode" onclick="setCameraMode('photo',this)">PHOTO</button>
<button class="cam-mode selected" onclick="setCameraMode('15',this)">15s</button>
<button class="cam-mode" onclick="setCameraMode('60',this)">60s</button>
<button class="cam-mode" onclick="setCameraMode('180',this)">3m</button>
</div>
<div class="camera-buttons">
<button class="cam-icon" onclick="document.getElementById('gallery').click()">▧<small>Upload</small></button>
<button class="record" id="recordBtn" onclick="captureAction()"></button>
<button class="cam-icon" onclick="showCameraFilters()">◉<small>Filters</small></button>
</div>
<div id="camHint">Tap to record</div>
<input id="gallery" type="file" accept="image/*,video/*" onchange="uploadGallery(this)">
</div>
</div>
<div id="postEditor" class="post-editor">
<div class="editor-head">
<button onclick="backToCamera()">‹ Back</button>
<b>New post</b>
</div>
<div id="postPreview" class="post-preview"></div>
<textarea id="postCaption" placeholder="Write a caption... Add hashtags #YOUSI" maxlength="2200"></textarea>
<div class="editor-options">
<div> # <span>Hashtags</span><small>Add hashtags in your caption</small></div>
<div>▣ <span>Cover</span><small>Preview your post</small></div>
<div>◉ <span>Who can watch</span>
<select id="postPrivacy"><option value="Everyone">Everyone</option><option value="Friends">Friends</option><option value="Only me">Only me</option></select></div>
<div>♡ <span>Allow comments</span><input id="allowComments" type="checkbox" checked></div>
</div>
<button class="publish-post" onclick="publishPost()">Post</button>
</div>

<script>
let selectedVideo=null,holdTimer=null,holdTriggered=false,stream=null,recorder=null,chunks=[],recordedBlob=null;
let facing="environment",filterValue="none",soundFrom=new URLSearchParams(location.search).get("sound");

function closeMenu(){document.getElementById('menuBackdrop').style.display='none';selectedVideo=null;}
function openMenu(card){
 selectedVideo=card.dataset.video;
 document.getElementById('menuBackdrop').style.display='block';
}

document.querySelectorAll('.video-card').forEach(card=>{
 const video=card.querySelector('video');
 let sx=0,sy=0,touchHold=false;
 card.addEventListener('contextmenu',e=>e.preventDefault());

 card.addEventListener('touchstart',e=>{
  if(e.target.closest('.side'))return;
  const t=e.touches[0]; sx=t.clientX; sy=t.clientY;
  touchHold=false;
  clearTimeout(holdTimer);
  holdTimer=setTimeout(()=>{
   touchHold=true;
   holdTriggered=true;
   openMenu(card);
   if(navigator.vibrate)navigator.vibrate(30);
  },600);
 },{passive:true});

 card.addEventListener('touchmove',e=>{
  const t=e.touches[0];
  if(Math.abs(t.clientX-sx)>15 || Math.abs(t.clientY-sy)>15)
   clearTimeout(holdTimer);
 },{passive:true});

 ['touchend','touchcancel'].forEach(ev=>{
  card.addEventListener(ev,()=>clearTimeout(holdTimer),{passive:true});
 });

 card.addEventListener('pointerdown',e=>{
  if(e.pointerType==='touch'||e.target.closest('.side'))return;
  clearTimeout(holdTimer);
  holdTriggered=false;
  holdTimer=setTimeout(()=>{holdTriggered=true;openMenu(card);},600);
 });
 ['pointerup','pointercancel','pointerleave'].forEach(ev=>{
  card.addEventListener(ev,()=>clearTimeout(holdTimer));
 });

 video.addEventListener('click',e=>{
  if(holdTriggered){
   e.preventDefault(); e.stopPropagation();
   holdTriggered=false; return;
  }
  if(video.paused){
   video.play().catch(()=>{});
   const mark=card.querySelector('.play-mark');
   if(mark)mark.style.display='none';
  }else{
   video.pause();
   const mark=card.querySelector('.play-mark');
   if(mark)mark.style.display='block';
  }
 });
});

document.addEventListener('keydown',e=>{if(e.key==="Escape")closeMenu();});

async function toggleLike(file,button){
 const r=await fetch('/like/'+encodeURIComponent(file),{method:'POST'});
 const d=await r.json();button.classList.toggle('liked',d.liked);
 button.querySelector('small').textContent=d.liked?'1':'0';
}
async function menuAction(action){
 const file=selectedVideo;if(!file)return;
 const link=location.origin+'/watch/'+encodeURIComponent(file);
 if(action==='delete'){
  if(!confirm('Delete this video?'))return;
  const r=await fetch('/delete/'+encodeURIComponent(file),{method:'POST'});
  if(r.ok)location.reload();
 }else if(action==='copy'){await copyText(link);closeMenu();}
 else if(action==='download'){location.href='/download/'+encodeURIComponent(file);closeMenu();}
 else if(action==='favorite'){
  const r=await fetch('/favorite/'+encodeURIComponent(file),{method:'POST'});
  const d=await r.json();alert(d.saved?'Added to Favorites':'Removed from Favorites');closeMenu();
 }else if(action==='share'){openShare(file);closeMenu();}
 else if(action==='whatsapp'){location.href='https://wa.me/?text='+encodeURIComponent(link);}
 else if(action==='facebook'){window.open('https://www.facebook.com/sharer/sharer.php?u='+encodeURIComponent(link),'_blank');}
 else if(action==='messenger'){window.open('https://www.facebook.com/dialog/send?link='+encodeURIComponent(link),'_blank');}
 else if(action==='speed'){document.getElementById('speedOptions').style.display='flex';}
 else if(action==='notinterested'){document.querySelector('[data-video="'+CSS.escape(file)+'"]').style.display='none';closeMenu();}
 else if(action==='report'){const reason=prompt('Why are you reporting this video?');if(reason)await fetch('/report/'+encodeURIComponent(file),{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({reason})});alert('Report submitted locally.');closeMenu();}
 else if(action==='sound'){location.href='/sound/'+encodeURIComponent(file);}
}
function setSpeed(n){document.querySelectorAll('.video-card video').forEach(v=>v.playbackRate=n);document.getElementById('speedOptions').style.display='none';closeMenu();}
async function copyText(t){try{await navigator.clipboard.writeText(t);alert('Link copied');}catch(e){prompt('Copy this link',t);}}
function openShare(file){const u=location.origin+'/watch/'+encodeURIComponent(file);if(navigator.share)navigator.share({title:'YOUSI video',url:u}).catch(()=>{});else copyText(u);}
function shareProfile(){if(navigator.share)navigator.share({title:'YOUSI Profile',url:location.href}).catch(()=>{});else copyText(location.href);}
async function saveSetting(key,value){await fetch('/setting',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({key,value})});}
async function openCamera(e){
 if(e)e.preventDefault();
 document.querySelectorAll('.feed-video').forEach(v=>v.pause());
 document.getElementById('camera').style.display='block';
 try{
  try {
    stream=await navigator.mediaDevices.getUserMedia({video:{facingMode:facing},audio:true});
  } catch(audioError) {
    stream=await navigator.mediaDevices.getUserMedia({video:{facingMode:facing},audio:false});
  }
  const v=document.getElementById('cameraView');
  v.srcObject=stream;
  v.style.filter=filterValue;
  await v.play();
}
 catch(err){alert('Camera error: '+err.name+' — '+err.message);}
}
function closeCamera(){if(stream)stream.getTracks().forEach(t=>t.stop());stream=null;document.getElementById('camera').style.display='none';}
async function switchCamera(){facing=facing==='environment'?'user':'environment';if(stream)stream.getTracks().forEach(t=>t.stop());stream=null;openCamera();}
function setFilter(f,b){filterValue=f;document.getElementById('cameraView').style.filter=f;document.querySelectorAll('.filter').forEach(x=>x.classList.remove('selected'));b.classList.add('selected');}

let cameraMode="15",timerDelay=0,flashOn=false,zoomLevel=1,speedLevel=1,beautyOn=false,recordLimit=null;

function setCameraMode(mode,btn){
 cameraMode=mode;
 document.querySelectorAll('.cam-mode').forEach(x=>x.classList.remove('selected'));
 btn.classList.add('selected');
 document.getElementById('camHint').textContent=mode==='photo'?'Tap to take photo':'Tap to record';
}
function captureAction(){
 if(cameraMode==='photo'){capturePhoto();return;}
 if(recorder&&recorder.state==='recording'){recorder.stop();clearTimeout(recordLimit);return;}
 if(timerDelay){let d=timerDelay;timerDelay=0;document.getElementById('camHint').textContent='Timer '+d/1000+'s';setTimeout(recordVideo,d);return;}
 recordVideo();
}

let recordedKind="video",previewURL=null;

function capturePhoto(){
 const v=document.getElementById('cameraView');
 if(!stream||!v.videoWidth){alert('Camera is not ready');return;}
 const c=document.createElement('canvas');
 c.width=v.videoWidth;c.height=v.videoHeight;
 const x=c.getContext('2d');
 x.filter=filterValue;
 if(facing==='user'){x.translate(c.width,0);x.scale(-1,1);}
 x.drawImage(v,0,0,c.width,c.height);
 c.toBlob(blob=>{
  if(!blob)return;
  recordedBlob=blob;
  recordedKind="photo";
  showPostEditor();
 },'image/jpeg',.92);
}

function showPostEditor(){
 if(!recordedBlob)return;
 if(previewURL)URL.revokeObjectURL(previewURL);
 previewURL=URL.createObjectURL(recordedBlob);
 const box=document.getElementById('postPreview');
 box.innerHTML='';
 let el=document.createElement(recordedKind==='photo'?'img':'video');
 el.src=previewURL;
 if(recordedKind==='video'){el.controls=true;el.playsInline=true;}
 box.appendChild(el);
 document.getElementById('postEditor').style.display='flex';
}

function backToCamera(){
 document.getElementById('postEditor').style.display='none';
}

async function publishPost(){
 if(!recordedBlob)return;
 const f=new FormData();
 f.append('video',recordedBlob,recordedKind==='photo'?'photo.jpg':'recording.webm');
 f.append('caption',document.getElementById('postCaption').value);
 f.append('privacy',document.getElementById('postPrivacy').value);
 f.append('allow_comments',document.getElementById('allowComments').checked?'yes':'no');
 const btn=document.querySelector('.publish-post');
 btn.disabled=true;btn.textContent='Posting...';
 try{
  const r=await fetch('/upload',{method:'POST',body:f});
  if(r.ok){location.href='/';}
  else{alert(await r.text());btn.disabled=false;btn.textContent='Post';}
 }catch(e){alert('Upload failed. Check your connection.');btn.disabled=false;btn.textContent='Post';}
}

async function uploadGallery(input){
 if(!input.files.length)return;
 recordedBlob=input.files[0];
 recordedKind=recordedBlob.type.startsWith('image/')?'photo':'video';
 showPostEditor();
 input.value='';
}
function toggleTimer(){timerDelay=timerDelay===0?3000:timerDelay===3000?10000:0;document.getElementById('camHint').textContent=timerDelay?'Timer '+timerDelay/1000+'s':'Timer off';}
async function toggleFlash(){
 if(!stream)return;
 try{flashOn=!flashOn;await stream.getVideoTracks()[0].applyConstraints({advanced:[{torch:flashOn}]});}
 catch(e){flashOn=false;alert('Flash is not supported on this device/browser.');}
}
function changeZoom(){
 zoomLevel=zoomLevel>=2?1:zoomLevel+.5;
 const v=document.getElementById('cameraView');
 v.style.transform='scale('+zoomLevel+')';
 document.getElementById('zoomLabel').textContent='Zoom '+zoomLevel+'x';
}
function changeSpeed(){speedLevel=speedLevel===1?2:speedLevel===2?.5:1;document.getElementById('speedLabel').textContent='Speed '+speedLevel+'x';if(recorder&&recorder.state==='recording'){alert('Speed applies to next recording.');}}
function toggleBeauty(){beautyOn=!beautyOn;document.getElementById('cameraView').style.filter=beautyOn?'brightness(1.08) contrast(.92) saturate(1.12)':filterValue;}
function showCameraFilters(){let f=document.getElementById('cameraFilters');f.style.display=f.style.display==='none'?'flex':'none';}
function cameraMusic(){
 const choices=['Original Sound','No Sound','Use Original Audio'];
 const pick=prompt('Sound options:\n1. Original Sound\n2. No Sound\n3. Use Original Audio','1');
 if(pick==='2'){soundFrom='';document.getElementById('camHint').textContent='No sound selected';}
 else if(pick==='3'){document.getElementById('camHint').textContent='Original camera audio selected';}
 else if(pick==='1'){document.getElementById('camHint').textContent='Original Sound selected';}
}
function cameraEffects(){
 const choices=[['Normal','none'],['Glow','brightness(1.18) saturate(1.25)'],['Dream','blur(.4px) brightness(1.12)'],['Vintage','sepia(.45) contrast(1.12)'],['Cool','hue-rotate(18deg) saturate(1.15)'],['Mono','grayscale(1)']];
 const menu=choices.map((x,i)=>(i+1)+'. '+x[0]).join('\n');
 const n=prompt('Choose an effect:\n'+menu,'1');
 const item=choices[Number(n)-1];
 if(item){filterValue=item[1];const v=document.getElementById('cameraView');if(v)v.style.filter=filterValue;document.getElementById('camHint').textContent=item[0]+' effect';}
}

function recordVideo(){
 if(!stream){alert('Allow camera permission first.');return;}
 if(recorder&&recorder.state==='recording'){recorder.stop();return;}
 const v=document.getElementById('cameraView');
 if(!v.videoWidth){alert('Camera is not ready');return;}
 const canvas=document.createElement('canvas');
 canvas.width=v.videoWidth;canvas.height=v.videoHeight;
 const ctx=canvas.getContext('2d');
 let frameId;
 function drawFrame(){
  ctx.save();ctx.clearRect(0,0,canvas.width,canvas.height);
  ctx.filter=beautyOn?'brightness(1.08) contrast(.92) saturate(1.12) '+filterValue:filterValue;
  ctx.translate(canvas.width/2,canvas.height/2);
  ctx.scale((facing==='user'?-1:1)*zoomLevel,zoomLevel);
  ctx.drawImage(v,-canvas.width/2,-canvas.height/2,canvas.width,canvas.height);
  ctx.restore();frameId=requestAnimationFrame(drawFrame);
 }
 drawFrame();
 const output=canvas.captureStream(30);
 stream.getAudioTracks().forEach(t=>output.addTrack(t));
 chunks=[];let opt={};
 if(MediaRecorder.isTypeSupported('video/webm;codecs=vp8,opus'))opt.mimeType='video/webm;codecs=vp8,opus';
 try{recorder=new MediaRecorder(output,opt);}catch(e){cancelAnimationFrame(frameId);output.getVideoTracks().forEach(t=>t.stop());alert('Video recording is not supported here.');return;}
 recorder.ondataavailable=e=>{if(e.data.size)chunks.push(e.data)};
 recorder.onstop=()=>{
  clearTimeout(recordLimit);cancelAnimationFrame(frameId);
  output.getVideoTracks().forEach(t=>t.stop());
  recordedBlob=new Blob(chunks,{type:recorder.mimeType||'video/webm'});
  recordedKind='video';
  document.getElementById('recordBtn').classList.remove('recording');
  document.getElementById('camHint').textContent='Preview your video';
  showPostEditor();
 };
 recorder.start();
 document.getElementById('recordBtn').classList.add('recording');
 document.getElementById('camHint').textContent='Recording... tap to stop';
 recordLimit=setTimeout(()=>{if(recorder&&recorder.state==='recording')recorder.stop();},parseInt(cameraMode)*1000);
}
async function uploadRecording(){if(!recordedBlob)return;let f=new FormData();f.append('video',recordedBlob,'recording.webm');await sendUpload(f);}

async function sendUpload(f){if(soundFrom)f.append('sound_from',soundFrom);let r=await fetch('/upload',{method:'POST',body:f});if(r.ok)location.href='/';else alert(await r.text());}
window.addEventListener('pagehide',()=>document.querySelectorAll('video').forEach(v=>v.pause()));
document.addEventListener('visibilitychange',()=>{if(document.hidden)document.querySelectorAll('video').forEach(v=>v.pause());});
const seenViews=new Set();
const observer=new IntersectionObserver(entries=>entries.forEach(e=>{const v=e.target;if(e.isIntersecting){document.querySelectorAll('.feed-video').forEach(o=>{if(o!==v)o.pause();});v.play().catch(()=>{});const card=v.closest('.video-card');const file=card?.dataset.video;if(file&&!seenViews.has(file)){seenViews.add(file);fetch('/view/'+encodeURIComponent(file),{method:'POST'}).catch(()=>{});}}else v.pause();}),{threshold:.65});
document.querySelectorAll('.feed-video').forEach(v=>observer.observe(v));
if(new URLSearchParams(location.search).get('camera')==='1')setTimeout(()=>openCamera(),1900);
</script>
<script>
function getCart(){
 try{return JSON.parse(localStorage.getItem("yousi_cart") || "[]")}
 catch(e){return []}
}
function saveCart(cart){
 localStorage.setItem("yousi_cart",JSON.stringify(cart));
 updateCartCount();
}
function updateCartCount(){
 const cart=getCart();
 const el=document.getElementById("cartCount");
 if(el)el.textContent=cart.reduce((sum,item)=>sum+item.qty,0);
}
function addToCart(name,price){
 const cart=getCart();
 const item=cart.find(x=>x.name===name);
 if(item)item.qty++;
 else cart.push({name:name,price:Number(price),qty:1});
 saveCart(cart);
 alert(name+" added to cart");
}
function showCart(){
 const box=document.getElementById("cartBox");
 if(!box)return;
 box.style.display="block";
 const items=document.getElementById("cartItems");
 const totalEl=document.getElementById("cartTotal");
 const cart=getCart();
 items.innerHTML="";
 let total=0;
 if(!cart.length)items.textContent="Your cart is empty.";
 cart.forEach(item=>{
  total+=item.price*item.qty;
  const row=document.createElement("div");
  row.className="cart-line";
  const name=document.createElement("span");
  name.textContent=item.name+" × "+item.qty;
  const price=document.createElement("b");
  price.textContent="Rs "+(item.price*item.qty);
  row.append(name,price);
  items.appendChild(row);
 });
 totalEl.textContent="Total: Rs "+total;
 box.scrollIntoView({behavior:"smooth"});
}
function clearCart(){
 saveCart([]);
 showCart();
}
function filterProducts(){
 const q=document.getElementById("shopSearch").value.toLowerCase();
 document.querySelectorAll(".product-card").forEach(card=>{
  card.style.display=card.dataset.name.includes(q)?"":"none";
 });
}
document.addEventListener("DOMContentLoaded",updateCartCount);
</script>
</body>
</html>
"""

def render(page="feed", tab="For You", heading="", message="", sound_file="",
           query="", results=None, profile_match=False, products=None):
    videos = video_list()
    meta = data.get("videos", {})
    for _v in videos:
        data.setdefault("views", {}).setdefault(_v, 0)
    sound_videos = []
    sound_name = "Original Sound"
    if sound_file:
        sound_name = meta.get(sound_file, {}).get("sound_name", "Original Sound")
        sound_videos = [v for v in videos if meta.get(v, {}).get("sound_name", "Original Sound") == sound_name]
    p = profile()
    return render_template_string(PAGE, page=page, tab=tab, videos=videos,
        liked=data["likes"], heading=heading, message=message,
        display_name=p["name"], username=p["username"], bio=p["bio"],
        avatar=p.get("avatar",""), metadata=meta, settings=data["settings"],
        sound_file=sound_file, sound_name=sound_name, sound_videos=sound_videos,
        query=query, results=results or [], profile_match=profile_match,
        products=products or [], wallet=data.get('wallet', {}),
        comments_data=data.get("comments", {}), views_data=data.get("views", {}))

@app.route("/wallet")
def wallet_page():
    data.setdefault("wallet", {"balance": 0.0, "total_earned": 0.0, "coins": 0})
    return render(page="wallet", tab="Profile")

@app.route("/")
def home():
    return render()

@app.route("/following")
def following():
    return render(tab="Following")

@app.route("/profile")
def profile_page():
    return render(page="profile")

@app.route("/edit-profile", methods=["GET","POST"])
def edit_profile():
    if request.method == "POST":
        p = profile()
        p["name"] = request.form.get("name","YOUSI User").strip()[:40]
        p["username"] = request.form.get("username","yousi_user").strip().replace(" ","_")[:25]
        p["bio"] = request.form.get("bio","")[:150]
        f = request.files.get("avatar")
        if f and f.filename:
            ext = os.path.splitext(secure_filename(f.filename))[1].lower()
            if ext in (".jpg",".jpeg",".png",".webp"):
                name = uuid.uuid4().hex + ext
                f.save(os.path.join(UPLOAD_DIR,name))
                p["avatar"] = "uploads/" + name
        save_data()
        return redirect(url_for("profile_page"))
    return render(page="edit")

@app.route("/settings")
def settings_page():
    return render(page="settings")

@app.route("/setting", methods=["POST"])
def setting():
    d = request.get_json(silent=True) or {}
    key = d.get("key")
    if key in ("private","notifications"):
        data["settings"][key] = bool(d.get("value"))
        save_data()
    return jsonify(ok=True)

@app.route("/upload", methods=["POST"])
def upload():
    f = request.files.get("video")
    if not f or not f.filename:
        return "No file selected", 400

    ext = os.path.splitext(secure_filename(f.filename))[1].lower()
    if ext not in MEDIA_ALLOWED:
        return "Unsupported image or video format", 400

    name = uuid.uuid4().hex + ext
    f.save(os.path.join(VIDEO_DIR, name))

    media_type = "photo" if ext in IMAGE_ALLOWED else "video"
    data["videos"][name] = {
        "caption": request.form.get("caption", "Welcome to YOUSI ✨"),
        "sound_name": "Original Sound",
        "sound_creator": profile()["username"],
        "media_type": media_type,
        "privacy": request.form.get("privacy", "Everyone"),
        "allow_comments": request.form.get("allow_comments", "yes") == "yes",
        "created": __import__("time").time()
    }
    data.setdefault("views", {}).setdefault(name, 0)
    data.setdefault("comments", {}).setdefault(name, [])
    save_data()
    return "OK", 200


@app.route("/view/<filename>", methods=["POST"])
def view(filename):
    if filename not in video_list(): return jsonify(error="Not found"), 404
    data.setdefault("views", {})[filename] = int(data.get("views", {}).get(filename, 0)) + 1
    save_data()
    return jsonify(views=data["views"][filename])

@app.route("/like/<filename>", methods=["POST"])
def like(filename):
    if filename not in video_list(): return jsonify(error="Not found"),404
    if filename in data["likes"]:
        data["likes"].remove(filename); liked=False
    else:
        data["likes"].append(filename); liked=True
    save_data()
    return jsonify(liked=liked)

@app.route("/favorite/<filename>", methods=["POST"])
def favorite(filename):
    if filename in data["favorites"]:
        data["favorites"].remove(filename); saved=False
    else:
        data["favorites"].append(filename); saved=True
    save_data()
    return jsonify(saved=saved)

@app.route("/delete/<filename>", methods=["POST"])
def delete(filename):
    if filename not in video_list(): return "Not found",404
    path=os.path.join(VIDEO_DIR,filename)
    if os.path.isfile(path): os.remove(path)
    data["likes"]=[x for x in data["likes"] if x!=filename]
    data["favorites"]=[x for x in data["favorites"] if x!=filename]
    data["videos"].pop(filename,None)
    save_data()
    return "OK"

@app.route("/download/<filename>")
def download(filename):
    return send_from_directory(VIDEO_DIR,filename,as_attachment=True)

@app.route("/watch/<filename>")
def watch(filename):
    if filename not in video_list(): return "Video not found",404
    return redirect(url_for("home",video=filename))

@app.route("/sound/<filename>")
def sound(filename):
    if filename not in video_list(): return "Sound not found",404
    return render(page="sound",sound_file=filename)

@app.route("/report/<filename>",methods=["POST"])
def report(filename):
    if filename not in video_list(): return "Not found",404
    return jsonify(ok=True)

@app.route("/comment/<filename>", methods=["GET", "POST"])
def comment(filename):
    if filename not in video_list(): return "Video not found", 404
    meta = data.get("videos", {}).get(filename, {})
    if request.method == "POST":
        if not meta.get("allow_comments", True): return "Comments are disabled for this post", 403
        body = request.form.get("comment", "").strip()[:500]
        if body:
            data.setdefault("comments", {}).setdefault(filename, []).append({
                "user": profile().get("username", "yousi_user"),
                "text": body,
                "time": __import__("time").time()
            })
            save_data()
        return redirect(url_for("comment", filename=filename))
    comments = data.setdefault("comments", {}).get(filename, [])
    return render(page="comments", heading="Comments", message="", results=comments,
                  sound_file=filename)

@app.route("/search")
def search():
    q = request.args.get("q", "").strip()
    q_lower = q.lower()
    results = []
    for v in video_list():
        caption = data.get("videos", {}).get(v, {}).get("caption", "")
        if q_lower and (q_lower in v.lower() or q_lower in caption.lower()):
            results.append(v)

    p = profile()
    profile_match = bool(q_lower and (
        q_lower in p.get("name", "").lower() or
        q_lower in p.get("username", "").lower()
    ))
    return render(page="search", tab="Search", query=q,
                  results=results, profile_match=profile_match)

@app.route("/shop")
def shop():
    products = [
        {"name":"Wireless Earbuds", "price":1800, "emoji":"🎧", "description":"Wireless audio"},
        {"name":"Smart Watch", "price":2500, "emoji":"⌚", "description":"Everyday smart watch"},
        {"name":"Mobile Cover", "price":500, "emoji":"📱", "description":"Stylish phone cover"},
        {"name":"Sports Shoes", "price":3200, "emoji":"👟", "description":"Comfortable shoes"},
        {"name":"Backpack", "price":1500, "emoji":"🎒", "description":"Daily use backpack"},
        {"name":"Sunglasses", "price":900, "emoji":"🕶️", "description":"Classic sunglasses"}
    ]
    return render(page="shop", tab="Shop", products=products)

@app.route("/live")
def live():
    return render(page="live", tab="LIVE")

@app.route("/inbox")
def inbox():
    return render(page="inbox", tab="Inbox")

if __name__ == "__main__":
    app.run(host="0.0.0.0",port=5001,debug=False)
