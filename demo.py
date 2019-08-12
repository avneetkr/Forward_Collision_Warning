#Libraries
import RPi.GPIO as GPIO
import time, datetime
from ops241.radar import OPS241Radar
import os
import obd

#GPIO Mode (BOARD / BCM)
GPIO.setmode(GPIO.BCM)

#set GPIO Pins
GPIO_TRIGGER = 18
GPIO_ECHO = 24
GPIO_LEDPIN = 17
GPIO_SPEAKERPIN = 27

#set GPIO direction (IN / OUT)
GPIO.setup(GPIO_TRIGGER, GPIO.OUT)
GPIO.setup(GPIO_LEDPIN, GPIO.OUT)
GPIO.setup(GPIO_SPEAKERPIN, GPIO.OUT)
GPIO.setup(GPIO_ECHO, GPIO.IN)

#obd setup
connection = obd.OBD(check_voltage=True)
cmd = connection.commands.SPEED


def setupOBD():
    time.sleep(1)
    #connection = obd.OBD()
    #while (connection.status() != OBDStatus.OBD_CONNECTED) #obd is connected but car ignition is off
    for tries = 1 to 10:
        if connection.status() == OBDStatus.NOT_CONNECTED:
            #1 beep per 0.1 second
            GPIO.output(GPIO_SPEAKERPIN,GPIO.HIGH)
            time.sleep(0.1)
            GPIO.output(GPIO_SPEAKERPIN,GPIO.LOW)
            connection = obd.OBD(check_voltage=True)
        else:
            break
        time.sleep(1)

    # if can't connect to obd after 10 tries
    if connection.status() == OBDStatus.NOT_CONNECTED:
        return False
    else:
        #setup completed successfully
        GPIO.output(GPIO_LEDPIN,GPIO.HIGH)
        GPIO.output(GPIO_SPEAKERPIN,GPIO.HIGH)
        time.sleep(2)
        GPIO.output(GPIO_LEDPIN,GPIO.LOW)
        GPIO.output(GPIO_SPEAKERPIN,GPIO.LOW)

        return True

def getCarSpeed():
    carSpeedResponse = connection.query(cmd)
    carSpeed = carSpeedResponse.value
    return carSpeed

def safeReboot():
    print("safeReboot Called")
    GPIO.cleanup()
    os.system('sudo shutdown -r now')


def safeShutdown():
    print("safeShutdown Called")
    GPIO.cleanup()
    os.system('sudo shutdown -h now')


def warningVA(frontCarSpeed, ownCarSpeed, magnitude):
    if (frontCarSpeed < 1.5 and magnitude > 200):
        print(datetime.datetime.now(), ': LED Alert')

        if (magnitude > 350):
            GPIO.output(GPIO_SPEAKERPIN,GPIO.HIGH)
            time.sleep(0.05)
            GPIO.output(GPIO_SPEAKERPIN,GPIO.LOW)
            time.sleep(0.05)
            GPIO.output(GPIO_SPEAKERPIN,GPIO.HIGH)
            print(datetime.datetime.now(), ': Speaker Alert')
        GPIO.output(GPIO_LEDPIN,GPIO.HIGH)
        time.sleep(0.2)
        GPIO.output(GPIO_LEDPIN,GPIO.LOW)
        GPIO.output(GPIO_SPEAKERPIN,GPIO.LOW)



with OPS241Radar() as radar:

    #give feedback for power on
    GPIO.output(GPIO_SPEAKERPIN,GPIO.HIGH)
    time.sleep(0.1)
    GPIO.output(GPIO_SPEAKERPIN,GPIO.LOW)

    timeArr = []
    count = 0

    connected = setupOBD()
    if not connected:
        #1 beep for 5 seconds and then reboot
        print("Failed to connect after 10 tries. Rebooting...")
        GPIO.output(GPIO_SPEAKERPIN,GPIO.HIGH)
        time.sleep(5)
        GPIO.output(GPIO_SPEAKERPIN,GPIO.LOW)
        #reboot & try again
        safeReboot()


    while True:
        while(connection.is_connected()):
            carSpeed = getCarSpeed()
            data = radar.read()
            if len(data) > 0:
                print ("original data: " + data)
                dataArr = data.split("\"")

                print ("Car Speed = " + str(carSpeed))
                if len(dataArr) > 9:
                    dataArr[2] = dataArr[2].replace(':','')
                    dataArr[2] = dataArr[2].replace(',','')
                    timeArr.append(float(dataArr[2]))
                    magnitude = float(dataArr[5])
                    frontCarspeed = float(dataArr[9])
                    warningVA(frontCarspeed, carSpeed, magnitude)
        #if car ignition is off
        if connection.status() == OBDStatus.OBD_CONNECTED:
            #wait
            time.sleep(1)
            continue
        else: #obd is not connected
            connected = setupOBD()
            if not connected:

                print("Could not re-connect. Shutting Down...")
                GPIO.output(GPIO_LEDPIN,GPIO.HIGH)
                for i = 1 to 3:
                    GPIO.output(GPIO_SPEAKERPIN,GPIO.HIGH)
                    time.sleep(1)
                    GPIO.output(GPIO_SPEAKERPIN,GPIO.LOW)
                    time.sleep(0.1)
                GPIO.output(GPIO_LEDPIN,GPIO.LOW)
                safeShutdown()
