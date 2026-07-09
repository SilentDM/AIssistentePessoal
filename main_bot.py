from __future__ import print_function
from  datetime import datetime, timedelta, timezone
import os.path
from pathlib import Path
from icalendar import Calendar
import pytz
from google import genai
import os, requests, json, importlib, subprocess, sys, dotenv
dotenv.load_dotenv()
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from dateutil.relativedelta import relativedelta
from google.genai import Client, types
from google.genai.types import GenerateContentConfig, GoogleSearch
import tiktoken
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

sys.stdout.reconfigure(encoding='utf-8',errors="replace")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
client = Client(api_key=GOOGLE_API_KEY)
tools = ["google_search"]
SCOPE = ['https://www.googleapis.com/auth/calendar.readonly']
usuario = os.getenv("FIAP_USER")
senha = os.getenv("FIAP_PASS")



def getFiapURL():
    driver = webdriver.Firefox()
    try:
        driver.get("https://on.fiap.com.br/")
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, "username-plataforma"))).send_keys(usuario)
        driver.find_element(By.ID, "password-plataforma").send_keys(senha)
        driver.find_element(By.CSS_SELECTOR,"loginbtn-plataforma").click()
        driver.get("https://on.fiap.com.br/local/calendarioaluno/")
        link = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, "//a[contains(@href,'export.php')]")))
        url_export = link.get_attribute("href")
        return url_export
    except Exception as e:
        print("\n--- ERRO DETECTADO ---")
        print(f"Tipo do Erro: {type(e).__name__}")
        print(f"Mensagem: {e}")
        return "Desculpe, tive um problema ao processar seu calendário da Fiap."
    finally:
        driver.quit()

def pegar_eventos_google():
    ##### Vamos criar o arquivo eventos.txt com os eventos do Google Calendar #####
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPE)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'client_secret_254663984504-e1q46mmhq0fu3arno08fp87figch8012.apps.googleusercontent.com.json', SCOPE)
            creds = flow.run_local_server(port=0)

        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    service = build('calendar', 'v3', credentials=creds)

    time_min = datetime.now().isoformat() + 'Z'
    ender = (datetime.now() + timedelta(days=30)).isoformat() + 'Z'


    events_result = service.events().list(
        calendarId='primary',
        timeMin=time_min,
        maxResults=100,
        timeMax=ender,
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    if os.path.exists('events.txt'):
        os.remove('events.txt')

    events = events_result.get('items', [])

    with open('events.txt', 'w+', encoding='Latin1') as f:
        f.write("=== Eventos do dia ===\n")
        if not events:
            f.write("Nenhum evento encontrado!")
            print('Nenhum evento encontrado.')
            return
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            line = f"{start} {event['summary']}:{event.get('description', 'Nenhuma descrição disponível')} \n"
            f.write(line)
            #print(start, event['summary'])
        f.seek(0)
        eventos_final=f.read()
    return eventos_final

def coletarCalendarioFIAP():
    pasta_destino = Path("E:\Programacao\GitHub\AIssistentePessoal")
    
    ICS_PATH = pasta_destino / "icalexport.ics"

    URL_EXPORT = (        
                "https://on.fiap.com.br/local/calendarioaluno/export.php"
                "?username=rm571240"
                "&authtoken=befb824594ea126960cca7ea940c7aeea493e835"
    )
    #URL_EXPORT = getFiapURL()
    

    response = requests.get(URL_EXPORT, timeout=30)
    response.raise_for_status()
    ICS_PATH.write_bytes(response.content)


    with open(ICS_PATH, "rb") as f:
        calendario = Calendar.from_ical(f.read())

    tz = pytz.timezone("America/Sao_Paulo")

    agora = datetime.now(tz)
    limite = agora + timedelta(days=7)

    eventos = []
    
    for component in calendario.walk():

        if component.name != "VEVENT":
            continue

        dtstart = component.get("DTSTART").dt

        if isinstance(dtstart, datetime):

            if dtstart.tzinfo is None:
                dtstart = tz.localize(dtstart)
            else:
                dtstart = dtstart.astimezone(tz)

        else:
            dtstart = tz.localize(
                datetime.combine(dtstart, datetime.min.time())
            )

        if agora <= dtstart <= limite:

            titulo = str(component.get("SUMMARY", ""))

            descricao = str(
                component.get("DESCRIPTION", "")
            )

            local = str(
                component.get("LOCATION", "")
            )

            eventos.append({
                "inicio": dtstart,
                "titulo": titulo,
                "descricao": descricao,
                "local": local
            })

    eventos.sort(key=lambda e: e["inicio"])

    texto = "Agenda FIAP - Próximos 7 dias\n\n"

    for evento in eventos:

        texto += (
            f"Data: {evento['inicio'].strftime('%d/%m/%Y %H:%M')}\n"
            f"Título: {evento['titulo']}\n"
            f"Local: {evento['local']}\n"
            f"Descrição: {evento['descricao']}\n"
            "-------------------------\n"
        )

    arquivo_saida = (
        pasta_destino / "agenda_fiap_proximos_7_dias.txt"
    )

    arquivo_saida.write_text(
        texto,
        encoding="utf-8"
    )

    return texto

def gerar_resposta_genai(prompt, eventosg, eventosf):
    agora = datetime.now()
    contexto_tempo = f"""
    DATA Atual: {agora.strftime('%d/%m/%Y')}
    HORA Atual: {agora.strftime('%H:%M')}
    Dia da semana: {agora.strftime('%A')}
    """
    
    instrucao_sistema = f"""
    Você é uma assistente chamada tIA, simpática, organizada e direta.
    Sua tarefa é ajudar o usuário com respostas claras e quando precisar, se basear na agenda dele.
    A data e hora de referência são as seguintes:
    {contexto_tempo}
    
    IMPORTANTE:
    - Considere que a data atual é exatamente a informada acima.
    - Se o usuário perguntar sobre "hoje", use a data acima.
    - Eventos do usuário na pasta google: {eventosg}\n
    - Eventos do usuário da faculdade: {eventosf}
    """

    corpo_usuario = f"{prompt}\n Por favor, responda de forma carinhosa, mas objetiva."

    # Configuração correta na nova SDK
    config = types.GenerateContentConfig(
        system_instruction=instrucao_sistema,
        temperature=0.5,
        top_p=0.9,
        max_output_tokens=320,
        # Habilita a pesquisa Google
        tools=[types.Tool(google_search=types.GoogleSearch())]
    )

    try:
        # Nota: Use "gemini-2.0-flash" (a versão 2.5 não existe ainda)
        response = client.models.generate_content(
            model="gemini-1.5-flash", 
            contents=corpo_usuario, 
            config=config
        )
        
        # Na nova SDK, acessamos o texto assim:
        return response.text
        
    except Exception as e:
        print("\n--- ERRO DETECTADO ---")
        print(f"Tipo do Erro: {type(e).__name__}")
        print(f"Mensagem: {e}")
        return "Desculpe, tive um problema ao processar sua resposta."


    
def main(prompt):
    try:
        eventosG = pegar_eventos_google()
    except Exception as e:
        print("\n--- ERRO DETECTADO ---")
        print(f"Tipo do Erro: {type(e).__name__}")
        print(f"Mensagem: {e}")
        return "Desculpe, tive um problema ao processar seu calendário google."
    
    try:
        eventosF = coletarCalendarioFIAP()
    except Exception as e:
        print("\n--- ERRO DETECTADO ---")
        print(f"Tipo do Erro: {type(e).__name__}")
        print(f"Mensagem: {e}")
        return "Desculpe, tive um problema ao processar seu calendário da Fiap."
    
    resposta = gerar_resposta_genai(prompt, eventosG, eventosF)
    return resposta
    
    

if __name__ == '__main__':
    prompt = sys.argv[1]
    resposta = main(prompt)
    print(resposta)
    with open("agenda_fiap_proximos_7_dias.txt", "w", encoding="utf-8") as f:
        pass

    
