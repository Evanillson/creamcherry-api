"""
CreamCherry — Flask Backend
Envio de e-mail via Resend API (HTTP — funciona no Render free tier)
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os, requests, threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

load_dotenv()

app = Flask(__name__)
CORS(app)
app.secret_key = os.getenv('SECRET_KEY', 'creamcherry-2026-secret')

RESEND_API_KEY = os.getenv('RESEND_API_KEY', '')
EMAIL_TO       = os.getenv('EMAIL_TO',   'comercial@creamcherry.com.br')
ATACADO_EMAIL  = os.getenv('ATACADO_EMAIL', EMAIL_TO)

# Remetente: usa domínio verificado ou fallback do Resend
EMAIL_FROM = 'CreamCherry Sobremesas <onboarding@resend.dev>'

_pool = ThreadPoolExecutor(max_workers=4)
contacts, newsletters, franquias_list, atacados = [], [], [], []


# ════════════════════════════════════════
#   ENVIO VIA RESEND API
# ════════════════════════════════════════
def send_email(subject: str, html: str, to: str = None) -> bool:
    """Dispara e-mail via Resend API (HTTPS) em background thread."""
    dest = to or EMAIL_TO
    resend_key = os.getenv('RESEND_API_KEY', '')
    if not resend_key:
        print(f"[DEV] RESEND_API_KEY não configurada. E-mail não enviado: {subject}")
        return True
    _email_pool.submit(_send_via_resend, subject, html, dest, resend_key)
    return True


def _send_via_resend(subject: str, html: str, dest: str, api_key: str):
    """Envia via Resend API — funciona no Render free tier (sem bloqueio SMTP)."""
    # Remetente: usa domínio verificado ou onboarding@resend.dev para testes
    resend_domain = os.getenv('RESEND_DOMAIN', 'onboarding@resend.dev')
    from_addr = f"CreamCherry Sobremesas <{resend_domain}>"

    payload = _json.dumps({
        "from":    from_addr,
        "to":      [dest],
        "subject": subject,
        "html":    html,
        "reply_to": EMAIL_TO,
    }).encode('utf-8')

    req = urllib.request.Request(
        'https://api.resend.com/emails',
        data=payload,
        headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type':  'application/json',
        },
        method='POST'
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = _json.loads(resp.read().decode())
            print(f"[RESEND OK] id={result.get('id')} | Para: {dest} | {subject}")
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"[RESEND ERRO HTTP {e.code}] {body}")
    except Exception as e:
        print(f"[RESEND ERRO] {type(e).__name__}: {e}")



# ════════════════════════════════════════
#   TEMPLATES
# ════════════════════════════════════════
def tpl_contato_team(d):
    return _wrap(f"""
<div class="hdr">
  <div class="badge">Formulário de Contato</div>
  <p class="hdr-title">Nova mensagem via site</p>
  <p class="hdr-sub">Recebida em {now_fmt()}</p>
</div>
<div class="body">
  <p class="sec">Dados do remetente</p>
  <div class="fields">
    <div class="field"><label>Nome</label><span>{d['name']}</span></div>
    <div class="field"><label>E-mail</label><span>{d['email']}</span></div>
    <div class="field full"><label>Assunto</label><span>{d['subject']}</span></div>
  </div>
  <p class="sec">Mensagem</p>
  <div class="obs">{d['message']}</div>
  <div class="cta"><a href="mailto:{d['email']}">Responder agora</a></div>
</div>""")

def tpl_contato_user(d):
    return _wrap(f"""
<div class="hdr">
  <div class="badge">Confirmação</div>
  <p class="hdr-title">Recebemos sua mensagem!</p>
  <p class="hdr-sub">{now_fmt()}</p>
</div>
<div class="body">
  <p class="greeting">Olá, {d['name'].split()[0]}!</p>
  <p class="intro">Recebemos sua mensagem e nossa equipe responderá em breve.<br>
  Para retorno urgente: <strong>(11) 98958-2586</strong> (WhatsApp)</p>
  <div class="fields">
    <div class="field"><label>Assunto</label><span>{d['subject']}</span></div>
    <div class="field"><label>Protocolo</label><span>#{datetime.now().strftime('%Y%m%d%H%M')}</span></div>
  </div>
  <div class="cta"><a href="https://wa.me/5511989582586">Falar pelo WhatsApp</a></div>
</div>""")

def tpl_newsletter_user(email):
    return _wrap(f"""
<div class="hdr">
  <div class="badge">Newsletter</div>
  <p class="hdr-title">Você está inscrito!</p>
  <p class="hdr-sub">{now_fmt()}</p>
</div>
<div class="body">
  <p class="greeting">Que bom ter você aqui!</p>
  <p class="intro">Você receberá em primeira mão novos sabores, promoções exclusivas e novidades da CreamCherry.</p>
  <div class="cta"><a href="https://oia.99app.com/dlp9/VkoEdY">Ver Cardápio</a></div>
</div>""")

def tpl_franquia_team(d):
    return _wrap(f"""
<div class="hdr">
  <div class="badge">Solicitação de Franquia</div>
  <p class="hdr-title">Novo interesse em franquia</p>
  <p class="hdr-sub">Recebido em {now_fmt()}</p>
</div>
<div class="body">
  <p class="sec">Dados do interessado</p>
  <div class="fields">
    <div class="field"><label>Nome</label><span>{d['fName']}</span></div>
    <div class="field"><label>E-mail</label><span>{d['fEmail']}</span></div>
    <div class="field"><label>Telefone</label><span>{d['fPhone']}</span></div>
    <div class="field"><label>Cidade</label><span>{d['fCity']}</span></div>
    <div class="field full"><label>Capital disponível</label><span>{d['fCapital']}</span></div>
  </div>
  <p class="sec">Mensagem</p>
  <div class="obs">{d['fMessage']}</div>
  <div class="cta"><a href="mailto:{d['fEmail']}">Entrar em contato</a></div>
</div>""")

def tpl_franquia_user(d):
    return _wrap(f"""
<div class="hdr">
  <div class="badge">Franquias CreamCherry</div>
  <p class="hdr-title">Proposta recebida!</p>
  <p class="hdr-sub">{now_fmt()}</p>
</div>
<div class="body">
  <p class="greeting">Olá, {d['fName'].split()[0]}!</p>
  <p class="intro">Recebemos sua proposta de franquia. Nossa equipe entrará em contato em até <strong>48 horas úteis</strong>.</p>
  <div class="fields">
    <div class="field"><label>Cidade</label><span>{d['fCity']}</span></div>
    <div class="field"><label>Capital</label><span>{d['fCapital']}</span></div>
  </div>
  <div class="cta"><a href="https://wa.me/5511989582586">Falar pelo WhatsApp</a></div>
</div>""")

def tpl_atacado_team(d):
    raw = d.get('produtos', [])
    prods = [
        {'produto': p.get('produto') or p.get('name') or str(p),
         'quantidade': int(p.get('quantidade') or p.get('qty') or 0)}
        if isinstance(p, dict) else {'produto': str(p), 'quantidade': 0}
        for p in raw
    ]
    rows  = ''.join(f"<tr><td>{p['produto']}</td><td style='text-align:center'>{p['quantidade']} un.</td></tr>" for p in prods)
    total = sum(p['quantidade'] for p in prods)
    obs   = f'<p class="sec">Observações</p><div class="obs">{d["obs"]}</div>' if d.get('obs') else ''
    return _wrap(f"""
<div class="hdr">
  <div class="badge">Pedido Atacado</div>
  <p class="hdr-title">Nova solicitação de encomenda</p>
  <p class="hdr-sub">Recebida em {now_fmt()}</p>
</div>
<div class="body">
  <p class="sec">Dados do solicitante</p>
  <div class="fields">
    <div class="field"><label>Nome</label><span>{d['nome']}</span></div>
    <div class="field"><label>Perfil</label><span>{d['perfil']}</span></div>
    <div class="field"><label>E-mail</label><span>{d['email']}</span></div>
    <div class="field"><label>Telefone</label><span>{d['telefone']}</span></div>
  </div>
  <p class="sec">Endereço de entrega</p>
  <div class="fields">
    <div class="field full"><label>Endereço</label><span>{d['logradouro']}, {d['numero']} {d.get('complemento','')} — {d['bairro']}</span></div>
    <div class="field"><label>Cidade/UF</label><span>{d['cidade']}</span></div>
    <div class="field"><label>CEP</label><span>{d['cep']}</span></div>
  </div>
  <p class="sec">Produtos solicitados</p>
  <table class="tbl">
    <thead><tr><th>Produto</th><th style="text-align:center">Qtd.</th></tr></thead>
    <tbody>{rows}<tr class="total"><td><strong>Total</strong></td><td style="text-align:center"><strong>{total} un.</strong></td></tr></tbody>
  </table>
  {obs}
  <div class="cta"><a href="mailto:{d['email']}">Responder ao cliente</a></div>
</div>""")

def tpl_atacado_user(d):
    raw = d.get('produtos', [])
    prods = [
        {'produto': p.get('produto') or p.get('name') or str(p),
         'quantidade': int(p.get('quantidade') or p.get('qty') or 0)}
        if isinstance(p, dict) else {'produto': str(p), 'quantidade': 0}
        for p in raw
    ]
    rows = ''.join(f"<tr><td>{p['produto']}</td><td style='text-align:center'>{p['quantidade']} un.</td></tr>" for p in prods)
    return _wrap(f"""
<div class="hdr">
  <div class="badge">Atacado &amp; Encomendas</div>
  <p class="hdr-title">Solicitação recebida!</p>
  <p class="hdr-sub">{now_fmt()}</p>
</div>
<div class="body">
  <p class="greeting">Olá, {d['nome'].split()[0]}!</p>
  <p class="intro">Recebemos sua solicitação. Nossa equipe retornará em até <strong>24 horas úteis</strong>.</p>
  <table class="tbl">
    <thead><tr><th>Produto</th><th style="text-align:center">Quantidade</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>
  <div class="fields">
    <div class="field"><label>Entrega em</label><span>{d['cidade']}</span></div>
    <div class="field"><label>Protocolo</label><span>#{datetime.now().strftime('%Y%m%d%H%M')}</span></div>
  </div>
  <div class="alert">⏱️ Prazo de produção: 3 a 5 dias úteis após confirmação e pagamento.</div>
  <div class="cta"><a href="https://wa.me/5511989582586">Acompanhar pelo WhatsApp</a></div>
</div>""")


# ════════════════════════════════════════
#   ROTAS
# ════════════════════════════════════════
@app.route('/api/contato', methods=['POST'])
def contato():
    d = request.get_json(force=True)
    for f in ['name','email','subject','message']:
        if not d.get(f): return jsonify({'error': f'Campo "{f}" obrigatório'}), 400
    contacts.append({**d, 'ts': datetime.now().isoformat()})
    send_email(f"[CreamCherry] Contato — {d['subject']}", tpl_contato_team(d))
    send_email("CreamCherry: recebemos sua mensagem", tpl_contato_user(d), to=d['email'])
    return jsonify({'success': True}), 201

@app.route('/api/newsletter', methods=['POST'])
def newsletter():
    d = request.get_json(force=True)
    email = d.get('email','').strip()
    if not email or '@' not in email: return jsonify({'error': 'E-mail inválido'}), 400
    if email in [n['email'] for n in newsletters]: return jsonify({'message': 'Já cadastrado'}), 200
    newsletters.append({'email': email, 'ts': datetime.now().isoformat()})
    send_email("CreamCherry: bem-vindo(a) à nossa newsletter!", tpl_newsletter_user(email), to=email)
    return jsonify({'success': True}), 201

@app.route('/api/franquia', methods=['POST'])
def franquia():
    d = request.get_json(force=True)
    for f in ['fName','fEmail','fPhone','fCity','fCapital','fMessage']:
        if not d.get(f): return jsonify({'error': f'Campo "{f}" obrigatório'}), 400
    franquias_list.append({**d, 'ts': datetime.now().isoformat()})
    send_email(f"[CreamCherry] Franquia — {d['fCity']}", tpl_franquia_team(d))
    send_email("CreamCherry: proposta recebida!", tpl_franquia_user(d), to=d['fEmail'])
    return jsonify({'success': True}), 201

@app.route('/api/atacado', methods=['POST'])
def atacado():
    d = request.get_json(force=True)
    for f in ['nome','email','telefone','perfil','cep','logradouro','bairro','cidade','numero','produtos']:
        if not d.get(f): return jsonify({'error': f'Campo "{f}" obrigatório'}), 400
    atacados.append({**d, 'ts': datetime.now().isoformat()})
    send_email(f"[CreamCherry Atacado] {d['nome']} / {d['cidade']}", tpl_atacado_team(d), to=ATACADO_EMAIL)
    send_email("CreamCherry: solicitação de atacado recebida!", tpl_atacado_user(d), to=d['email'])
    return jsonify({'success': True}), 201

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    print(f"\n🍒 CreamCherry API — http://localhost:{port}")
    print(f"   Resend: {'configurado' if RESEND_API_KEY else 'SEM API KEY'}\n")
    app.run(host='0.0.0.0', port=port, debug=False)
