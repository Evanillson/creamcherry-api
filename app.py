"""
CreamCherry — Flask Backend
Envio de e-mail via Resend API (HTTP — funciona no Render free tier)
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os, threading, json
import urllib.request, urllib.error
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

_email_pool = ThreadPoolExecutor(max_workers=4)
contacts, newsletters, franquias_list, atacados = [], [], [], []


# ════════════════════════════════════════
#   ENVIO VIA RESEND API
# ════════════════════════════════════════
def send_email(subject: str, html: str, to: str = None) -> bool:
    """Envia e-mail via Resend API de forma síncrona."""
    dest = to or EMAIL_TO
    resend_key = os.getenv('RESEND_API_KEY', '')
    if not resend_key:
        print(f"[DEV] RESEND_API_KEY não configurada. E-mail não enviado: {subject}")
        return True
    _send_via_resend(subject, html, dest, resend_key)
    return True


def _send_via_resend(subject: str, html: str, dest: str, api_key: str):
    """Envia via Resend SDK oficial."""
    import resend
    resend_domain = os.getenv('RESEND_DOMAIN', 'noreply@creamcherry.com.br')
    resend.api_key = api_key
    try:
        r = resend.Emails.send({
            "from":     f"CreamCherry Sobremesas <{resend_domain}>",
            "to":       [dest],
            "subject":  subject,
            "html":     html,
            "reply_to": EMAIL_TO,
        })
        print(f"[RESEND OK] id={r.get('id')} | Para: {dest} | {subject}")
    except Exception as e:
        print(f"[RESEND ERRO] {type(e).__name__}: {e}")




EMAIL_BASE = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
  *{{margin:0;padding:0;box-sizing:border-box}}
  body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#F0F0F0;color:#1A1A1A}}
  .outer{{padding:32px 16px;background:#F0F0F0}}
  .card{{max-width:580px;margin:0 auto;background:#FFFFFF;border-radius:16px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,0.10)}}
  .hdr{{background:linear-gradient(135deg,#C8102E 0%,#9E0B23 100%);padding:36px 40px 28px;text-align:center;position:relative}}
  .hdr::after{{content:'';position:absolute;bottom:0;left:0;right:0;height:4px;background:linear-gradient(90deg,rgba(255,255,255,0.1),rgba(255,255,255,0.3),rgba(255,255,255,0.1))}}
  .hdr-logo{{font-size:22px;font-weight:800;color:white;letter-spacing:-0.5px;margin-bottom:6px}}
  .hdr-logo span{{opacity:0.7;font-weight:400}}
  .hdr-badge{{display:inline-block;background:rgba(255,255,255,0.15);border:1px solid rgba(255,255,255,0.25);color:rgba(255,255,255,0.9);font-size:10px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;padding:3px 12px;border-radius:99px;margin-bottom:10px}}
  .hdr-title{{color:white;font-size:20px;font-weight:700;line-height:1.3}}
  .hdr-sub{{color:rgba(255,255,255,0.65);font-size:12px;margin-top:4px}}
  .body{{padding:32px 40px}}
  .greeting{{font-size:17px;font-weight:700;color:#1A1A1A;margin-bottom:6px}}
  .intro{{font-size:14px;color:#555;line-height:1.75;margin-bottom:24px}}
  .sec{{margin-bottom:20px}}
  .sec-title{{font-size:9px;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:#C8102E;margin-bottom:10px;padding-bottom:6px;border-bottom:2px solid #FFF0F2}}
  .row{{display:flex;gap:10px;margin-bottom:8px;flex-wrap:wrap}}
  .field{{flex:1;min-width:140px;background:#FAFAFA;border:1px solid #F0F0F0;border-radius:10px;padding:10px 14px}}
  .field.full{{flex:1 1 100%}}
  .field label{{font-size:9px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#AAA;display:block;margin-bottom:3px}}
  .field span{{font-size:14px;color:#1A1A1A;font-weight:500;word-break:break-word}}
  .obs{{background:#FFF8F5;border-left:3px solid #C8102E;border-radius:0 8px 8px 0;padding:12px 16px;font-size:13px;color:#444;line-height:1.75;margin-bottom:20px}}
  .prod-table{{width:100%;border-collapse:collapse;margin-bottom:20px;font-size:13px;border-radius:10px;overflow:hidden}}
  .prod-table thead tr{{background:#1A1A1A}}
  .prod-table th{{text-align:left;padding:10px 14px;font-weight:700;color:white;font-size:10px;letter-spacing:.1em;text-transform:uppercase}}
  .prod-table td{{padding:10px 14px;border-bottom:1px solid #F5F5F5;color:#333}}
  .prod-table tr:last-child td{{border-bottom:none}}
  .prod-table .total td{{background:#FFF0F2;font-weight:700;color:#C8102E}}
  .badge{{display:inline-block;padding:3px 10px;border-radius:99px;font-size:11px;font-weight:700}}
  .badge-red{{background:#FFF0F2;color:#C8102E}}
  .alert{{background:#FFFBEB;border:1px solid #FCD34D;border-radius:10px;padding:12px 16px;font-size:13px;color:#92400E;margin-bottom:20px;display:flex;gap:10px;align-items:flex-start}}
  .cta{{text-align:center;margin:24px 0 8px}}
  .cta a{{display:inline-block;background:#C8102E;color:white;padding:13px 32px;border-radius:99px;font-size:14px;font-weight:700;text-decoration:none;letter-spacing:0.02em}}
  .divider{{height:1px;background:#F0F0F0;margin:20px 0}}
  .footer{{background:#1A1A1A;padding:24px 40px;text-align:center}}
  .footer-brand{{color:white;font-size:15px;font-weight:700;margin-bottom:2px}}
  .footer-sub{{color:#888;font-size:12px;line-height:1.6}}
  .footer a{{color:#FF6B6B;text-decoration:none}}
  .footer-legal{{color:#555;font-size:11px;margin-top:12px;padding-top:12px;border-top:1px solid #333}}
  @media(max-width:480px){{.body,.hdr{{padding:24px 20px}}.row{{flex-direction:column}}.field{{min-width:unset}}}}
</style>
</head>
<body>
<div class="outer">
<div class="card">
{content}
<div class="footer">
  <div class="footer-brand">🍒 CreamCherry Sobremesas</div>
  <div class="footer-sub">Sorvetes &amp; Gelattos Artesanais Premium · São Paulo, SP<br>
  <a href="mailto:{email_to}">{email_to}</a> · (11) 98958-2586</div>
  <div class="footer-legal">© 2026 CreamCherry Sobremesas LTDA. Todos os direitos reservados.</div>
</div>
</div>
</div>
</body>
</html>"""


def _wrap(content_html: str) -> str:
    return EMAIL_BASE.replace('{content}', content_html).replace('{email_to}', EMAIL_TO)


def now_fmt():
    return datetime.now().strftime('%d/%m/%Y às %H:%M')

# ════════════════════════════════════════
#   TEMPLATES
# ════════════════════════════════════════
def tpl_contato_team(d):
    return _wrap(f"""
<div class="hdr">
  <div class="hdr-badge">Formulário de Contato</div>
  <div class="hdr-title">Nova mensagem via site</div>
  <div class="hdr-sub">Recebida em {now_fmt()}</div>
</div>
<div class="body">
  <div class="sec">
    <div class="sec-title">Dados do remetente</div>
    <div class="row">
      <div class="field"><label>Nome</label><span>{d['name']}</span></div>
      <div class="field"><label>E-mail</label><span>{d['email']}</span></div>
    </div>
    <div class="row">
      <div class="field full"><label>Assunto</label><span>{d['subject']}</span></div>
    </div>
  </div>
  <div class="sec">
    <div class="sec-title">Mensagem</div>
    <div class="obs">{d['message']}</div>
  </div>
  <div class="cta"><a href="mailto:{d['email']}">↩ Responder agora</a></div>
</div>""")


def tpl_contato_user(d):
    return _wrap(f"""
<div class="hdr">
  <div class="hdr-badge">Confirmação de Contato</div>
  <div class="hdr-title">Recebemos sua mensagem!</div>
  <div class="hdr-sub">{now_fmt()}</div>
</div>
<div class="body">
  <p class="greeting">Olá, {d['name'].split()[0]}!</p>
  <p class="intro">Sua mensagem foi recebida com sucesso. Nossa equipe responderá em breve. Para retorno urgente, fale pelo WhatsApp.</p>
  <div class="sec">
    <div class="row">
      <div class="field"><label>Assunto</label><span>{d['subject']}</span></div>
      <div class="field"><label>Protocolo</label><span>#{datetime.now().strftime('%Y%m%d%H%M')}</span></div>
    </div>
  </div>
  <div class="cta"><a href="https://wa.me/5511989582586">💬 Falar pelo WhatsApp</a></div>
</div>""")


def tpl_newsletter_user(email):
    return _wrap(f"""
<div class="hdr">
  <div class="hdr-badge">Newsletter</div>
  <div class="hdr-title">Nova inscrição recebida!</div>
  <div class="hdr-sub">{now_fmt()}</div>
</div>
<div class="body">
  <div class="sec">
    <div class="sec-title">E-mail cadastrado</div>
    <div class="row">
      <div class="field full"><label>E-mail do cliente</label><span>{email}</span></div>
    </div>
  </div>
  <p class="intro">Um novo cliente se inscreveu para receber novidades da CreamCherry.</p>
  <div class="cta"><a href="mailto:{email}">✉️ Enviar e-mail ao cliente</a></div>
</div>""")


def tpl_franquia_team(d):
    return _wrap(f"""
<div class="hdr">
  <div class="hdr-badge">Proposta de Franquia</div>
  <div class="hdr-title">Novo interesse em franquia</div>
  <div class="hdr-sub">Recebido em {now_fmt()}</div>
</div>
<div class="body">
  <div class="sec">
    <div class="sec-title">Dados do interessado</div>
    <div class="row">
      <div class="field"><label>Nome</label><span>{d['fName']}</span></div>
      <div class="field"><label>E-mail</label><span>{d['fEmail']}</span></div>
    </div>
    <div class="row">
      <div class="field"><label>Telefone</label><span>{d['fPhone']}</span></div>
      <div class="field"><label>Cidade / Estado</label><span>{d['fCity']}</span></div>
    </div>
    <div class="row">
      <div class="field full"><label>Capital disponível</label><span>{d['fCapital']}</span></div>
    </div>
  </div>
  <div class="sec">
    <div class="sec-title">Mensagem</div>
    <div class="obs">{d['fMessage']}</div>
  </div>
  <div class="cta"><a href="mailto:{d['fEmail']}">↩ Entrar em contato</a></div>
</div>""")


def tpl_franquia_user(d):
    return _wrap(f"""
<div class="hdr">
  <div class="hdr-badge">Franquias CreamCherry</div>
  <div class="hdr-title">Proposta recebida com sucesso!</div>
  <div class="hdr-sub">{now_fmt()}</div>
</div>
<div class="body">
  <p class="greeting">Olá, {d['fName'].split()[0]}!</p>
  <p class="intro">Recebemos sua proposta de franquia. Nossa equipe analisará seu perfil e entrará em contato em até <strong>48 horas úteis</strong>.</p>
  <div class="sec">
    <div class="row">
      <div class="field"><label>Cidade de interesse</label><span>{d['fCity']}</span></div>
      <div class="field"><label>Capital declarado</label><span>{d['fCapital']}</span></div>
    </div>
  </div>
  <div class="alert">💡 Prepare informações sobre o ponto comercial desejado e seu histórico profissional para nossa conversa.</div>
  <div class="cta"><a href="https://wa.me/5511989582586">💬 Falar pelo WhatsApp</a></div>
</div>""")


def tpl_atacado_team(d):
    raw_prods = d.get('produtos', [])
    prods = []
    for p in raw_prods:
        if isinstance(p, dict):
            prods.append({{'produto': p.get('produto') or p.get('name') or str(p), 'quantidade': int(p.get('quantidade') or p.get('qty') or 0)}})
        else:
            prods.append({{'produto': str(p), 'quantidade': 0}})
    rows = ''.join(f"<tr><td>{p['produto']}</td><td style='text-align:center;font-weight:600'>{p['quantidade']} un.</td></tr>" for p in prods)
    total = sum(p['quantidade'] for p in prods)
    obs_block = f'<div class="sec"><div class="sec-title">Observações</div><div class="obs">{d["obs"]}</div></div>' if d.get('obs') else ''
    return _wrap(f"""
<div class="hdr">
  <div class="hdr-badge">Pedido Atacado</div>
  <div class="hdr-title">Nova solicitação de encomenda</div>
  <div class="hdr-sub">Recebida em {now_fmt()}</div>
</div>
<div class="body">
  <div class="sec">
    <div class="sec-title">Dados do solicitante</div>
    <div class="row">
      <div class="field"><label>Nome</label><span>{d['nome']}</span></div>
      <div class="field"><label>Perfil</label><span>{d['perfil']}</span></div>
    </div>
    <div class="row">
      <div class="field"><label>E-mail</label><span>{d['email']}</span></div>
      <div class="field"><label>Telefone</label><span>{d['telefone']}</span></div>
    </div>
  </div>
  <div class="sec">
    <div class="sec-title">Endereço de entrega</div>
    <div class="row">
      <div class="field full"><label>Endereço</label><span>{d['logradouro']}, {d['numero']} {d.get('complemento','')} — {d['bairro']}</span></div>
    </div>
    <div class="row">
      <div class="field"><label>Cidade / UF</label><span>{d['cidade']}</span></div>
      <div class="field"><label>CEP</label><span>{d['cep']}</span></div>
    </div>
  </div>
  <div class="sec">
    <div class="sec-title">Produtos solicitados</div>
    <table class="prod-table">
      <thead><tr><th>Produto</th><th style="text-align:center">Qtd.</th></tr></thead>
      <tbody>{rows}<tr class="total"><td><strong>Total</strong></td><td style="text-align:center"><strong>{total} un.</strong></td></tr></tbody>
    </table>
  </div>
  {obs_block}
  <div class="cta"><a href="mailto:{d['email']}">↩ Responder ao cliente</a></div>
</div>""")


def tpl_atacado_user(d):
    raw_prods2 = d.get('produtos', [])
    prods2 = [{{'produto': p.get('produto') or str(p), 'quantidade': int(p.get('quantidade') or 0)}} if isinstance(p, dict) else {{'produto': str(p), 'quantidade': 0}} for p in raw_prods2]
    rows = ''.join(f"<tr><td>{p['produto']}</td><td style='text-align:center'>{p['quantidade']} un.</td></tr>" for p in prods2)
    return _wrap(f"""
<div class="hdr">
  <div class="hdr-badge">Atacado &amp; Encomendas</div>
  <div class="hdr-title">Solicitação recebida!</div>
  <div class="hdr-sub">{now_fmt()}</div>
</div>
<div class="body">
  <p class="greeting">Olá, {d['nome'].split()[0]}!</p>
  <p class="intro">Recebemos sua solicitação de encomenda. Nossa equipe retornará em até <strong>24 horas úteis</strong> com orçamento e confirmação.</p>
  <div class="sec">
    <div class="sec-title">Resumo do pedido</div>
    <table class="prod-table">
      <thead><tr><th>Produto</th><th style="text-align:center">Quantidade</th></tr></thead>
      <tbody>{rows}</tbody>
    </table>
  </div>
  <div class="sec">
    <div class="row">
      <div class="field"><label>Entrega em</label><span>{d['cidade']}</span></div>
      <div class="field"><label>Protocolo</label><span>#{datetime.now().strftime('%Y%m%d%H%M')}</span></div>
    </div>
  </div>
  <div class="alert">⏱️ <strong>Prazo de produção:</strong> 3 a 5 dias úteis após confirmação e pagamento.</div>
  <div class="cta"><a href="https://wa.me/5511989582586">💬 Acompanhar pelo WhatsApp</a></div>
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
    send_email(f"[CreamCherry] Nova inscrição na newsletter — {email}", tpl_newsletter_user(email), to=EMAIL_TO)
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
