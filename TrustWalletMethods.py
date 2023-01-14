import time

import uiautomator2
import uiautomator2 as u2
import PlayerClasses


def InputPin(instance):
    instance.U2(resourceId=f"{instance.Manager.PackageName}:id/pass_code_view").must_wait(True, 30.0)
    for num in PlayerClasses.Pin:
        instance.U2(resourceId=f"{instance.Manager.PackageName}:id/pass_code_view").click(offset=(_getX(num), _getY(num)))
    instance.U2(resourceId=f"{instance.Manager.PackageName}:id/pass_code_view").wait_gone(timeout=20)

def CheckInputPin(instance):
    if instance.U2(resourceId=f"{instance.Manager.PackageName}:id/pass_code_view").exists(0.1):
        for num in PlayerClasses.Pin:
            instance.U2(resourceId=f"{instance.Manager.PackageName}:id/pass_code_view").click(offset=(_getX(num), _getY(num)))
        instance.U2(resourceId=f"{instance.Manager.PackageName}:id/pass_code_view").wait_gone(timeout=20)


def _getY(num) -> float:
    numsY = [0.9, 0.3, 0.3, 0.3, 0.6, 0.6, 0.6, 0.75, 0.75, 0.75]
    return numsY[int(num)]
def _getX(num) -> float:
    numsX = [0.5, 0.17, 0.5, 0.83, 0.17, 0.5, 0.83, 0.17, 0.5, 0.83]
    return numsX[int(num)]

def GoHome(instance):
    if instance.U2(resourceId=f"com.wallet.crypto.trustapp:id/pass_code_view").exists():
        InputPin(instance)
        return

    elif instance.U2(resourceId="com.wallet.crypto.trustapp:id/header"). \
            child(resourceId="com.wallet.crypto.trustapp:id/actions"). \
            child(resourceId="com.wallet.crypto.trustapp:id/action_receive").exists():
        return
    else:
        while not instance.U2(resourceId="com.wallet.crypto.trustapp:id/header"). \
                child(resourceId="com.wallet.crypto.trustapp:id/actions"). \
                child(resourceId="com.wallet.crypto.trustapp:id/action_receive").exists():
            instance.U2.press('back')

            if instance.U2(resourceId="com.bluestacks.launcher:id/desktop").exists(timeout=0.1) or instance.U2(resourceId="com.bluestacks.appmart:id/fragmentContailer").exists(timeout=0.1):
                AppStart(instance)
                time.sleep(5)


    if not instance.U2(textContains="%").exists(timeout=10):
        # Начались ЛАГИ из-за превышения кол-ва импортированных кошельков
        AppStart(instance)

def AppStart(instance):
    if instance.U2(resourceId="com.bluestacks.launcher:id/desktop").exists(timeout=0.1) or instance.U2(resourceId="com.bluestacks.appmart:id/fragmentContailer").exists(timeout=0.1):
        instance.U2.app_start(PlayerClasses.PackageName, ".ui.start.activity.RootHostActivity")
        time.sleep(5)
    instance.U2.app_wait(PlayerClasses.PackageName, front=True)
    GoHome(instance)

def isTrustRunning(d: uiautomator2.Device) -> bool:
    if d.app_current()['package'] == 'com.wallet.crypto.trustapp':
        return True
    else:
        return False

def AppStartTest(d):
    d.app_stop_all()
    d.app_start("com.wallet.crypto.trustapp", ".ui.start.activity.RootHostActivity")
    d.app_wait("com.wallet.crypto.trustapp", front=True)
    InputPinTest(d)

def InputPinTest(d, config):
    d(resourceId=f"com.wallet.crypto.trustapp:id/pass_code_view").must_wait(True, 30.0)
    for num in config['Main']['pin']:
        d(resourceId=f"com.wallet.crypto.trustapp:id/pass_code_view").click(offset=(_getX(num), _getY(num)))
    d(resourceId=f"com.wallet.crypto.trustapp:id/pass_code_view").wait_gone(timeout=20)

def InputPinTest2(d, pin):
    d(resourceId=f"com.wallet.crypto.trustapp:id/pass_code_view").must_wait(True, 30.0)
    for num in pin:
        d(resourceId=f"com.wallet.crypto.trustapp:id/pass_code_view").click(offset=(_getX(num), _getY(num)))
    d(resourceId=f"com.wallet.crypto.trustapp:id/pass_code_view").wait_gone(timeout=20)

def InputPinDontWait(d):
    #pin = PlayerClasses.config['Main']['pin']
    pin = '505151'
    d(resourceId=f"com.wallet.crypto.trustapp:id/pass_code_view").must_wait(True, 30.0)
    for num in pin:
        d(resourceId=f"com.wallet.crypto.trustapp:id/pass_code_view").click(offset=(_getX(num), _getY(num)))
    time.sleep(3)

def GoHomeTest(d):
    if d(resourceId=f"com.wallet.crypto.trustapp:id/pass_code_view").exists():
        InputPin(d)
        return

    elif d(resourceId="com.wallet.crypto.trustapp:id/header"). \
            child(resourceId="com.wallet.crypto.trustapp:id/actions"). \
            child(resourceId="com.wallet.crypto.trustapp:id/action_receive").exists():
        return
    else:
        while not d(resourceId="com.wallet.crypto.trustapp:id/header"). \
            child(resourceId="com.wallet.crypto.trustapp:id/actions"). \
            child(resourceId="com.wallet.crypto.trustapp:id/action_receive").exists():
            d.press('back')

    if not d(textContains="%").exists(timeout=10):
        # Начались ЛАГИ из-за превышения кол-ва импортированных кошельков
        AppStartTest(d)