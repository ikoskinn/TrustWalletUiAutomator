import configparser
import re
from typing import Tuple

import PlayerClasses


class Coins:
    List = ("Bitcoin", "Ethereum", "Ravencoin", "Tron", "BNB Beacon Chain", "BNB Smart Chain", "XRP", "Bitcoin Cash",
            "Litecoin", "Polygon", "Polkadot", "Tezos", "Stellar", "Cosmos Hub", "VeChain", "Dash",
            "Zcash", "Arbitrum", "Avalanche C-Chain", "Fantom", "Ethereum Classic", "Ontology", "Dogecoin",
            "Waves", "Theta", "Zilliqa", "Solana", "POA Network", "Aion", "Kin", "NEAR")
    Tokens = ('BTC', 'ETH', 'RVN', 'TRX', 'BNB', 'BNB', 'XRP', 'BCH', 'LTC', 'MATIC', 'DOT', 'VET',
              'XLM', 'ATOM', 'DASH', 'ZEC', 'ARETH', 'AVAX', 'FTM', 'ETC', 'ONTB', 'DOGE', 'WAVES',
              'THETA', 'ZIL', 'SOL', 'POA', 'AION', 'KIN', 'NEAR')

class MultiCoinWallet:
    Id = 0
    Mnemonic = ""
    Imported = 0
    InstanceName = ""
    Adresses = {}

    def __init__(self, tuple: Tuple):
        self.Id = int(tuple[0])
        self.Mnemonic = str(tuple[1])
        self.Imported = int(tuple[2])
        self.InstanceName = str(tuple[3])
        for adr in tuple[4:]:
            if adr != "" and adr is not None:
                self.Adresses[Coins.List[tuple[4:].index(adr)]] = adr

    def __str__(self):
        result = f"ID: {self.Id}; " \
               f"Phrase: {self.Mnemonic}; " \
               f"Imported: {self.Imported}; " \
               f"InstanceName: {self.InstanceName};\nADRESSES: "
        for key, value in self.Adresses:
            result += f"{key}:{value}"
        return result

    def getProperty(self, prop: str):
        if prop.lower() == "id":
            return self.Id
        elif prop.lower() == "mnemonic":
            return self.Mnemonic
        elif prop.lower() == "imported":
            return self.Imported
        elif prop.lower() == "instancename":
            return self.InstanceName
        elif prop.lower() == "adresses":
            return self.Adresses
        else:
            return self.Adresses.get(prop)

class TrustNotification:
    Title = ''
    Text = ''

    isReceive = False
    ReceiveMinAmount = 0.0
    ReceiveAmount = 0.0
    ReceiveToken = ''
    ReceiveCoin = ''
    ReceiveAdress = ''

    def __init__(self, initstr, config):
        self.Title = re.findall('(?<=android\.title=String \().*?(?=\))', initstr)[0]
        self.Text = re.findall('(?<=android\.text=String \().*?(?=\))', initstr)[0]
        if 'Received: ' in self.Title:
            self.isReceive = True
            self.ReceiveAmount = float(str(self.Title).split(' ')[2])
            self.ReceiveToken = str(self.Title).split(' ')[3]
            try:
                self.ReceiveCoin = Coins.List[Coins.Tokens.index(self.ReceiveToken)]
                self.ReceiveMinAmount = float(config['Coins'][self.ReceiveCoin].split(';')[1])
            except:
                self.ReceiveMinAmount = 0.0

class Notifications:
    List = []
    ReceivedCount = 0

    def __init__(self, notificationsStr, config):
        try:
            if len(self.List) > 0:
                self.List.clear()
        except:
            pass
        results = re.findall('extras={[\w\W]*?com\.wallet\.crypto\.trustapp}\)', notificationsStr)
        for result in results:
            if 'android.title=String' in result:
                r = TrustNotification(result, config)
                self.List.append(r)
                if r.isReceive is True:
                    self.ReceivedCount += 1