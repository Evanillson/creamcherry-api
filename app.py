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
<title>CreamCherry</title>
</head>
<body style="margin:0;padding:0;background:#F6F6F6;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#F6F6F6;padding:40px 0">
<tr><td align="center">
<table width="560" cellpadding="0" cellspacing="0" style="max-width:560px;width:100%">

  <!-- Logo -->
  <tr><td style="padding:0 0 24px;text-align:center">
    <span style="font-size:13px;font-weight:700;color:#C8102E;letter-spacing:.08em;text-transform:uppercase">🍒 CREAMCHERRY SOBREMESAS</span>
  </td></tr>

  <!-- Card -->
  <tr><td style="background:#FFFFFF;border-radius:12px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.08)">

    <!-- Red top bar -->
    <table width="100%" cellpadding="0" cellspacing="0">
    <tr><td style="background:#C8102E;height:4px;font-size:0">&nbsp;</td></tr>
    </table>

    <!-- Content -->
    <table width="100%" cellpadding="0" cellspacing="0">
    <tr><td style="padding:36px 40px 32px">
      {content}
    </td></tr>
    </table>

    <!-- Footer inside card -->
    <table width="100%" cellpadding="0" cellspacing="0">
    <tr><td style="background:#FAFAFA;border-top:1px solid #F0F0F0;padding:20px 40px;text-align:center">
      <p style="margin:0 0 4px;font-size:13px;font-weight:600;color:#18181B">CreamCherry Sobremesas</p>
      <p style="margin:0;font-size:12px;color:#A1A1AA;line-height:1.6">
        Sorvetes &amp; Gelattos Artesanais · São Paulo, SP<br>
        <a href="mailto:{email_to}" style="color:#C8102E;text-decoration:none">{email_to}</a> &nbsp;·&nbsp; (11) 98958-2586
      </p>
      <p style="margin:12px 0 0;font-size:11px;color:#D4D4D8">© 2026 CreamCherry Sobremesas LTDA. Todos os direitos reservados.</p>
    </td></tr>
    </table>

  </td></tr>

</table>
</td></tr>
</table>
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
<p style="margin:0 0 4px;font-size:11px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#C8102E">Formulário de Contato</p>
<h1 style="margin:0 0 4px;font-size:26px;font-weight:700;color:#18181B;line-height:1.2">Nova mensagem via site</h1>
<p style="margin:0 0 28px;font-size:13px;color:#A1A1AA">Recebida em {now_fmt()}</p>

<p style="margin:0 0 10px;font-size:10px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:#A1A1AA">Dados do remetente</p>
<table width="100%" cellpadding="0" cellspacing="0" style="border:1px solid #F0F0F0;border-radius:8px;overflow:hidden;margin-bottom:24px">
  <tr>
    <td width="50%" style="padding:14px 16px;border-right:1px solid #F0F0F0;border-bottom:1px solid #F0F0F0;vertical-align:top">
      <p style="margin:0 0 3px;font-size:10px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:#A1A1AA">Nome</p>
      <p style="margin:0;font-size:14px;color:#18181B;font-weight:500">{d['name']}</p>
    </td>
    <td width="50%" style="padding:14px 16px;border-bottom:1px solid #F0F0F0;vertical-align:top">
      <p style="margin:0 0 3px;font-size:10px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:#A1A1AA">E-mail</p>
      <p style="margin:0;font-size:14px;color:#18181B;font-weight:500">{d['email']}</p>
    </td>
  </tr>
  <tr>
    <td colspan="2" style="padding:14px 16px;vertical-align:top">
      <p style="margin:0 0 3px;font-size:10px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:#A1A1AA">Assunto</p>
      <p style="margin:0;font-size:14px;color:#18181B;font-weight:500">{d['subject']}</p>
    </td>
  </tr>
</table>

<p style="margin:0 0 10px;font-size:10px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:#A1A1AA">Mensagem</p>
<div style="background:#FAFAFA;border:1px solid #F0F0F0;border-radius:8px;padding:16px;font-size:14px;color:#3F3F46;line-height:1.8;margin-bottom:28px">{d['message']}</div>

<table cellpadding="0" cellspacing="0"><tr><td style="background:#C8102E;border-radius:8px">
  <a href="mailto:{d['email']}" style="display:inline-block;padding:14px 32px;font-size:14px;font-weight:600;color:#FFFFFF;text-decoration:none;letter-spacing:.01em">Responder agora →</a>
</td></tr></table>
""")


def tpl_contato_user(d):
    return _wrap(f"""
<p style="margin:0 0 4px;font-size:11px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#C8102E">Confirmação</p>
<h1 style="margin:0 0 4px;font-size:26px;font-weight:700;color:#18181B;line-height:1.2">Recebemos sua mensagem!</h1>
<p style="margin:0 0 24px;font-size:13px;color:#A1A1AA">{now_fmt()}</p>

<p style="margin:0 0 8px;font-size:16px;font-weight:600;color:#18181B">Olá, {d['name'].split()[0]}!</p>
<p style="margin:0 0 28px;font-size:14px;color:#71717A;line-height:1.8">Sua mensagem foi recebida com sucesso. Nossa equipe responderá em breve. Para retorno urgente, fale pelo WhatsApp.</p>

<table width="100%" cellpadding="0" cellspacing="0" style="border:1px solid #F0F0F0;border-radius:8px;overflow:hidden;margin-bottom:28px">
  <tr>
    <td width="50%" style="padding:14px 16px;border-right:1px solid #F0F0F0;vertical-align:top">
      <p style="margin:0 0 3px;font-size:10px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:#A1A1AA">Assunto</p>
      <p style="margin:0;font-size:14px;color:#18181B;font-weight:500">{d['subject']}</p>
    </td>
    <td width="50%" style="padding:14px 16px;vertical-align:top">
      <p style="margin:0 0 3px;font-size:10px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:#A1A1AA">Protocolo</p>
      <p style="margin:0;font-size:14px;color:#18181B;font-weight:500">#{datetime.now().strftime('%Y%m%d%H%M')}</p>
    </td>
  </tr>
</table>

<table cellpadding="0" cellspacing="0"><tr><td style="background:#C8102E;border-radius:8px">
  <a href="https://wa.me/5511989582586" style="display:inline-block;padding:14px 32px;font-size:14px;font-weight:600;color:#FFFFFF;text-decoration:none">💬 Falar pelo WhatsApp</a>
</td></tr></table>
""")


def tpl_newsletter_user(email):
    return _wrap(f"""
<p style="margin:0 0 4px;font-size:11px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#C8102E">Newsletter</p>
<h1 style="margin:0 0 4px;font-size:26px;font-weight:700;color:#18181B;line-height:1.2">Nova inscrição recebida!</h1>
<p style="margin:0 0 28px;font-size:13px;color:#A1A1AA">{now_fmt()}</p>

<p style="margin:0 0 10px;font-size:10px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:#A1A1AA">E-mail cadastrado</p>
<table width="100%" cellpadding="0" cellspacing="0" style="border:1px solid #F0F0F0;border-radius:8px;overflow:hidden;margin-bottom:28px">
  <tr>
    <td style="padding:16px;vertical-align:top">
      <p style="margin:0 0 3px;font-size:10px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:#A1A1AA">E-mail do cliente</p>
      <p style="margin:0;font-size:15px;color:#18181B;font-weight:600">{email}</p>
    </td>
  </tr>
</table>

<p style="margin:0 0 28px;font-size:14px;color:#71717A;line-height:1.8">Um novo cliente se inscreveu para receber novidades da CreamCherry.</p>

<table cellpadding="0" cellspacing="0"><tr><td style="background:#C8102E;border-radius:8px">
  <a href="mailto:{email}" style="display:inline-block;padding:14px 32px;font-size:14px;font-weight:600;color:#FFFFFF;text-decoration:none">Enviar e-mail ao cliente →</a>
</td></tr></table>
""")


def tpl_franquia_team(d):
    return _wrap(f"""
<p style="margin:0 0 4px;font-size:11px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#C8102E">Proposta de Franquia</p>
<h1 style="margin:0 0 4px;font-size:26px;font-weight:700;color:#18181B;line-height:1.2">Novo interesse em franquia</h1>
<p style="margin:0 0 28px;font-size:13px;color:#A1A1AA">Recebido em {now_fmt()}</p>

<p style="margin:0 0 10px;font-size:10px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:#A1A1AA">Dados do interessado</p>
<table width="100%" cellpadding="0" cellspacing="0" style="border:1px solid #F0F0F0;border-radius:8px;overflow:hidden;margin-bottom:24px">
  <tr>
    <td width="50%" style="padding:14px 16px;border-right:1px solid #F0F0F0;border-bottom:1px solid #F0F0F0;vertical-align:top">
      <p style="margin:0 0 3px;font-size:10px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:#A1A1AA">Nome</p>
      <p style="margin:0;font-size:14px;color:#18181B;font-weight:500">{d['fName']}</p>
    </td>
    <td width="50%" style="padding:14px 16px;border-bottom:1px solid #F0F0F0;vertical-align:top">
      <p style="margin:0 0 3px;font-size:10px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:#A1A1AA">E-mail</p>
      <p style="margin:0;font-size:14px;color:#18181B;font-weight:500">{d['fEmail']}</p>
    </td>
  </tr>
  <tr>
    <td width="50%" style="padding:14px 16px;border-right:1px solid #F0F0F0;border-bottom:1px solid #F0F0F0;vertical-align:top">
      <p style="margin:0 0 3px;font-size:10px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:#A1A1AA">Telefone</p>
      <p style="margin:0;font-size:14px;color:#18181B;font-weight:500">{d['fPhone']}</p>
    </td>
    <td width="50%" style="padding:14px 16px;border-bottom:1px solid #F0F0F0;vertical-align:top">
      <p style="margin:0 0 3px;font-size:10px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:#A1A1AA">Cidade / Estado</p>
      <p style="margin:0;font-size:14px;color:#18181B;font-weight:500">{d['fCity']}</p>
    </td>
  </tr>
  <tr>
    <td colspan="2" style="padding:14px 16px;vertical-align:top">
      <p style="margin:0 0 3px;font-size:10px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:#A1A1AA">Capital disponível</p>
      <p style="margin:0;font-size:14px;color:#18181B;font-weight:500">{d['fCapital']}</p>
    </td>
  </tr>
</table>

<p style="margin:0 0 10px;font-size:10px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:#A1A1AA">Mensagem</p>
<div style="background:#FAFAFA;border:1px solid #F0F0F0;border-radius:8px;padding:16px;font-size:14px;color:#3F3F46;line-height:1.8;margin-bottom:28px">{d['fMessage']}</div>

<table cellpadding="0" cellspacing="0"><tr><td style="background:#C8102E;border-radius:8px">
  <a href="mailto:{d['fEmail']}" style="display:inline-block;padding:14px 32px;font-size:14px;font-weight:600;color:#FFFFFF;text-decoration:none">Entrar em contato →</a>
</td></tr></table>
""")


def tpl_franquia_user(d):
    return _wrap(f"""
<p style="margin:0 0 4px;font-size:11px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#C8102E">Franquias CreamCherry</p>
<h1 style="margin:0 0 4px;font-size:26px;font-weight:700;color:#18181B;line-height:1.2">Proposta recebida!</h1>
<p style="margin:0 0 24px;font-size:13px;color:#A1A1AA">{now_fmt()}</p>

<p style="margin:0 0 8px;font-size:16px;font-weight:600;color:#18181B">Olá, {d['fName'].split()[0]}!</p>
<p style="margin:0 0 28px;font-size:14px;color:#71717A;line-height:1.8">Recebemos sua proposta de franquia. Nossa equipe analisará seu perfil e entrará em contato em até <strong style="color:#18181B">48 horas úteis</strong>.</p>

<table width="100%" cellpadding="0" cellspacing="0" style="border:1px solid #F0F0F0;border-radius:8px;overflow:hidden;margin-bottom:24px">
  <tr>
    <td width="50%" style="padding:14px 16px;border-right:1px solid #F0F0F0;vertical-align:top">
      <p style="margin:0 0 3px;font-size:10px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:#A1A1AA">Cidade de interesse</p>
      <p style="margin:0;font-size:14px;color:#18181B;font-weight:500">{d['fCity']}</p>
    </td>
    <td width="50%" style="padding:14px 16px;vertical-align:top">
      <p style="margin:0 0 3px;font-size:10px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:#A1A1AA">Capital declarado</p>
      <p style="margin:0;font-size:14px;color:#18181B;font-weight:500">{d['fCapital']}</p>
    </td>
  </tr>
</table>

<div style="background:#FFFBEB;border:1px solid #FDE68A;border-radius:8px;padding:14px 16px;font-size:13px;color:#92400E;line-height:1.7;margin-bottom:28px">
  💡 Prepare informações sobre o ponto comercial desejado e seu histórico profissional para nossa conversa.
</div>

<table cellpadding="0" cellspacing="0"><tr><td style="background:#C8102E;border-radius:8px">
  <a href="https://wa.me/5511989582586" style="display:inline-block;padding:14px 32px;font-size:14px;font-weight:600;color:#FFFFFF;text-decoration:none">💬 Falar pelo WhatsApp</a>
</td></tr></table>
""")


def tpl_atacado_team(d):
    raw_prods = d.get('produtos', [])
    prods = []
    for p in raw_prods:
        if isinstance(p, dict):
            prods.append({{'produto': p.get('produto') or p.get('name') or str(p), 'quantidade': int(p.get('quantidade') or p.get('qty') or 0)}})
        else:
            prods.append({{'produto': str(p), 'quantidade': 0}})
    rows = ''.join(f"""<tr>
      <td style="padding:12px 16px;border-bottom:1px solid #F9F9F9;color:#3F3F46;font-size:14px">{p['produto']}</td>
      <td style="padding:12px 16px;border-bottom:1px solid #F9F9F9;color:#3F3F46;font-size:14px;text-align:center;font-weight:600">{p['quantidade']} un.</td>
    </tr>""" for p in prods)
    total = sum(p['quantidade'] for p in prods)
    obs_block = f"""<p style="margin:0 0 10px;font-size:10px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:#A1A1AA">Observações</p>
<div style="background:#FAFAFA;border:1px solid #F0F0F0;border-radius:8px;padding:16px;font-size:14px;color:#3F3F46;line-height:1.8;margin-bottom:24px">{d['obs']}</div>""" if d.get('obs') else ''
    return _wrap(f"""
<p style="margin:0 0 4px;font-size:11px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#C8102E">Pedido Atacado</p>
<h1 style="margin:0 0 4px;font-size:26px;font-weight:700;color:#18181B;line-height:1.2">Nova solicitação de encomenda</h1>
<p style="margin:0 0 28px;font-size:13px;color:#A1A1AA">Recebida em {now_fmt()}</p>

<p style="margin:0 0 10px;font-size:10px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:#A1A1AA">Dados do solicitante</p>
<table width="100%" cellpadding="0" cellspacing="0" style="border:1px solid #F0F0F0;border-radius:8px;overflow:hidden;margin-bottom:24px">
  <tr>
    <td width="50%" style="padding:14px 16px;border-right:1px solid #F0F0F0;border-bottom:1px solid #F0F0F0;vertical-align:top">
      <p style="margin:0 0 3px;font-size:10px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:#A1A1AA">Nome</p>
      <p style="margin:0;font-size:14px;color:#18181B;font-weight:500">{d['nome']}</p>
    </td>
    <td width="50%" style="padding:14px 16px;border-bottom:1px solid #F0F0F0;vertical-align:top">
      <p style="margin:0 0 3px;font-size:10px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:#A1A1AA">Perfil</p>
      <p style="margin:0;font-size:14px;color:#18181B;font-weight:500">{d['perfil']}</p>
    </td>
  </tr>
  <tr>
    <td width="50%" style="padding:14px 16px;border-right:1px solid #F0F0F0;vertical-align:top">
      <p style="margin:0 0 3px;font-size:10px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:#A1A1AA">E-mail</p>
      <p style="margin:0;font-size:14px;color:#18181B;font-weight:500">{d['email']}</p>
    </td>
    <td width="50%" style="padding:14px 16px;vertical-align:top">
      <p style="margin:0 0 3px;font-size:10px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:#A1A1AA">Telefone</p>
      <p style="margin:0;font-size:14px;color:#18181B;font-weight:500">{d['telefone']}</p>
    </td>
  </tr>
</table>

<p style="margin:0 0 10px;font-size:10px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:#A1A1AA">Endereço de entrega</p>
<table width="100%" cellpadding="0" cellspacing="0" style="border:1px solid #F0F0F0;border-radius:8px;overflow:hidden;margin-bottom:24px">
  <tr>
    <td style="padding:14px 16px;border-bottom:1px solid #F0F0F0;vertical-align:top">
      <p style="margin:0 0 3px;font-size:10px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:#A1A1AA">Endereço</p>
      <p style="margin:0;font-size:14px;color:#18181B;font-weight:500">{d['logradouro']}, {d['numero']} {d.get('complemento','')} — {d['bairro']}</p>
    </td>
  </tr>
  <tr>
    <td width="50%" style="padding:14px 16px;vertical-align:top">
      <p style="margin:0 0 3px;font-size:10px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:#A1A1AA">Cidade / CEP</p>
      <p style="margin:0;font-size:14px;color:#18181B;font-weight:500">{d['cidade']} — {d['cep']}</p>
    </td>
  </tr>
</table>

<p style="margin:0 0 10px;font-size:10px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:#A1A1AA">Produtos solicitados</p>
<table width="100%" cellpadding="0" cellspacing="0" style="border:1px solid #F0F0F0;border-radius:8px;overflow:hidden;margin-bottom:24px">
  <tr style="background:#18181B">
    <th style="padding:10px 16px;text-align:left;font-size:10px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#FFFFFF">Produto</th>
    <th style="padding:10px 16px;text-align:center;font-size:10px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#FFFFFF">Qtd.</th>
  </tr>
  {rows}
  <tr style="background:#FFF5F5">
    <td style="padding:12px 16px;font-size:14px;font-weight:700;color:#C8102E">Total</td>
    <td style="padding:12px 16px;font-size:14px;font-weight:700;color:#C8102E;text-align:center">{total} un.</td>
  </tr>
</table>

{obs_block}

<table cellpadding="0" cellspacing="0"><tr><td style="background:#C8102E;border-radius:8px">
  <a href="mailto:{d['email']}" style="display:inline-block;padding:14px 32px;font-size:14px;font-weight:600;color:#FFFFFF;text-decoration:none">Responder ao cliente →</a>
</td></tr></table>
""")


def tpl_atacado_user(d):
    raw_prods2 = d.get('produtos', [])
    prods2 = [{{'produto': p.get('produto') or str(p), 'quantidade': int(p.get('quantidade') or 0)}} if isinstance(p, dict) else {{'produto': str(p), 'quantidade': 0}} for p in raw_prods2]
    rows = ''.join(f"""<tr>
      <td style="padding:12px 16px;border-bottom:1px solid #F9F9F9;color:#3F3F46;font-size:14px">{p['produto']}</td>
      <td style="padding:12px 16px;border-bottom:1px solid #F9F9F9;color:#3F3F46;font-size:14px;text-align:center">{p['quantidade']} un.</td>
    </tr>""" for p in prods2)
    return _wrap(f"""
<p style="margin:0 0 4px;font-size:11px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#C8102E">Atacado &amp; Encomendas</p>
<h1 style="margin:0 0 4px;font-size:26px;font-weight:700;color:#18181B;line-height:1.2">Solicitação recebida!</h1>
<p style="margin:0 0 24px;font-size:13px;color:#A1A1AA">{now_fmt()}</p>

<p style="margin:0 0 8px;font-size:16px;font-weight:600;color:#18181B">Olá, {d['nome'].split()[0]}!</p>
<p style="margin:0 0 28px;font-size:14px;color:#71717A;line-height:1.8">Recebemos sua solicitação de encomenda. Nossa equipe retornará em até <strong style="color:#18181B">24 horas úteis</strong> com orçamento e confirmação.</p>

<p style="margin:0 0 10px;font-size:10px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:#A1A1AA">Resumo do pedido</p>
<table width="100%" cellpadding="0" cellspacing="0" style="border:1px solid #F0F0F0;border-radius:8px;overflow:hidden;margin-bottom:24px">
  <tr style="background:#18181B">
    <th style="padding:10px 16px;text-align:left;font-size:10px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#FFFFFF">Produto</th>
    <th style="padding:10px 16px;text-align:center;font-size:10px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#FFFFFF">Qtd.</th>
  </tr>
  {rows}
</table>

<table width="100%" cellpadding="0" cellspacing="0" style="border:1px solid #F0F0F0;border-radius:8px;overflow:hidden;margin-bottom:24px">
  <tr>
    <td width="50%" style="padding:14px 16px;border-right:1px solid #F0F0F0;vertical-align:top">
      <p style="margin:0 0 3px;font-size:10px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:#A1A1AA">Entrega em</p>
      <p style="margin:0;font-size:14px;color:#18181B;font-weight:500">{d['cidade']}</p>
    </td>
    <td width="50%" style="padding:14px 16px;vertical-align:top">
      <p style="margin:0 0 3px;font-size:10px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:#A1A1AA">Protocolo</p>
      <p style="margin:0;font-size:14px;color:#18181B;font-weight:500">#{datetime.now().strftime('%Y%m%d%H%M')}</p>
    </td>
  </tr>
</table>

<div style="background:#FFFBEB;border:1px solid #FDE68A;border-radius:8px;padding:14px 16px;font-size:13px;color:#92400E;line-height:1.7;margin-bottom:28px">
  ⏱️ <strong>Prazo de produção:</strong> 3 a 5 dias úteis após confirmação e pagamento.
</div>

<table cellpadding="0" cellspacing="0"><tr><td style="background:#C8102E;border-radius:8px">
  <a href="https://wa.me/5511989582586" style="display:inline-block;padding:14px 32px;font-size:14px;font-weight:600;color:#FFFFFF;text-decoration:none">💬 Acompanhar pelo WhatsApp</a>
</td></tr></table>
""")


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
