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
        self.lmain = tk.Label(root)
        self.lmain.pack()
        self.m = tk.Menu(root, tearoff=0)
        self.m.add_command(label="設定", command=self.setting)
        # m.add_separator()
        self.lmain.bind("<Button-3>", self.popup_menu)
        try:
            self.camera = lepton_control.Lepton()
        except:
            root.destroy()
            messagebox.showwarning("Lepton Viewer", "カメラが見つかりません\nカメラを差し直してください")
            exit()

        if auto_tone_mapping:
            raw = self.camera.update_frame()
            self.tone_min = int(raw.min())
            self.tone_max = int(raw.max())
        else:
            self.tone_min = int(config['TONE MAPPING']['manual_min'])
            self.tone_max = int(config['TONE MAPPING']['manual_max'])

    def popup_menu(self, event):
        try:
            self.m.tk_popup(event.x_root, event.y_root)
        finally:
            self.m.grab_release()

    def show_lepton_frame(self):
        raw = self.camera.update_frame()
        current_min = int(raw.min())
        current_max = int(raw.max())
        if auto_tone_mapping:
            gray = np.interp(raw, (self.tone_min + black_p, self.tone_max - white_p), (0, 255)).astype('uint8')
        else:
            gray = np.interp(raw, (manual_min_k, manual_max_k), (0, 255)).astype('uint8')
        gray = np.dstack([gray, gray, gray])
        overheat = np.transpose(np.where(raw >= t_k))
        for i, j in overheat:
            gray[i, j] = lut_overheat(raw[i, j] - t_k)
        if flip:
            gray = cv2.flip(gray, 1)
        if rotate == 0:
            res = cv2.resize(gray, (w_size[0], w_size[1]), interpolation=cv2.INTER_LANCZOS4)
        if rotate == 1:
            gray = cv2.rotate(gray, cv2.ROTATE_90_CLOCKWISE)
            res = cv2.resize(gray, (w_size[1], w_size[0]), interpolation=cv2.INTER_LANCZOS4)
        elif rotate == 2:
            gray = cv2.rotate(gray, cv2.ROTATE_180)
            res = cv2.resize(gray, (w_size[0], w_size[1]), interpolation=cv2.INTER_LANCZOS4)
        elif rotate == 3:
            gray = cv2.rotate(gray, cv2.ROTATE_90_COUNTERCLOCKWISE)
            res = cv2.resize(gray, (w_size[1], w_size[0]), interpolation=cv2.INTER_LANCZOS4)

        if warning_sign:
            if current_max >= t_k:
                res[:5, :] = [255, 32, 32]
                res[-5:, :] = [255, 32, 32]
                res[:, :5] = [255, 32, 32]
                res[:, -5:] = [255, 32, 32]
            else:
                res[:5, :] = [32, 223, 32]
                res[-5:, :] = [32, 223, 32]
                res[:, :5] = [32, 223, 32]
                res[:, -5:] = [32, 223, 32]
        if display_temp:
            text = "{:.2f}".format(centikelvin_to_celsius(current_max))
            res = cv2.putText(res, text, (10, 30), cv2.FONT_HERSHEY_PLAIN, 1.5, (255, 255, 255), 1)
        imgtk = ImageTk.PhotoImage(image=Image.fromarray(res))
        self.lmain.imgtk = imgtk
        self.lmain.configure(image=imgtk)
        self.lmain.after(1, self.show_lepton_frame)

        # Auto tone mapping
        if auto_tone_mapping:
            if self.tone_min - current_min > 200 or self.tone_min - current_min < -200:
                self.tone_min -= int(map_speed * (self.tone_min - current_min))
            if self.tone_max - current_max > 200 or self.tone_max - current_max < -200:
                self.tone_max -= int(map_speed * (self.tone_max - current_max))

    def setting(self):
        top = tk.Toplevel(self)
        top.resizable(0,0)
        top.title("設定")
        top.iconbitmap('./logo.ico')

        LF_display = tk.LabelFrame(top, text="画面設定")
        LF_display.pack(fill="both", expand="yes", padx=10, pady=10)

        display_frame1 = tk.Frame(LF_display)
        display_frame1.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        L1 = tk.Label(display_frame1, text="画面横サイズ")
        L1.pack(side=tk.LEFT)
        self.varS1 = tk.StringVar()
        self.varS1.set(w_size[0])
        self.S1 = tk.Spinbox(display_frame1, from_=160, to=4000, increment=100, textvariable=self.varS1, width=6, command=self.updateViewSetting)
        self.S1.pack(side=tk.RIGHT)

        display_frame2 = tk.Frame(LF_display)
        display_frame2.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.varC1 = tk.IntVar()
        if flip:
            self.varC1.set(1)
        self.C1 = tk.Checkbutton(display_frame2, text="左右反転", variable=self.varC1, command=self.updateViewSetting)
        self.C1.pack(side=tk.LEFT)

        display_frame3 = tk.Frame(LF_display)
        display_frame3.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        L2 = tk.Label(display_frame3, text="回転")
        L2.pack(side=tk.LEFT)
        self.varR = tk.IntVar()
        self.varR.set(rotate)
        r1 = tk.Radiobutton(display_frame3, text="0°", value=0, variable=self.varR, command=self.updateViewSetting)
        r1.pack(side=tk.LEFT)
        r2 = tk.Radiobutton(display_frame3, text="90°", value=1, variable=self.varR, command=self.updateViewSetting)
        r2.pack(side=tk.LEFT)
        r3 = tk.Radiobutton(display_frame3, text="180°", value=2, variable=self.varR, command=self.updateViewSetting)
        r3.pack(side=tk.LEFT)
        r3 = tk.Radiobutton(display_frame3, text="270°", value=3, variable=self.varR, command=self.updateViewSetting)
        r3.pack(side=tk.LEFT)

        LF_tone = tk.LabelFrame(top, text="トーンマッピング")
        LF_tone.pack(fill="both", expand="yes", padx=10, pady=10)

        tone_frame1 = tk.Frame(LF_tone)
        tone_frame1.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.varC2 = tk.IntVar()
        if auto_tone_mapping:
            self.varC2.set(1)
        self.C2 = tk.Checkbutton(tone_frame1, text="自動トーンマッピング", variable=self.varC2, command=self.updateToneSetting)
        self.C2.pack(side=tk.LEFT)

        tone_frame2 = tk.Frame(LF_tone)
        tone_frame2.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        L3 = tk.Label(tone_frame2, text="速度")
        L3.pack(side=tk.LEFT)
        self.varS3 = tk.StringVar()
        self.varS3.set(map_speed)
        self.S3 = tk.Spinbox(tone_frame2, from_=0.005, to=1, format="%.3f", increment=0.005, textvariable=self.varS3, width=6, command=self.updateToneSetting)
        self.S3.pack(side=tk.RIGHT)

        tone_frame3 = tk.Frame(LF_tone)
        tone_frame3.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        L4 = tk.Label(tone_frame3, text="ブラックポイント")
        L4.pack(side=tk.LEFT)
        self.varS4 = tk.StringVar()
        self.varS4.set(black_p)
        self.S4 = tk.Spinbox(tone_frame3, from_=-1000, to=1000, increment=50, textvariable=self.varS4, width=6, command=self.updateToneSetting)
        self.S4.pack(side=tk.RIGHT)

        tone_frame4 = tk.Frame(LF_tone)
        tone_frame4.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        L5 = tk.Label(tone_frame4, text="ホワイトポイント")
        L5.pack(side=tk.LEFT)
        self.varS5 = tk.StringVar()
        self.varS5.set(white_p)
        self.S5 = tk.Spinbox(tone_frame4, from_=-1000, to=1000, increment=50, textvariable=self.varS5, width=6, command=self.updateToneSetting)
        self.S5.pack(side=tk.RIGHT)

        tone_frame5 = tk.Frame(LF_tone)
        tone_frame5.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        L6 = tk.Label(tone_frame5, text="手動マッピング温度 min")
        L6.pack(side=tk.LEFT)
        self. varS6 = tk.StringVar()
        self.varS6.set(manual_min)
        self.S6 = tk.Spinbox(tone_frame5, from_=-100, to=500, increment=1, textvariable=self.varS6, width=6, command=self.updateToneSetting)
        if self.varC2:
            self.S6.configure(state=tk.DISABLED)
        self.S6.pack(side=tk.RIGHT)
        tone_frame6 = tk.Frame(LF_tone)
        tone_frame6.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        L7 = tk.Label(tone_frame6, text="手動マッピング温度 max")
        L7.pack(side=tk.LEFT)
        self.varS7 = tk.StringVar()
        self.varS7.set(manual_max)
        self.S7 = tk.Spinbox(tone_frame6, from_=-100, to=500, increment=1, textvariable=self.varS7, width=6, command=self.updateToneSetting)
        if self.varC2:
            self.S7.configure(state=tk.DISABLED)
        self.S7.pack(side=tk.RIGHT)

        LF_thershold = tk.LabelFrame(top, text="閾値")
        LF_thershold.pack(fill="both", expand="yes", padx=10, pady=10)

        thershold_frame1 = tk.Frame(LF_thershold)
        thershold_frame1.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        L8 = tk.Label(thershold_frame1, text="閾値温度")
        L8.pack(side=tk.LEFT)
        self.varS8 = tk.StringVar()
        self.varS8.set(t_c)
        self.S8 = tk.Spinbox(thershold_frame1, from_=-100, to=500, format ="%.2f", increment=0.1, width=6, textvariable=self.varS8, command=self.updateTemp)
        self.S8.pack(side=tk.RIGHT)

        thershold_frame2 = tk.Frame(LF_thershold)
        thershold_frame2.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.varC3 = tk.IntVar()
        if warning_sign:
            self.varC3.set(1)
        self.C3 = tk.Checkbutton(thershold_frame2, text="超過表示", variable=self.varC3, command=self.updateDisplaySetting)
        self.C3.pack(side=tk.LEFT)

        thershold_frame3 = tk.Frame(LF_thershold)
        thershold_frame3.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.varC4 = tk.IntVar()
        if display_temp:
            self.varC4.set(1)
        C4 = tk.Checkbutton( thershold_frame3, text="最大温度表示", variable=self.varC4, command=self.updateDisplaySetting)
        C4.pack(side=tk.LEFT)

        save_frame = tk.Frame(top)
        save_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        saveButton = tk.Button(save_frame, text="保存", width=8, command=self.saveSetting)
        saveButton.pack(side=tk.RIGHT)

    def updateViewSetting(self):
        global flip, rotate, w_size
        if self.varC1.get() == 0:
            flip = False
        else:
            flip = True
        rotate = self.varR.get()
        w_size[0] = int(self.S1.get())
        w_size[1] =  w_size[0] * 3 // 4

    def updateToneSetting(self):
        global auto_tone_mapping, map_speed, black_p, white_p, manual_min, manual_max, manual_min_k, manual_max_k
        if self.varC2.get() == 0:
            auto_tone_mapping = False
            self.S6.configure(state=tk.NORMAL)
            self.S7.configure(state=tk.NORMAL)
        else:
            auto_tone_mapping = True
            self.S6.configure(state=tk.DISABLED)
            self.S7.configure(state=tk.DISABLED)
        map_speed = float(self.S3.get())
        black_p = int(self.S4.get())
        white_p = int(self.S5.get())
        manual_min = int(self.S6.get())
        manual_min_k = celsius_to_centikelvin(manual_min)
        manual_max = int(self.S7.get())
        manual_max_k = celsius_to_centikelvin(manual_max)

    def updateTemp(self):
        global t_c, t_k
        t_c = float(self.S8.get())
        t_k = celsius_to_centikelvin(t_c)

    def updateDisplaySetting(self):
        global warning_sign, display_temp
        if self.varC3.get() == 0:
            warning_sign = False
        else:
            warning_sign = True
        if self.varC4.get() == 0:
            display_temp = False
        else:
            display_temp = True

    def saveSetting(self):
        config = configparser.RawConfigParser()

        config.add_section('VIEWER')
        config.set('VIEWER', 'window_width', str(w_size[0]))
        config.set('VIEWER', 'flip', "{}".format(flip))
        config.set('VIEWER', 'rotate', str(rotate))

        config.add_section('TONE MAPPING')
        config.set('TONE MAPPING', 'auto', "{}".format(auto_tone_mapping))
        config.set('TONE MAPPING', 'speed', str(map_speed))
        config.set('TONE MAPPING', 'black_point', str(black_p))
        config.set('TONE MAPPING', 'white_point', str(white_p))
        config.set('TONE MAPPING', 'manual_min', str(manual_min))
        config.set('TONE MAPPING', 'manual_max', str(manual_max))

        config.add_section('THERSHOLD')
        config.set('THERSHOLD', 'temputure', str(t_c))
        config.set('THERSHOLD', 'warning_sign', "{}".format(warning_sign))
        config.set('THERSHOLD', 'display_temputure', "{}".format(display_temp))

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

w_size = [int(config['VIEWER']['window_width']), int(config['VIEWER']['window_width']) * 3 // 4]
flip = config.getboolean('VIEWER', 'flip')
rotate = int(config['VIEWER']['rotate'])

auto_tone_mapping = config.getboolean('TONE MAPPING', 'auto')
map_speed = float(config['TONE MAPPING']['speed'])
black_p = int(config['TONE MAPPING']['black_point'])
white_p = int(config['TONE MAPPING']['white_point'])
manual_min = float(config['TONE MAPPING']['manual_min'])
manual_min_k = celsius_to_centikelvin(manual_min)
manual_max = float(config['TONE MAPPING']['manual_max'])
manual_max_k = celsius_to_centikelvin(manual_max)

t_c = float(config['THERSHOLD']['temputure'])
t_k = celsius_to_centikelvin(t_c)
display_temp = config.getboolean('THERSHOLD', 'display_temputure')
warning_sign = config.getboolean('THERSHOLD', 'warning_sign')


if __name__ == "__main__":
    root = tk.Tk()
    app = Application(master=root)
    root.title("Lepton Viewer")
    root.iconbitmap('./logo.ico')
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.show_lepton_frame()
    app.mainloop()
