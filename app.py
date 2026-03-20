"""
========================================
CreamCherry — Flask Backend
Configurado para Outlook / Office365
========================================
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os, smtplib, ssl, threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

load_dotenv()

app = Flask(__name__)
CORS(app)
app.secret_key = os.getenv('SECRET_KEY', 'creamcherry-dev-secret')

# ── Configurações SMTP ──────────────────
SMTP_HOST     = os.getenv('SMTP_HOST',  'smtp.office365.com')
SMTP_PORT     = int(os.getenv('SMTP_PORT', 587))
SMTP_USER     = os.getenv('SMTP_USER',  '')
SMTP_PASS     = os.getenv('SMTP_PASS',  '')
EMAIL_FROM    = os.getenv('EMAIL_FROM', SMTP_USER)
EMAIL_TO      = os.getenv('EMAIL_TO',   'Comercial@creamcherry.com.br')
ATACADO_EMAIL = os.getenv('ATACADO_EMAIL', EMAIL_TO)

# ── Armazenamento em memória ────────────
# Substitua por banco de dados em produção
contacts, newsletters, franquias_list, atacados = [], [], [], []


# ════════════════════════════════════════
#   ENVIO DE E-MAIL — Outlook / Office365
# ════════════════════════════════════════
def send_email(subject: str, html: str, to: str = None) -> bool:
    """Envia e-mail de forma síncrona — gthread worker garante não bloquear."""
    dest = to or EMAIL_TO
    if not SMTP_USER or not SMTP_PASS:
        print(f"[DEV] E-mail não enviado (sem SMTP): {subject}")
        return True
    return _send_email_sync(subject, html, dest)


def _send_email_sync(subject: str, html: str, dest: str) -> bool:
    """Envio SMTP real."""
    if not SMTP_USER or not SMTP_PASS:
        return False

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From']    = f"CreamCherry Sobremesas <{EMAIL_FROM}>"
    msg['To']      = dest
    msg['Reply-To']= EMAIL_FROM
    msg.attach(MIMEText(html, 'html', 'utf-8'))

    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.check_hostname = False
    context.verify_mode    = ssl.CERT_NONE

    try:
        print(f"[SMTP] Conectando smtp.office365.com:587...")
        print(f"[SMTP] USER: {SMTP_USER}")
        server = smtplib.SMTP('smtp.office365.com', 587, timeout=60)
        server.set_debuglevel(0)
        server.ehlo()
        print(f"[SMTP] STARTTLS...")
        server.starttls(context=context)
        server.ehlo()
        print(f"[SMTP] Login...")
        server.login(SMTP_USER, SMTP_PASS)
        print(f"[SMTP] Enviando para {dest}...")
        server.sendmail(EMAIL_FROM, dest, msg.as_string())
        server.quit()
        print(f"[EMAIL OK] ✓ Para: {dest} | {subject}")
        return True
    except smtplib.SMTPAuthenticationError as e:
        print(f"[ERRO AUTH] Autenticação falhou: {e}")
        print(f"[ERRO AUTH] Verifique SMTP_PASS no Render > Environment")
        return False
    except smtplib.SMTPConnectError as e:
        print(f"[ERRO CONNECT] Não conectou: {e}")
        return False
    except smtplib.SMTPException as e:
        print(f"[ERRO SMTP] {type(e).__name__}: {e}")
        return False
    except Exception as e:
        print(f"[ERRO GERAL] {type(e).__name__}: {e}")
        return False


def now_fmt():
    return datetime.now().strftime('%d/%m/%Y às %H:%M')


# ════════════════════════════════════════
#   TEMPLATES DE E-MAIL HTML
# ════════════════════════════════════════
EMAIL_BASE = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
  *{{margin:0;padding:0;box-sizing:border-box}}
  body{{font-family:'Segoe UI',Arial,sans-serif;background:#F5F5F5;color:#333}}
  .wrap{{max-width:600px;margin:0 auto;background:white;border-radius:12px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,.08)}}
  .hdr{{background:#C8102E;padding:32px 40px;text-align:center}}
  .hdr-badge{{display:inline-block;background:rgba(255,255,255,.15);border:1px solid rgba(255,255,255,.3);color:white;font-size:11px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;padding:4px 14px;border-radius:99px;margin-bottom:12px}}
  .hdr-title{{color:white;font-size:22px;font-weight:700;margin:0}}
  .hdr-sub{{color:rgba(255,255,255,.7);font-size:13px;margin-top:4px}}
  .body{{padding:36px 40px}}
  .greeting{{font-size:18px;font-weight:600;color:#222;margin-bottom:8px}}
  .intro{{font-size:14px;color:#666;line-height:1.7;margin-bottom:24px}}
  .sec-title{{font-size:10px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#C8102E;margin-bottom:10px;padding-bottom:6px;border-bottom:1px solid #F0E8E8}}
  .fields{{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:20px}}
  .field{{background:#F9F6F4;border-radius:8px;padding:10px 14px}}
  .field label{{font-size:10px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:#999;display:block;margin-bottom:2px}}
  .field span{{font-size:14px;color:#222;font-weight:500}}
  .field.full{{grid-column:1/-1}}
  .obs{{background:#FFF8F5;border:1px solid #F0E0D8;border-radius:8px;padding:12px 16px;font-size:13px;color:#555;line-height:1.7;margin-bottom:20px}}
  .prod-table{{width:100%;border-collapse:collapse;margin-bottom:20px;font-size:13px}}
  .prod-table th{{background:#F5F0EC;text-align:left;padding:8px 12px;font-weight:700;color:#666;font-size:10px;letter-spacing:.06em;text-transform:uppercase}}
  .prod-table td{{padding:8px 12px;border-bottom:1px solid #F0EBE7;color:#333}}
  .prod-table tr:last-child td{{border-bottom:none}}
  .total-row td{{background:#FFF0F2;font-weight:700;color:#C8102E}}
  .alert{{background:#FFF8E1;border:1px solid #FFD740;border-radius:8px;padding:12px 16px;font-size:13px;color:#6D4C00;margin-bottom:20px}}
  .cta{{text-align:center;margin:24px 0}}
  .cta a{{display:inline-block;background:#C8102E;color:white;padding:12px 28px;border-radius:99px;font-size:14px;font-weight:700;text-decoration:none}}
  .footer{{background:#2E2420;padding:24px 40px;text-align:center}}
  .footer p{{color:rgba(255,255,255,.5);font-size:12px;line-height:1.6}}
  .footer a{{color:rgba(255,255,255,.7);text-decoration:none}}
  @media(max-width:480px){{.body,.hdr{{padding:24px 20px}}.fields{{grid-template-columns:1fr}}.footer{{padding:20px}}}}
</style>
</head>
<body>
<div style="padding:20px 0;background:#F5F5F5">
<div class="wrap">
{content}
<div class="footer">
  <p style="color:rgba(255,255,255,.85);font-size:15px;font-weight:700;margin-bottom:4px">CreamCherry Sobremesas</p>
  <p>Sorvetes &amp; Gelattos Artesanais Premium — São Paulo, SP</p>
  <p style="margin-top:8px"><a href="mailto:{email_to}">{email_to}</a></p>
  <hr style="border:none;border-top:1px solid rgba(255,255,255,.1);margin:14px 0">
  <p style="font-size:11px">© 2025 CreamCherry Sobremesas LTDA. Todos os direitos reservados.</p>
</div>
</div>
</div>
</body>
</html>"""

def _wrap(content):
    return EMAIL_BASE.replace('{content}', content).replace('{email_to}', EMAIL_TO)


# ── Templates individuais ─────────────

def tpl_contato_team(d):
    return _wrap(f"""
<div class="hdr">
  <div class="hdr-badge">Formulário de Contato</div>
  <p class="hdr-title">Nova mensagem via site</p>
  <p class="hdr-sub">Recebida em {now_fmt()}</p>
</div>
<div class="body">
  <p class="sec-title">Dados do remetente</p>
  <div class="fields">
    <div class="field"><label>Nome</label><span>{d['name']}</span></div>
    <div class="field"><label>E-mail</label><span>{d['email']}</span></div>
    <div class="field full"><label>Assunto</label><span>{d['subject']}</span></div>
  </div>
  <p class="sec-title">Mensagem</p>
  <div class="obs">{d['message']}</div>
  <div class="cta"><a href="mailto:{d['email']}">Responder agora</a></div>
</div>""")

def tpl_contato_user(d):
    return _wrap(f"""
<div class="hdr">
  <div class="hdr-badge">Confirmação</div>
  <p class="hdr-title">Recebemos sua mensagem!</p>
  <p class="hdr-sub">{now_fmt()}</p>
</div>
<div class="body">
  <p class="greeting">Olá, {d['name'].split()[0]}!</p>
  <p class="intro">Recebemos sua mensagem e responderemos em breve.<br>
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
  <div class="hdr-badge">Newsletter</div>
  <p class="hdr-title">Você está inscrito!</p>
  <p class="hdr-sub">{now_fmt()}</p>
</div>
<div class="body">
  <p class="greeting">Que bom ter você aqui!</p>
  <p class="intro">A partir de agora você receberá novos sabores, promoções exclusivas e novidades da CreamCherry em primeira mão.</p>
  <div class="cta"><a href="https://oia.99app.com/dlp9/VkoEdY">Ver Cardápio</a></div>
</div>""")

def tpl_franquia_team(d):
    return _wrap(f"""
<div class="hdr">
  <div class="hdr-badge">Solicitação de Franquia</div>
  <p class="hdr-title">Novo interesse em franquia</p>
  <p class="hdr-sub">Recebido em {now_fmt()}</p>
</div>
<div class="body">
  <p class="sec-title">Dados do interessado</p>
  <div class="fields">
    <div class="field"><label>Nome</label><span>{d['fName']}</span></div>
    <div class="field"><label>E-mail</label><span>{d['fEmail']}</span></div>
    <div class="field"><label>Telefone</label><span>{d['fPhone']}</span></div>
    <div class="field"><label>Cidade / Estado</label><span>{d['fCity']}</span></div>
    <div class="field full"><label>Capital disponível</label><span>{d['fCapital']}</span></div>
  </div>
  <p class="sec-title">Mensagem</p>
  <div class="obs">{d['fMessage']}</div>
  <div class="cta"><a href="mailto:{d['fEmail']}">Entrar em contato</a></div>
</div>""")

def tpl_franquia_user(d):
    return _wrap(f"""
<div class="hdr">
  <div class="hdr-badge">Franquias CreamCherry</div>
  <p class="hdr-title">Proposta recebida!</p>
  <p class="hdr-sub">{now_fmt()}</p>
</div>
<div class="body">
  <p class="greeting">Olá, {d['fName'].split()[0]}!</p>
  <p class="intro">Recebemos sua proposta de franquia. Nossa equipe analisará seu perfil e entrará em contato em até <strong>48 horas úteis</strong>.</p>
  <div class="fields">
    <div class="field"><label>Cidade de interesse</label><span>{d['fCity']}</span></div>
    <div class="field"><label>Capital declarado</label><span>{d['fCapital']}</span></div>
  </div>
  <div class="alert">💡 Prepare informações sobre o ponto comercial desejado e seu histórico profissional para a nossa conversa.</div>
  <div class="cta"><a href="https://wa.me/5511989582586">Falar pelo WhatsApp</a></div>
</div>""")

def tpl_atacado_team(d):
    # Normalize products — handles both dict and string formats
    raw_prods = d.get('produtos', [])
    prods_normalized = []
    for p in raw_prods:
        if isinstance(p, dict):
            prods_normalized.append({
                'produto':    p.get('produto') or p.get('name') or str(p),
                'quantidade': int(p.get('quantidade') or p.get('qty') or 0),
            })
        else:
            prods_normalized.append({'produto': str(p), 'quantidade': 0})

    rows = ''.join(
        f"<tr><td>{p['produto']}</td><td style='text-align:center'>{p['quantidade']} un.</td></tr>"
        for p in prods_normalized
    )
    total = sum(p['quantidade'] for p in prods_normalized)
    obs_block = f'<p class="sec-title">Observações</p><div class="obs">{d["obs"]}</div>' if d.get('obs') else ''
    return _wrap(f"""
<div class="hdr">
  <div class="hdr-badge">Pedido no Atacado</div>
  <p class="hdr-title">Nova solicitação de encomenda</p>
  <p class="hdr-sub">Recebida em {now_fmt()}</p>
</div>
<div class="body">
  <p class="sec-title">Dados do solicitante</p>
  <div class="fields">
    <div class="field"><label>Nome</label><span>{d['nome']}</span></div>
    <div class="field"><label>Perfil</label><span>{d['perfil']}</span></div>
    <div class="field"><label>E-mail</label><span>{d['email']}</span></div>
    <div class="field"><label>Telefone</label><span>{d['telefone']}</span></div>
  </div>
  <p class="sec-title">Endereço de entrega</p>
  <div class="fields">
    <div class="field full"><label>Endereço</label><span>{d['logradouro']}, {d['numero']} {d.get('complemento','')} — {d['bairro']}</span></div>
    <div class="field"><label>Cidade / UF</label><span>{d['cidade']}</span></div>
    <div class="field"><label>CEP</label><span>{d['cep']}</span></div>
  </div>
  <p class="sec-title">Produtos solicitados</p>
  <table class="prod-table">
    <thead><tr><th>Produto</th><th style="text-align:center">Qtd (un.)</th></tr></thead>
    <tbody>
      {rows}
      <tr class="total-row"><td><strong>Total</strong></td><td style="text-align:center"><strong>{total} un.</strong></td></tr>
    </tbody>
  </table>
  {obs_block}
  <div class="cta"><a href="mailto:{d['email']}">Responder ao cliente</a></div>
</div>""")

def tpl_atacado_user(d):
    raw_prods2 = d.get('produtos', [])
    prods2 = [
        {'produto': p.get('produto') or p.get('name') or str(p),
         'quantidade': int(p.get('quantidade') or p.get('qty') or 0)}
        if isinstance(p, dict) else {'produto': str(p), 'quantidade': 0}
        for p in raw_prods2
    ]
    rows = ''.join(
        f"<tr><td>{p['produto']}</td><td style='text-align:center'>{p['quantidade']} un.</td></tr>"
        for p in prods2
    )
    return _wrap(f"""
<div class="hdr">
  <div class="hdr-badge">Atacado &amp; Encomendas</div>
  <p class="hdr-title">Solicitação recebida!</p>
  <p class="hdr-sub">{now_fmt()}</p>
</div>
<div class="body">
  <p class="greeting">Olá, {d['nome'].split()[0]}!</p>
  <p class="intro">Recebemos sua solicitação de encomenda no atacado. Nossa equipe retornará em até <strong>24 horas úteis</strong>.</p>
  <p class="sec-title">Resumo do pedido</p>
  <table class="prod-table">
    <thead><tr><th>Produto</th><th style="text-align:center">Quantidade</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>
  <div class="fields">
    <div class="field"><label>Entrega em</label><span>{d['cidade']}</span></div>
    <div class="field"><label>Protocolo</label><span>#{datetime.now().strftime('%Y%m%d%H%M')}</span></div>
  </div>
  <div class="alert">⏱️ <strong>Prazo de produção:</strong> 3 a 5 dias úteis após confirmação e pagamento.</div>
  <div class="cta"><a href="https://wa.me/5511989582586">Acompanhar pelo WhatsApp</a></div>
</div>""")


# ════════════════════════════════════════
#   ROTAS
# ════════════════════════════════════════

@app.route('/api/contato', methods=['POST'])
def contato():
    d = request.get_json(force=True)
    for f in ['name','email','subject','message']:
        if not d.get(f):
            return jsonify({'error': f'Campo "{f}" obrigatório'}), 400
    contacts.append({**d, 'created_at': datetime.now().isoformat()})
    send_email(f"[CreamCherry] Contato via site — {d['subject']}", tpl_contato_team(d))
    send_email("CreamCherry: recebemos sua mensagem", tpl_contato_user(d), to=d['email'])
    return jsonify({'success': True}), 201


@app.route('/api/newsletter', methods=['POST'])
def newsletter():
    d     = request.get_json(force=True)
    email = d.get('email','').strip()
    if not email or '@' not in email:
        return jsonify({'error': 'E-mail inválido'}), 400
    if email in [n['email'] for n in newsletters]:
        return jsonify({'message': 'Já cadastrado'}), 200
    newsletters.append({'email': email, 'created_at': datetime.now().isoformat()})
    send_email("CreamCherry: bem-vindo(a) à nossa newsletter!", tpl_newsletter_user(email), to=email)
    return jsonify({'success': True}), 201


@app.route('/api/franquia', methods=['POST'])
def franquia():
    d = request.get_json(force=True)
    for f in ['fName','fEmail','fPhone','fCity','fCapital','fMessage']:
        if not d.get(f):
            return jsonify({'error': f'Campo "{f}" obrigatório'}), 400
    franquias_list.append({**d, 'created_at': datetime.now().isoformat()})
    send_email(f"[CreamCherry] Proposta de Franquia — {d['fCity']}", tpl_franquia_team(d))
    send_email("CreamCherry: sua proposta de franquia foi recebida!", tpl_franquia_user(d), to=d['fEmail'])
    return jsonify({'success': True}), 201


@app.route('/api/atacado', methods=['POST'])
def atacado():
    d = request.get_json(force=True)
    for f in ['nome','email','telefone','perfil','cep','logradouro','bairro','cidade','numero','produtos']:
        if not d.get(f):
            return jsonify({'error': f'Campo "{f}" obrigatório'}), 400
    atacados.append({**d, 'created_at': datetime.now().isoformat()})
    send_email(
        f"[CreamCherry Atacado] Pedido — {d['nome']} / {d['cidade']}",
        tpl_atacado_team(d),
        to=ATACADO_EMAIL  # FIXO no servidor, nunca exposto no front-end
    )
    send_email("CreamCherry: solicitação de atacado recebida!", tpl_atacado_user(d), to=d['email'])
    return jsonify({'success': True}), 201


# ── Admin (proteger com auth em produção) ──
@app.route('/api/admin/contacts')    
def admin_contacts():    return jsonify(contacts)
@app.route('/api/admin/newsletters') 
def admin_newsletters(): return jsonify(newsletters)
@app.route('/api/admin/franquias')   
def admin_franquias():   return jsonify(franquias_list)
@app.route('/api/admin/atacados')    
def admin_atacados():    return jsonify(atacados)


if __name__ == '__main__':
    port  = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG', 'false').lower() == 'true'
    print(f"""
╔══════════════════════════════════════╗
║   CreamCherry Backend — Flask        ║
║   http://localhost:{port}               ║
╚══════════════════════════════════════╝
  SMTP:  {SMTP_HOST}:{SMTP_PORT}
  FROM:  {EMAIL_FROM or '(não configurado)'}
  TO:    {EMAIL_TO}
""")
    app.run(host='0.0.0.0', port=port, debug=debug)
