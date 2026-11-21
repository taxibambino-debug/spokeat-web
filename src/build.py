"""Build the static public site for spokeat.com (Cloudflare Pages). Output: public/"""
import json, re, os, shutil, subprocess, html, datetime
import markdown

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = f"{ROOT}/public"
SITE = "https://spokeat.com"
ART = f"{ROOT}/content/articles"
TODAY = datetime.date.today().isoformat()
esc = lambda s: html.escape(str(s), quote=True)
def lc(s): return " ".join(w if (len(w) > 1 and w[1].isupper()) or i else (w[:1].lower() + w[1:]) for i, w in enumerate(s.split(" ")))

slugs = json.load(open(f"{ART}/slugs.json"))
EX = json.load(open(f"{ROOT}/content/expertise.json"))
AREAS = [("leadership", "Leadership", "Ledarskap"), ("ai", "AI and digitalisation", "AI och digitalisering"), ("finance", "Finance, fintech and payments", "Ekonomi, fintech och betalningar"),
         ("marketing", "Marketing and communication", "Marknadsföring och kommunikation"), ("hr", "HR and the future of work", "HR och arbetsliv"), ("sustainability", "Sustainability and ESG", "Hållbarhet och ESG"),
         ("health", "Health, wellbeing and stress", "Hälsa, välmående och stress"), ("entrepreneurship", "Entrepreneurship and innovation", "Entreprenörskap och innovation"), ("security", "Security and risk", "Säkerhet och risk")]
AREA_NAME = {k: {"en": e, "sv": s} for k, e, s in AREAS}

# ---------- URL scheme ----------
def u_home(l): return "/" if l == "en" else "/sv/"
def u_article(l, s): return f"/{l}/{s}/"
def u_guides(l): return "/en/guides/" if l == "en" else "/sv/guider/"
def u_exp(l, k=""): return ("/en/expertise/" if l == "en" else "/sv/expertis/") + (f"{k}/" if k else "")
def u_contact(l, topic=""): return ("/contact/" if l == "en" else "/sv/kontakt/") + (f"#{topic}" if topic else "")
def u_early(l): return "/early-access/" if l == "en" else "/sv/tidig-tillgang/"
def u_faq(l): return "/en/faq/" if l == "en" else "/sv/vanliga-fragor/"
def u_why(l): return "/en/why-speak/" if l == "en" else "/sv/varfor-tala/"
def u_how(l): return "/en/how-it-works/" if l == "en" else "/sv/sa-fungerar-det/"
def u_opps(l): return "/en/speaking-opportunities/" if l == "en" else "/sv/talaruppdrag/"
def u_find(l): return "/en/find-a-speaker/" if l == "en" else "/sv/hitta-en-talare/"
U_AUTHOR = "/authors/ted-scheiman/"
U_POLICY = "/about/editorial-policy/"

def map_proto(frag, l):
    """Map a prototype artifact #fragment to a site URL."""
    m = re.match(r"a-(en|sv)-(.+)$", frag)
    if m: return u_article(m.group(1), m.group(2))
    m = re.match(r"(expertise|expertis)(?:-(.+))?$", frag)
    if m: return u_exp("en" if m.group(1) == "expertise" else "sv", m.group(2) or "")
    if re.match(r"(speakers|talare)", frag): return u_contact("en" if frag.startswith("speakers") else "sv", "organiser")
    m = re.match(r"(contact|kontakt)(?:-(.+))?$", frag)
    if m: return u_contact("en" if m.group(1) == "contact" else "sv", m.group(2) or "")
    if frag == "articles": return u_guides(l)
    return u_early(l)

# ---------- shared chrome ----------
CSS = """
:root{--ink:#1A1D29;--muted:#3D4254;--soft:#5B6072;--line:#E1E2E6;--bg:#F7F7F5;--brand:#1F3A8A;--accent:#F5B83D;--tint:#EEF1F8}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font-family:Inter,system-ui,-apple-system,"Segoe UI",sans-serif;line-height:1.6}
a{color:var(--brand)}h1,h2,h3{font-family:"Space Grotesk",Inter,system-ui,sans-serif;line-height:1.15;text-wrap:balance}
.wrap{max-width:1200px;margin:0 auto;padding:0 24px}.narrow{max-width:780px}
.top{background:#fff;border-bottom:1px solid var(--line)}.top .wrap{display:flex;flex-wrap:wrap;gap:16px;align-items:center;justify-content:space-between;padding:14px 24px}
.logo{display:flex;align-items:center;gap:10px;text-decoration:none;color:var(--ink);font-weight:700;font-size:17px}
.mark{width:26px;height:26px;border-radius:7px;background:var(--brand);display:flex;align-items:flex-end;justify-content:center;padding-bottom:6px}.mark span{width:14px;height:4px;border-radius:2px;background:var(--accent)}
nav.main{display:flex;flex-wrap:wrap;gap:18px;align-items:center;font-size:15px}nav.main a{color:var(--muted);text-decoration:none}nav.main a.btn{color:#fff}
.btn{display:inline-flex;align-items:center;min-height:44px;padding:12px 20px;border-radius:12px;font-weight:600;text-decoration:none;background:var(--brand);color:#fff}
.btn.ghost{background:#fff;color:var(--brand);border:1px solid #C9CEDB}
.langbar{background:var(--ink)}.langbar .wrap{display:flex;justify-content:flex-end;gap:10px;padding:8px 24px;font-size:13px;color:#9A9FB2}.langbar a{color:#C7CAD6;text-decoration:none}.langbar b{color:#fff}
main{padding:40px 0 64px}.crumbs{font-size:14px;color:var(--soft);margin-bottom:12px}.crumbs a{color:var(--soft)}
article.prose{background:#fff;border:1px solid var(--line);border-radius:16px;padding:40px clamp(20px,5vw,56px)}
.prose h1{font-size:clamp(30px,4vw,42px);margin:0 0 16px}.prose h2{font-size:26px;margin:36px 0 10px}.prose h3{font-size:20px;margin:26px 0 8px}
.prose blockquote{margin:0 0 24px;padding:12px 16px;background:var(--tint);border-radius:10px;font-size:15px;color:var(--muted)}.prose blockquote p{margin:0}
.tw{overflow-x:auto;margin:16px 0;max-width:100%}.prose table{border-collapse:collapse;width:100%;font-size:15px;margin:0}.prose{min-width:0;overflow-wrap:break-word}.prose th,.prose td{border:1px solid var(--line);padding:8px 10px;text-align:left;vertical-align:top}.prose th{background:var(--tint)}
.prose li{margin:4px 0}.prose img{max-width:100%}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:14px}
.card{background:#fff;border:1px solid var(--line);border-radius:14px;padding:20px}.card h3{margin:0 0 6px;font-size:18px}.card p{margin:0;color:var(--muted);font-size:15px}
a.card{text-decoration:none;color:inherit;display:block}a.card:hover{border-color:var(--brand)}
.chips{display:flex;flex-wrap:wrap;gap:8px}.chip{background:#fff;border:1px solid #D5D8E0;border-radius:999px;padding:8px 14px;font-size:14px;text-decoration:none;color:var(--ink)}
details.card summary{font-weight:600;cursor:pointer}details.card p{margin-top:8px}
.cta{background:var(--ink);color:#fff;border-radius:20px;padding:40px;display:flex;flex-wrap:wrap;gap:20px;align-items:center;justify-content:space-between;margin-top:40px}
.cta h2{margin:0;color:#fff;font-size:28px}.cta p{margin:6px 0 0;color:#C7CAD6}.cta .btn{background:var(--accent);color:var(--ink)}
footer.site{border-top:1px solid var(--line);background:#fff;font-size:14px;color:var(--soft)}footer.site .wrap{display:flex;flex-wrap:wrap;gap:20px;padding:24px}footer.site a{color:var(--soft)}
.muted{color:var(--soft)}.lead{font-size:19px;color:var(--muted)}
.sr{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)}
.navt{position:absolute;opacity:0;pointer-events:none}.burger{display:none;width:44px;height:44px;border:1px solid var(--line);border-radius:10px;flex-direction:column;justify-content:center;align-items:center;gap:5px;cursor:pointer}.burger i{display:block;width:20px;height:2px;background:var(--ink);border-radius:2px}
footer.site .wrap{flex-direction:column;gap:14px;padding:32px 24px}.fbrand{display:flex;flex-wrap:wrap;gap:16px;align-items:center}.flinks{display:flex;flex-wrap:wrap;gap:10px 22px;font-size:15px}.flinks a{text-decoration:none}.flinks a:hover{text-decoration:underline}.fnote{font-size:13px}
main.lp{padding:0}main.lp section{scroll-margin-top:16px}
@media(max-width:900px){
 .burger{display:flex}.top .wrap{flex-wrap:wrap}
 nav.main{display:none;width:100%;flex-direction:column;align-items:stretch;gap:0}
 .navt:checked~nav.main{display:flex}
 nav.main a{padding:14px 2px;border-top:1px solid var(--line);font-size:16px}nav.main a.btn{justify-content:center;margin-top:12px;border-top:0}
 .navt:focus-visible+.burger{outline:2px solid var(--brand);outline-offset:2px}
}
@media(max-width:640px){
 .lp [style*="padding: 80px 24px"],.lp [style*="padding: 88px 24px"],.lp [style*="padding: 72px 24px"],.lp [style*="padding: 64px 24px"]{padding-top:48px!important;padding-bottom:48px!important;padding-left:20px!important;padding-right:20px!important}
 .lp [style*="padding: 72px 24px 64px"]{padding:40px 20px 40px!important}
 .lp [style*="padding: 80px 24px 0"]{padding:48px 20px 0!important}
 .lp [style*="padding: 48px 40px"],.lp [style*="padding: 48px"]{padding:28px 20px!important}
 .lp [style*="padding: 0 24px 80px"]{padding:0 16px 48px!important}
 .lp h1{font-size:36px!important}.lp h2{font-size:28px!important}
 .lp [style*="font-size: 20px"]{font-size:18px!important}
 .prose h2{font-size:22px}.cta{padding:28px 20px}.cta h2{font-size:24px}
 article.prose{padding:24px 18px}
 main{padding:24px 0 40px}.wrap{padding-left:16px;padding-right:16px}.top .wrap{padding:12px 16px}
 .langbar .wrap{padding:8px 16px}
}
img,svg{max-width:100%}
.popg{list-style:none;padding:0;margin:24px 0 0;display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:12px}.popg a{display:block;height:100%;background:var(--bg);border:1px solid var(--line);border-radius:12px;padding:16px 18px;font-weight:600;color:var(--ink);text-decoration:none;line-height:1.4}.popg a:hover{border-color:var(--brand);color:var(--brand)}
.cc{position:fixed;left:16px;right:16px;bottom:16px;z-index:50;max-width:720px;margin:0 auto;background:#fff;border:1px solid var(--line);border-radius:14px;box-shadow:0 10px 30px rgba(20,24,40,.18);padding:18px 20px;display:flex;flex-wrap:wrap;gap:12px 20px;align-items:center}
.cc[hidden]{display:none}.cc p{margin:0;flex:1 1 320px;font-size:15px;color:var(--ink)}.ccb{display:flex;gap:10px}
.cc button{font:inherit;font-weight:600;font-size:15px;min-height:44px;padding:10px 18px;border-radius:10px;cursor:pointer;border:1px solid #1F3A8A;background:#fff;color:#1F3A8A}.cc button[data-accept]{background:#1F3A8A;color:#fff}
.opps{display:grid;gap:16px;margin:24px 0}.opp{background:#fff;border:1px solid var(--line);border-radius:14px;padding:20px 22px}
.opp h2,.opp h3{font-size:19px;margin:0 0 4px;line-height:1.3}.opp h2 a,.opp h3 a{color:var(--ink);text-decoration:none}.opp h2 a:hover,.opp h3 a:hover{text-decoration:underline}
.opp .meta{color:var(--muted);font-size:15px;margin:0 0 10px}.dl{display:inline-block;background:#FFF4D6;color:#7A4B00;border-radius:999px;padding:3px 12px;font-size:14px;font-weight:600;margin:0 0 10px}.dl.none{background:#EEF1F6;color:var(--muted)}
.opp dl{display:grid;grid-template-columns:150px 1fr;gap:6px 14px;margin:10px 0 12px;font-size:15px}.opp dt{color:var(--soft)}.opp dd{margin:0}
.opp ul{margin:0;padding-left:18px}.opp .go{font-weight:600;font-size:15px}
.chips{display:flex;flex-wrap:wrap;gap:6px;margin:0}.chips span{background:#EEF1F6;border-radius:8px;padding:3px 9px;font-size:13px}
.oppgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:16px;margin:24px 0}
.ophead{display:flex;flex-wrap:wrap;justify-content:space-between;align-items:flex-end;gap:12px}
@media(max-width:640px){.opp dl{grid-template-columns:1fr;gap:2px}.opp dt{margin-top:8px}}
"""
import hashlib
FONTS = '<link rel="preload" href="/assets/fonts/inter-latin-wght-normal.woff2" as="font" type="font/woff2" crossorigin><link rel="preload" href="/assets/fonts/space-grotesk-latin-wght-normal.woff2" as="font" type="font/woff2" crossorigin>'
FONT_CSS = "".join(
    f"@font-face{{font-family:'{fam}';font-style:normal;font-display:swap;font-weight:{w};src:url(/assets/fonts/{f}-{sub}-wght-normal.woff2) format('woff2');unicode-range:{ur}}}"
    for fam, f, w in (("Inter", "inter", "100 900"), ("Space Grotesk", "space-grotesk", "300 700"))
    for sub, ur in (("latin", "U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD"),
                    ("latin-ext", "U+0100-02BA,U+02BD-02C5,U+02C7-02CC,U+02CE-02D7,U+02DD-02FF,U+0304,U+0308,U+0329,U+1D00-1DBF,U+1E00-1E9F,U+1EF2-1EFF,U+2020,U+20A0-20AB,U+20AD-20C0,U+2113,U+2C60-2C7F,U+A720-A7FF")))
NAV = {"en": [("Speaking opportunities", u_opps("en")), ("How it works", u_how("en")), ("Why speak", u_why("en")), ("Why us", "/#why-us"), ("For executives", "/#executive")],
       "sv": [("Talaruppdrag", u_opps("sv")), ("Så fungerar det", u_how("sv")), ("Varför tala", u_why("sv")), ("Varför oss", "/sv/#why-us"), ("För företag", "/sv/#executive")]}
FOOT = {"en": [("Articles", u_guides("en")), ("By expertise", u_exp("en")), ("Find a speaker", u_find("en")), ("FAQ", u_faq("en")), ("Contact", u_contact("en")), ("How we research", U_POLICY)],
        "sv": [("Artiklar", u_guides("sv")), ("Per expertområde", u_exp("sv")), ("Hitta en talare", u_find("sv")), ("Vanliga frågor", u_faq("sv")), ("Kontakt", u_contact("sv")), ("Så researchar vi", U_POLICY)]}
EARLY = {"en": "Get early access", "sv": "Få tidig tillgång"}
GA_ID = "G-E9MGLSWHFS"
# Google Analytics loads only after the visitor clicks Accept (stored in localStorage); Decline removes any _ga cookies.
CONSENT_JS = """<script>(function(){var K='sa_consent',ID='%s';
function load(){if(window.__sa_ga)return;window.__sa_ga=1;window.dataLayer=window.dataLayer||[];window.gtag=function(){dataLayer.push(arguments)};gtag('js',new Date());gtag('config',ID);var s=document.createElement('script');s.async=true;s.src='https://www.googletagmanager.com/gtag/js?id='+ID;document.head.appendChild(s);}
function clear(){document.cookie.split(';').forEach(function(c){var n=c.split('=')[0].trim();if(n.indexOf('_ga')===0){['', '.spokeat.com', 'spokeat.com'].forEach(function(d){document.cookie=n+'=; Max-Age=0; path=/'+(d?'; domain='+d:'');});}});}
var c=null;try{c=localStorage.getItem(K)}catch(e){}
if(c==='yes')load();
document.addEventListener('DOMContentLoaded',function(){var b=document.getElementById('cc');if(!b)return;if(c!=='yes'&&c!=='no')b.hidden=false;
function set(v){try{localStorage.setItem(K,v)}catch(e){};c=v;b.hidden=true;if(v==='yes')load();else clear();}
b.querySelector('[data-accept]').addEventListener('click',function(){set('yes')});b.querySelector('[data-decline]').addEventListener('click',function(){set('no')});
document.querySelectorAll('[data-cookie-settings]').forEach(function(a){a.addEventListener('click',function(e){e.preventDefault();b.hidden=false;});});});})();</script>""" % GA_ID
CONSENT_TXT = {
 "en": ("We would like to use Google Analytics cookies to see how visitors use this site. Nothing is tracked unless you accept, and you can change your choice at any time under Cookie settings at the bottom of every page.", "Accept", "Decline", "Cookie settings"),
 "sv": ("Vi vill använda kakor från Google Analytics för att se hur besökare använder webbplatsen. Inget spåras om du inte godkänner, och du kan ändra ditt val när som helst under Kakinställningar längst ner på varje sida.", "Godkänn", "Avböj", "Kakinställningar")}

CSS_V = hashlib.md5((FONT_CSS + CSS).encode()).hexdigest()[:8]
OG_ALT = {"en": "Spoke At: speaking opportunities for professionals", "sv": "Spoke At: talaruppdrag för erfarna yrkespersoner"}

def head(l, title, desc, path, alt=None, extra=""):
    alts = ""
    if alt:
        en, sv = (path, alt) if l == "en" else (alt, path)
        alts = f'<link rel="alternate" hreflang="en" href="{SITE}{en}"><link rel="alternate" hreflang="sv" href="{SITE}{sv}"><link rel="alternate" hreflang="x-default" href="{SITE}{en}">'
    return f"""<!doctype html><html lang="{l}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
{CONSENT_JS}<title>{esc(title)}</title><meta name="description" content="{esc(desc)}"><link rel="canonical" href="{SITE}{path}">{alts}
<meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}"><meta property="og:url" content="{SITE}{path}"><meta property="og:type" content="website"><meta property="og:site_name" content="Spoke At"><meta property="og:locale" content="{"en_GB" if l == "en" else "sv_SE"}"><meta property="og:locale:alternate" content="{"sv_SE" if l == "en" else "en_GB"}">
<meta property="og:image" content="{SITE}/assets/og-{l}.png"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta property="og:image:alt" content="{esc(OG_ALT[l])}">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:image" content="{SITE}/assets/og-{l}.png">
{FONTS}<link rel="stylesheet" href="/assets/site.css?v={CSS_V}"><link rel="icon" href="/favicon.svg" type="image/svg+xml">{extra}</head>"""

def chrome_top(l, alt=None):
    other = "sv" if l == "en" else "en"
    lab = {"en": "English", "sv": "Svenska"}
    swap = f'<a href="{alt or u_home(other)}" lang="{other}">{lab[other]}</a>'
    langbar = f'<div class="langbar"><div class="wrap"><span>{"Language" if l == "en" else "Språk"}:</span><b>{lab[l]}</b><span>|</span>{swap}</div></div>'
    nav = "".join(f'<a href="{h}">{esc(t)}</a>' for t, h in NAV[l])
    burger = f'<input type="checkbox" id="navt" class="navt" aria-hidden="true"><label for="navt" class="burger"><span class="sr">{"Menu" if l == "en" else "Meny"}</span><i></i><i></i><i></i></label>'
    return f'<body>{langbar}<header class="top"><div class="wrap"><a class="logo" href="{u_home(l)}"><span class="mark" aria-hidden="true"><span></span></span>Spoke At</a>{burger}<nav class="main" aria-label="Main">{nav}<a class="btn" href="{u_early(l)}">{EARLY[l]}</a></nav></div></header>'

def chrome_foot(l):
    note = "Not affiliated with any organiser we list." if l == "en" else "Inte knutna till någon arrangör vi listar."
    links = "".join(f'<a href="{h}">{esc(x)}</a>' for x, h in FOOT[l])
    ct = CONSENT_TXT[l]
    banner = f'<div id="cc" class="cc" role="region" aria-label="{ct[3]}" hidden><p>{esc(ct[0])}</p><div class="ccb"><button type="button" data-decline>{ct[2]}</button><button type="button" data-accept>{ct[1]}</button></div></div>'
    return f'<footer class="site"><div class="wrap"><div class="fbrand"><a class="logo" href="{u_home(l)}"><span class="mark" aria-hidden="true"><span></span></span>Spoke At</a><span>hello@spokeat.com</span></div><nav class="flinks" aria-label="{"Footer" if l == "en" else "Sidfot"}">{links}</nav><span class="fnote">{note} · <a href="#" data-cookie-settings>{CONSENT_TXT[l][3]}</a></span></div></footer>{banner}</body></html>'

def cta_block(l):
    if l == "en": h, p = "Find out where you could speak this term", "Join the early-access list and be among the first to see your matches. Free, no card needed."
    else: h, p = "Ta reda på var du kan tala den här terminen", "Skriv upp dig för tidig tillgång och bli bland de första att se dina matchningar. Gratis, inget kort behövs."
    return f'<section class="cta"><div><h2>{esc(h)}</h2><p>{esc(p)}</p></div><a class="btn" href="{u_early(l)}">{EARLY[l]}</a></section>'

PAGES = []  # (path, alt_path or None, lang)
def write(path, content, lang=None, alt=None, sitemap=True):
    fp = DIST + path + ("index.html" if path.endswith("/") else "")
    os.makedirs(os.path.dirname(fp), exist_ok=True)
    if '<article class="prose">' in content:  # wide tables scroll inside their own box on phones
        content = re.sub(r"<table\b", '<div class="tw"><table', content).replace("</table>", "</table></div>")
    open(fp, "w", encoding="utf-8").write(content)
    if sitemap: PAGES.append((path, alt, lang))

def ld(obj): return '<script type="application/ld+json">' + json.dumps(obj, ensure_ascii=False) + "</script>"

# ---------- articles ----------
def fm_field(fm, k):
    m = re.search(r"^" + k + r":\s*(.*)$", fm, re.M)
    return m.group(1).strip().strip('"') if m else ""

ARTS = {}  # (lang, n) -> dict
def article_link(href, l):
    if re.match(r"^/(en|sv)?/?start/?$", href): return u_early(l)
    m = re.match(r"^/(en|sv)/([a-z0-9-]+)/?$", href)
    if m: return u_article(m.group(1), m.group(2))
    if href.startswith("/authors/"): return U_AUTHOR
    if href.startswith("/about/editorial-policy"): return U_POLICY
    return href

def build_articles():
    for n, v in slugs.items():
        for l in ("en", "sv"):
            t = open(f"{ART}/{l}/{v[l]}.md", encoding="utf-8").read()
            m = re.match(r"^---\n(.*?)\n---\n", t, re.S); fm, body = m.group(1), t[m.end():]
            ARTS[(l, int(n))] = dict(slug=v[l], title=fm_field(fm, "title"), meta_title=fm_field(fm, "meta_title"), desc=fm_field(fm, "meta_description"),
                                     cluster=fm_field(fm, "cluster"), reviewed=fm_field(fm, "last_reviewed"), fm=fm, body=body, alt=fm_field(fm, "alternate"))
    for (l, n), a in ARTS.items():
        body = a["body"]
        parts = body.split("<!-- schema -->")
        main_md = re.sub(r"<!--.*?-->\n?", "", parts[0], flags=re.S)
        h = markdown.markdown(main_md.strip(), extensions=["tables"])
        h = re.sub(r'href="([^"]+)"', lambda mo: f'href="{esc(article_link(mo.group(1), l))}"' + (' target="_blank" rel="noopener"' if mo.group(1).startswith("http") else ""), h)
        schema = ""
        if len(parts) > 1:
            sm = re.search(r"```json\s*(\{.*?\})\s*```", parts[1], re.S)
            if sm:
                s = sm.group(1).replace("[SITE]", SITE).replace("[PUBLISH DATE]", a["reviewed"])
                s = re.sub(r'"(url|@id|mainEntityOfPage)": "/', lambda mo: f'"{mo.group(1)}": "{SITE}/', s)
                try: schema = ld(json.loads(s))
                except Exception as e: print("schema error", l, a["slug"], e)
        path = u_article(l, a["slug"]); alt = (a["alt"].rstrip("/") + "/") if a["alt"] else None
        crumbs = f'<div class="crumbs"><a href="{u_home(l)}">Spoke At</a> › <a href="{u_guides(l)}">{"Guides" if l == "en" else "Guider"}</a></div>'
        page = head(l, (a["meta_title"] or a["title"]) + " · Spoke At", a["desc"], path, alt, schema) + chrome_top(l, alt) + \
            f'<main><div class="wrap narrow">{crumbs}<article class="prose">{h}</article>{cta_block(l)}</div></main>' + chrome_foot(l)
        write(path, page, l, alt)

def build_guides():
    for l in ("en", "sv"):
        groups = {}
        for (al, n), a in sorted(ARTS.items(), key=lambda x: x[0][1]):
            if al != l: continue
            groups.setdefault(a["cluster"] or ("Other" if l == "en" else "Övrigt"), []).append(a)
        sec = "".join(f'<section><h2>{esc(g)}</h2><div class="grid">' + "".join(f'<a class="card" href="{u_article(l, a["slug"])}"><h3>{esc(a["title"])}</h3><p>{esc(a["desc"])}</p></a>' for a in items) + "</div></section>" for g, items in groups.items())
        title = "Guides to speaking opportunities" if l == "en" else "Guider till talaruppdrag"
        lead = ("Practical, sourced guides on finding speaking opportunities, contacting organisers and giving talks that build your reputation." if l == "en"
                else "Praktiska guider med källor om att hitta talaruppdrag, kontakta arrangörer och hålla föreläsningar som bygger ditt rykte.")
        path, alt = u_guides(l), u_guides("sv" if l == "en" else "en")
        write(path, head(l, title + " · Spoke At", lead, path, alt) + chrome_top(l, alt) + f'<main><div class="wrap"><h1>{esc(title)}</h1><p class="lead narrow">{esc(lead)}</p>{sec}{cta_block(l)}</div></main>' + chrome_foot(l), l, alt)

# ---------- expertise ----------
EXT = {
  "en": dict(hubH="Speaking opportunities by expertise", hubLead="Most professionals look for speaking opportunities through their own field. Pick your area of expertise to see where people like you speak and the angles organisers book.",
    angles="Angles organisers book", venues=lambda a: "Where " + a + " experts speak", read="Read more", faq="Questions", other="Other areas of expertise", updated="Updated", broad="Broad areas", more="More in ",
    subVenues=lambda n: "Where speakers on " + n + " are booked"),
  "sv": dict(hubH="Talaruppdrag per expertområde", hubLead="De flesta yrkespersoner letar efter talaruppdrag utifrån sitt eget område. Välj ditt expertområde och se var personer som du föreläser och vilka vinklar arrangörer bokar.",
    angles="Vinklar som arrangörer bokar", venues=lambda a: "Här föreläser experter inom " + a, read="Läs mer", faq="Vanliga frågor", other="Andra expertområden", updated="Uppdaterad", broad="Breda ämnesområden", more="Mer inom ",
    subVenues=lambda n: "Här bokas talare inom " + n),
}
def faq_ld(faq): return ld({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]})
def crumbs_ld(items): return ld({"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": n, "item": SITE + p} for i, (n, p) in enumerate(items)]})

def build_expertise():
    for l in ("en", "sv"):
        T = EXT[l]; other = "sv" if l == "en" else "en"
        # hub
        groups = "".join(f'<section><h2>{esc(g[l])}</h2><div class="grid">' + "".join(
            f'<a class="card" href="{u_exp(l, k)}"><h3>{esc(EX["subs"][k][l]["name"])}</h3><p>{esc(EX["subs"][k][l]["desc"])}</p></a>' for k in g["subs"] if k in EX["subs"]) + "</div></section>" for g in EX["groups"])
        broad = f'<section><h2>{T["broad"]}</h2><div class="grid">' + "".join(f'<a class="card" href="{u_exp(l, k)}"><h3>{esc(AREA_NAME[k][l])}</h3><p>{esc(EX["areas"][k][l]["h1"])}</p></a>' for k, *_ in AREAS) + "</div></section>"
        path, alt = u_exp(l), u_exp(other)
        write(path, head(l, T["hubH"] + " · Spoke At", T["hubLead"], path, alt) + chrome_top(l, alt) + f'<main><div class="wrap"><h1>{esc(T["hubH"])}</h1><p class="lead narrow">{esc(T["hubLead"])}</p>{groups}{broad}{cta_block(l)}</div></main>' + chrome_foot(l), l, alt)

        def related(nums):
            items = [ARTS.get((l, n)) for n in nums]; items = [a for a in items if a]
            return (f'<section><h2>{T["read"]}</h2><ul>' + "".join(f'<li><a href="{u_article(l, a["slug"])}">{esc(a["title"])}</a></li>' for a in items) + "</ul></section>") if items else ""
        def page(key, h1, desc, intro, angles, venues_h, venues, faq, crumb_mid, arts, nav_h, nav_items):
            p, a = u_exp(l, key), u_exp(other, key)
            crumb_items = [("Spoke At", u_home(l)), (T["hubH"], u_exp(l))] + ([crumb_mid] if crumb_mid else []) + [(h1, p)]
            crumbs = '<div class="crumbs">' + " › ".join(f'<a href="{u}">{esc(n)}</a>' for n, u in crumb_items[:-1]) + "</div>"
            body = (f'<main><div class="wrap">{crumbs}<div class="narrow"><h1>{esc(h1)}</h1>' + (f'<p class="lead">{esc(desc)}</p>' if desc else "") +
                    "".join(f"<p>{esc(x)}</p>" for x in intro) + f'<p class="muted">{T["updated"]} {esc(EX.get("updated", TODAY))}</p></div>'
                    f'<div class="grid"><div class="card"><h2 style="margin-top:0;font-size:20px">{T["angles"]}</h2><ul>' + "".join(f"<li>{esc(x)}</li>" for x in angles) + "</ul></div>"
                    f'<div class="card"><h2 style="margin-top:0;font-size:20px">{esc(venues_h)}</h2><ul>' + "".join(f"<li>{esc(x)}</li>" for x in venues) + "</ul></div></div>"
                    + related(arts) + f'<section><h2>{T["faq"]}</h2>' + "".join(f'<details class="card"><summary>{esc(q)}</summary><p>{esc(an)}</p></details>' for q, an in faq) + "</section>"
                    f'<nav aria-label="{esc(nav_h)}"><h2 style="font-size:18px">{esc(nav_h)}</h2><div class="chips">' + "".join(f'<a class="chip" href="{u}">{esc(n)}</a>' for n, u in nav_items) + "</div></nav>"
                    + cta_block(l) + "</div></main>")
            write(p, head(l, h1 + " · Spoke At", desc or intro[0][:155], p, a, faq_ld(faq) + crumbs_ld(crumb_items)) + chrome_top(l, a) + body + chrome_foot(l), l, a)
        for k, *_ in AREAS:
            c = EX["areas"][k][l]; name = AREA_NAME[k][l]
            page(k, c["h1"], "", c["intro"], c["angles"], T["venues"](lc(name)), c["venues"], c["faq"], None, EX["areas"][k].get("articles", []),
                 T["other"], [(AREA_NAME[o][l], u_exp(l, o)) for o, *_ in AREAS if o != k])
        for g in EX["groups"]:
            for k in g["subs"]:
                sb = EX["subs"].get(k)
                if not sb: continue
                c, par = sb[l], EX["areas"][sb["parent"]]
                page(k, c["h1"], c["desc"], c["intro"], c["angles"], T["subVenues"](lc(c["name"])), par[l]["venues"], c["faq"] + par[l]["faq"][:1], (g[l], u_exp(l)),
                     par.get("articles", []), T["more"] + lc(g[l]), [(EX["subs"][o][l]["name"], u_exp(l, o)) for o in g["subs"] if o != k and o in EX["subs"]])

# ---------- landing ----------
LANDING_FIX = {
  "en": [(r'<a href="#start"[^>]*>Sign in</a>\s*', ""), ('>Find where to speak<', ">Get early access<"), ('>Upload your LinkedIn profile, free<', ">Get early access, free<"),
         ('>Upload your LinkedIn profile<', ">Get early access<"), ("Upload your LinkedIn profile and see your matches. Free, no card needed.", "Join the early-access list and be among the first to see your matches. Free, no card needed.")],
  "sv": [(r'<a href="#start"[^>]*>Logga in</a>\s*', ""), ('>Hitta var du kan tala<', ">Få tidig tillgång<"), ('>Ladda upp din LinkedIn-profil, gratis<', ">Få tidig tillgång, gratis<"),
         ('>Ladda upp din LinkedIn-profil<', ">Få tidig tillgång<"), ("Ladda upp din LinkedIn-profil och se dina matchningar. Gratis, inget kort behövs.", "Skriv upp dig för tidig tillgång och bli bland de första att se dina matchningar. Gratis, inget kort behövs.")],
}
def build_landing():
    for f, l in (("Main.dc.html", "en"), ("Main-sv.dc.html", "sv")):
        out = json.loads(subprocess.check_output(["node", f"{ROOT}/src/render_landing.js", f"{ROOT}/content/landing/{f}"]))
        b = out["body"]
        b = re.sub(r'https://claude\.ai/artifact/UBTL1x61VaTqeUTMGanaCZ#([a-z0-9-]+)', lambda m: map_proto(m.group(1), l), b)
        b = b.replace('href="Main-sv.dc.html"', 'href="/sv/"').replace('href="Main.dc.html"', 'href="/"')
        for a, r in LANDING_FIX[l]:
            b, n = re.subn(a, r, b) if a.startswith("<a") else (b.replace(a, r), b.count(a))
        # remaining in-page CTAs that pointed at the (non-existent) upload form
        b = re.sub(r'href="#(start|top)"(?=[^>]*>(Get early access|Få tidig tillgång))', f'href="{u_early(l)}"', b)
        b = b.replace('href="#start"', f'href="{u_early(l)}"')
        for x, y in (("[University name] · ", ""), ("[Universitetets namn] · ", ""), ("[Your university]", "Your university"), ("[Ditt universitet]", "Ditt universitet")): b = b.replace(x, y)
        b = b.replace(" [PRICING DETAILS]", " Prices are published before launch.").replace(" [PRISUPPGIFTER]", " Priserna publiceras före lansering.")
        title = "Spoke At: speaking opportunities for professionals" if l == "en" else "Spoke At: talaruppdrag för yrkespersoner"
        desc = ("Find guest lectures, panels, seminars and conference slots that match your expertise, and reach the right organiser in their language."
                if l == "en" else "Hitta gästföreläsningar, paneler, seminarier och konferensuppdrag som matchar din expertis, och nå rätt arrangör på deras språk.")
        path, alt = u_home(l), u_home("sv" if l == "en" else "en")
        org = ld({"@context": "https://schema.org", "@graph": [
            {"@type": "Organization", "@id": f"{SITE}/#organization", "name": "Spoke At", "url": f"{SITE}/", "email": "hello@spokeat.com",
             "logo": {"@type": "ImageObject", "url": f"{SITE}/assets/logo-512.png", "width": 512, "height": 512},
             "contactPoint": {"@type": "ContactPoint", "contactType": "customer support", "email": "hello@spokeat.com", "availableLanguage": ["English", "Swedish"]}},
            {"@type": "WebSite", "@id": f"{SITE}/#website", "name": "Spoke At", "url": f"{SITE}/", "inLanguage": ["en", "sv"], "publisher": {"@id": f"{SITE}/#organization"}},
            {"@type": "WebPage", "@id": f"{SITE}{path}#webpage", "url": f"{SITE}{path}", "name": title, "description": desc, "inLanguage": l,
             "isPartOf": {"@id": f"{SITE}/#website"}, "about": {"@id": f"{SITE}/#organization"}, "primaryImageOfPage": f"{SITE}/assets/og-{l}.png"}]})
        b, found = split_landing(b, l)
        lhead = re.sub(r'<link[^>]+fonts\.(googleapis|gstatic)\.com[^>]*>', "", out["head"])
        page = head(l, title, desc, path, alt, lhead + org) + chrome_top(l, alt) + f'<main class="lp">{b}</main>' + chrome_foot(l)
        write(path, page, l, alt)
        build_moved(l, found, alt_l="sv" if l == "en" else "en")

def cut_section(b, sid):
    """Remove <section id=sid>…</section> (nesting-aware); return (body, section_html)."""
    i = b.find(f'<section id="{sid}"')
    if i < 0: raise SystemExit(f"landing section {sid} missing")
    depth, pos = 0, i
    for m in re.finditer(r"<(/?)section\b", b[i:]):
        depth += -1 if m.group(1) else 1
        if depth == 0:
            end = i + m.end() + b[i + m.end():].find(">") + 1
            return b[:i] + b[end:], b[i:end]
    raise SystemExit("unbalanced section")

def cut_tag(b, tag):
    i = b.find(f"<{tag}"); j = b.find(f"</{tag}>", i)
    return b[:i] + b[j + len(tag) + 3:]

POPULAR = {"en": ["how-to-get-speaking-opportunities", "become-a-guest-lecturer-at-a-university", "call-for-speakers-guide", "speak-at-your-old-university", "guest-lecture-email-templates", "do-guest-lecturers-get-paid"],
           "sv": ["sa-far-du-uppdrag-som-forelasare", "bli-gastforelasare-pa-universitet", "call-for-speakers-guide", "forelasa-pa-ditt-gamla-universitet", "mejl-gastforelasning-kursansvarig", "far-gastforelasare-betalt"]}
POP_T = {"en": ("Popular guides", "Practical guides to finding and landing speaking opportunities.", "All guides"),
         "sv": ("Populära guider", "Praktiska guider för att hitta och få talaruppdrag.", "Alla guider")}

def art_title(l, slug):
    m = re.search(r'^title:\s*"?(.*?)"?\s*$', open(f"{ART}/{l}/{slug}.md", encoding="utf-8").read(), re.M)
    return m.group(1)

def popular_guides(l):
    h, sub, allt = POP_T[l]
    items = "".join(f'<li><a href="{u_article(l, s)}">{esc(art_title(l, s))}</a></li>' for s in POPULAR[l])
    return (f'<section id="guides" style="background:#fff;border-top:1px solid #E4E7EE"><div class="wrap" style="max-width:1200px;padding:56px 24px">'
            f'<div class="ophead"><div><h2 style="margin:0 0 6px;font-size:30px">{h}</h2><p class="muted" style="margin:0">{sub}</p></div>'
            f'<a class="go" style="font-weight:600" href="{u_guides(l)}">{allt} →</a></div><ul class="popg">{items}</ul></div></section>')

def insert_before_section(b, sid, html_):
    i = b.find(f'<section id="{sid}"')
    if i < 0: raise SystemExit(f"landing section {sid} missing")
    return b[:i] + html_ + b[i:]

def split_landing(b, l):
    # drop the design's own language bar, header and footer: the shared chrome replaces them
    i = max(b.find('<nav aria-label="Language"'), b.find('<nav aria-label="Språk"'))
    if i < 0: raise SystemExit("landing language bar not found")
    s = b.rfind("<div", 0, i); e = b.find("</div>", b.find("</nav>", i)) + 6
    b = b[:s] + b[e:]
    b = cut_tag(b, "header"); b = cut_tag(b, "footer")
    found = {}
    for sid in ("by-expertise", "find-speaker", "benefits", "how", "articles", "faq"):
        b, found[sid] = cut_section(b, sid)
    for a, h in (("#faq", u_faq(l)), ("#articles", u_guides(l)), ("#by-expertise", u_exp(l)), ("#find-speaker", u_find(l)), ("#benefits", u_why(l)), ("#how", u_how(l))):
        b = b.replace(f'href="{a}"', f'href="{h}"')
    b = insert_before_section(b, "start", popular_guides(l))
    b, hero = cut_section(b, "top")
    i = b.find("<section")
    b = b[:i] + hero + opps_teaser(l) + b[i:]
    return b, found

MOVED = {
 "en": {"how": ("How it works", "How Spoke At finds speaking opportunities that match your expertise and helps you reach the right organiser."),
        "why": ("Why speaking is worth your time", "What speaking at universities, associations and events gives professionals: visibility, content and self-improvement."),
        "find": ("Find a speaker for your event or course", "Universities, associations and event organisers: describe the session and we suggest experienced professionals who fit."),
        "faq": ("Frequently asked questions", "Answers about Spoke At: who it is for, what is free, pricing, eligibility, privacy and how organisers opt out.")},
 "sv": {"how": ("Så fungerar det", "Så hittar Spoke At talaruppdrag som matchar din expertis och hjälper dig att nå rätt arrangör."),
        "why": ("Därför är det värt din tid att tala", "Vad föreläsningar på universitet, i föreningar och på evenemang ger yrkespersoner: synlighet, innehåll och utveckling."),
        "find": ("Hitta en talare till ditt evenemang eller din kurs", "Universitet, föreningar och arrangörer: beskriv tillfället så föreslår vi erfarna yrkespersoner som passar."),
        "faq": ("Vanliga frågor", "Svar om Spoke At: vem det är för, vad som är gratis, priser, behörighet, integritet och hur arrangörer avregistrerar sig.")}}

def build_moved(l, found, alt_l):
    for key, sid, url in (("find", "find-speaker", u_find), ("faq", "faq", u_faq), ("why", "benefits", u_why), ("how", "how", u_how)):
        title, desc = MOVED[l][key]
        sec = found[sid]
        for a, h in (("#faq", u_faq(l)), ("#articles", u_guides(l)), ("#by-expertise", u_exp(l)), ("#find-speaker", u_find(l)), ("#benefits", u_why(l)), ("#how", u_how(l)), ("#start", u_early(l)), ("#top", u_home(l))):
            sec = sec.replace(f'href="{a}"', f'href="{h}"')
        extra = ""
        if key == "faq":
            qa = re.findall(r"<h3[^>]*>(.*?)</h3>\s*<p[^>]*>(.*?)</p>", sec, re.S)
            extra = ld({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
                {"@type": "Question", "name": re.sub("<[^>]+>", "", q).strip(), "acceptedAnswer": {"@type": "Answer", "text": re.sub("<[^>]+>", "", a).strip()}} for q, a in qa]})
            sec = re.sub(r"(<h2[^>]*>)[^<]*(</h2>)", lambda m: m.group(1) + esc(title) + m.group(2), sec, count=1).replace("<h2", "<h1", 1).replace("</h2>", "</h1>", 1)
        else:
            sec = sec.replace("<h2", "<h1", 1).replace("</h2>", "</h1>", 1)
        path, alt = url(l), url(alt_l)
        write(path, head(l, title + " · Spoke At", desc, path, alt, extra) + chrome_top(l, alt) + f'<main class="lp">{sec}<div class="wrap" style="padding-bottom:56px">{cta_block(l)}</div></main>' + chrome_foot(l), l, alt)

# ---------- speaking opportunities (weekly listings) ----------
import datetime, glob as _glob
MON = {"en": "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split(), "sv": "jan feb mar apr maj jun jul aug sep okt nov dec".split()}
def fdate(s, l):
    if not s: return ""
    d = datetime.date.fromisoformat(s); return f"{d.day} {MON[l][d.month - 1]} {d.year}"

def weekly():
    """Latest weekly file; drop calls whose deadline has passed at build time; nearest deadline first, rolling calls last."""
    f = sorted(_glob.glob(f"{ROOT}/content/weekly/*.json"))[-1]
    w = json.load(open(f, encoding="utf-8"))
    today = datetime.date.today().isoformat()
    items = [i for i in w["items"] if not i.get("deadline") or i["deadline"] >= today]
    items.sort(key=lambda i: (i.get("deadline") is None, i.get("deadline") or ""))
    return w, items

OPP_T = {
 "en": {"title": "Speaking opportunities", "h1": "Open calls for speakers",
        "desc": "Open calls for speakers we found and checked this week, ordered by deadline, with formats, topics, requirements and what speaking costs.",
        "deadline": "Deadline", "rolling": "No deadline stated", "when": "Event", "where": "Where", "mode": "Format", "lang": "Language",
        "formats": "Session types", "topics": "Topics", "req": "What they ask for", "cost": "Speaker costs", "apply": "Go to the call page", "checked": "Checked",
        "updated": "Updated", "teaser_h": "Nearest deadlines", "teaser_p": "Open calls for speakers, checked this week.", "all": "See all open calls",
        "note": ""},
 "sv": {"title": "Talaruppdrag", "h1": "Öppna utlysningar för talare",
        "desc": "Öppna utlysningar för talare som vi hittat och kontrollerat den här veckan, sorterade efter sista ansökningsdag, med format, ämnen, krav och vad det kostar att tala.",
        "deadline": "Sista dag", "rolling": "Ingen sista dag angiven", "when": "Evenemang", "where": "Plats", "mode": "Form", "lang": "Språk",
        "formats": "Typ av pass", "topics": "Ämnen", "req": "Vad de vill ha", "cost": "Kostnad för talare", "apply": "Till utlysningen", "checked": "Kontrollerad",
        "updated": "Uppdaterad", "teaser_h": "Närmast sista ansökningsdag", "teaser_p": "Öppna utlysningar för talare, kontrollerade den här veckan.", "all": "Se alla öppna utlysningar",
        "note": "Uppgifterna om varje utlysning är på engelska, så som arrangörerna publicerat dem."}}
OPP_INTRO_SV = "Öppna utlysningar för talare som vi hittat och kontrollerat den här veckan, sorterade efter sista ansökningsdag. Varje rad länkar till arrangörens egen utlysning."
OPP_METHOD_SV = "Så tar vi fram listan: vi söker på arrangörers webbplatser, Sessionize och det öppna konferensdataprojektet på GitHub efter utlysningar för talare som nyligen publicerats eller öppnats och som fortfarande är öppna. Varje utlysning öppnas och kontrolleras på arrangörens sida innan den tas med. Uppgifter kan ändras, så kontrollera alltid på utlysningens sida innan du ansöker. Vissa utlysningar tar betalt av talare; det framgår under Kostnad för talare."

def place(i):
    return ", ".join(x for x in (i.get("city"), i.get("country")) if x)

def dl_badge(i, l):
    T = OPP_T[l]
    return f'<p class="dl">{T["deadline"]}: {fdate(i["deadline"], l)}</p>' if i.get("deadline") else f'<p class="dl none">{T["rolling"]}</p>'

def opp_card(i, l, full=True, hl="h2"):
    T = OPP_T[l]
    ext = 'rel="nofollow noopener" target="_blank"'
    meta = " · ".join(x for x in (esc(i.get("organiser") or ""), esc(place(i)), esc(i.get("mode") or "")) if x)
    if not full:
        ed = i.get("event_dates") or ""
        dates = "" if not ed or ed.lower().startswith("not stated") else f'<p class="meta" style="margin:0">{esc(ed)}</p>'
        return f'<div class="opp">{dl_badge(i, l)}<h3><a href="{u_opps(l)}#{esc(i["id"])}">{esc(i["title"])}</a></h3><p class="meta">{meta}</p>{dates}</div>'
    rows = [(T["when"], esc(i.get("event_dates") or "–")), (T["where"], esc(place(i) or "–")), (T["mode"], esc(i.get("mode") or "–"))]
    if i.get("language") and i["language"] != "Not stated": rows.append((T["lang"], esc(i["language"])))
    if i.get("formats"): rows.append((T["formats"], "<ul>" + "".join(f"<li>{esc(x)}</li>" for x in i["formats"]) + "</ul>"))
    if i.get("topics"): rows.append((T["topics"], '<p class="chips">' + "".join(f"<span>{esc(x)}</span>" for x in i["topics"]) + "</p>"))
    if i.get("requirements"): rows.append((T["req"], "<ul>" + "".join(f"<li>{esc(x)}</li>" for x in i["requirements"]) + "</ul>"))
    if i.get("speaker_costs"): rows.append((T["cost"], esc(i["speaker_costs"])))
    dl = "".join(f"<dt>{k}</dt><dd>{v}</dd>" for k, v in rows)
    return (f'<article class="opp" id="{esc(i["id"])}">{dl_badge(i, l)}<{hl}><a href="{esc(i["url"])}" {ext}>{esc(i["title"])}</a></{hl}>'
            f'<p class="meta">{esc(i.get("organiser") or "")}</p><dl>{dl}</dl>'
            f'<a class="go" href="{esc(i["url"])}" {ext}>{T["apply"]} ↗</a> <span class="muted" style="font-size:13px;margin-left:8px">{T["checked"]} {fdate(i.get("checked"), l)}</span></article>')

def opps_teaser(l, n=3):
    w, items = weekly(); T = OPP_T[l]
    if not items: return ""
    cards = "".join(opp_card(i, l, full=False) for i in items[:n])
    return (f'<section id="opportunities" style="background:#fff;border-bottom:1px solid #E4E7EE"><div class="wrap" style="max-width:1200px;padding:56px 24px">'
            f'<div class="ophead"><div><h2 style="margin:0 0 6px;font-size:30px">{T["teaser_h"]}</h2><p class="muted" style="margin:0">{T["teaser_p"]}</p></div>'
            f'<a class="go" style="font-weight:600" href="{u_opps(l)}">{T["all"]} ({len(items)}) →</a></div><div class="oppgrid">{cards}</div></div></section>')

def build_opps():
    w, items = weekly()
    for l in ("en", "sv"):
        T = OPP_T[l]; alt_l = "sv" if l == "en" else "en"
        path, alt = u_opps(l), u_opps(alt_l)
        intro = w["intro"] if l == "en" else OPP_INTRO_SV
        method = w["method"] if l == "en" else OPP_METHOD_SV
        note = f'<p class="muted">{T["note"]}</p>' if T["note"] else ""
        cards = "".join(opp_card(i, l) for i in items)
        listld = ld({"@context": "https://schema.org", "@type": "ItemList", "name": T["h1"], "itemListElement": [
            {"@type": "ListItem", "position": n + 1, "name": i["title"], "url": i["url"]} for n, i in enumerate(items)]})
        body = (f'<main><div class="wrap"><article class="prose" style="max-width:880px;background:none;border:0;padding:0">'
                f'<h1>{T["h1"]}</h1><p class="lead">{esc(intro)}</p><p class="muted">{T["updated"]} {fdate(w["date"], l)}</p>{note}'
                f'<div class="opps">{cards}</div><p class="muted" style="font-size:15px">{esc(method)}</p>{cta_block(l)}</article></div></main>')
        write(path, head(l, T["title"] + " · Spoke At", T["desc"], path, alt, listld) + chrome_top(l, alt) + body + chrome_foot(l), l, alt)

# ---------- simple pages ----------
def md_page(l, path, alt, title, desc, md_text, extra_ld=""):
    h = markdown.markdown(md_text, extensions=["tables"])
    write(path, head(l, title + " · Spoke At", desc, path, alt, extra_ld) + chrome_top(l, alt) + f'<main><div class="wrap narrow"><article class="prose">{h}</article></div></main>' + chrome_foot(l), l, alt)

def build_author():
    t = open(f"{ART}/authors/ted-scheiman.md", encoding="utf-8").read()
    m = re.match(r"^---\n(.*?)\n---\n", t, re.S); fm, body = m.group(1), t[m.end():]
    parts = body.split("<!-- schema -->")
    main = "\n".join(x for x in parts[0].split("\n") if "listed in a 2026 interview" not in x)  # unconfirmed row
    main = re.sub(r"\[CONFIRM[^\]]*\]", "", main)
    main = re.sub(r"\[(ROLE|YEARS|TOPIC|NUMBER)\]", "–", main)
    main = re.sub(r"^\[PHOTO[^\]]*\]\s*$", "", main, flags=re.M)
    sch = ""
    sm = re.search(r"```json\s*(\{.*?\})\s*```", parts[1] if len(parts) > 1 else "", re.S)
    if sm: sch = ld(json.loads(sm.group(1).replace("[SITE]", SITE)))
    md_page("en", U_AUTHOR, None, fm_field(fm, "meta_title").replace(" | Author at Spoke At", ""), fm_field(fm, "meta_description"), main, sch)

POLICY = """# How we research and write

Spoke At publishes guides for professionals who want to speak at universities, associations, meetups, conferences and podcasts. This page explains how those guides are made.

## Who writes the guides
The guides are written by [Ted Scheiman](/authors/ted-scheiman/), who has more than 25 years of experience in banking, payments and investing and speaks at fintech conferences and universities.

## How we research
- Facts come from primary sources wherever possible: university and course pages, organisers' own call pages, laws and official statistics, and peer-reviewed research.
- Every guide lists its sources with the date they were checked, and links to them.
- We use AI tools to help with research and drafting. Every guide is checked against its sources and edited before it is published.

## Keeping guides current
Each guide shows when it was last reviewed. We review guides when sources change, and at least once a year.

## Independence
No organiser, university, course provider or event pays to be listed or recommended. Where a guide mentions Spoke At's own service, it says so openly.

## Corrections
If you find an error, email hello@spokeat.com and we will correct it.

---

## Så researchar och skriver vi (svenska)
Guiderna skrivs av Ted Scheiman. Fakta hämtas i första hand från primärkällor som kurssidor, arrangörers egna utlysningar, lagar och forskning, och varje guide listar sina källor med datum. Vi använder AI-verktyg som stöd i research och utkast; varje guide kontrolleras mot sina källor och redigeras innan den publiceras. Ingen arrangör betalar för att listas. Hittar du ett fel, mejla hello@spokeat.com.
"""

CONTACT = {
 "en": ("Contact us", "Questions about Spoke At, organiser requests, executive speaker search and opt-outs.", """# Contact us

Email **[hello@spokeat.com](mailto:hello@spokeat.com)**. We reply within two working days.

<h2 id="early-access">Early access</h2>
Spoke At is opening in stages. [Request early access](mailto:hello@spokeat.com?subject=Early%20access) and tell us your field and the kind of talks you want to give.

<h2 id="organiser">For organisers: find a speaker</h2>
Looking for a speaker, panellist or moderator for an unpaid slot (guest lecture, breakfast seminar, panel, podcast)? [Email us the topic, date, format and audience](mailto:hello@spokeat.com?subject=Speaker%20request) and we will propose matching speakers. Free for slots without a speaker fee.

<h2 id="executive">Executive speaker search</h2>
For senior executives and companies: our team runs the search and outreach for you, with an agreed number of speaking slots. [Book a call](mailto:hello@spokeat.com?subject=Executive%20speaker%20search).

<h2 id="opt-out">Organisers: opt out</h2>
If you do not want to receive speaker proposals through Spoke At, [email us from your work address](mailto:hello@spokeat.com?subject=Opt%20out) and we will stop all outreach to you.
"""),
 "sv": ("Kontakta oss", "Frågor om Spoke At, förfrågningar från arrangörer, executive speaker search och avregistrering.", """# Kontakta oss

Mejla **[hello@spokeat.com](mailto:hello@spokeat.com)**. Vi svarar inom två arbetsdagar.

<h2 id="tidig-tillgang">Tidig tillgång</h2>
Spoke At öppnar stegvis. [Be om tidig tillgång](mailto:hello@spokeat.com?subject=Tidig%20tillg%C3%A5ng) och berätta om ditt område och vilka uppdrag du vill ha.

<h2 id="organiser">För arrangörer: hitta en talare</h2>
Söker du en föreläsare, paneldeltagare eller moderator till ett arvodesfritt uppdrag (gästföreläsning, frukostseminarium, panel, podd)? [Mejla ämne, datum, format och publik](mailto:hello@spokeat.com?subject=F%C3%B6rfr%C3%A5gan%20om%20talare) så föreslår vi passande talare. Kostnadsfritt för uppdrag utan arvode.

<h2 id="executive">Executive speaker search</h2>
För ledande befattningshavare och företag: vårt team sköter sökning och kontakt åt dig, med ett överenskommet antal talaruppdrag. [Boka ett samtal](mailto:hello@spokeat.com?subject=Executive%20speaker%20search).

<h2 id="avregistrering">Arrangörer: avregistrering</h2>
Vill du inte få talarförslag via Spoke At? [Mejla oss från din jobbadress](mailto:hello@spokeat.com?subject=Avregistrering) så stoppar vi all kontakt.
"""),
}
EARLY_PAGE = {
 "en": ("Get early access", "Spoke At opens in stages. Request early access to find speaking opportunities that match your expertise.", """# Get early access

Spoke At finds university courses, business schools, societies, associations and events that host speakers like you, and helps you reach the right person in their language.

We are opening in stages. To get early access:

1. [Email hello@spokeat.com](mailto:hello@spokeat.com?subject=Early%20access) with the subject "Early access".
2. Tell us your field, your role and two or three topics you would like to speak about.
3. Add your LinkedIn profile link if you want us to see your background.

Early access is free. Searching and seeing your matches will stay free; you only pay when you choose to reach out to an organiser.

While you wait, read our [guides to speaking opportunities](/en/guides/) or browse [speaking opportunities by expertise](/en/expertise/).
"""),
 "sv": ("Få tidig tillgång", "Spoke At öppnar stegvis. Be om tidig tillgång för att hitta talaruppdrag som matchar din expertis.", """# Få tidig tillgång

Spoke At hittar universitetskurser, handelshögskolor, föreningar, branschorganisationer och event som tar emot talare som du, och hjälper dig att nå rätt person på deras språk.

Vi öppnar stegvis. Så får du tidig tillgång:

1. [Mejla hello@spokeat.com](mailto:hello@spokeat.com?subject=Tidig%20tillg%C3%A5ng) med ämnet "Tidig tillgång".
2. Berätta om ditt område, din roll och två eller tre ämnen du vill föreläsa om.
3. Lägg gärna till länken till din LinkedIn-profil.

Tidig tillgång är gratis. Att söka och se dina matchningar förblir gratis; du betalar först när du väljer att kontakta en arrangör.

Under tiden kan du läsa våra [guider till talaruppdrag](/sv/guider/) eller bläddra bland [talaruppdrag per expertområde](/sv/expertis/).
"""),
}

def build_misc():
    md_page("en", U_POLICY, None, "How we research and write", "How Spoke At researches, writes, sources and updates its guides.", POLICY)
    for l in ("en", "sv"):
        o = "sv" if l == "en" else "en"
        t, d, m = CONTACT[l]; md_page(l, u_contact(l), u_contact(o), t, d, m)
        t, d, m = EARLY_PAGE[l]; md_page(l, u_early(l), u_early(o), t, d, m)
    nf = head("en", "Page not found · Spoke At", "Page not found", "/404") + chrome_top("en") + '<main><div class="wrap narrow"><h1>Page not found</h1><p>The page you were looking for does not exist. Try the <a href="/en/guides/">guides</a> or the <a href="/">home page</a>.</p></div></main>' + chrome_foot("en")
    write("/404.html", nf, sitemap=False)
    os.makedirs(f"{DIST}/assets", exist_ok=True)
    open(f"{DIST}/assets/site.css", "w").write(FONT_CSS + CSS.strip())
    shutil.copytree(f"{ROOT}/content/assets", f"{DIST}/assets", dirs_exist_ok=True)
    open(f"{DIST}/favicon.svg", "w").write('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><rect width="32" height="32" rx="8" fill="#1F3A8A"/><rect x="8" y="20" width="16" height="5" rx="2.5" fill="#F5B83D"/></svg>')
    open(f"{DIST}/robots.txt", "w").write(f"User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n")
    open(f"{DIST}/_headers", "w").write("/assets/*\n  Cache-Control: public, max-age=86400\n")
    open(f"{DIST}/_redirects", "w").write("/en/ / 301\n/en / 301\n/sv /sv/ 301\n")

def build_sitemap():
    rows = []
    for path, alt, l in PAGES:
        x = f"<url><loc>{SITE}{path}</loc><lastmod>{TODAY}</lastmod>"
        if alt:
            en, sv = (path, alt) if l == "en" else (alt, path)
            x += f'<xhtml:link rel="alternate" hreflang="en" href="{SITE}{en}"/><xhtml:link rel="alternate" hreflang="sv" href="{SITE}{sv}"/><xhtml:link rel="alternate" hreflang="x-default" href="{SITE}{en}"/>'
        rows.append(x + "</url>")
    open(f"{DIST}/sitemap.xml", "w").write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">' + "".join(rows) + "</urlset>")

if __name__ == "__main__":
    shutil.rmtree(DIST, ignore_errors=True); os.makedirs(DIST)
    build_articles(); build_guides(); build_expertise(); build_landing(); build_opps(); build_author(); build_misc(); build_sitemap()
    print(len(PAGES), "pages in sitemap")
