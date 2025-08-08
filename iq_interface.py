import time

#Verifica se a Api iqpotionapi está instalada
try:
    from iqoptionapi.stable_api import IQ_Option
except ModuleNotFoundError:
    print("Erro: Módulo 'iqoptionapi' não encontrado. \nInstale com: pip install iqoptionapi")
    exit(1)

class IQBot:
    def __init__(self, email, password):
        self.IQ = IQ_Option(email, password)
        self.IQ.connect()
        while not self.IQ.check_connect():
            print("Conectando...")
            time.sleep(1)
        print("Conectado com sucesso!")
    
    def change_balance_mode(self, mode="PRACTICE"):
        # mode pode ser "REAL" ou "PRACTICE"
        if mode.upper() in ["REAL", "PRACTICE"]:
            self.IQ.change_balance(mode.upper())
            print(f"Modo de conta alterado para: {mode.upper()}")
        else:
            print("modo inválido. Use 'REAL' ou 'PRACTICE'.")

    def get_balance(self):
        return self.IQ.get_balance()
    
    def get_candles(self, asset, interval, count):
        candles = self.IQ.get_candles(asset, interval, count, time.time())
        return candles
    
    def make_operation(self, asset, amount, direction, duration):
        status, id = self.IQ.buy(amount, asset, direction, duration)
        return status, id
    
if __name__ == "__main__":
    email = "SEU_EMAIL"
    senha = "SUA_SENHA"
    bot = IQBot(email, senha)

    #Menu para selecionar o tipo de conta
    modo = input("Selecione o modo de conta (REAL, ou PRACTICE):").strip().upper()
    bot.change_balance_mode(modo)

    #Mostra o Saldo
    print("Saldo atual:", bot.get_balance())

    #Mostra as candles recentes
    ativo = input("Digite o ativo (ex: EURUSD): ").strip().upper()
    candles = bot.get_candles(ativo, 60, 5)
    print(f"\nÚltimos candles de 1 minuto ({ativo}):")
    for candle in candles:
        print(candle)