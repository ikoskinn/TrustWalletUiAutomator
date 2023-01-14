import time

import uiautomator2
import uiautomator2 as u2
import PlayerClasses
import TrustWalletMethods

CurrentTabManual = -5

class Tabs:
    SomeList = -2
    PassCode = -1
    Home = 0
    ReceiveList = 10
    ReceiveAdress = 11
    SendList = 21
    SendAmount = 22
    SendAccept = 23
    SendAccept2 = 24
    Settings = 1
    Wallets = 2
    WalletAdd = 3
    WalletAddMultiCoinChoose = 4
    WalletAddSetPhrase = 5
    WalletAddSuccess = 6

def CurrentTab(instance: PlayerClasses.PInstance):
     if instance.U2(resourceId="com.wallet.crypto.trustapp:id/header"). \
            child(resourceId="com.wallet.crypto.trustapp:id/actions"). \
            child(resourceId="com.wallet.crypto.trustapp:id/action_receive").exists(timeout=0.1):
         return Tabs.Home
     elif instance.U2(resourceId="com.wallet.crypto.trustapp:id/wallets_title").exists(timeout=0.1):
         return Tabs.Settings
     elif instance.U2(resourceId="com.wallet.crypto.trustapp:id/action_add").exists(timeout=0.1):
         return Tabs.Wallets
     elif instance.U2(text="Search - Receive").exists(timeout=0.1):
         return Tabs.ReceiveList
     elif instance.U2(text="Search - Send").exists(timeout=0.1):
         return Tabs.SendList
     elif instance.U2(text="Recipient Address").exists(timeout=0.1):
         return Tabs.SendAmount
     elif instance.U2(resourceId="com.wallet.crypto.trustapp:id/address").exists(timeout=0.1):
         return Tabs.ReceiveAdress
     elif instance.U2(resourceId="com.wallet.crypto.trustapp:id/max_total_title").exists(timeout=0.1):
         return Tabs.SendAccept
     elif instance.U2(text="I already have a wallet").exists(timeout=0.1):
         return Tabs.WalletAdd
     elif instance.U2(text="Multi-Coin Wallet").exists(timeout=0.1):
         return Tabs.WalletAddMultiCoinChoose
     elif instance.U2(text="Import Multi-Coin Wallet").exists(timeout=0.1):
         return Tabs.WalletAddSetPhrase
     elif instance.U2(text="Your wallet was successfully imported.").exists(timeout=0.1):
         return Tabs.WalletAddSuccess


def CurrentTabTest(U2: uiautomator2.Device):
    if U2(resourceId="com.wallet.crypto.trustapp:id/header"). \
            child(resourceId="com.wallet.crypto.trustapp:id/actions"). \
            child(resourceId="com.wallet.crypto.trustapp:id/action_receive").exists(timeout=0):
        return Tabs.Home
    elif U2(resourceId="com.wallet.crypto.trustapp:id/wallets_title").exists(timeout=0):
        return Tabs.Settings
    elif U2(resourceId="com.wallet.crypto.trustapp:id/action_add").exists(timeout=0):
        return Tabs.Wallets
    elif U2(resourceId="com.wallet.crypto.trustapp:id/search_query").exists(timeout=0):
        if CurrentTabManual == Tabs.SendList:
            return Tabs.SendList
        elif CurrentTabManual == Tabs.ReceiveList:
            return Tabs.ReceiveList
        else:
            return Tabs.SomeList
    elif U2(resourceId="com.wallet.crypto.trustapp:id/action_max").exists(timeout=0):
        return Tabs.SendAmount
    elif U2(resourceId="com.wallet.crypto.trustapp:id/address").exists(timeout=0):
        return Tabs.ReceiveAdress
    elif U2(resourceId="com.wallet.crypto.trustapp:id/max_total_title").exists(timeout=0):
        return Tabs.SendAccept
    elif U2(text="I already have a wallet").exists(timeout=0):
        return Tabs.WalletAdd
    elif U2(text="Multi-Coin Wallet").exists(timeout=0):
        return Tabs.WalletAddMultiCoinChoose
    elif U2(text="Import Multi-Coin Wallet").exists(timeout=0):
        return Tabs.WalletAddSetPhrase
    elif U2(text="Your wallet was successfully imported.").exists(timeout=0):
        return Tabs.WalletAddSuccess



def GoTo(instance: PlayerClasses.PInstance, tab: int):
    if instance.U2.app_current()['package'] != PlayerClasses.PackageName:
        TrustWalletMethods.AppStart(instance)
    TrustWalletMethods.GoHome(instance)

    if tab == 10:
        instance.U2(resourceId="com.wallet.crypto.trustapp:id/header"). \
            child(resourceId="com.wallet.crypto.trustapp:id/actions"). \
            child(resourceId="com.wallet.crypto.trustapp:id/action_receive").click_gone()


def GoToTest(U2: uiautomator2.Device, tab: int):
    global CurrentTabManual

    if U2.app_current()['package'] != PlayerClasses.PackageName:
        TrustWalletMethods.AppStartTest(U2)
    CurrentTabManual = CurrentTabTest(U2)

    if CurrentTabManual == -1:
        TrustWalletMethods.InputPinTest2(U2, '5051')
        CurrentTabManual = 0
    elif CurrentTabManual == -2:
        TrustWalletMethods.GoHomeTest(U2)
        CurrentTabManual = 0

    if CurrentTabManual == 0:
        if tab == Tabs.ReceiveList:
            U2(resourceId="com.wallet.crypto.trustapp:id/header"). \
                child(resourceId="com.wallet.crypto.trustapp:id/actions"). \
                child(resourceId="com.wallet.crypto.trustapp:id/action_receive").click_gone()



    if tab == 10:
        U2(resourceId="com.wallet.crypto.trustapp:id/header"). \
            child(resourceId="com.wallet.crypto.trustapp:id/actions"). \
            child(resourceId="com.wallet.crypto.trustapp:id/action_receive").click_gone()