"""
Agente de Notícias — Coleta diária automatizada
Fontes: G1, CNN Brasil, Poder360, Agência Brasil, Correio Braziliense, ANBA
Temas: STF, Lula, Congresso, Câmara, Investimentos, Exportações, GDF, Países árabes
Envio: E-mail HTML diário às 07h30 (horário de Brasília)
"""

import anthropic
import smtplib
import os
import re
from datetime import datetime
from zoneinfo import ZoneInfo
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # Em produção (GitHub Actions), as vars já estão no ambiente

# ─────────────────────────────────────────────────────────────
# CONFIGURAÇÃO — edite aqui para personalizar
# ─────────────────────────────────────────────────────────────

SOURCES = [
    "G1 (g1.globo.com)",
    "CNN Brasil (cnnbrasil.com.br)",
    "Poder360 (poder360.com.br)",
    "Agência Brasil (agenciabrasil.ebc.com.br)",
    "Correio Braziliense (correiobraziliense.com.br)",
    "ANBA — Agência de Notícias Brasil-Árabe (anba.com.br)",
]

TOPICS = [
    "STF (Supremo Tribunal Federal)",
    "Presidente Lula",
    "Congresso Nacional",
    "Câmara dos Deputados",
    "Investimentos",
    "Exportações",
    "GDF (Governo do Distrito Federal)",
    "Países árabes",
]

MODEL = "claude-opus-5-5"
MAX_CONTINUACOES = 5  # retomadas após pause_turn (limite de segurança)
FUSO = ZoneInfo("America/Sao_Paulo")


def hoje() -> str:
    """Data de hoje no fuso de Brasília (o runner do GitHub usa UTC)."""
    return datetime.now(FUSO).strftime("%d/%m/%Y")

# ─────────────────────────────────────────────────────────────
# CREDENCIAIS — via variáveis de ambiente (nunca hardcode)
# ─────────────────────────────────────────────────────────────

EMAIL_TO   = os.environ["EMAIL_TO"]
EMAIL_FROM = os.environ["EMAIL_FROM"]
EMAIL_PASS = os.environ["EMAIL_PASS"]
SMTP_HOST  = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT  = int(os.environ.get("SMTP_PORT", "587"))

# ─────────────────────────────────────────────────────────────
# PROMPTS
# ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """Você é um agente especializado em monitoramento e análise de notícias
brasileiras. Sua função é pesquisar, filtrar, organizar e sintetizar informações
jornalísticas de forma objetiva, clara e formal. Nunca inclua opiniões pessoais.
Mantenha sempre o foco informativo e a precisão dos fatos. Produza apenas HTML
limpo e compatível com clientes de e-mail (sem JavaScript, sem CSS externo)."""

def build_user_prompt() -> str:
    today_str = hoje()
    sources_list = "\n".join(f"- {s}" for s in SOURCES)
    topics_list  = "\n".join(f"- {t}" for t in TOPICS)

    return f"""
Data de hoje: {today_str}

FONTES A PESQUISAR (obrigatório buscar em cada uma):
{sources_list}

TEMAS PARA FILTRAR (selecione notícias que abordem ao menos um):
{topics_list}

INSTRUÇÕES:
1. Use a ferramenta de busca para pesquisar notícias de HOJE em cada fonte acima.
2. Para cada fonte, busque com queries como:
   "site:g1.globo.com STF Lula Congresso investimentos hoje"
   "site:cnnbrasil.com.br Câmara exportações GDF hoje"
   (adapte para cada fonte e tema)
3. Selecione as 8 a 12 notícias mais relevantes e recentes.
4. Priorize notícias de hoje — {today_str}.

FORMATO DE SAÍDA — HTML completo para e-mail:

Estruture o HTML assim:

<html>
<body style="font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; color: #333;">

  <h1>Relatório de Notícias — {today_str}</h1>
  <p>Fontes monitoradas: G1, CNN Brasil, Poder360, Agência Brasil, Correio Braziliense, ANBA</p>

  <h2>Resumo em Tabela</h2>
  <table border="1" cellpadding="8" cellspacing="0" style="width:100%; border-collapse:collapse;">
    <thead>
      <tr style="background:#1a5f3c; color:white;">
        <th>Fonte</th><th>Título</th><th>Resumo breve</th>
      </tr>
    </thead>
    <tbody>
      <!-- Uma linha por notícia -->
    </tbody>
  </table>

  <h2>Síntese Detalhada</h2>
  <!-- Para cada notícia: título, fonte, link, 4+ linhas de análise -->

</body>
</html>

REQUISITOS:
- Resumo breve: 2 a 3 linhas por notícia na tabela
- Síntese detalhada: mínimo 4 linhas por notícia, com contexto e possíveis implicações
- Linguagem: clara, objetiva, formal
- Sem opiniões; apenas fatos verificáveis
- HTML compatível com Gmail/Outlook (inline styles, sem JS)

Gere o relatório HTML completo agora.
"""


# ─────────────────────────────────────────────────────────────
# AGENTE — execução com web search
# ─────────────────────────────────────────────────────────────

def extract_html(text: str) -> str:
    """Isola o documento HTML, descartando narração e cercas de código."""
    match = re.search(r"<html.*</html>", text, re.DOTALL | re.IGNORECASE)
    return match.group(0) if match else text.strip()


def run_agent() -> str:
    """Executa o agente Claude com web search e retorna o HTML do relatório."""
    client = anthropic.Anthropic()
    print(f"[{hoje()}] Iniciando coleta de notícias...")

    messages = [{"role": "user", "content": build_user_prompt()}]

    for _ in range(MAX_CONTINUACOES + 1):
        # Streaming evita timeout HTTP em respostas longas com muitas buscas.
        # fallbacks="default": se o modelo recusar por política, a API refaz
        # a requisição em outro modelo automaticamente.
        with client.beta.messages.stream(
            model=MODEL,
            max_tokens=32000,
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            output_config={"effort": "medium"},
            tools=[{"type": "web_search_20260209", "name": "web_search"}],
            system=SYSTEM_PROMPT,
            messages=messages,
        ) as stream:
            response = stream.get_final_message()

        # A busca roda num loop no servidor; ao atingir o limite de iterações
        # ele pausa. Reenvia a resposta parcial para o servidor continuar.
        if response.stop_reason != "pause_turn":
            break
        messages = messages[:1] + [{"role": "assistant", "content": response.content}]
    else:
        raise RuntimeError("Limite de continuações (pause_turn) atingido.")

    if response.stop_reason == "refusal":
        raise RuntimeError(f"O modelo recusou a solicitação: {response.stop_details}")
    if response.stop_reason == "max_tokens":
        print("AVISO: resposta truncada por max_tokens.")

    text = "\n".join(b.text for b in response.content if b.type == "text")
    html_content = extract_html(text)

    if not html_content:
        raise ValueError("O agente não retornou conteúdo HTML. Verifique a API key.")

    print(f"Relatório gerado com sucesso ({len(html_content)} caracteres).")
    return html_content


# ─────────────────────────────────────────────────────────────
# ENVIO DE E-MAIL
# ─────────────────────────────────────────────────────────────

def send_email(html_body: str) -> None:
    """Envia o relatório HTML por e-mail via SMTP."""
    today_str = hoje()
    subject = f"Relatório de Notícias — {today_str}"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = EMAIL_FROM
    msg["To"]      = EMAIL_TO

    # Fallback em texto puro
    text_fallback = (
        f"Relatório de Notícias — {today_str}\n\n"
        "Este e-mail contém um relatório em HTML. "
        "Por favor, abra-o em um cliente que suporte HTML."
    )
    msg.attach(MIMEText(text_fallback, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    print(f"Enviando e-mail para {EMAIL_TO}...")
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.ehlo()
        server.starttls()
        server.login(EMAIL_FROM, EMAIL_PASS)
        server.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())

    print(f"E-mail enviado com sucesso para {EMAIL_TO}.")


# ─────────────────────────────────────────────────────────────
# PONTO DE ENTRADA
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    try:
        html_report = run_agent()
        send_email(html_report)
        print("Agente finalizado com sucesso.")
    except Exception as e:
        print(f"ERRO: {e}")
        raise
