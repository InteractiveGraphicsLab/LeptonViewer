# -*- coding: UTF-8 -*-
import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk
import cv2
import numpy as np
import math
import configparser
import lepton_control


class Application(tk.Frame):

    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.pack()

        # MainPanel を 全体に配置し、右クリックをpopup menu に対応付け
        self.lmain = tk.Label(root)
        self.lmain.pack()
        self.lmain.bind("<Button-3>", self.right_button_clicked)

        #Menu 作成
        self.m = tk.Menu(root, tearoff=0)
        self.m.add_command(label="ここの温度を表示", command=self.start_show_temp )
        self.m.add_command(label="温度非表示"     , command=self.stop_show_temp  )
        self.m.add_separator()
        self.m.add_command(label="設定"          , command=self.setting)

        #lepton カメラの読み込み
        try:
            self.camera = lepton_control.Lepton()
        except:
            root.destroy()
            messagebox.showwarning("Lepton Viewer", "カメラが見つかりません\nカメラを差し直してください")
            exit()

        raw = self.camera.update_frame()
        if AUTO_TONE_MAPPING:
            self.tone_min = int(np.min(raw))
            self.tone_max = int(np.min(raw))
        else:
            self.tone_min = int(config['TONE MAPPING']['manual_min'])
            self.tone_max = int(config['TONE MAPPING']['manual_max'])
        self.popup_point = self.temperature_point = (W_SIZE[0] // 2, W_SIZE[1] // 2)


    def right_button_clicked(self, event):
        self.popup_point = (event.x, event.y)
        try:
            self.m.tk_popup(event.x_root, event.y_root)
        finally:
            self.m.grab_release()


    def stop_show_temp(self):
        global SHOW_TEMPERATURE
        SHOW_TEMPERATURE = False


    def start_show_temp(self):
        global SHOW_TEMPERATURE
        SHOW_TEMPERATURE = True
        self.temperature_point = self.popup_point


    def show_lepton_frame(self) :
        # get lepton image (raw) and convert it to temperature (temp)
        raw = self.camera.update_frame(ROTATE, FLIP)
        camera_temp = self.camera.camera_temp()

        if self.camera.tlinear:
            # Lepton 3.5 (with radiometric accuracy)
            temp = raw + OFFSET
        else:
            # Lepton 3.0 (without radiometric accuracy), need to calibrate the coefficient(COEF)
            # centikelvin = (raw_data - 8192) * coefficient + camera_temperature
            temp = raw * COEF + camera_temp - 8192 * COEF + OFFSET
        temp_max = int(np.max(temp))

        #tone mapping ここまでみたよ！
        current_min = int(np.min(raw))
        current_max = int(np.max(raw))

        if AUTO_TONE_MAPPING:
            gray = np.interp(raw, (self.tone_min + BLACK_POINT, self.tone_max - WHITE_POINT), (0, 255)).astype('uint8')
        else:
            gray = np.interp(raw, (MANUAL_MIN_K, MANUAL_MAX_K), (0, 255)).astype('uint8')
        gray = np.dstack([gray, gray, gray])
        overheat = np.transpose(np.where(temp >= T_K))
        for i, j in overheat:
            gray[i, j] = lut_overheat(temp[i, j] - T_K)

        if ROTATE % 2 == 0:
            res = cv2.resize(gray, (W_SIZE[0], W_SIZE[1]), interpolation=cv2.INTER_LANCZOS4)
        else:
            res = cv2.resize(gray, (W_SIZE[1], W_SIZE[0]), interpolation=cv2.INTER_LANCZOS4)


        if WARNING_SIGN:
            if temp_max >= T_K:
                res[:5, :] = [255, 32, 32]
                res[-5:, :] = [255, 32, 32]
                res[:, :5] = [255, 32, 32]
                res[:, -5:] = [255, 32, 32]
            else:
                res[:5, :] = [32, 223, 32]
                res[-5:, :] = [32, 223, 32]
                res[:, :5] = [32, 223, 32]
                res[:, -5:] = [32, 223, 32]

        if DISPLAY_TEMP:
            text = "MAX: {:.2f}".format(centikelvin_to_celsius(temp_max))
            res = cv2.putText(res, text, (10, 25), cv2.FONT_HERSHEY_PLAIN, 1.25, (255, 255, 255), 1, cv2.LINE_AA)

        if DISPLAY_CAMERA_TEMP:
            text = "CAM: {:.2f}".format(centikelvin_to_celsius(camera_temp))
            res = cv2.putText(res, text, (W_SIZE[0]-125, 25), cv2.FONT_HERSHEY_PLAIN, 1.25, (255, 255, 255), 1, cv2.LINE_AA)

        if SHOW_TEMPERATURE:
            scale = raw.shape[1] / W_SIZE[0]
            r_p = (int(self.temperature_point[0] * scale), int(self.temperature_point[1] * scale))
            shift = int(10 * scale)
            point_temp = np.mean(temp[r_p[1]-shift : r_p[1]+shift, r_p[0]-shift : r_p[0]+shift])
            text = "{:.2f}".format(centikelvin_to_celsius(point_temp))
            res = cv2.putText(res, text, (self.temperature_point[0] - 28, self.temperature_point[1] - 20),
                              cv2.FONT_HERSHEY_PLAIN, 1.25, (32, 32, 255), 1, cv2.LINE_AA)
            res = cv2.rectangle(res, (self.temperature_point[0] + 10, self.temperature_point[1] + 10),
                                (self.temperature_point[0] - 10, self.temperature_point[1] - 10),
                                (32, 32, 255), 1, cv2.LINE_AA, 0)

        imgtk = ImageTk.PhotoImage(image=Image.fromarray(res))
        self.lmain.imgtk = imgtk
        self.lmain.configure(image=imgtk)
        self.lmain.after(1, self.show_lepton_frame)

        if AUTO_TONE_MAPPING:
            if self.camera.tlinear:
                deadband = 200
            else:
                deadband = 200 / COEF
            if self.tone_min - current_min > deadband or self.tone_min - current_min < -deadband:
                self.tone_min -= int(MAX_SPEED * (self.tone_min - current_min))
            if self.tone_max - current_max > deadband or self.tone_max - current_max < -deadband:
                self.tone_max -= int(MAX_SPEED * (self.tone_max - current_max))




    def setting(self):
        top = tk.Toplevel(self)
        top.resizable(0,0)
        top.title("設定")
        top.iconbitmap('./logo.ico')

        LF_display = tk.LabelFrame(top, text="画面設定")
        LF_display.pack(fill="both", expand="yes", padx=10, pady=5)

        display_frame1 = tk.Frame(LF_display)
        display_frame1.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        L1 = tk.Label(display_frame1, text="画面横サイズ")
        L1.pack(side=tk.LEFT)
        self.varS1 = tk.StringVar()
        self.varS1.set(W_SIZE[0])
        self.S1 = tk.Spinbox(display_frame1, from_=160, to=4000, increment=100, textvariable=self.varS1, width=6, command=self.update_view_setting)
        self.S1.pack(side=tk.RIGHT)

        display_frame2 = tk.Frame(LF_display)
        display_frame2.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.varC1 = tk.IntVar()
        if FLIP:
            self.varC1.set(1)
        self.C1 = tk.Checkbutton(display_frame2, text="左右反転", variable=self.varC1, command=self.update_view_setting)
        self.C1.pack(side=tk.LEFT)

        display_frame3 = tk.Frame(LF_display)
        display_frame3.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        L2 = tk.Label(display_frame3, text="回転")
        L2.pack(side=tk.LEFT)
        self.varR = tk.IntVar()
        self.varR.set(ROTATE)
        r1 = tk.Radiobutton(display_frame3, text="0°", value=0, variable=self.varR, command=self.update_view_setting)
        r1.pack(side=tk.LEFT)
        r2 = tk.Radiobutton(display_frame3, text="90°", value=1, variable=self.varR, command=self.update_view_setting)
        r2.pack(side=tk.LEFT)
        r3 = tk.Radiobutton(display_frame3, text="180°", value=2, variable=self.varR, command=self.update_view_setting)
        r3.pack(side=tk.LEFT)
        r3 = tk.Radiobutton(display_frame3, text="270°", value=3, variable=self.varR, command=self.update_view_setting)
        r3.pack(side=tk.LEFT)

        LF_tone = tk.LabelFrame(top, text="トーンマッピング")
        LF_tone.pack(fill="both", expand="yes", padx=10, pady=5)

        tone_frame1 = tk.Frame(LF_tone)
        tone_frame1.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.varC2 = tk.IntVar()
        if AUTO_TONE_MAPPING:
            self.varC2.set(1)
        self.C2 = tk.Checkbutton(tone_frame1, text="自動トーンマッピング", variable=self.varC2, command=self.update_tone_setting)
        self.C2.pack(side=tk.LEFT)

        tone_frame2 = tk.Frame(LF_tone)
        tone_frame2.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        L3 = tk.Label(tone_frame2, text="調整速度")
        L3.pack(side=tk.LEFT)
        self.varS3 = tk.StringVar()
        self.varS3.set(MAX_SPEED)
        self.S3 = tk.Spinbox(tone_frame2, from_=0.005, to=1, format="%.3f", increment=0.005, textvariable=self.varS3, width=6, command=self.update_tone_setting)
        if not self.varC2:
            self.S3.configure(state=tk.DISABLED)
        self.S3.pack(side=tk.RIGHT)

        tone_frame3 = tk.Frame(LF_tone)
        tone_frame3.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        L4 = tk.Label(tone_frame3, text="ブラックポイント")
        L4.pack(side=tk.LEFT)
        self.varS4 = tk.StringVar()
        self.varS4.set(BLACK_POINT)
        self.S4 = tk.Spinbox(tone_frame3, from_=-1000, to=1000, increment=50, textvariable=self.varS4, width=6, command=self.update_tone_setting)
        self.S4.pack(side=tk.RIGHT)

        tone_frame4 = tk.Frame(LF_tone)
        tone_frame4.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        L5 = tk.Label(tone_frame4, text="ホワイトポイント")
        L5.pack(side=tk.LEFT)
        self.varS5 = tk.StringVar()
        self.varS5.set(WHITE_POINT)
        self.S5 = tk.Spinbox(tone_frame4, from_=-1000, to=1000, increment=50, textvariable=self.varS5, width=6, command=self.update_tone_setting)
        self.S5.pack(side=tk.RIGHT)

        tone_frame5 = tk.Frame(LF_tone)
        tone_frame5.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        L6 = tk.Label(tone_frame5, text="手動マッピング温度 min")
        L6.pack(side=tk.LEFT)
        self. varS6 = tk.StringVar()
        self.varS6.set(MANUAL_MIN)
        self.S6 = tk.Spinbox(tone_frame5, from_=-100, to=500, increment=1, textvariable=self.varS6, width=6, command=self.update_tone_setting)
        if self.varC2:
            self.S6.configure(state=tk.DISABLED)
        self.S6.pack(side=tk.RIGHT)
        tone_frame6 = tk.Frame(LF_tone)
        tone_frame6.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        L7 = tk.Label(tone_frame6, text="手動マッピング温度 max")
        L7.pack(side=tk.LEFT)
        self.varS7 = tk.StringVar()
        self.varS7.set(MANUAL_MAX)
        self.S7 = tk.Spinbox(tone_frame6, from_=-100, to=500, increment=1, textvariable=self.varS7, width=6, command=self.update_tone_setting)
        if self.varC2:
            self.S7.configure(state=tk.DISABLED)
        self.S7.pack(side=tk.RIGHT)

        LF_thershold = tk.LabelFrame(top, text="閾値")
        LF_thershold.pack(fill="both", expand="yes", padx=10, pady=5)

        thershold_frame1 = tk.Frame(LF_thershold)
        thershold_frame1.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        L8 = tk.Label(thershold_frame1, text="閾値温度")
        L8.pack(side=tk.LEFT)
        self.varS8 = tk.StringVar()
        self.varS8.set(T_C)
        self.S8 = tk.Spinbox(thershold_frame1, from_=-100, to=500, format ="%.2f", increment=0.1, width=6, textvariable=self.varS8, command=self.update_thershold_setting)
        self.S8.pack(side=tk.RIGHT)

        thershold_frame2 = tk.Frame(LF_thershold)
        thershold_frame2.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.varC3 = tk.IntVar()
        if WARNING_SIGN:
            self.varC3.set(1)
        self.C3 = tk.Checkbutton(thershold_frame2, text="超過表示", variable=self.varC3, command=self.update_thershold_setting)
        self.C3.pack(side=tk.LEFT)

        thershold_frame3 = tk.Frame(LF_thershold)
        thershold_frame3.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.varC4 = tk.IntVar()
        if DISPLAY_TEMP:
            self.varC4.set(1)
        C4 = tk.Checkbutton(thershold_frame3, text="最大温度表示", variable=self.varC4, command=self.update_thershold_setting)
        C4.pack(side=tk.LEFT)

        thershold_frame4 = tk.Frame(LF_thershold)
        thershold_frame4.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.varC5 = tk.IntVar()
        if DISPLAY_CAMERA_TEMP:
            self.varC5.set(1)
        C5 = tk.Checkbutton(thershold_frame4, text="カメラ温度表示", variable=self.varC5, command=self.update_thershold_setting)
        C5.pack(side=tk.LEFT)

        LF_calibration = tk.LabelFrame(top, text="キャリブレーション")
        LF_calibration.pack(fill="both", expand="yes", padx=10, pady=5)

        calibration_frame1 = tk.Frame(LF_calibration)
        calibration_frame1.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        L9 = tk.Label(calibration_frame1, text="オフセット")
        L9.pack(side=tk.LEFT)
        self.varS9 = tk.StringVar()
        self.varS9.set(OFFSET)
        self.S9 = tk.Spinbox(calibration_frame1, from_=-100, to=100, format ="%.2f", increment=0.1, width=6, textvariable=self.varS9, command=self.update_calibration)
        self.S9.pack(side=tk.RIGHT)

        calibration_frame2 = tk.Frame(LF_calibration)
        calibration_frame2.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        L10 = tk.Label(calibration_frame2, text="係数（Lepton 3.0 のみ有効）")
        L10.pack(side=tk.LEFT)
        self.varS10 = tk.StringVar()
        self.varS10.set(COEF / 100)
        self.S10 = tk.Spinbox(calibration_frame2, from_=-100, to=100, format ="%.3f", increment=0.001, width=6, textvariable=self.varS10, command=self.update_calibration)
        if self.camera.tlinear:
            self.S10.configure(state=tk.DISABLED)
        self.S10.pack(side=tk.RIGHT)

        calibration_frame3 = tk.Frame(LF_calibration)
        calibration_frame3.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        if self.camera.tlinear:
            L11 = tk.Label(calibration_frame3, text="このカメラは Radiometric Accuracy に対応\nしています\n温度 = Output - 273.15 + オフセット",
                           justify=tk.LEFT)
        else:
            L11 = tk.Label(calibration_frame3, text="このカメラは Radiometric Accuracy に対応\nしていません\n温度 = 係数 * (Output - 8192) + カメラ温度\n- 273.15 + オフセット",
                           justify=tk.LEFT)
        L11.pack(side=tk.LEFT)


        save_frame = tk.Frame(top)
        save_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        saveButton = tk.Button(save_frame, text="保存", width=8, command=self.save_setting)
        saveButton.pack(side=tk.RIGHT)

    def update_view_setting(self):
        global FLIP, ROTATE, W_SIZE, SHOW_TEMPERATURE
        if self.varC1.get() == 0:
            FLIP = False
        else:
            FLIP = True
        ROTATE = self.varR.get()
        W_SIZE[0] = int(self.S1.get())
        W_SIZE[1] = int(W_SIZE[0] * 3 // 4)
        SHOW_TEMPERATURE = False

    def update_tone_setting(self):
        global AUTO_TONE_MAPPING, MAX_SPEED, BLACK_POINT, WHITE_POINT, MANUAL_MIN, MANUAL_MAX, MANUAL_MIN_K, MANUAL_MAX_K
        if self.varC2.get() == 0:
            AUTO_TONE_MAPPING = False
            self.S3.configure(state=tk.DISABLED)
            self.S6.configure(state=tk.NORMAL)
            self.S7.configure(state=tk.NORMAL)
        else:
            AUTO_TONE_MAPPING = True
            self.S3.configure(state=tk.NORMAL)
            self.S6.configure(state=tk.DISABLED)
            self.S7.configure(state=tk.DISABLED)
        MAX_SPEED = float(self.S3.get())
        BLACK_POINT = int(self.S4.get())
        WHITE_POINT = int(self.S5.get())
        MANUAL_MIN = int(self.S6.get())
        MANUAL_MIN_K = celsius_to_centikelvin(MANUAL_MIN)
        MANUAL_MAX = int(self.S7.get())
        MANUAL_MAX_K = celsius_to_centikelvin(MANUAL_MAX)

    def update_thershold_setting(self):
        global T_C, T_K, WARNING_SIGN, DISPLAY_TEMP, DISPLAY_CAMERA_TEMP
        T_C = float(self.S8.get())
        T_K = celsius_to_centikelvin(T_C)
        if self.varC3.get() == 0:
            WARNING_SIGN = False
        else:
            WARNING_SIGN = True
        if self.varC4.get() == 0:
            DISPLAY_TEMP = False
        else:
            DISPLAY_TEMP = True
        if self.varC5.get() == 0:
            DISPLAY_CAMERA_TEMP = False
        else:
            DISPLAY_CAMERA_TEMP = True

    def update_calibration(self):
        global OFFSET, COEF
        OFFSET = int(float(self.S9.get()) * 100)
        COEF = float(self.S10.get()) * 100

    def save_setting(self):
        config = configparser.RawConfigParser()

        config.add_section('VIEWER')
        config.set('VIEWER', 'window_width', str(W_SIZE[0]))
        config.set('VIEWER', 'flip', "{}".format(FLIP))
        config.set('VIEWER', 'rotate', str(ROTATE))

        config.add_section('TONE MAPPING')
        config.set('TONE MAPPING', 'auto', "{}".format(AUTO_TONE_MAPPING))
        config.set('TONE MAPPING', 'speed', str(MAX_SPEED))
        config.set('TONE MAPPING', 'black_point', str(BLACK_POINT))
        config.set('TONE MAPPING', 'white_point', str(WHITE_POINT))
        config.set('TONE MAPPING', 'manual_min', str(MANUAL_MIN))
        config.set('TONE MAPPING', 'manual_max', str(MANUAL_MAX))

        config.add_section('THERSHOLD')
        config.set('THERSHOLD', 'temperature', str(T_C))
        config.set('THERSHOLD', 'warning_sign', "{}".format(WARNING_SIGN))
        config.set('THERSHOLD', 'display_temperature', "{}".format(DISPLAY_TEMP))
        config.set('THERSHOLD', 'display_camera_temperature', "{}".format(DISPLAY_CAMERA_TEMP))

        config.add_section('CALIBRATION')
        config.set('CALIBRATION', 'offset', str(OFFSET))
        config.set('CALIBRATION', 'coefficient', str(COEF / 100))

        with open('./config.ini', 'w') as configfile:
            config.write(configfile)

    def on_closing(self):
        self.camera.stop_streaming()
        root.destroy()

def lut_overheat(x):
    rgb = np.array([255, round(math.pow(1.005, -x) * 128), 32], np.uint8)
    return rgb

def celsius_to_centikelvin(c):
    return int(c * 100 + 27315)

def centikelvin_to_celsius(t):
    return (t - 27315) / 100


config = configparser.ConfigParser()
config.read("./config.ini")

W_SIZE = [int(config['VIEWER']['window_width']), int(config['VIEWER']['window_width']) * 3 // 4]
FLIP = config.getboolean('VIEWER', 'flip')
ROTATE = int(config['VIEWER']['rotate'])

AUTO_TONE_MAPPING = config.getboolean('TONE MAPPING', 'auto')
MAX_SPEED = float(config['TONE MAPPING']['speed'])
BLACK_POINT = int(config['TONE MAPPING']['black_point'])
WHITE_POINT = int(config['TONE MAPPING']['white_point'])
MANUAL_MIN = float(config['TONE MAPPING']['manual_min'])
MANUAL_MIN_K = celsius_to_centikelvin(MANUAL_MIN)
MANUAL_MAX = float(config['TONE MAPPING']['manual_max'])
MANUAL_MAX_K = celsius_to_centikelvin(MANUAL_MAX)

T_C = float(config['THERSHOLD']['temperature'])
T_K = celsius_to_centikelvin(T_C)
DISPLAY_TEMP = config.getboolean('THERSHOLD', 'display_temperature')
DISPLAY_CAMERA_TEMP = config.getboolean('THERSHOLD', 'display_camera_temperature')
WARNING_SIGN = config.getboolean('THERSHOLD', 'warning_sign')

OFFSET = int(config['CALIBRATION']['offset'])
COEF = float(config['CALIBRATION']['coefficient']) * 100

SHOW_TEMPERATURE = False


if __name__ == "__main__":
    root = tk.Tk()
    app = Application(master=root)
    root.title("Lepton Viewer")
    root.iconbitmap('./logo.ico')
    root.protocol("WM_DELETE_WINDOW", app.on_closing)


    app.show_lepton_frame()
    app.mainloop()
