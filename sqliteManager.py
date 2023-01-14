import sqlite3
import threading
import time

import Classes

lock = threading.Lock()
lockget = threading.Lock()
lockCount = threading.Lock()

class SQLite:
    con = None
    cur = None

    def __init__(self, dbName):
        self.con = sqlite3.connect(f'{dbName}.db', check_same_thread=False)
        self.cur = self.con.cursor()

    def getNotImportedWallet(self):
        with lockget:
            try:
                result = self.executeFetchOne("SELECT * FROM Adresses WHERE Imported = 0")
                self.execute(f"UPDATE Adresses SET Imported = -1, Unix = {str(int(time.time()))} WHERE Id = {str(result[0])}")
                if result != None:
                    return Classes.MultiCoinWallet(result)
                else:
                    return None
            except Exception as e:
                print(e)
                return None
    def getNotParsedWallet(self, InstanceName):
        with lockget:
            try:
                result = self.executeFetchAll(f'SELECT * FROM Adresses WHERE InstanceName = \'{InstanceName}\'')
                for row in result:
                    if None in row[5:]:
                        self.execute(f'UPDATE Adresses SET Imported = -2 WHERE InstanceName = \'{InstanceName}\'')
                        return row[0]

            except Exception as e:
                print(e)
                return None
    def importedByInstanceNameCount(self, InstanceName) -> int:
        with lockCount:
            result = self.execute(f"SELECT Id FROM Adresses WHERE Imported = \'1\' AND InstanceName = \'{InstanceName}\'").fetchall()
            if result is None:
                return 0
            else:
                return len(result)
    def walletFullUpdate(self, wallet):
        executeStr = (f"UPDATE Adresses SET Imported = {wallet.Imported}, InstanceName = \'{wallet.InstanceName}\', ")

        for key, value in wallet.Adresses.items():
            if value != '':
                executeStr += f"\'{key}\' = \'{value}\', "

        executeStr = executeStr[:-2] + f" WHERE Mnemonic = \'{wallet.Mnemonic}\'"
        self.execute(executeStr)
    def walletKeyUpdate(self, Key, wallet):
        executeStr = (f"UPDATE Adresses SET \'{Key}\' = \'{wallet.getProperty(f'{Key}')}\' WHERE Mnemonic = \'{wallet.Mnemonic}\'")
        self.execute(executeStr)
    def deleteNotImported(self):
        executeStr = (f"UPDATE Adresses SET \'Imported\' = 0 WHERE Imported = -1")
        self.execute(executeStr)
    def importPhrase(self, phrase):
        phrase = phrase.replace('\n', '')
        self.execute(f'INSERT INTO Adresses(Mnemonic) VALUES(\'{phrase}\')')
    def getPhrase(self, phrase):
        phrase = phrase.replace('\n', '')
        str = f"SELECT Mnemonic FROM Adresses WHERE Mnemonic = \'{phrase}\'"
        resp = self.execute(str)
        return resp
    def getAllPhrases(self):
        str = f"SELECT Mnemonic FROM Adresses"
        resp = self.execute(str)
        return resp
    def getWalletIdByTokenAndAdress(self, token, adress):
        coin = Classes.Coins.List[Classes.Coins.Tokens.index(token)]
        if token == 'BNB':
            str = f"SELECT Id FROM Adresses WHERE {coin} = \'{adress}\'"
            resp = self.execute(str)
            if resp.fetchone() == None:
                coin = Classes.Coins.List[Classes.Coins.Tokens[Classes.Coins.Tokens.index(token)+1:].index(token)]
                str = f"SELECT Id FROM Adresses WHERE {coin}= \'{adress}\'"
                resp = self.execute(str)
        else:
            str = f"SELECT Id FROM Adresses WHERE {coin} = \'{adress}\'"
            resp = self.execute(str)
        return resp
    def getWalletIdByCoinAndAdress(self, coin, adress):
        str = f"SELECT Id FROM Adresses WHERE {coin} = \'{adress}\'"
        resp = self.execute(str)
        return resp

    def execute(self, cmd):
        ok = False
        with lock:
            while ok is False:
                try:
                    print(f'Выполняем команду: {cmd}..')
                    execResult = self.cur.execute(f'{cmd}')
                    self.con.commit()
                    return execResult
                except Exception as e:
                    print(f'Не смогли выполнить команду: {cmd}!')
                    print(f'Ошибка: {str(e)}!')
                    time.sleep(5)
    def executeFetchAll(self, cmd):
        ok = False
        with lock:
            while ok is False:
                try:
                    print(f'Выполняем команду: {cmd}..')
                    execResult = self.cur.execute(f'{cmd}')
                    self.con.commit()
                    return execResult.fetchall()
                except:
                    pass
    def executeFetchOne(self, cmd):
        ok = False
        with lock:
            while ok is False:
                try:
                    print(f'Выполняем команду: {cmd}..')
                    execResult = self.cur.execute(f'{cmd}')
                    self.con.commit()
                    return execResult.fetchone()
                except:
                    pass