import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator
from ta.volatility import BollingerBands


def detectar_padroes(df):
    """
    Detecta padrões b´pasicos de velas no Dataframe.
    """
    padroes = []

    for i in range(1, len(df)):
        candle_atual = df.iloc[i]
        candle_anterior = df.iloc[i - 1]

        corpo = abs(candle_atual['close'] - candle_atual['open'])
        sombra_superior = candle_atual['high'] - max(candle_atual['close'], candle_atual['open'])
        sombra_inferior = min(candle_atual['close'], candle_atual['open']) - candle_atual['low']

        # Martelo
        if corpo < sombra_inferior and sombra_superior < corpo:
            padroes.append('martelo')

        # Doji
        elif corpo < (candle_atual['high'] - candle_atual['low']) * 0.1:
            padroes.append('doji')
        
        # Engolfo de alta
        elif (candle_anterior['close'] < candle_anterior['open'] and
              candle_atual['close'] > candle_atual['open'] and
              candle_atual['close'] > candle_anterior['open'] and
              candle_atual['open'] < candle_anterior['close']):
            padroes.append('engolfo_alta')
        
        # Engolfo de baixa
        elif (candle_anterior['close'] > candle_anterior['open'] and
              candle_atual['close'] < candle_atual['open'] and
              candle_atual['open'] > candle_anterior['close'] and
              candle_atual['close'] < candle_anterior['open']):
            padroes.append('engolfo_baixa')
        else:
            padroes.append('nenhum')

    padroes.insert(0, 'nenhum') # Primeiro candle não comparação
    df['padrao_vela'] = padroes
    return df

def process_candles(candles, suporte_resistencia_periodo=20):
    """
    Transforma a lista de candles do IQ Option em um DataFrame e calcula indicadores técnicos.
    """
    df = pd.DataFrame(candles)
    df = df.rename(columns={
        'open': 'open',
        'close': 'close',
        'max': 'high',
        'min': 'low',
        'volume': 'volume',
        'from': 'timestamp'
    })
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
    df.set_index('timestamp', inplace=True)
    df = df[['open', 'high', 'low', 'close', 'volume']]

    #criação dos indicadores técnicos
    df['RSI'] = RSIIndicator(close=df['close'], window=14).rsi()
    df['EMA9'] = EMAIndicator(close=df['close'], window=9).ema_indicator()
    df['EMA20'] = EMAIndicator(close=df['close'], window=20).ema_indicator()
    df['EMA50'] = EMAIndicator(close=df['close'], window=50).ema_indicator()

    # Bandas de Bollinger
    bb = BollingerBands(close=df['close'], window=20, window_dev=2)
    df['bb_upper'] = bb.bollinger_hband()
    df['bb_lower'] = bb.bollinger_hband()
    df['bb_percent'] = bb.bollinger_hband()

    #configurando o suporte e resistência:
    # Suporte = menor mínima recente 
    # Resistência = maior máxima recente

    df['suporte'] = df['low'].rolling(window=suporte_resistencia_periodo).min()
    df["resistencia"] = df['high'].rolling(window=suporte_resistencia_periodo).max()

    # Padrões de velas
    df = detectar_padroes(df)

    return df

#Exemplo de uso isolado (para teste):
if __name__ == "__main__":
    from iq_interface import IQBot

    email = "zarkwolff.trade@gmail.com"
    senha = "@RivDfe7B@Lp#3"
    bot = IQBot(email, senha)
    bot.change_balance_mode("PRACTICE")

    ativo = "EURUSD"
    candles = bot.get_candles(ativo, 60,100) # 100 candles de 1 minuto

    df = process_candles(candles)
    print(df.tail(20)) # Mostra os últimos 10 candles com indicadores