import pyautogui
import time

# time.sleep(3)
while 1 > 0:
        #打开网页，刷新，复制链接
        pyautogui.click(647,1056)#谷歌浏览器底部图标坐标
        time.sleep(1)
        pyautogui.click('D:\\CODE\\pyauto\\refresh.PNG')
        time.sleep(10)
        pos1 = pyautogui.locateOnScreen('D:\\CODE\\pyauto\\AVATER.PNG')
        print("here")
        print(pos1)
        pointmid = pyautogui.center(pos1)
        x,y = pointmid
        pyautogui.moveTo(x,y)
        time.sleep(1)
        pyautogui.click('D:\\CODE\\pyauto\\MARU.PNG')
        time.sleep(1)
        pyautogui.click('D:\\CODE\\pyauto\\download.PNG')
        time.sleep(1)
        pyautogui.click('D:\\CODE\\pyauto\\cURL.PNG')
        time.sleep(2)
        pyautogui.click('D:\\CODE\\pyauto\\COPY.PNG')
        time.sleep(1)
        #跳到桌面点开运行，打开文件位置，复制粘贴，开始下载
        with pyautogui.hold('win'):
                pyautogui.press('d')
        time.sleep(1)
        pyautogui.click('D:\\CODE\\pyauto\\ICON.PNG')
        time.sleep(2)
        pyautogui.press('enter')
        time.sleep(2)
        print("start")
        pyautogui.write('cd /d D:\\download', interval=0.1)
        print("finish")
        time.sleep(1)
        pyautogui.press('enter')
        time.sleep(1)
        with pyautogui.hold('ctrl'):
                pyautogui.press('v')
        time.sleep(1)
        pyautogui.press('enter')
        #一段时间后关闭运行
        time.sleep(150)
        pyautogui.click('D:\\CODE\\pyauto\\x.PNG')
