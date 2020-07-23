from datetime import datetime
from gpiozero import Button
import RPi.GPIO as GPIO
import picamera
import time
import threading

class CameraControl():
    ###GPIOの基本設定###
    shutter_button = Button(14)
    iso_plus_button = Button(15)
    iso_minus_button = Button(23) 
    ss_plus_button = Button(20)
    ss_minus_button = Button(21)

    awb_plus_button = Button(5)
    awb_minus_button = Button(6)

    meter_modes_button = Button(13)

    #picameraのインスタンス生成
    pi_camera = picamera.PiCamera()

    #iso感度
    iso_sensitivity_dict = {
        "-1":64, "0":100, "1":125, "2":160, "3":200, \
        "4":320, "5":400, "6":500, "7":640, "8":800
    }

    #ss(framerate0.001－120 = ss1/0.001-1/120)
    shutter_speed_dict = {
        "-13":120000000,"-12":60000000,"-11":30000000,"-10":15000000,
        "-9":8000000,"-8":4000000,"-7":2000000,"-6":1000000,\
        "-5":500000,"-4":250000,"-3":125000,"-2":66666,"-1":33333,\
        "0":20000,"1":16666, "2":8333
    }
    shutter_speed_display_dict = {
        "-13":"120","-12":"60","-11":"30","-10":"15",
        "-9":"8","-8":"4","-7":"2","-6":"1",\
        "-5":"1/2","-4":"1/4","-3":"1/8","-2":"1/15","-1":"1/30",\
        "0":"1/40","1":"1/60", "2":"1/120"
    }

    #framerate
    framerate_dict = {
        "-13":0.0083,"-12":0.016,"-11":0.033,"-10":0.066,
        "-9":0.12,"-8":0.25,"-7":0.50,"-6":1.0,\
        "-5":2.0,"-4":4.0,"-3":8.0,"-2":15,"-1":30,\
        "0":40,"1":60, "2":120
    }

    #AWB offにするとエラーが出る？
    auto_white_balance_dict={
        "0":"auto","1":"auto","2":"sunlight","3":"cloudy","4":"shade","5":"tungsten", \
        "6":"fluorescent","7":"incandescent","8":"flash","9":"horizon"
    }
    """
    auto_white_balance_dict={
        "0":"off","1":"auto","2":"sunlight","3":"cloudy","4":"shade","5":"tungsten", \
        "6":"fluorescent","7":"incandescent","8":"flash","9":"horizon"
    }
    """

    #測光
    #average:平均,spot:スポット,backlit:逆光,matrix	多分割
    meter_mode_dict={
        "0":"average","1":"spot","2":"backlit","3":"matrix",
    }

    def preview_start(self):
        self.pi_camera.start_preview(fullscreen = False, window = (0, 67, 640, 480))

        self.preview_display_settings()
        
    def preview_display_settings(self):
        #プレビュー画面に表示する文字の設定
        self.pi_camera.annotate_text_size = 80 #(valid range 6-160)
        self.pi_camera.annotate_text = "mode:" + str(self.camera_mode) +\
            "\nss:" +  self.shutter_speed_display_dict[str(self.ss_dict_key)] + \
                "\niso:"+  str(self.pi_camera.iso) + \
                    "\nmeter_mode:"+  str(self.pi_camera.meter_mode) + \
                        "\nwhite_balance:"+  str(self.pi_camera.awb_mode)
        
    def preview_stop(self):
        self.pi_camera.stop_preview()

    def iso_plus(self):
        if self.iso_lower_limit_key <= self.iso_dict_key < self.iso_upper_limit_key:
            self.iso_dict_key += 1
            self.pi_camera.iso = self.iso_sensitivity_dict[str(self.iso_dict_key)] 

            #プレビュー画面に表示する情報の更新
            self.preview_display_settings()

            print("iso:" + str(self.pi_camera.iso))
        else:
            print("iso_dict_key over " + str(self.iso_upper_limit_key))  
    
    def iso_minus(self):
        if self.iso_lower_limit_key < self.iso_dict_key <= self.iso_upper_limit_key:
            self.iso_dict_key -= 1
            self.pi_camera.iso = self.iso_sensitivity_dict[str(self.iso_dict_key)] 

            #プレビュー画面に表示する情報の更新
            self.preview_display_settings()

            print("iso:" + str(self.pi_camera.iso))
        else:
            print("iso_dict_key under " + str(self.iso_lower_limit_key)) 

    def ss_plus(self):
        #デフォルトのframerateではss=1/30より遅くできない。
        if self.ss_lower_limit_key <= self.ss_dict_key < self.ss_upper_limit_key:
            self.ss_dict_key += 1
            self.pi_camera.framerate = self.framerate_dict[str(self.ss_dict_key)]   #framerate設定後にssを設定
            self.pi_camera.shutter_speed = self.shutter_speed_dict[str(self.ss_dict_key)]

            #プレビュー画面に表示する情報の更新
            self.preview_display_settings()

            #TEST CODE
            print("ss_dict:" + str(self.ss_dict_key))
            print("ss:" + str(self.pi_camera.shutter_speed))
            print("fps:" + str(self.pi_camera.framerate))
        else:
            print("ss setting error (plus)")
            print("ss_dict:" + str(self.ss_dict_key))

    def ss_minus(self):
        #デフォルトのframerateではss=1/30より遅くできない。
        if self.ss_lower_limit_key < self.ss_dict_key <= self.ss_upper_limit_key:
            self.ss_dict_key -= 1
            self.pi_camera.framerate = self.framerate_dict[str(self.ss_dict_key)]   #framerate設定後にssを設定
            self.pi_camera.shutter_speed = self.shutter_speed_dict[str(self.ss_dict_key)]

            #プレビュー画面に表示する情報の更新
            self.preview_display_settings()

            #TEST CODE
            print("ss_dict:" + str(self.ss_dict_key))
            print("ss:" + str(self.pi_camera.shutter_speed))
            print("fps:" + str(self.pi_camera.framerate))
        else:
            print("ss setting error (minus)")
            print("ss_dict:" + str(self.ss_dict_key))

    def auto_white_balance_plus(self):
        if self.awb_dict_key == 9:
            self.awb_dict_key = 0
        else:
            self.awb_dict_key += 1

        self.pi_camera.awb_mode = self.auto_white_balance_dict[str(self.awb_dict_key)]
        
        #プレビュー画面に表示する情報の更新
        self.preview_display_settings()

    def auto_white_balance_minus(self):
        if self.awb_dict_key == 0:
            self.awb_dict_key = 9
        else:
            self.awb_dict_key -= 1

        self.pi_camera.awb_mode = self.auto_white_balance_dict[str(self.awb_dict_key)]

        #プレビュー画面に表示する情報の更新
        self.preview_display_settings()

    def meter_mode_select(self):
        if self.meter_mode_dict_key == 3:
            self.meter_mode_dict_key = 0
        else:
            self.meter_mode_dict_key += 1

        self.pi_camera.meter_mode = self.meter_mode_dict[str(self.meter_mode_dict_key)]

        #プレビュー画面に表示する情報の更新
        self.preview_display_settings()

    def image_denoise(self):
        self.pi_camera.image_denoise = True     #defalt = True

    def take_picture(self):
        #設定情報の画面表示を停止。停止しないと、写真に設定情報が入る。
        self.pi_camera.annotate_text = ""

        ###test_code###
        self.pi_camera.exposure_mode = 'off'

        timestamp = datetime.now()
        self.pi_camera.capture('pic_' + str(timestamp) + '.jpg') #taking the picture
        
        #設定情報の画面表示を再開
        self.pi_camera.annotate_text = "mode:" + str(self.camera_mode) +\
            "\nss:" +  self.shutter_speed_display_dict[str(self.ss_dict_key)] + \
                "\niso:"+  str(self.pi_camera.iso) + \
                    "\nmeter_mode:"+  str(self.pi_camera.meter_mode) + \
                        "\nwhite_balance:"+  str(self.pi_camera.meter_mode)
        
        print("filename:" + 'pic_'  + str(timestamp) + '.jpg')
        print("sensor_mode:" + str(self.pi_camera.sensor_mode))

    def button_settings(self):
        self.iso_plus_button.when_pressed = self.iso_plus
        self.iso_minus_button.when_pressed = self.iso_minus

        self.ss_plus_button.when_pressed = self.ss_plus
        self.ss_minus_button.when_pressed = self.ss_minus

        self.awb_plus_button.when_pressed = self.auto_white_balance_plus
        self.awb_minus_button.when_pressed = self.auto_white_balance_minus

        self.meter_modes_button.when_pressed = self.meter_mode_select

        self.shutter_button.when_pressed = self.take_picture
           

class StandardCamera(CameraControl):
    """
    HQカメラsensor_mode設定一覧
    https://www.raspberrypi.org/documentation/raspbian/applications/camera.md

    ###StandardCamera###
    sensor_mode = 2
    pi_camera.resolution = (2028, 1520)
    framerate_upper_limit = 50
    framerate_lower_limit = 0.1
    ss_upper_limit = 1 / framerate_upper_limit * 1000000 = 20000
    ss_lower_limit = 1 / framerate_lower_limit * 1000000 = 10000000
    """
    def __init__(self):
        ###カメラの基本設定###
        #全般
        self.camera_state = True
        self.camera_mode = "StandardCamera"

        #iso感度設定一覧
        defalt_iso_dict_key = 0
        self.iso_dict_key = defalt_iso_dict_key
        self.iso_upper_limit_key = 8
        self.iso_lower_limit_key = -1
        
        #ss設定一覧
        #シャッター速度は1/fpsまでしか遅くできない。
        #デフォルトではframerate=30なので、33333μ秒＝1/30より遅くできない。
        defalt_ss_dict_key = -1
        self.ss_dict_key = defalt_ss_dict_key
        self.ss_upper_limit_key = 0
        self.ss_lower_limit_key = -6 #-9まで行けるが、framerateが下がると起動までの時間が伸びるので、-6までとする。

        #AWB
        defalt_awb_dict_key = 0
        self.awb_dict_key = defalt_awb_dict_key

        #測光モード設定
        defalt_meter_mode_dict_key = 0
        self.meter_mode_dict_key = defalt_meter_mode_dict_key

        #設定反映
        self.pi_camera.sensor_mode = 2
        self.pi_camera.resolution = (2028, 1520)
        self.pi_camera.iso = self.iso_sensitivity_dict[str(self.iso_dict_key)]
        self.pi_camera.shutter_speed = self.shutter_speed_dict[str(self.ss_dict_key)] 
        self.pi_camera.framerate = self.framerate_dict[str(self.ss_dict_key)] 
        self.pi_camera.awb_mode = self.auto_white_balance_dict[str(self.awb_dict_key)]
        self.pi_camera.meter_mode = self.meter_mode_dict[str(self.meter_mode_dict_key)]

class HighResolutionCamera(CameraControl):
    """    
    ###HighResolutionCamera###
    sensor_mode = 3
    pi_camera.resolution = (4056, 3040)
    framerate_upper_limit = 10
    framerate_lower_limit = 0.005
    ss_upper_limit = 1 / framerate_upper_limit * 1000000 = 100000
    ss_lower_limit = 1 / framerate_lower_limit * 1000000 = 10000000
    """
    def __init__(self):
        self.camera_state = True
        self.camera_mode = "HighResolutionCamera"

        #iso感度設定一覧
        defalt_iso_dict_key = 0
        self.iso_dict_key = defalt_iso_dict_key
        self.iso_upper_limit_key = 8
        self.iso_lower_limit_key = -1
        
        #ss設定一覧
        #シャッター速度は1/fpsまでしか遅くできない。
        #デフォルトではframerate=30なので、33333μ秒＝1/30より遅くできない。
        defalt_ss_dict_key = -3
        self.ss_dict_key = defalt_ss_dict_key
        self.ss_upper_limit_key = -3
        self.ss_lower_limit_key = -6 #-13まで行けるが、framerateが下がると起動までの時間が伸びるので、-6までとする。

        #AWB
        defalt_awb_dict_key = 0
        self.awb_dict_key = defalt_awb_dict_key

        #測光モード設定
        defalt_meter_mode_dict_key = 0
        self.meter_mode_dict_key = defalt_meter_mode_dict_key

        #カメラ側に設定を反映
        self.pi_camera.sensor_mode = 3
        self.pi_camera.resolution = (4056, 3040)    #GPUメモリが128MBでは動作しない。256MBなら動作する。
        self.pi_camera.iso = self.iso_sensitivity_dict[str(self.iso_dict_key)]
        self.pi_camera.shutter_speed = self.shutter_speed_dict[str(self.ss_dict_key)] 
        self.pi_camera.framerate = self.framerate_dict[str(self.ss_dict_key)] 
        self.pi_camera.awb_mode = self.auto_white_balance_dict[str(self.awb_dict_key)]
        self.pi_camera.meter_mode = self.meter_mode_dict[str(self.meter_mode_dict_key)]
        
class LongExposeCamera(CameraControl):
    """
    #LongExposeCamera###
    sensor_mode = 3
    pi_camera.resolution = (4056, 3040)
    framerate_upper_limit = 0.1
    framerate_lower_limit = 0.005
    ss_upper_limit = 1 / framerate_upper_limit * 1000000 = 10000000
    ss_lower_limit = 1 / framerate_lower_limit * 1000000 = 200000000
    """
    def __init__(self):
        self.camera_state = True
        self.camera_mode = "LongExposeCamera"

        #iso感度設定一覧
        defalt_iso_dict_key = 0
        self.iso_dict_key = defalt_iso_dict_key
        self.iso_upper_limit_key = 8
        self.iso_lower_limit_key = -1
        
        #ss設定一覧
        #シャッター速度は1/fpsまでしか遅くできない。
        #デフォルトではframerate=30なので、33333μ秒＝1/30より遅くできない。
        defalt_ss_dict_key = -6
        self.ss_dict_key = defalt_ss_dict_key
        self.ss_upper_limit_key = -6
        self.ss_lower_limit_key = -13 #-13まで行けるが、framerateが下がると起動までの時間が伸びるので、-6までとする。

        #AWB
        defalt_awb_dict_key = 0
        self.awb_dict_key = defalt_awb_dict_key

        #測光モード設定
        defalt_meter_mode_dict_key = 0
        self.meter_mode_dict_key = defalt_meter_mode_dict_key

        #カメラ側に設定を反映
        self.pi_camera.sensor_mode = 3
        self.pi_camera.resolution = (4056, 3040)    #GPUメモリが128MBでは動作しない。256MBなら動作する。
        self.pi_camera.iso = self.iso_sensitivity_dict[str(self.iso_dict_key)]
        self.pi_camera.shutter_speed = self.shutter_speed_dict[str(self.ss_dict_key)] 
        self.pi_camera.framerate = self.framerate_dict[str(self.ss_dict_key)] 
        self.pi_camera.awb_mode = self.auto_white_balance_dict[str(self.awb_dict_key)]
        self.pi_camera.meter_mode = self.meter_mode_dict[str(self.meter_mode_dict_key)]

    def take_picture(self):
        #設定情報の画面表示を停止。停止しないと、写真に設定情報が入る。
        self.pi_camera.annotate_text = ""

        ###test_code###
        #長時間露光する場合、恐らくexposure_mode = 'off'にする必要あり
        self.pi_camera.exposure_mode = 'off'

        timestamp = datetime.now()
        self.pi_camera.capture('pic_' + str(timestamp) + '.jpg') #taking the picture
        
        #設定情報の画面表示を再開
        self.pi_camera.annotate_text = "mode:" + str(self.camera_mode) +\
            "\nss:" +  self.shutter_speed_display_dict[str(self.ss_dict_key)] + \
                "\niso:"+  str(self.pi_camera.iso) + \
                    "\nmeter_mode:"+  str(self.pi_camera.meter_mode) + \
                        "\nwhite_balance:"+  str(self.pi_camera.meter_mode)

        print("filename:" + 'pic_'  + str(timestamp) + '.jpg')
        print("sensor_mode:" + str(self.pi_camera.sensor_mode))

class HighSpeedCamera(CameraControl):
    """
    #HighSpeedCamera###
    sensor_mode = 4
    pi_camera.resolution = (1012, 760)
    framerate_upper_limit = 120
    framerate_lower_limit = 50.1
    ss_upper_limit = 1 / framerate_upper_limit * 1000000 = 8333
    ss_lower_limit = 1 / framerate_lower_limit * 1000000 = 19960
    """
    def __init__(self):
        self.camera_state = True
        self.camera_mode = "HighSpeedCamera"

        #iso感度設定一覧
        defalt_iso_dict_key = 0
        self.iso_dict_key = defalt_iso_dict_key
        self.iso_upper_limit_key = 8
        self.iso_lower_limit_key = -1
        
        #ss設定一覧
        #シャッター速度は1/fpsまでしか遅くできない。
        defalt_ss_dict_key = 1
        self.ss_dict_key = defalt_ss_dict_key
        self.ss_upper_limit_key = 2
        self.ss_lower_limit_key = 1 #-13まで行けるが、framerateが下がると起動までの時間が伸びるので、-6までとする。

        #AWB
        defalt_awb_dict_key = 0
        self.awb_dict_key = defalt_awb_dict_key

        #測光モード設定
        defalt_meter_mode_dict_key = 0
        self.meter_mode_dict_key = defalt_meter_mode_dict_key
        
        #カメラ側に設定を反映
        self.pi_camera.sensor_mode = 4
        self.pi_camera.resolution = (1012, 760)   
        self.pi_camera.iso = self.iso_sensitivity_dict[str(self.iso_dict_key)]
        self.pi_camera.shutter_speed = self.shutter_speed_dict[str(self.ss_dict_key)] 
        self.pi_camera.framerate = self.framerate_dict[str(self.ss_dict_key)] 
        self.pi_camera.awb_mode = self.auto_white_balance_dict[str(self.awb_dict_key)]
        self.pi_camera.meter_mode = self.meter_mode_dict[str(self.meter_mode_dict_key)]

"""
# ストロボ用フォトカプラ
    pc_817_A = 5
class FlashCamera(CameraControl):
    ##ストロボ発光が同期せず
    def __init__(self):
        ###カメラの基本設定###
        #全般
        self.camera_state = True
        self.camera_mode = "FlashCamera"
        
        #ストロボ回路設定
        GPIO.setup(self.pc_817_A, GPIO.OUT)

        #iso感度設定一覧
        defalt_iso_dict_key = 0
        self.iso_dict_key = defalt_iso_dict_key
        self.iso_upper_limit_key = 8
        self.iso_lower_limit_key = -1
        
        #ss設定一覧
        #シャッター速度は1/fpsまでしか遅くできない。
        #デフォルトではframerate=30なので、33333μ秒＝1/30より遅くできない。
        defalt_ss_dict_key = -1
        self.ss_dict_key = defalt_ss_dict_key
        self.ss_upper_limit_key = 0
        self.ss_lower_limit_key = -6 #-9まで行けるが、framerateが下がると起動までの時間が伸びるので、-6までとする。

        self.pi_camera.sensor_mode = 2
        self.pi_camera.resolution = (2028, 1520)
        self.pi_camera.iso = self.iso_sensitivity_dict[str(self.iso_dict_key)]
        self.pi_camera.shutter_speed = self.shutter_speed_dict[str(self.ss_dict_key)] 
        self.pi_camera.framerate = self.framerate_dict[str(self.ss_dict_key)] 

    def take_picture(self):
        #設定情報の画面表示を停止。停止しないと、写真に設定情報が入る。
        self.pi_camera.annotate_text = ""

        timestamp_start = datetime.now()
        print("s_start:" + str(timestamp_start))

        ###test_code###
        self.pi_camera.exposure_mode = 'off'

        self.pi_camera.capture('pic_' + str(timestamp_start) + '.jpg') #taking the picture

        timestamp_stop = datetime.now()
        print("s_stop:" + str(timestamp_stop))

        #設定情報の画面表示を再開
        self.pi_camera.annotate_text = "mode:" + str(self.camera_mode) +"\nss:" +  self.shutter_speed_display_dict[str(self.ss_dict_key)] + "\niso:"+  str(self.pi_camera.iso)

    def flash_on(self):
        #ストロボ発光信号発信
        GPIO.output(self.pc_817_A, GPIO.LOW)      

        time.sleep(0.001)
        timestamp = datetime.now()
        print("flash  :" + str(timestamp))
        GPIO.output(self.pc_817_A, GPIO.HIGH)   #発光信号

        time.sleep(0.01)
        GPIO.output(self.pc_817_A, GPIO.LOW)


    def button_settings(self):
        self.iso_plus_button.when_pressed = self.iso_plus
        self.iso_minus_button.when_pressed = self.iso_minus
        self.ss_plus_button.when_pressed = self.ss_plus
        self.ss_minus_button.when_pressed = self.ss_minus

        def take_flash_photo():
            thread_flash = threading.Thread(target=self.flash_on)
            thread_shutter = threading.Thread(target=self.take_picture)

            time.sleep(0.01)
            thread_flash.start()
            thread_shutter.start()
            
        self.shutter_button.when_pressed = take_flash_photo
"""

def main():
    #インスタンス生成
    global test_camera
    test_camera = StandardCamera()
    #test_camera = HighResolutionCamera()
    #test_camera = LongExposeCamera()
    #test_camera = HighSpeedCamera()
    #test_camera = FlashCamera()

    test_camera.preview_start()

    #シャッターボタンを押すと写真を撮る
    test_camera.button_settings()
    
    while test_camera.camera_state == True:
        time.sleep(0.1)
    
try:
    main()
except KeyboardInterrupt:
    #we detect Ctrl-C then quit the program
    test_camera.preview_stop()
    test_camera.camera_state = False
    #del test_camera