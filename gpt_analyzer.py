import os
import pandas as pd
import requests
import json
from openai import OpenAI
from datetime import datetime

# Chave de API
OPENROUTER_API_KEY = "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"

#Informando quais modelos de IA serão usados
modelos = ["google/gemma-3n-e2b-it:free",
           "mistralai/mistral-7b-instruct:free",
           "cohere/command-r-plus:free"]

HEADERS = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "Content-Type": "applocation/json",
    "HTTP-Referer": "https://zaktrader.local",
    "X-Title": "ZakTrader GPT"
}

def enviar_para_openrouter(contexto, modelo):
    body = {
        "model": modelo,
        "messages":[
            {"role": "user", "content": contexto}
        ]
    }

    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions",
                                 headers=HEADERS, data=json.dumps(body))
        
        if response.status_code == 429:
            print(f"[{modelo}] Limite atingido.")
            return "erro_limite"
        
        if response.status_code != 200:
            print(f"[{modelo}] Erro HTTP {response.status_code}: {response.text}")
            return "erro"
        
        data = response.json()
        if "choices" not in data:
            print(f"[{modelo}] Resposta inesperada:", json.dumps(data, indent=2))
            return "erro"
        
        mensagem = data["choices"][0]["message"]["content"].strip().lower()
        print(f"[{modelo}] Resposta: {mensagem}")
        return mensagem
    
    except Exception as e:
        print(f"[{modelo}] Erro ao conectar:", e)
        return "erro"
    
def analisar_com_openrouter(df: pd.DataFrame, ativo: str):

#resetar o índice
    df = df.reset_index()
    
#Pegando as ultimas 20 linhas com os indicadores calculados
    candles = df.tail(20)[["timestamp", "open", "close", "high", "low", "volume",
                            "EMA9", "EMA20", "EMA50", "RSI", "bb_upper", "bb_lower",
                              "suporte", "resistencia", "padrao_vela"]].to_string(index=False)

#O prompt que será enviado para a IA
    contexto = f"""
    Você é um analista técnico profissional especializado em operações de 1 minuto.

    Abaixo estão os últimos 20 candles do ativo {ativo}, com indicadores técnicos já calculados:
    - Médias Móveis: EMA9, EMA20 e EMA50
    - RSI (14 períodos)
    - Bandas de Bollinger (20 períodos, 2 desvios padrão)
    - Níveis de Suporte e Resistência
    - Padrões de velas (martelo, doji, engolfo, estrela cadente, etc.)

    ### Suas diretrizes de análise são:

    1. **Tendência (Médias Móveis):**
    - EMA20 acima da EMA50 = tendência de alta
    - EMA20 abaixo da EMA50 = tendência de baixa
    - Se EMA20 e EMA50 estiverem muito próximas, considere tendência indefinida

    2. **RSI:**
    - RSI abaixo de 30 = sobrevenda = possível reversão de alta
    - RSI acima de 70 = sobrecompra = possível reversão de baixa

    3. **Bandas de Bollinger:**
    - Preço tocando a banda inferior = possível alta
    - Preço tocando a banda superior = possível queda

    4. **Suporte e Resistência:**
    - Preço próximo ao suporte + padrão de reversão = possível COMPRA
    - Preço próximo à resistência + padrão de reversão = possível VENDA

    5. **Padrão de vela (último candle):**
    - Martelo ou Engolfo de Alta = possível COMPRA
    - Estrela cadente ou Engolfo de Baixa = possível VENDA
    - Doji = sinal de indecisão → NÃO OPERAR

    ### Decisão final:
    Só recomende uma entrada se pelo menos **3 indicadores estiverem alinhados na mesma direção** (por exemplo: tendência + RSI + padrão de vela).

    **Evite operar se:**
    - Os indicadores estiverem em conflito entre si
    - O mercado estiver lateralizado ou sem direção clara
    - Não houver padrão de vela significativo

    ---

    ### Dados recebidos:

    - Últimos 20 candles com indicadores:
    {candles}

    - Últimos valores dos indicadores:
    - EMA9: {df["EMA9"].iloc[-1]:.2f}
    - EMA20: {df["EMA20"].iloc[-1]:.2f}
    - EMA50: {df["EMA50"].iloc[-1]:.2f}
    - RSI: {df["RSI"].iloc[-1]:.2f}
    - Banda Superior (BB): {df["bb_upper"].iloc[-1]:.5f}
    - Banda Inferior (BB): {df["bb_lower"].iloc[-1]:.5f}
    - Suporte: {df["suporte"].iloc[-1]:.5f}
    - Resistência: {df["resistencia"].iloc[-1]:.5f}
    - Padrão de vela identificado: {df["padrao_vela"].iloc[-1]}

    ---

    ### Responda APENAS com uma das palavras abaixo, sem explicações:
    - **compra**
    - **venda**
    - **não operar**
    """

#Realiza a troca da IA quando o limite de chamadas da IA atual é atingido
    for modelo in modelos:
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] tentando com: {modelo}")
        resposta = enviar_para_openrouter(contexto, modelo)
        if resposta not in ["erro", "erro_limite"]:
            return resposta
        
    return "erro"



# Teste
if __name__ == "__main__":
    import data_collector
    from iq_interface import IQBot
    import time
    
    email = "zarkwolff.trade@gmail.com"
    senha = "@RivDfe7B@Lp#3"
    bot = IQBot(email, senha)
    bot.change_balance_mode("PRACTICE")

    ativo = input("Em qual ativo irá operar? ")

    tempo_espera = 60
    contador = 1
    tempo_previsto = 10

    while contador <= tempo_previsto:
        candles = bot.get_candles(ativo, 60,35) # 35 candles de 1 minuto

        dados = data_collector.process_candles(candles)
        df = pd.DataFrame(dados)
        direcao = analisar_com_openrouter(df, ativo)
        
        contador += 1
        time.sleep(tempo_espera)
