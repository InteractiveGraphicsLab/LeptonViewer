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

        # Menu 作成
        self.m = tk.Menu(root, tearoff=0)
        self.m.add_command(label="ここの温度を表示", command=self.start_show_temp)
        self.m.add_command(label="温度非表示", command=self.stop_show_temp)
        self.m.add_separator()
        self.m.add_command(label="設定", command=self.setting)

        # lepton カメラの読み込み
        try:
            self.camera = lepton_control.Lepton()
        except:
            root.destroy()
            messagebox.showwarning("Lepton Viewer", "カメラが見つかりません\nカメラを差し直してください")
            exit()
        self.popup_point = self.temperature_point = (W_SIZE[0] // 2, W_SIZE[1] // 2)

    def right_button_clicked(self, event):
        self.popup_point = (event.x, event.y)
        try:
            self.m.tk_popup(event.x_root, event.y_root)
        finally:
            self.m.grab_release()

    def stop_show_temp(self):
        global SHOW_TEMP_AT_POINT
        SHOW_TEMP_AT_POINT = False
        self.temperature_point = (W_SIZE[0] // 2, W_SIZE[1] // 2)

    def start_show_temp(self):
        global SHOW_TEMP_AT_POINT
        SHOW_TEMP_AT_POINT = True
        self.temperature_point = self.popup_point

    def show_lepton_frame(self):
        # get lepton image (raw) and convert it to temperature (temp)
        raw_img, temp_img = self.camera.update_frame(ROTATE, FLIP, COEFFICIENT, OFFSET)
        temp_max = int(np.max(temp_img))
        camera_temp = self.camera.camera_temp()

        # tone mapping
        gray = np.interp(temp_img, (TONE_MIN, TONE_MAX), (0, 255)).astype('uint8')
        gray = np.dstack([gray, gray, gray])

        # paint overheat pixels in RED
        overheat = np.transpose(np.where(temp_img >= THRESHOLD))
        for i, j in overheat:
            gray[i, j] = lut_overheat(temp_img[i, j] - THRESHOLD)

        if ROTATE % 2 == 0:
            res = cv2.resize(gray, (W_SIZE[0], W_SIZE[1]), interpolation=cv2.INTER_LANCZOS4)
        else:
            res = cv2.resize(gray, (W_SIZE[1], W_SIZE[0]), interpolation=cv2.INTER_LANCZOS4)

        if temp_max >= THRESHOLD:
            res[:5, :] = [255, 32, 32]
            res[-5:, :] = [255, 32, 32]
            res[:, :5] = [255, 32, 32]
            res[:, -5:] = [255, 32, 32]
        else:
            res[:5, :] = [32, 223, 32]
            res[-5:, :] = [32, 223, 32]
            res[:, :5] = [32, 223, 32]
            res[:, -5:] = [32, 223, 32]

        if SHOW_MAXTEMP:
            text = "MAX: {:.2f}".format(temp_max)
            res = cv2.putText(res, text, (10, 25), cv2.FONT_HERSHEY_PLAIN, 1.25, (255, 255, 255), 1, cv2.LINE_AA)

        if SHOW_CAMTEMP:
            text = "CAM: {:.2f}".format(camera_temp)
            res = cv2.putText(res, text, (W_SIZE[0]-125, 25), cv2.FONT_HERSHEY_PLAIN, 1.25, (255, 255, 255), 1, cv2.LINE_AA)

        if SHOW_TEMP_AT_POINT:
            scale = raw_img.shape[1] / W_SIZE[0]
            r_p = (int(self.temperature_point[0] * scale), int(self.temperature_point[1] * scale))
            shift = int(10 * scale)
            point_temp = np.mean(temp_img[r_p[1]-shift : r_p[1]+shift, r_p[0]-shift : r_p[0]+shift])
            text = "{:.2f}".format(point_temp)
            res = cv2.putText(res, text, (self.temperature_point[0] - 28, self.temperature_point[1] - 20),
                              cv2.FONT_HERSHEY_PLAIN, 1.25, (32, 32, 255), 1, cv2.LINE_AA)
            res = cv2.rectangle(res, (self.temperature_point[0] + 10, self.temperature_point[1] + 10),
                                (self.temperature_point[0] - 10, self.temperature_point[1] - 10),
                                (32, 32, 255), 1, cv2.LINE_AA, 0)

        imgtk = ImageTk.PhotoImage(image=Image.fromarray(res))
        self.lmain.imgtk = imgtk
        self.lmain.configure(image=imgtk)
        self.lmain.after(1, self.show_lepton_frame)

    def setting(self):
        top = tk.Toplevel(self)
        top.resizable(0,0)
        top.title("設定")
        top.iconbitmap('./logo.ico')

        # 画面設定 -----------------------------------------------------------
        LF_display = tk.LabelFrame(top, text="画面設定")
        LF_display.pack(fill="both", expand="yes", padx=10, pady=5)

        display_frame1 = tk.Frame(LF_display)
        display_frame1.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        L1 = tk.Label(display_frame1, text="画面横サイズ")
        L1.pack(side=tk.LEFT)
        self.var_dispsize = tk.StringVar()
        self.var_dispsize.set(W_SIZE[0])
        self.spin_dispsize = tk.Spinbox(display_frame1, from_=160, to=4000, increment=100, textvariable=self.var_dispsize, width=6, command=self.update_view_setting)
        self.spin_dispsize.pack(side=tk.LEFT)

        display_frame2 = tk.Frame(LF_display)
        display_frame2.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.var_flip = tk.IntVar()
        if FLIP:
            self.var_flip.set(1)
        self.check_flip = tk.Checkbutton(display_frame2, text="左右反転", variable=self.var_flip, command=self.update_view_setting)
        self.check_flip.pack(side=tk.LEFT)

        display_frame3 = tk.Frame(LF_display)
        display_frame3.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        L2 = tk.Label(display_frame3, text="回転")
        self.var_rot = tk.IntVar()
        self.var_rot.set(ROTATE)
        r1 = tk.Radiobutton(display_frame3, text="0°  ", value=0, variable=self.var_rot, command=self.update_view_setting)
        r2 = tk.Radiobutton(display_frame3, text="90° ", value=1, variable=self.var_rot, command=self.update_view_setting)
        r3 = tk.Radiobutton(display_frame3, text="180°", value=2, variable=self.var_rot, command=self.update_view_setting)
        r4 = tk.Radiobutton(display_frame3, text="270°", value=3, variable=self.var_rot, command=self.update_view_setting)
        L2.pack(side=tk.LEFT)
        r1.pack(side=tk.LEFT)
        r2.pack(side=tk.LEFT)
        r3.pack(side=tk.LEFT)
        r4.pack(side=tk.LEFT)

        display_frame4 = tk.Frame(LF_display)
        display_frame4.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.var_maxtemp = tk.IntVar()
        self.var_camtemp = tk.IntVar()
        if SHOW_MAXTEMP:
            self.var_maxtemp.set(1)
        if SHOW_CAMTEMP:
            self.var_camtemp.set(1)
        check_maxtemp = tk.Checkbutton(display_frame4, text="最大温度表示 ", variable=self.var_maxtemp, command=self.update_view_setting)
        check_camtemp = tk.Checkbutton(display_frame4, text="カメラ温度表示", variable=self.var_camtemp, command=self.update_view_setting)
        check_maxtemp.pack(side=tk.LEFT)
        check_camtemp.pack(side=tk.LEFT)

        # トーンマッピング --------------------------------------------------------------------------------
        LF_tone = tk.LabelFrame(top, text="Tone mapping")
        LF_tone.pack(fill="both", expand="yes", padx=10, pady=5)

        tone_label1 = tk.Label(LF_tone, text="  min[℃]")
        tone_label2 = tk.Label(LF_tone, text="  max[℃]")
        tone_label1.grid(row=0, column=0, padx=5, pady=5)
        tone_label2.grid(row=0, column=2, padx=5, pady=5)
        self.var_tonemin = tk.StringVar()
        self.var_tonemax = tk.StringVar()
        self.var_tonemin.set(TONE_MIN)
        self.var_tonemax.set(TONE_MAX)
        self.spin_tonemin = tk.Spinbox(LF_tone, from_=-100, to=500, increment=1, textvariable=self.var_tonemin, width=6, command=self.update_tone_setting)
        self.spin_tonemax = tk.Spinbox(LF_tone, from_=-100, to=500, increment=1, textvariable=self.var_tonemax, width=6, command=self.update_tone_setting)
        self.spin_tonemin.grid(row=0, column=1, padx=5, pady=5)
        self.spin_tonemax.grid(row=0, column=3, padx=5, pady=5)

        # threshold --------------------------------------------------------------------------------
        LF_thershold = tk.LabelFrame(top, text="Threshold - 超過温度可視化")
        LF_thershold.pack(fill="both", expand="yes", padx=10, pady=5, ipady=5)

        L8 = tk.Label(LF_thershold, text="    閾値温度[℃] ")
        L8.pack(side=tk.LEFT)
        self.var_threshold = tk.StringVar()
        self.var_threshold.set(THRESHOLD)
        self.spin_threshold = tk.Spinbox(LF_thershold, from_=-100, to=500, format ="%.2f", increment=0.1, width=6, textvariable=self.var_threshold, command=self.update_threshold_setting)
        self.spin_threshold.pack(side=tk.LEFT)

        # calibration  --------------------------------------------------------------------------------
        LF_calibration = tk.LabelFrame(top, text="Calibration")
        LF_calibration.pack(fill="both", expand="yes", padx=10, pady=5)

        label_ofst = tk.Label(LF_calibration, text="offset [℃]")
        self.var_offset = tk.StringVar()
        self.var_offset.set(OFFSET)
        self.spin_ofst = tk.Spinbox(LF_calibration, from_=-100, to=100, format ="%.2f", increment=0.1, width=6, textvariable=self.var_offset, command=self.update_calibration)

        label_coef = tk.Label(LF_calibration, text="coef (Lepton 3.0 のみ）")
        self.var_coef = tk.StringVar()
        self.var_coef.set(COEFFICIENT)
        self.spin_coef = tk.Spinbox(LF_calibration, from_=-100, to=100, format ="%.3f", increment=0.001, width=6, textvariable=self.var_coef, command=self.update_calibration)
        if self.camera.tlinear:
            self.spin_coef.configure(state=tk.DISABLED)

        if self.camera.tlinear:
            message = "このカメラはRadiometric Accuracy に対応\nしています\n 温度 = Output - 273.15 + offset"
        else:
            message = "このカメラはRadiometric Accuracy に対応\nしていません\n温度 = coef * (Output - 8192) + カメラ温度\n- 273.15 + offset"
        label_message = tk.Label(LF_calibration, text=message, justify=tk.LEFT)
        label_ofst.grid(row=0, column=0, padx=5, pady=5,sticky=tk.W)
        label_coef.grid(row=1, column=0, padx=5, pady=5,sticky=tk.W)
        self.spin_ofst.grid(row=0, column=1, padx=5, pady=5,sticky=tk.E)
        self.spin_coef.grid(row=1, column=1, padx=5, pady=5,sticky=tk.E)
        label_message.grid(row=2, column=0, padx=5, pady=5, columnspan=2, sticky=tk.E+tk.W)

        save_frame = tk.Frame(top)
        save_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        btn_save = tk.Button(save_frame, text="保存", width=8, command=save_setting)
        btn_save.pack(side=tk.RIGHT)

    def update_view_setting(self):
        global FLIP, ROTATE, W_SIZE, SHOW_TEMP_AT_POINT, SHOW_MAXTEMP, SHOW_CAMTEMP
        FLIP = bool(self.var_flip.get())
        SHOW_MAXTEMP = bool(self.var_maxtemp.get())
        SHOW_CAMTEMP = bool(self.var_camtemp.get())
        ROTATE = self.var_rot.get()
        W_SIZE[0] = int(self.spin_dispsize.get())
        W_SIZE[1] = int(W_SIZE[0] * 3 // 4)
        SHOW_TEMP_AT_POINT = False

    def update_tone_setting(self):
        global TONE_MIN, TONE_MAX
        TONE_MIN = int(self.spin_tonemin.get())
        TONE_MAX = int(self.spin_tonemax.get())

    def update_threshold_setting(self):
        global THRESHOLD
        THRESHOLD = float(self.spin_threshold.get())

    def update_calibration(self):
        global OFFSET, COEFFICIENT
        OFFSET = int(float(self.spin_ofst.get()))
        COEFFICIENT = float(self.spin_coef.get())

    def on_closing(self):
        self.camera.stop_streaming()
        root.destroy()


def lut_overheat(x):
    rgb = np.array([255, round(math.pow(1.005, -x) * 128), 32], np.uint8)
    return rgb


def save_setting():
    config = configparser.RawConfigParser()

    config.add_section('VIEWER')
    config.set('VIEWER', 'window_width', str(W_SIZE[0]))
    config.set('VIEWER', 'flip', "{}".format(FLIP))
    config.set('VIEWER', 'rotate', str(ROTATE))

    config.add_section('TONE MAPPING')
    config.set('TONE MAPPING', 'tone_min', str(TONE_MIN))
    config.set('TONE MAPPING', 'tone_max', str(TONE_MAX))

    config.add_section('THRESHOLD')
    config.set('THRESHOLD', 'temperature', str(THRESHOLD))
    config.set('THRESHOLD', 'show_max_temperature', "{}".format(SHOW_MAXTEMP))
    config.set('THRESHOLD', 'show_cam_temperature', "{}".format(SHOW_CAMTEMP))

    config.add_section('CALIBRATION')
    config.set('CALIBRATION', 'offset', str(OFFSET))
    config.set('CALIBRATION', 'coefficient', str(COEFFICIENT))

    with open('./config.ini', 'w') as configfile:
        config.write(configfile)


config = configparser.ConfigParser()
config.read("./config.ini")

W_SIZE = [int(config['VIEWER']['window_width']), int(config['VIEWER']['window_width']) * 3 // 4]
FLIP = config.getboolean('VIEWER', 'flip')
ROTATE = int(config['VIEWER']['rotate'])

TONE_MIN = float(config['TONE MAPPING']['tone_min'])
TONE_MAX = float(config['TONE MAPPING']['tone_max'])
THRESHOLD = float(config['THRESHOLD']['temperature'])
SHOW_MAXTEMP = config.getboolean('THRESHOLD', 'show_max_temperature')
SHOW_CAMTEMP = config.getboolean('THRESHOLD', 'show_cam_temperature')

OFFSET = int(config['CALIBRATION']['offset'])
COEFFICIENT = float(config['CALIBRATION']['coefficient'])

SHOW_TEMP_AT_POINT = False


if __name__ == "__main__":
    root = tk.Tk()
    app = Application(master=root)
    root.title("Lepton Viewer")
    root.iconbitmap('./logo.ico')
    root.protocol("WM_DELETE_WINDOW", app.on_closing)

    app.show_lepton_frame()
    app.mainloop()
