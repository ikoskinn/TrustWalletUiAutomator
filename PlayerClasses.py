import configparser
import os
import re
import subprocess

import Classes
import threading
import uiautomator2 as u2
import TBot
import asyncio
import time

import TrustWalletMethods
import sqliteManager


lockk = threading.Lock()
BSType = 'BS5'
walletKeyUpdateLock = threading.Lock()
sqlite = sqliteManager.SQLite('Adresses')
PackageName = ""
Pin = ""
MaxImportCount = 0
config = configparser.ConfigParser()
playerType = 'Pie64'



PLAYERS_BS4 = {}



ImportingNow = False

class PManager:
    Instances = []
    PackageName = ''


    def __init__(self, _BSType):
        global Pin, MaxImportCount, PackageName, playerType, BSType, PLAYERS_BS4
        BSType = _BSType
        config.read("settings.ini")
        Pin = config['Main']['pin']
        MaxImportCount = int(config['Main']['maxwallets'])

        if BSType == 'BS4':
            Ports = str(config['BS4']['Ports']).replace(' ', '').split(',')
            playerType = 'N64'
            # Добавляем названия инстансов в список
            for port in Ports:
                if port == '5555':
                    PLAYERS_BS4['N64_0'] = port
                else:
                    delta_port = int(port)-5555
                    if delta_port == 0:
                        PLAYERS_BS4['N64_1'] = port
                    else:
                        PLAYERS_BS4['N64_' + str(int(delta_port/10))] = port
        else:
            self.PlayerDir = config['Main']['PlayerDir']
            self.ConfDir = config['Main']['ConfDir']
            self.PlayerNames = config['Main']['PlayerNames'].split(',')
            if len(self.PlayerNames) == 1 and self.PlayerNames[0] == "":
                self.PlayerNames.clear()
                l = os.listdir(self.ConfDir + "\\Engine")
                for fol in l:
                    if playerType in fol:
                        self.PlayerNames.append(fol)
            for name in self.PlayerNames:
                self.PlayerNames[self.PlayerNames.index(name)] = name.replace(' ', '')

        TBot.Usernames.extend(config['TelegramBot']['UsernamesToResponse'].split(','))
        TBot.BOT_TOKEN = config['TelegramBot']['Token']
        TBot.Manager = self
        TBot.SendMessage('Запустили бот')

        PackageName = config['Main']['packagename']
        self.PackageName = PackageName

        sqlite.deleteNotImported()
        if BSType == 'BS4':
            for player in PLAYERS_BS4:
                self.Instances.append(PInstance(player, self))
        else:
            for playername in self.PlayerNames:
                self.Instances.append(PInstance(playername, self))



        for instance in self.Instances:
            instance.start()
            time.sleep(5)

        asyncio.run(TBot.main())

    def save_config(self, tag, name, value):
        config[tag][name] = value
        with open('settings.ini', 'w') as configfile:  # save
            config.write(configfile)


class PInstance(threading.Thread):
    U2 = None
    CurrentWallet = None
    Port = '0'

    def __init__(self, name, pmanager):
        threading.Thread.__init__(self)
        self.Manager = pmanager
        self.Index = int(len(pmanager.Instances))
        self.Name = name
        if BSType == 'BS4':
            self.Port = PLAYERS_BS4[name]

    def run(self):
        if BSType == 'BS4':
            pass
        else:
            f = open(self.Manager.ConfDir + "\\bluestacks.conf", "r")
            t = 'bst.instance.' + self.Name + '.adb_port='
            for x in f:
                if t in x:
                    self.Port = x.split('adb_port=')[1].replace('\"', "").replace('\n', '')
                    break

        print('Подключаемся к ' + self.Name + ' \'127.0.0.1:' + self.Port + '\'\n')
        connected = False
        while connected is False:
            try:
                self.U2 = u2.connect('127.0.0.1:' + self.Port)
                connected = True
            except:
                print(f'Окно {self.Name} не запущено! Ожидаем запуска пользователем.. Проверяем через 10 секунд еще раз..')
                time.sleep(10)
        print('Инициализировали окно ' + self.Name)
        TrustWalletMethods.AppStart(self)

        self.StartImporting()
    def StartImporting(self):
        restart = 0
        while True:
            try:
                while ImportingNow is True:
                    time.sleep(5)
                count = sqlite.importedByInstanceNameCount(self.Name)
                print(f'Импортировали в кошелек {self.Name} уже {count} кошельков.')
                if count >= MaxImportCount:
                    print(f'МАКСИМУМ ИМПОРТИРОВАННЫХ КОШЕЛЬКОВ [{sqlite.importedByInstanceNameCount(self.Name)}]')
                    wallet = None
                else:
                    while ImportingNow is True:
                        time.sleep(5)
                    print(f'{self.Name} - Пробуем взять кошелек на импорт!')
                    with lockk:
                        wallet = sqlite.getNotImportedWallet()
                        time.sleep(2)
                    try:
                        print(f'{self.Name} - Взяли кошелек на импорт (ID: {wallet.Id})!')
                    except:
                        print(f'{self.Name} - Закончились кошельки на импорт!')
                if wallet is not None:
                    restart += 1
                    if restart > 3:
                        print(f'[{self.Name}]: Рестартим приложение!')
                        self.U2.app_stop_all()
                        time.sleep(5)
                        TrustWalletMethods.AppStart(self)
                        restart = 0
                    print(f'{self.Name} - Взяли кошелек!')
                    TrustWalletMethods.GoHome(self)

                    while not self.U2(text="Wallets").exists(timeout=1.0):
                        self.U2(text="Settings").click()

                    while not self.U2(resourceId=f"{self.Manager.PackageName}:id/action_add").exists(timeout=1.0):
                        self.U2(text="Wallets").click()

                    self.U2(resourceId=f"{self.Manager.PackageName}:id/action_add").click_gone(maxretry=10,
                                                                                               interval=2.0)
                    self.U2(text="I already have a wallet").click_gone(maxretry=10, interval=2.0)
                    self.U2(text="Multi-Coin Wallet").click_gone(maxretry=10, interval=2.0)

                    imported = False

                    while wallet.Imported != 1:
                        self.U2(className="android.widget.EditText",
                                resourceId=f"{self.Manager.PackageName}:id/name").set_text(
                            f"Wallet{wallet.Id}")
                        self.U2(className="android.widget.EditText",
                                resourceId=f"{self.Manager.PackageName}:id/field_target").set_text(
                            f"{wallet.Mnemonic}")
                        self.U2(resourceId=f"{self.Manager.PackageName}:id/action_import", text="IMPORT").click()
                        time.sleep(10.0)
                        UIBUG = 0

                        while not self.U2(resourceId=f"{self.Manager.PackageName}:id/textinput_error").exists(
                                timeout=0.5) \
                                and not self.U2(resourceId=f"{self.Manager.PackageName}:id/action_done").exists(
                            timeout=0.5) \
                                and not self.U2(resourceId=f"{self.Manager.PackageName}:id/action_receive").exists(
                            timeout=0.5) \
                                and not self.U2(resourceId=f"{self.Manager.PackageName}:id/pass_code_view").exists(
                            timeout=0.5):
                            UIBUG += 1
                            if UIBUG > 5:
                                self.U2.open_notification()
                                time.sleep(5)
                                print(f'[{self.Name}]:' + 'Нажимаем кнопочку back')
                                self.U2.press("back")
                                time.sleep(2)
                                TrustWalletMethods.CheckInputPin(self)
                                UIBUG = 0
                            pass
                        if self.U2(resourceId=f"{self.Manager.PackageName}:id/action_done").exists():
                            # Все ок
                            self.U2(resourceId=f"{self.Manager.PackageName}:id/action_done").click_gone(maxretry=10,
                                                                                                        interval=2.0)
                            wallet.Imported = 1
                            wallet.InstanceName = self.Name
                            sqlite.walletKeyUpdate('Imported', wallet)
                            sqlite.walletKeyUpdate('InstanceName', wallet)
                            self.getAdresses(wallet)
                        else:
                            self.U2(resourceId=f"{self.Manager.PackageName}:id/action_import", text="IMPORT").click()
                            time.sleep(0.5)

                            while not self.U2(resourceId=f"{self.Manager.PackageName}:id/textinput_error").exists(
                                    timeout=0.1) and not self.U2(
                                resourceId=f"{self.Manager.PackageName}:id/action_done").exists(
                                timeout=0.1):
                                time.sleep(1)

                            if self.U2(resourceId=f"{self.Manager.PackageName}:id/action_done").exists():
                                # Все ок
                                self.U2(resourceId=f"{self.Manager.PackageName}:id/action_done").click_gone(maxretry=10,
                                                                                                            interval=2.0)
                                wallet.Imported = 1
                                wallet.InstanceName = self.Name
                                with lockk:
                                    sqlite.walletFullUpdate(wallet)
                                    time.sleep(5)
                                self.getAdresses(wallet)
                else:
                    #self.check_transactions()
                    time.sleep(5)
            except Exception as e:
                print(e)
                self.checkIfCleared()
                time.sleep(10)

    def ImportWallet(self, wallet):
        TrustWalletMethods.GoHome(self)

        while not self.U2(text="Wallets").exists(timeout=1.0):
            self.U2(text="Settings").click()

        while not self.U2(resourceId=f"{self.Manager.PackageName}:id/action_add").exists(timeout=1.0):
            self.U2(text="Wallets").click()

        self.U2(resourceId=f"{self.Manager.PackageName}:id/action_add").click_gone(maxretry=10,
                                                                                   interval=2.0)
        self.U2(text="I already have a wallet").click_gone(maxretry=10, interval=2.0)
        self.U2(text="Multi-Coin Wallet").click_gone(maxretry=10, interval=2.0)

        imported = False

        while wallet.Imported != 1:
            while 'Multi' in self.U2(className="android.widget.EditText",
                    resourceId=f"{self.Manager.PackageName}:id/name").info['text'] \
                    or f'Wallet{wallet.Id}' != self.U2(className="android.widget.EditText",
                    resourceId=f"{self.Manager.PackageName}:id/name").info['text']:
                time.sleep(2)
                self.U2(className="android.widget.EditText",
                        resourceId=f"{self.Manager.PackageName}:id/name").set_text(
                    f"Wallet{wallet.Id}")

            self.U2(className="android.widget.EditText",
                    resourceId=f"{self.Manager.PackageName}:id/field_target").set_text(
                f"{wallet.Mnemonic}")
            self.U2(resourceId=f"{self.Manager.PackageName}:id/action_import", text="IMPORT").click()
            time.sleep(10.0)
            UIBUG = 0

            while not self.U2(resourceId=f"{self.Manager.PackageName}:id/textinput_error").exists(
                    timeout=0.5) \
                    and not self.U2(resourceId=f"{self.Manager.PackageName}:id/action_done").exists(
                timeout=0.5) \
                    and not self.U2(resourceId=f"{self.Manager.PackageName}:id/action_receive").exists(
                timeout=0.5) \
                    and not self.U2(resourceId=f"{self.Manager.PackageName}:id/pass_code_view").exists(
                timeout=0.5):
                UIBUG += 1
                if UIBUG > 5:
                    self.U2.open_notification()
                    time.sleep(5)
                    print(f'[{self.Name}]:' + 'Нажимаем кнопочку back')
                    self.U2.press("back")
                    time.sleep(2)
                    TrustWalletMethods.CheckInputPin(self)
                    UIBUG = 0
                pass
            if self.U2(resourceId=f"{self.Manager.PackageName}:id/action_done").exists():
                # Все ок
                self.U2(resourceId=f"{self.Manager.PackageName}:id/action_done").click_gone(maxretry=10,
                                                                                            interval=2.0)
                wallet.Imported = 1
                wallet.InstanceName = self.Name
                sqlite.walletKeyUpdate('Imported', wallet)
                sqlite.walletKeyUpdate('InstanceName', wallet)
                self.getAdresses(wallet)
            else:
                self.U2(resourceId=f"{self.Manager.PackageName}:id/action_import", text="IMPORT").click()
                time.sleep(0.5)

                while not self.U2(resourceId=f"{self.Manager.PackageName}:id/textinput_error").exists(
                        timeout=0.1) and not self.U2(
                    resourceId=f"{self.Manager.PackageName}:id/action_done").exists(
                    timeout=0.1):
                    time.sleep(1)

                if self.U2(resourceId=f"{self.Manager.PackageName}:id/action_done").exists():
                    # Все ок
                    self.U2(resourceId=f"{self.Manager.PackageName}:id/action_done").click_gone(maxretry=10,
                                                                                                interval=2.0)
                    wallet.Imported = 1
                    wallet.InstanceName = self.Name
                    with lockk:
                        sqlite.walletFullUpdate(wallet)
                        time.sleep(5)

    def getAdresses(self, Wallet):
        TrustWalletMethods.GoHome(self)
        self.U2(resourceId="com.wallet.crypto.trustapp:id/header"). \
            child(resourceId="com.wallet.crypto.trustapp:id/actions"). \
            child(resourceId="com.wallet.crypto.trustapp:id/action_receive").click_gone()
        resend_check_count = 1
        for coin in Classes.Coins.List:
            ok = False
            while ok is False:
                try:
                    self.U2(resourceId="com.wallet.crypto.trustapp:id/search_query").clear_text()
                    time.sleep(0.5)
                    self.U2(resourceId="com.wallet.crypto.trustapp:id/search_query").set_text(coin)
                    time.sleep(2)
                    upper_timeout = 0

                    while True:
                        try:
                            self.U2(resourceId="com.wallet.crypto.trustapp:id/name", text=coin).click(timeout=0.1)
                        except:
                            if TrustWalletMethods.isTrustRunning(self.U2) is False:
                                raise TypeError('Trust is crashed')

                            if self.U2(resourceId="android:id/addToDictionaryButton").exists(timeout=0.1):
                                self.U2.press('back')
                            else:
                                TrustWalletMethods.CheckInputPin(self)
                            upper_timeout += 1

                        if upper_timeout >= 1:
                            self.U2.swipe(100, 400, 100, 200, duration=0.5, steps=10)
                            time.sleep(1)
                            self.U2.swipe(100, 200, 100, 600, duration=0.5, steps=2)
                            upper_timeout = 0


                        if self.U2(resourceId="com.wallet.crypto.trustapp:id/address").exists(timeout=5):
                            break
                        else:
                            TrustWalletMethods.CheckInputPin(self)
                    Address = self.U2(resourceId="com.wallet.crypto.trustapp:id/address").info['text']
                    while Address == "":
                        time.sleep(5)
                        Address = self.U2(resourceId="com.wallet.crypto.trustapp:id/address").info['text']

                    print(f"{self.Name} | Спарсили кошелек {coin}: {self.U2(resourceId='com.wallet.crypto.trustapp:id/address').info['text']}")
                    Wallet.Adresses[coin] = self.U2(resourceId='com.wallet.crypto.trustapp:id/address').info['text']
                    self.U2.press('back')

                    resend_check_count += 1
                    if resend_check_count == 5:
                        resend_check_count = 1
                        #self.check_transactions_back(Wallet, getAdresses=True)
                    ok = True
                except Exception as e:
                    if str(e) == 'Trust is crashed':
                        TrustWalletMethods.AppStart(self)
                        TrustWalletMethods.GoHome(self)
                        self.U2(resourceId="com.wallet.crypto.trustapp:id/header"). \
                            child(resourceId="com.wallet.crypto.trustapp:id/actions"). \
                            child(resourceId="com.wallet.crypto.trustapp:id/action_receive").click_gone()
                        time.sleep(1)
                    self.checkIfCleared()
                    TrustWalletMethods.CheckInputPin(self)

        with lockk:
            sqlite.walletFullUpdate(Wallet)
            time.sleep(5)
        self.U2.press('back')

    def checkIfCleared(self):
        cleared = False

        if self.U2(text="I already have a wallet").exists(timeout=0.1):
            self.U2(text="I already have a wallet").click_gone(maxretry=10, interval=2.0)
            if self.U2(text="I've read and accept the Terms of Service and Privacy Policy.").exists(timeout=0.1):
                cleared = True
        elif self.U2(text="I've read and accept the Terms of Service and Privacy Policy.").exists(timeout=0.1):
            cleared = True

        if cleared is True:
            sqlite.execute(
                f"UPDATE Adresses SET 'Imported' = '0' WHERE 'InstanceName' = '{self.Name}'")
            TBot.SendMessage(
                f"У окна {self.Name} сбросился кэш! Зайдите и настройте окно вручную для дальнейшей работы")
    def getManyAdresses(self, SqlReturn, Wallet):
        TrustWalletMethods.GoHome(self)
        self.U2(resourceId="com.wallet.crypto.trustapp:id/header"). \
            child(resourceId="com.wallet.crypto.trustapp:id/actions"). \
            child(resourceId="com.wallet.crypto.trustapp:id/action_receive").click_gone()
        resend_check_count = 1


        for coin in Classes.Coins.List:
            ok = False
            while ok is False:
                try:
                    self.U2(resourceId="com.wallet.crypto.trustapp:id/search_query").clear_text()
                    time.sleep(0.5)
                    self.U2(resourceId="com.wallet.crypto.trustapp:id/search_query").set_text(coin)
                    time.sleep(2)
                    upper_timeout = 0

                    while True:
                        try:
                            self.U2(resourceId="com.wallet.crypto.trustapp:id/name", text=coin).click(timeout=0.1)
                        except:
                            if TrustWalletMethods.isTrustRunning(self.U2) is False:
                                raise TypeError('Trust is crashed')

                            if self.U2(resourceId="android:id/addToDictionaryButton").exists(timeout=0.1):
                                self.U2.press('back')
                            else:
                                TrustWalletMethods.CheckInputPin(self)
                            upper_timeout += 1

                        if upper_timeout >= 1:
                            self.U2.swipe(100, 400, 100, 200, duration=0.5, steps=10)
                            time.sleep(1)
                            self.U2.swipe(100, 200, 100, 600, duration=0.5, steps=2)
                            upper_timeout = 0


                        if self.U2(resourceId="com.wallet.crypto.trustapp:id/address").exists(timeout=0.1):
                            break
                        else:
                            TrustWalletMethods.CheckInputPin(self)

                    Wallet.Adresses.update({coin: self.U2(resourceId="com.wallet.crypto.trustapp:id/address").info['text']})
                    sqlite.walletKeyUpdate(coin, Wallet)
                    self.U2.press('back')

                    resend_check_count += 1
                    if resend_check_count == 5:
                        resend_check_count = 1
                        self.check_transactions_back(Wallet, getAdresses=True)
                    ok = True
                except Exception as e:
                    if str(e) == 'Trust is crashed':
                        TrustWalletMethods.AppStart(self)
                        TrustWalletMethods.GoHome(self)
                        self.U2(resourceId="com.wallet.crypto.trustapp:id/header"). \
                            child(resourceId="com.wallet.crypto.trustapp:id/actions"). \
                            child(resourceId="com.wallet.crypto.trustapp:id/action_receive").click_gone()
                        time.sleep(1)
                    TrustWalletMethods.CheckInputPin(self)


        self.U2.press('back')
    def check_transactions(self):
        return
        notif = Classes.Notifications(self.U2.shell(["dumpsys", "notification", "--noredact"]).output, config)
        if notif.ReceivedCount == 0:
            print('Нет входящих транзакций!')
            return

        print(f'Нашли входящие транзакции! ({notif.ReceivedCount}')
        self.U2.open_notification()
        time.sleep(2)
        if len(notif.List) > 5:
            print(f'Разворачиваем список уведомлений потому что их больше 5..')
            self.U2(resourceId="android:id/app_name_text", text="Trust Wallet").click()

        for trustnotif in notif.List:
            if not trustnotif.isReceive or \
                    trustnotif.ReceiveAmount == 0.0 or \
                    trustnotif.ReceiveAmount < trustnotif.ReceiveMinAmount or \
                    trustnotif.ReceiveToken not in Classes.Coins.Tokens:
                print(f'Уведомление о транзакции (\'{trustnotif.Title};{trustnotif.Text}\') не подходит по критерию!')
                self.swipe_notification(self.U2(text=f'{trustnotif.Title}'))
                pass
            else:
                print(f'Уведомлени о транзакции (\'{trustnotif.Title};{trustnotif.Text}\') подходит! Ищем его в списке..')
                while not self.U2(text=f'{trustnotif.Title}').exists(0.1):
                    print(self.U2.dump_hierarchy())
                    self.U2(scrollable='true').scroll(steps=30, max_swipes=1)

                print('Нашли уведомление, переходим по нему..')
                self.U2.shell(['logcat', '-c'])
                self.U2(text=f'{trustnotif.Title}').click()
                self.U2(text='Transfer').wait(timeout=20)
                # trust://transaction_details?wallet_id - ,"status"
                trans_details = re.search(r'(dat=trust://transaction_details\?wallet_id).*(\"status\":)',
                                          self.U2.shell(['logcat', '-d']).output).group(0)
                trustnotif.ReceiveAdress = re.search('(?<="to":").*?(?=",")', trans_details).group(0)
                WalletName = "Wallet" + str(sqlite.getWalletIdByTokenAndAdress(
                    trustnotif.ReceiveToken,
                    trustnotif.ReceiveAdress).fetchone()[0])
                print(f'На кошелек {WalletName} на адрес {trustnotif.ReceiveAdress} пришла транзакция {trustnotif.ReceiveAmount} {trustnotif.ReceiveToken}')
                self.change_wallet(WalletName)
                self.send_allcoins()
    def check_transactions_back(self, WalletBack, getAdresses):
        return
        notif = Classes.Notifications(self.U2.shell(["dumpsys", "notification", "--noredact"]).output, config)
        okk = False

        if notif.ReceivedCount == 0:
            print('Нет входящих транзакций!')
            return

        print(f'Нашли входящие транзакции! ({notif.ReceivedCount} шт.)')
        self.U2.open_notification()
        time.sleep(2)
        if len(notif.List) >= 4:
            print(f'Разворачиваем список уведомлений потому что их больше 3..')
            self.U2(resourceId="android:id/app_name_text", text="Trust Wallet").click()
        time.sleep(2)
        for trustnotif in notif.List:
            if trustnotif.ReceiveToken == 'BNB':
                tokenInIni = 'BNB' in config['Coins'] or 'Smart Chain' in config['Coins']
            else:
                try:
                    tokenInIni = Classes.Coins.List[Classes.Coins.Tokens.index(trustnotif.ReceiveToken)] in config['Coins']
                except:
                    tokenInIni = False

            if tokenInIni is False or \
                    not trustnotif.isReceive or \
                    trustnotif.ReceiveAmount == 0.0 or \
                    trustnotif.ReceiveAmount < trustnotif.ReceiveMinAmount:
                print(f'Уведомление о транзакции (\'{trustnotif.Title};{trustnotif.Text}\') не подходит по критерию!')
                self.swipe_notification(self.U2(text=f'{trustnotif.Title}'))
                time.sleep(0.5)
                pass
            else:
                okk = True
                print(f'Уведомлени о транзакции (\'{trustnotif.Title};{trustnotif.Text}\') подходит! Ищем его в списке..')
                while not self.U2(text=f'{trustnotif.Title}').exists(0.1):
                    print(self.U2.dump_hierarchy())
                    self.U2(scrollable='true').scroll(steps=30, max_swipes=1)

                print('Нашли уведомление, переходим по нему..')
                self.U2.shell(['logcat', '-c'])
                self.U2(text=f'{trustnotif.Title}').click()
                self.U2(text='Transfer').wait(timeout=20)
                # trust://transaction_details?wallet_id - ,"status"
                trans_details = re.search(r'(dat=trust://transaction_details\?wallet_id).*(\"status\":)',
                                          self.U2.shell(['logcat', '-d']).output).group(0)
                trustnotif.ReceiveAdress = re.search('(?<="to":").*?(?=",")', trans_details).group(0)
                WalletName = "Wallet" + str(sqlite.getWalletIdByTokenAndAdress(
                    trustnotif.ReceiveToken,
                    trustnotif.ReceiveAdress).fetchone()[0])
                print(f'На кошелек {WalletName} на адрес {trustnotif.ReceiveAdress} пришла транзакция {trustnotif.ReceiveAmount} {trustnotif.ReceiveToken}')
                self.change_wallet(WalletName)

                if trustnotif.ReceiveToken == 'BNB':
                    if 'bnb' in trustnotif.ReceiveAdress:
                        Coin = 'BNB'
                    else:
                        Coin = 'Smart Chain'
                else:
                    Coin = Classes.Coins.List[Classes.Coins.Tokens.index(trustnotif.ReceiveToken)]

                self.send_allcoins(Coin)

                TrustWalletMethods.GoHome(self)
                self.change_wallet(f'Wallet{WalletBack.Id}')
                if getAdresses is True:
                    self.U2(resourceId="com.wallet.crypto.trustapp:id/header"). \
                        child(resourceId="com.wallet.crypto.trustapp:id/actions"). \
                        child(resourceId="com.wallet.crypto.trustapp:id/action_receive").click_gone()

        if okk is False:
            self.U2.press('back')
    def swipe_notification(self, notif):
        while notif.exists(timeout=1):
            self.U2.swipe(int(notif.info['bounds']['left']),
                    int(notif.info['bounds']['bottom']),
                    int(notif.info['bounds']['left']) + 600,
                    int(notif.info['bounds']['bottom']),
                    duration=0.5, steps=5)
            time.sleep(1)
    def change_wallet(self, name):
        TrustWalletMethods.GoHome(self)
        while not self.U2(text="Wallets").exists(timeout=1.0):
            self.U2(text="Settings").click()

        while not self.U2(resourceId=f"com.wallet.crypto.trustapp:id/action_add").exists(timeout=1.0):
            self.U2(text="Wallets").click()

        while not self.U2(text=name).exists():
            if self.U2(scrollable="true").exists():
                self.U2(scrollable="true").scroll(steps=20, max_swipes=1)
            pass

        time.sleep(1)
        self.U2(text=name).click()

        self.U2(resourceId="com.wallet.crypto.trustapp:id/header"). \
            child(resourceId="com.wallet.crypto.trustapp:id/actions"). \
            child(resourceId="com.wallet.crypto.trustapp:id/action_receive").wait(timeout=60)
    def send_allcoins(self, coinToSend):
        print('Переводим все коины с кошелька!')
        TrustWalletMethods.GoHome(self)

        self.U2.swipe(260, 300, 260, 500, duration=0.25, steps=10)
        time.sleep(2)

        self.U2(resourceId="com.wallet.crypto.trustapp:id/header"). \
            child(resourceId="com.wallet.crypto.trustapp:id/actions"). \
            child(resourceId="com.wallet.crypto.trustapp:id/action_send").click()
        time.sleep(2)
        ok = False
        while ok is False:
            for view in self.U2(resourceId="com.wallet.crypto.trustapp:id/swipe_layout").child(resourceId="com.wallet.crypto.trustapp:id/assetLayout"):
                coin = view.child(resourceId="com.wallet.crypto.trustapp:id/name").info['text']
                amount = str(view.child(resourceId="com.wallet.crypto.trustapp:id/crypto_amount").info['text']).split(' ')[0].replace(',', '')

                if coin == coinToSend:
                    ok = True

                skip = False
                try:
                    test = config['Coins'][coin].split(';')[0]
                except:
                    skip = True

                if skip is True:
                    print(f'Пропускаем {coin} т.к. его нет в списке на пересылку.')
                    continue
                try:
                    if float(amount) >= float(config['Coins'][coin].split(';')[1]):
                        minAmountOk = True
                    else:
                        minAmountOk = False
                except:
                    minAmountOk = True

                if coin in Classes.Coins.List and minAmountOk is True:
                    maxtries = int(config['Main']['maxtriesresend'])

                    print(f'Есть средства подходящие по критерию! У валюты {coin} {float(amount)} токенов')
                    view.child(resourceId="com.wallet.crypto.trustapp:id/name").click()
                    self.U2(resourceId='com.wallet.crypto.trustapp:id/input_value').set_text(
                        config['Coins'][coin].split(';')[0]
                    )
                    self.U2(resourceId='com.wallet.crypto.trustapp:id/action_max').click()
                    self.U2(resourceId='com.wallet.crypto.trustapp:id/action_continue').click()

                    try:
                        self.U2(text="CONFIRM", resourceId="com.wallet.crypto.trustapp:id/action_send").click(timeout=10)
                        self.U2(resourceId="com.wallet.crypto.trustapp:id/pass_code_view").must_wait(10)
                        TrustWalletMethods.InputPin(self)
                        print(f"Перевели все средства на адрес {config['Coins'][coin].split(';')[0]}")
                        time.sleep(10)
                    except:
                        self.U2.press('back')
                        self.U2.press('back')