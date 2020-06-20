# -*- coding: UTF-8 -*-
import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk
import cv2
import numpy as np
import math
import configparser
import lepton_control
import params


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
        self.m.add_command(label="設定", command=self.show_param_dlg)

        # lepton カメラの読み込み
        try:
            self.camera = lepton_control.Lepton()
        except:
            root.destroy()
            messagebox.showwarning("Lepton Viewer", "カメラが見つかりません\nカメラを差し直してください")
            exit()
        self.popup_point = self.point = (params.W_SIZE[0] // 2, params.W_SIZE[1] // 2)

    def right_button_clicked(self, event):
        self.popup_point = (event.x, event.y)
        try:
            self.m.tk_popup(event.x_root, event.y_root)
        finally:
            self.m.grab_release()

    def stop_show_temp(self):
        global SHOW_TEMP_AT_POINT
        SHOW_TEMP_AT_POINT = False
        self.point = (params.W_SIZE[0] // 2, params.W_SIZE[1] // 2)

    def start_show_temp(self):
        global SHOW_TEMP_AT_POINT
        SHOW_TEMP_AT_POINT = True
        self.point = self.popup_point

    def show_lepton_frame(self):
        # get lepton image (raw) and convert it to temperature (temp)
        raw_img, temp_img = self.camera.update_frame(params.ROTATE, params.FLIP, params.COEFFICIENT, params.OFFSET)
        temp_max = np.max(temp_img)

        # tone mapping
        gray = np.interp(temp_img, (params.TONE_MIN, params.TONE_MAX), (0, 255)).astype('uint8')
        gray = np.dstack([gray, gray, gray])

        # paint overheat pixels in RED
        overheat = np.transpose(np.where(temp_img >= params.THRESHOLD))
        for i, j in overheat:
            gray[i, j] = lut_overheat(temp_img[i, j] - params.THRESHOLD)

        if params.ROTATE % 2 == 0:
            res = cv2.resize(gray, (params.W_SIZE[0], params.W_SIZE[1]), interpolation=cv2.INTER_LANCZOS4)
        else:
            res = cv2.resize(gray, (params.W_SIZE[1], params.W_SIZE[0]), interpolation=cv2.INTER_LANCZOS4)

        if temp_max >= params.THRESHOLD:
            res[:5, :] = [255, 32, 32]
            res[-5:, :] = [255, 32, 32]
            res[:, :5] = [255, 32, 32]
            res[:, -5:] = [255, 32, 32]
        else:
            res[:5, :] = [32, 223, 32]
            res[-5:, :] = [32, 223, 32]
            res[:, :5] = [32, 223, 32]
            res[:, -5:] = [32, 223, 32]

        if params.SHOW_MAXTEMP:
            text = "MAX: {:.2f}".format(temp_max)
            res = cv2.putText(res, text, (10, 25), cv2.FONT_HERSHEY_PLAIN, 1.25, (0, 0, 0), 5, cv2.LINE_AA)
            res = cv2.putText(res, text, (10, 25), cv2.FONT_HERSHEY_PLAIN, 1.25, (255, 255, 255), 1, cv2.LINE_AA)

        if params.SHOW_CAMTEMP:
            camera_temp = self.camera.camera_temp()
            text = "CAM: {:.2f}".format(camera_temp)
            res = cv2.putText(res, text, (150, 25), cv2.FONT_HERSHEY_PLAIN, 1.25, (0, 0, 0), 5, cv2.LINE_AA)
            res = cv2.putText(res, text, (150, 25), cv2.FONT_HERSHEY_PLAIN, 1.25, (255, 255, 255), 1, cv2.LINE_AA)

        if SHOW_TEMP_AT_POINT:
            # note self.point represent the point in the displayed image (not in temp_img)
            # r_p (point*scale) is the point in temp_img (or raw image)
            scale = raw_img.shape[1] / params.W_SIZE[0]
            r_p = (int(self.point[0] * scale), int(self.point[1] * scale))
            shift = int(10 * scale)
            point_temp = np.mean(temp_img[r_p[1]-shift: r_p[1]+shift, r_p[0]-shift: r_p[0]+shift])
            text = "{:.2f}".format(point_temp)

            pt = (self.point[0] - 28, self.point[1] - 20)
            res = cv2.putText(res, text, pt, cv2.FONT_HERSHEY_PLAIN, 1.25, (255, 255, 255), 4, cv2.LINE_AA)
            res = cv2.putText(res, text, pt, cv2.FONT_HERSHEY_PLAIN, 1.25, (32, 32, 255), 1, cv2.LINE_AA)
            b1 = (self.point[0] + 10, self.point[1] + 10)
            b2 = (self.point[0] - 10, self.point[1] - 10)
            res = cv2.rectangle(res, b1, b2, (255, 255, 255), 2, cv2.LINE_AA, 0)
            res = cv2.rectangle(res, b1, b2, (32, 32, 255), 1, cv2.LINE_AA, 0)

        imgtk = ImageTk.PhotoImage(image=Image.fromarray(res))
        self.lmain.imgtk = imgtk
        self.lmain.configure(image=imgtk)
        self.lmain.after(66, self.show_lepton_frame)

    def show_param_dlg(self):
        params.SettingDlg(self.camera.tlinear)

    def on_closing(self):
        self.camera.stop_streaming()
        root.destroy()


def lut_overheat(x):
    rgb = np.array([255, round(math.pow(1.005, -x) * 128), 32], np.uint8)
    return rgb


SHOW_TEMP_AT_POINT = False


if __name__ == "__main__":
    params.init()

    root = tk.Tk()
    app = Application(master=root)
    root.title("Lepton Viewer")
    root.iconbitmap('./logo.ico')
    root.protocol("WM_DELETE_WINDOW", app.on_closing)

    app.show_lepton_frame()
    app.mainloop()
