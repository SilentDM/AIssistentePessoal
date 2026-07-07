from __future__ import print_function
from  datetime import datetime, timedelta, timezone
import os.path
from google import genai
import os, requests, json
import importlib, subprocess, sys
import dotenv
dotenv.load_dotenv()
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from dateutil.relativedelta import relativedelta
from google.genai import Client, types
from google.genai.types import GenerateContentConfig, GoogleSearch
import tiktoken
import google.generativeai as generai

sys.stdout.reconfigure(encoding='utf-8',errors="replace")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
client = Client(api_key=GOOGLE_API_KEY)
generai.configure(api_key=GOOGLE_API_KEY, transport='rest') # transport='rest' ajuda em alguns ambientes
model = generai.GenerativeModel("gemini-2.5-flash")
tools = ["google_search"]

SCOPE = ['https://www.googleapis.com/auth/calendar.readonly']

def pegar_eventos():
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

def gerar_resposta_genai(prompt, eventos):
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
    - Eventos do usuário: {eventos}
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
            model="gemini-2.5-flash", 
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

def gerar_resposta_generai(prompt, eventos):
    # Implement the logic to generate a response based on the prompt and events
    agora = datetime.now()
    contexto_tempo = f"""
    DATA Atual: {agora.strftime('%d/%m/%Y')}\n
    HORA Atual: {agora.strftime('%H:%M')}\n
    Dia da semana: {agora.strftime('%A')}
    """
    instrucao_sistema = f"""
    Você é uma assistente chamada tIA, simpática, organizada e direta.
    Sua tarefa é ajudar o usuário com respostas claras e quando precisar, se basear na agenda dele.
    A data e hora de referência são as seguintes:
    {contexto_tempo}\n
    IMPORTANTE:
    - Considere que a data atual é exatamente a informada acima.
    - Não invente datas.
    - Não assuma datas diferentes.
    - Se o usuário perguntar sobre "hoje", use a data acima.
    - Se perguntar sobre "amanhã", considere o dia seguinte à data acima.

    Eventos do usuário:
    {eventos}
    """

    corpo_usuario = f"{prompt}\n Por favor, responda de forma carinhosa, mas objetiva com base nos eventos listados acima."
    generation_config = {
        "temperature": 0.5,
        "top_p": 0.9,
        "max_output_tokens": 320 # Equivalente ao seu max_length        
    }
    model = generai.GenerativeModel(
        model_name="gemini-2.5-flash",
        system_instruction=instrucao_sistema,
        generation_config=generation_config,
        tools=tools
    )
    try:
        response = model.generate_content(corpo_usuario, generation_config=generation_config)
        return response.output_text
    except Exception as e:
        print("\n--- ERRO DETECTADO ---")
        print(f"Tipo do Erro: {type(e).__name__}")
        print(f"Mensagem:{e}")
    
def main(prompt):
    eventos = pegar_eventos()
    #resposta = gerar_resposta_generai(prompt, eventos)
    resposta = gerar_resposta_genai(prompt, eventos)
    return resposta
    
    

if __name__ == '__main__':
    prompt = sys.argv[1]
    resposta = main(prompt)
    print(resposta)

    
