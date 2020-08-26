# -*- coding: UTF-8 -*-
import tkinter as tk
import numpy as np
import configparser

# visualization window size
W_SIZE = [800, 600]

# ROI (x,y,W,H)
ROI_RECT = [0, 0, 800, 600]

#Bell Type 0, 1, or 2
BELL_TYPE = 0

# flag for flipping image
FLIP = True

# flag for rotate image (0:non, 1:90, 2:180, 3:270)
ROTATE = 0

# window level for tone mapping [℃]
TONE_MIN = 20.0
TONE_MAX = 40.0

# threshold for highlight and show warning
THRESHOLD = 37.5

# flag for visualizing max/camera temperature
SHOW_MAXTEMP = True
SHOW_CAMTEMP = True

# Coefficient and offset for calibrating temperature
OFFSET = 0.0
COEFFICIENT = 0.05


def init():
    global W_SIZE, FLIP, ROTATE, TONE_MIN, TONE_MAX, THRESHOLD, SHOW_MAXTEMP, SHOW_CAMTEMP, OFFSET, COEFFICIENT
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

    OFFSET = float(config['CALIBRATION']['offset'])
    COEFFICIENT = float(config['CALIBRATION']['coefficient'])


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


class SettingDlg:
    def __init__(self, camera_is_tlinear):
        top = tk.Toplevel()
        top.resizable(0, 0)
        top.title("設定")
        top.iconbitmap('./logo.ico')

        # 画面設定 -----------------------------------------------------------
        lf_display = tk.LabelFrame(top, text="画面設定")
        lf_display.pack(fill="both", expand="yes", padx=10, pady=5)

        display_frame1 = tk.Frame(lf_display)
        display_frame1.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        label_size = tk.Label(display_frame1, text="画面横サイズ")
        label_size.pack(side=tk.LEFT)
        self.var_size = tk.StringVar()
        self.var_size.set(W_SIZE[0])
        self.spin_size = tk.Spinbox(display_frame1, from_=160, to=4000, increment=100,
                                    textvariable=self.var_size, width=6, command=self.update)
        self.spin_size.pack(side=tk.LEFT)

        display_frame2 = tk.Frame(lf_display)
        display_frame2.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.var_flip = tk.IntVar()
        if FLIP:
            self.var_flip.set(1)
        self.check_flip = tk.Checkbutton(display_frame2, text="左右反転", variable=self.var_flip, command=self.update)
        self.check_flip.pack(side=tk.LEFT)

        display_frame3 = tk.Frame(lf_display)
        display_frame3.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        label_rotation = tk.Label(display_frame3, text="回転 ")
        label_rotation.pack(side=tk.LEFT)
        self.var_rot = tk.IntVar()
        self.var_rot.set(ROTATE)
        r1 = tk.Radiobutton(display_frame3, text="0°  ", value=0, variable=self.var_rot, command=self.update)
        r2 = tk.Radiobutton(display_frame3, text="90° ", value=1, variable=self.var_rot, command=self.update)
        r3 = tk.Radiobutton(display_frame3, text="180°", value=2, variable=self.var_rot, command=self.update)
        r4 = tk.Radiobutton(display_frame3, text="270°", value=3, variable=self.var_rot, command=self.update)
        r1.pack(side=tk.LEFT)
        r2.pack(side=tk.LEFT)
        r3.pack(side=tk.LEFT)
        r4.pack(side=tk.LEFT)

        display_frame4 = tk.Frame(lf_display)
        display_frame4.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.var_maxtemp = tk.IntVar()
        self.var_camtemp = tk.IntVar()
        if SHOW_MAXTEMP:
            self.var_maxtemp.set(1)
        if SHOW_CAMTEMP:
            self.var_camtemp.set(1)
        check_maxtemp = tk.Checkbutton(display_frame4, text="最大温度表示 ", variable=self.var_maxtemp, command=self.update)
        check_camtemp = tk.Checkbutton(display_frame4, text="カメラ温度表示", variable=self.var_camtemp, command=self.update)
        check_maxtemp.pack(side=tk.LEFT)
        check_camtemp.pack(side=tk.LEFT)

        # トーンマッピング --------------------------------------------------------------------------------
        lf_tone = tk.LabelFrame(top, text="Tone mapping")
        lf_tone.pack(fill="both", expand="yes", padx=10, pady=5)

        tone_label1 = tk.Label(lf_tone, text="  min[℃]")
        tone_label2 = tk.Label(lf_tone, text="  max[℃]")
        tone_label1.grid(row=0, column=0, padx=5, pady=5)
        tone_label2.grid(row=0, column=2, padx=5, pady=5)
        self.var_tonemin = tk.StringVar()
        self.var_tonemax = tk.StringVar()
        self.var_tonemin.set(TONE_MIN)
        self.var_tonemax.set(TONE_MAX)
        self.spin_tonemin = tk.Spinbox(lf_tone, from_=-100, to=500, increment=1,
                                       textvariable=self.var_tonemin, width=6, command=self.update)
        self.spin_tonemax = tk.Spinbox(lf_tone, from_=-100, to=500, increment=1,
                                       textvariable=self.var_tonemax, width=6, command=self.update)
        self.spin_tonemin.grid(row=0, column=1, padx=5, pady=5)
        self.spin_tonemax.grid(row=0, column=3, padx=5, pady=5)

        # トーンマッピング --------------------------------------------------------------------------------
        lf_roi = tk.LabelFrame(top, text="ROI rect")
        lf_roi.pack(fill="both", expand="yes", padx=10, pady=5)
        roi_label1 = tk.Label(lf_roi, text="位置　(x, y)")
        roi_label2 = tk.Label(lf_roi, text="大きさ(W, H)")
        roi_label1.grid(row=0, column=0, padx=5, pady=5)
        roi_label2.grid(row=1, column=0, padx=5, pady=5)
        self.var_roix = tk.StringVar()
        self.var_roiy = tk.StringVar()
        self.var_roiw = tk.StringVar()
        self.var_roih = tk.StringVar()
        self.var_roix.set(ROI_RECT[0])
        self.var_roiy.set(ROI_RECT[1])
        self.var_roiw.set(ROI_RECT[2])
        self.var_roih.set(ROI_RECT[3])
        self.spin_roix = tk.Spinbox(lf_roi, from_=0, to=600, increment=1, textvariable=self.var_roix, width=6, command=self.update)
        self.spin_roiy = tk.Spinbox(lf_roi, from_=0, to=800, increment=1, textvariable=self.var_roiy, width=6, command=self.update)
        self.spin_roiw = tk.Spinbox(lf_roi, from_=1, to=600, increment=1, textvariable=self.var_roiw, width=6, command=self.update)
        self.spin_roih = tk.Spinbox(lf_roi, from_=1, to=800, increment=1, textvariable=self.var_roih, width=6, command=self.update)
        self.spin_roix.grid(row=0, column=1, padx=2, pady=2)
        self.spin_roiy.grid(row=0, column=2, padx=2, pady=2)
        self.spin_roiw.grid(row=1, column=1, padx=2, pady=2)
        self.spin_roih.grid(row=1, column=2, padx=2, pady=2)

        # threshold --------------------------------------------------------------------------------
        lf_threshold = tk.LabelFrame(top, text="Threshold - 超過温度可視化")
        lf_threshold.pack(fill="both", expand="yes", padx=10, pady=5, ipady=5)

        label_threshold = tk.Label(lf_threshold, text="    閾値温度[℃] ")
        label_threshold.pack(side=tk.LEFT)
        self.var_threshold = tk.StringVar()
        self.var_threshold.set(THRESHOLD)
        self.spin_threshold = tk.Spinbox(lf_threshold, from_=-100, to=500, format="%.2f", increment=0.1, width=6,
                                         textvariable=self.var_threshold, command=self.update)
        self.spin_threshold.pack(side=tk.LEFT)

        # calibration  --------------------------------------------------------------------------------
        lf_calibration = tk.LabelFrame(top, text="Calibration")
        lf_calibration.pack(fill="both", expand="yes", padx=10, pady=5)

        label_ofst = tk.Label(lf_calibration, text="offset [℃]")
        self.var_offset = tk.StringVar()
        self.var_offset.set(OFFSET)
        self.spin_ofst = tk.Spinbox(lf_calibration, from_=-100, to=100, format="%.2f", increment=0.1, width=6,
                                    textvariable=self.var_offset, command=self.update)

        label_coef = tk.Label(lf_calibration, text="coef (Lepton 3.0 のみ）")
        self.var_coef = tk.StringVar()
        self.var_coef.set(COEFFICIENT)
        self.spin_coef = tk.Spinbox(lf_calibration, from_=-100, to=100, format="%.3f", increment=0.001, width=6,
                                    textvariable=self.var_coef, command=self.update)
        if camera_is_tlinear:
            self.spin_coef.configure(state=tk.DISABLED)

        if camera_is_tlinear:
            message = "このカメラはRadiometric Accuracy に対応\nしています\n 温度 = Output - 273.15 + offset"
        else:
            message = "このカメラはRadiometric Accuracy に対応\nしていません\n温度 = coef * (Output - 8192) + カメラ温度\n- 273.15 + offset"
        label_message = tk.Label(lf_calibration, text=message, justify=tk.LEFT)
        label_ofst.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        label_coef.grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.spin_ofst.grid(row=0, column=1, padx=5, pady=5, sticky=tk.E)
        self.spin_coef.grid(row=1, column=1, padx=5, pady=5, sticky=tk.E)
        label_message.grid(row=2, column=0, padx=5, pady=5, columnspan=2, sticky=tk.E+tk.W)

        save_frame = tk.Frame(top)
        save_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        btn_save = tk.Button(save_frame, text="保存", width=8, command=save_setting)
        btn_save.pack(side=tk.RIGHT)

    def update(self):
        global FLIP, ROTATE, W_SIZE, SHOW_MAXTEMP, SHOW_CAMTEMP, TONE_MIN, TONE_MAX, THRESHOLD, OFFSET, COEFFICIENT
        FLIP = bool(self.var_flip.get())
        SHOW_MAXTEMP = bool(self.var_maxtemp.get())
        SHOW_CAMTEMP = bool(self.var_camtemp.get())
        ROTATE = self.var_rot.get()
        W_SIZE[0] = int(self.spin_size.get())
        W_SIZE[1] = int(W_SIZE[0] * 3 // 4)

        TONE_MIN = float(self.spin_tonemin.get())
        TONE_MAX = float(self.spin_tonemax.get())

        ROI_RECT[0] = int(self.spin_roix.get())
        ROI_RECT[1] = int(self.spin_roiy.get())
        ROI_RECT[2] = int(self.spin_roiw.get())
        ROI_RECT[3] = int(self.spin_roih.get())

        THRESHOLD = float(self.spin_threshold.get())

        OFFSET = float(self.spin_ofst.get())
        COEFFICIENT = float(self.spin_coef.get())
