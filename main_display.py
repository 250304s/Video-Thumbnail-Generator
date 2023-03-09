import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
import os, sys
import thumbnail_generator as tg
import configparser
import threading


class Application(tk.Frame):
    def __init__(self, master = None):
        self.application_path = tg.initialize()
        self.save_directory = self.read_ini('thumbnail_savepath')
        self.ffmpeg_path = self.read_ini('ffmpeg_path')
        self.__x_grid = self.read_ini('xgrid')
        self.__y_grid = self.read_ini('ygrid')
        self.__width_size = self.read_ini('width')
        self.videolist = []
        super().__init__(master)

        # ウィンドウタイトル
        self.master.title("ThumbnailGenerator")

        self.master.geometry("500x300") 

        # メニューの作成
        self.create_menu()
        # ツールバーの作成
        #self.create_tool_bar()
        # ステータスバーの作成
        self.create_status_bar()
        # サイドパネル
        self.create_side_panel()

        # 残りの領域にキャンバスを作成
        canvas = tk.Canvas(self.master, background="#008080")
        canvas.pack(expand=True,  fill=tk.BOTH)

    def create_menu(self):
        ''' メニューの作成'''
        menu_bar = tk.Menu(self)

        # ファイルメニュー
        file_menu = tk.Menu(menu_bar, tearoff = tk.OFF)
        menu_bar.add_cascade(label="ファイル", menu = file_menu)
        file_menu.add_command(label = "開く(O)", command = self.menu_open_click)
        file_menu.add_command(label= "環境設定", command= self.create_modal_dialog)
        file_menu.add_separator() # セパレータ
        file_menu.add_command(label = "終了", command = self.master.destroy)

        # ヘルプメニュー
        help_menu = tk.Menu(menu_bar, tearoff=tk.OFF)
        menu_bar.add_cascade(label="ヘルプ", menu = help_menu)
        help_menu.add_command(label = "開く", command = self.menu_open_click, accelerator = "Alt+H")

        # ショートカットの設定
        menu_bar.bind_all("<Alt-o>", self.menu_open_click)
        menu_bar.bind_all("<Alt-h>", self.help_menu_open_click)

        # 親のメニューに設定
        self.master.config(menu = menu_bar)

    def menu_open_click(self, event=None):
        ''' ファイルを開く'''
        fTpy = [('ビデオファイル', '*.mp4 *.avi *.wmv *.mkv')]
        # ファイルを開くダイアログ
        filenames = filedialog.askopenfilenames(filetypes=fTpy, initialdir = os.getcwd())
        #filename = tk.filedialog.askopenfilenames(filetypes=fTpy, initialdir = os.getcwd())
        self.videolist = list(filenames)
        print(filenames)
        
    def help_menu_open_click(self, event=None):
        ''' ヘルプを開く '''
        pass

    def read_ini(self, ini_key: str):
        ini_file = os.path.join(self.application_path, 'config.ini')
        ini = configparser.ConfigParser()
        ini.read(ini_file, 'UTF-8')
        return ini['DEFAULT'][ini_key]

    def create_modal_dialog(self):
        def ask_save_directory():
            self.save_directory = filedialog.askdirectory(initialdir = self.save_directory)
            if self.save_directory:
                var_save_dir.set(self.save_directory)
        def ask_ffmpeg_path():
            self.ffmpeg_path = filedialog.askdirectory(initialdir = self.ffmpeg_path)
            if self.ffmpeg_path:
                var_ffmpeg_path.set(self.ffmpeg_path)
                
        def save_ini():
            config_ini_path = os.path.join(self.application_path, 'config.ini')
            ini = configparser.ConfigParser(comment_prefixes='#', allow_no_value=True)
            ini.read(config_ini_path, 'UTF-8')
            defa = ini['DEFAULT']
            defa['ffmpeg_path'] = self.ffmpeg_path
            defa['thumbnail_savepath'] = self.save_directory
            with open(config_ini_path, 'w') as configfile:
                # 指定したconfigファイルを書き込み
                ini.write(configfile)
            

        '''モーダルダイアログボックスの作成'''
        dlg_modal = tk.Toplevel(master=self.master)
        dlg_modal.title("環境設定") # ウィンドウタイトル
        dlg_modal.geometry("400x600")   # ウィンドウサイズ(幅x高さ)
        
        # モーダルにする設定
        dlg_modal.grab_set()        # モーダルにする
        dlg_modal.focus_set()       # フォーカスを新しいウィンドウをへ移す
        dlg_modal.transient(self.master)   # タスクバーに表示しない
        
        config_frame = tk.Frame(dlg_modal, borderwidth = 5, relief = tk.GROOVE, width= 250)
        
        checkbutton_use_gpu = tk.Checkbutton(config_frame, text="Nvidiaグラフィックボードを使用してサムネイルを生成")
        checkbutton_use_gpu.pack()
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        frame_1 = tk.LabelFrame(config_frame, text="FFMPEGのパス", borderwidth=5, relief=tk.GROOVE)
        
        var_ffmpeg_path = tk.StringVar()
        var_ffmpeg_path.set(self.read_ini('ffmpeg_path'))
        entry_ffmpeg_path = tk.Entry(frame_1, textvariable=var_ffmpeg_path, width=50)
        entry_ffmpeg_path.pack(padx=5, side='left')
        
        button_ask_ffmpeg_path = tk.Button(frame_1, text="参照", command=ask_ffmpeg_path)
        button_ask_ffmpeg_path.pack(side='left')
        
        frame_1.pack(pady=10)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        frame_2 = tk.LabelFrame(config_frame, text="デフォルトのサムネイル保存先", borderwidth=5, relief=tk.GROOVE)
        
        var_save_dir = tk.StringVar()
        var_save_dir.set(self.read_ini('thumbnail_savepath'))
        entry_save_path = tk.Entry(frame_2, textvariable=var_save_dir, width=50)
        entry_save_path.pack(padx=5, side='left')
        
        button_ask_directory = tk.Button(frame_2, text="参照", command=ask_save_directory)
        button_ask_directory.pack(side='left')
        
        frame_2.pack(pady=10)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        save_close = tk.Frame(dlg_modal, borderwidth = 2, relief = tk.SUNKEN, width= 250)
        
        save_button = tk.Button(save_close, text="保存", command=save_ini)
        save_button.pack(side='left')
        
        close_button = tk.Button(save_close, text='閉じる', command= dlg_modal.destroy)
        close_button.pack(side='right')
        
        save_close.pack(side='bottom')
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        config_frame.pack(padx=10)

        # ダイアログが閉じられるまで待つ
        app.wait_window(dlg_modal)  
        print("ダイアログが閉じられた")    

    def create_tool_bar(self):
        def clicked_43():
            button1['state'] = 'disabled'
            button2['state'] = 'normal'
        def clicked_169():
            button1['state'] = 'normal'
            button2['state'] = 'disabled'
        ''' ツールバー'''

        frame_tool_bar = tk.Frame(self.master, borderwidth = 2, relief = tk.SUNKEN)

        label1 = tk.Label(frame_tool_bar, text="アスペクト比を選択")
        button1 = tk.Button(frame_tool_bar, text = "4:3", width = 4, command=clicked_43)
        button2 = tk.Button(frame_tool_bar, text = "16:9", width = 4, command=clicked_169)
        #button3 = tk.Button(frame_tool_bar, text = "3", width = 2)

        label1.pack(side = tk.LEFT)
        button1.pack(side = tk.LEFT, padx=5)
        button2.pack(side = tk.LEFT, padx=5)
        #button3.pack(side = tk.LEFT)

        frame_tool_bar.pack(fill = tk.X)

    def create_status_bar(self):
        '''ステータスバー'''
        frame_status_bar = tk.Frame(self.master, borderwidth = 2, relief = tk.SUNKEN)
        
        pbval = tk.IntVar(value=0)
        pb = ttk.Progressbar(frame_status_bar, orient="horizontal", variable=pbval, maximum=10, length=150 ,mode="determinate")
        pb.pack(side='left')

        self.label1 = tk.Label(frame_status_bar, text = "ステータスラベル１")
        self.label2 = tk.Label(frame_status_bar, text = "ステータスラベル２")
        
        self.label1.pack(side = tk.LEFT)
        self.label2.pack(side = tk.RIGHT)

        frame_status_bar.pack(side = tk.BOTTOM, fill = tk.X)

    def create_side_panel(self):
        '''サイドパネル'''
        def clicked_960():
            button1['state'] = 'disabled'
            button2['state'] = 'normal'
            button1.configure(bg='#03dfa6')
            button2.configure(bg='#f2f2f2')
            self.__width_size = "960"
        def clicked_480():
            button1['state'] = 'normal'
            button2['state'] = 'disabled'
            button1.configure(bg='#f2f2f2')
            button2.configure(bg='#03dfa6')
            self.__width_size = "480"
        def execute_generate():
            x = int(self.__width_size)
            y = (x//16)*9
            config_ini_path = os.path.join(self.application_path, 'config.ini')
            ini = configparser.ConfigParser(comment_prefixes='#', allow_no_value=True)
            ini.read(config_ini_path, 'UTF-8')
            defa = ini['DEFAULT']
            defa['xgrid'] = str(self.__x_grid)
            defa['ygrid'] = str(self.__y_grid)
            defa['width'] = str(x)
            defa['height'] = str(y)
            if not self.videolist:
                self.bell()
                return
            else:
                with open(config_ini_path, 'w') as configfile:
                    # 指定したconfigファイルを書き込み
                    ini.write(configfile)
                thread1 = threading.Thread(target=tg.list_to_path, args=(self.videolist,))
                thread1.start()
                self.videolist.clear()
        side_panel = tk.Frame(self.master, borderwidth = 2, relief = tk.SUNKEN)
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        width_setting_panel = tk.Frame(side_panel, borderwidth = 2, relief = tk.SUNKEN)
        
        label1 = tk.Label(width_setting_panel, text="横幅")
        button1 = tk.Button(width_setting_panel, text = "960", width = 15, command=clicked_960)
        button2 = tk.Button(width_setting_panel, text = "480", width = 15, command=clicked_480)
        label1.pack()
        button1.pack()
        button2.pack()
        if self.__width_size == "960":
            clicked_960()
        else:
            clicked_480()
        
        width_setting_panel.pack()
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        grid_setting_panel = tk.Frame(side_panel, borderwidth = 2)
        
        x_intVar = tk.IntVar(value=0)
        x_intVar.set(self.__x_grid)
        grid_setting_panel1 = tk.Frame(grid_setting_panel, borderwidth = 2, relief = tk.SUNKEN)
        label2 = tk.Label(grid_setting_panel1, text="横の数")
        x_spin = tk.Spinbox(grid_setting_panel1, from_=1, to=5, increment=1, width=7, textvariable=x_intVar, state='readonly')
        self.__x_grid = x_spin.get()
        label2.pack()
        x_spin.pack()
        grid_setting_panel1.pack(side='left')
        y_intVar = tk.IntVar(value=0)
        y_intVar.set(self.__y_grid)
        grid_setting_panel2 = tk.Frame(grid_setting_panel, borderwidth = 2, relief = tk.SUNKEN)
        label3 = tk.Label(grid_setting_panel2, text="縦の数")
        y_spin = tk.Spinbox(grid_setting_panel2, from_=1, to=10, increment=1, width=7, textvariable=y_intVar, state='readonly')
        self.__y_grid = y_spin.get()
        label3.pack()
        y_spin.pack()
        grid_setting_panel2.pack(side='right')
        
        grid_setting_panel.pack()
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        execute_panel = tk.Frame(side_panel, borderwidth = 2, relief = tk.SUNKEN)
        
        execute_button = tk.Button(execute_panel, text = "実行", width=15, command=execute_generate)
        execute_button.pack()
        
        execute_panel.pack(side="bottom")
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        side_panel.pack(side = tk.RIGHT, fill = tk.Y)
        


if __name__ == "__main__":
    root = tk.Tk()
    app = Application(master = root)
    app.mainloop()