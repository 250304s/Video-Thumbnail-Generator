import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
import os


class Application(tk.Frame):
    def __init__(self, master = None):
        super().__init__(master)

        # ウィンドウタイトル
        self.master.title("ThumbnailGenerator")

        self.master.geometry("500x300") 

        # メニューの作成
        self.create_menu()
        # ツールバーの作成
        self.create_tool_bar()
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

    def menu_dummy(self, event=None):
        pass

    def menu_open_click(self, event=None):
        ''' ファイルを開く'''

        # ファイルを開くダイアログ
        filename = tk.filedialog.askopenfilename(
            initialdir = os.getcwd() # カレントディレクトリ
            )
        print(filename)
        
    def help_menu_open_click(self, event=None):
        ''' ヘルプを開く '''
        pass

    def create_tool_bar(self):
        ''' ツールバー'''

        frame_tool_bar = tk.Frame(self.master, borderwidth = 2, relief = tk.SUNKEN)

        label1 = tk.Label(frame_tool_bar, text="アスペクト比を選択")
        button1 = tk.Button(frame_tool_bar, text = "4:3", width = 4)
        button2 = tk.Button(frame_tool_bar, text = "16:9", width = 4)
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

        """self.label1 = tk.Label(frame_status_bar, text = "ステータスラベル１")
        self.label2 = tk.Label(frame_status_bar, text = "ステータスラベル２")

        self.label1.pack(side = tk.LEFT)
        self.label2.pack(side = tk.RIGHT)"""

        frame_status_bar.pack(side = tk.BOTTOM, fill = tk.X)

    def create_side_panel(self):
        '''サイドパネル'''
        side_panel = tk.Frame(self.master, borderwidth = 2, relief = tk.SUNKEN)
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        width_setting_panel = tk.Frame(side_panel, borderwidth = 2, relief = tk.SUNKEN)
        
        label1 = tk.Label(width_setting_panel, text="横幅")
        button1 = tk.Button(width_setting_panel, text = "960", width = 15)
        button2 = tk.Button(width_setting_panel, text = "480", width = 15)
        label1.pack()
        button1.pack()
        button2.pack()
        
        width_setting_panel.pack()
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        grid_setting_panel = tk.Frame(side_panel, borderwidth = 2)
        
        x_intVar = tk.IntVar(value=0)
        x_intVar.set(4)
        grid_setting_panel1 = tk.Frame(grid_setting_panel, borderwidth = 2, relief = tk.SUNKEN)
        label2 = tk.Label(grid_setting_panel1, text="横の数")
        x_spin = tk.Spinbox(grid_setting_panel1, from_=1, to=5, increment=1, width=7, textvariable=x_intVar)
        label2.pack()
        x_spin.pack()
        grid_setting_panel1.pack(side='left')
        
        y_intVar = tk.IntVar(value=0)
        y_intVar.set(4)
        grid_setting_panel2 = tk.Frame(grid_setting_panel, borderwidth = 2, relief = tk.SUNKEN)
        label3 = tk.Label(grid_setting_panel2, text="縦の数")
        y_spin = tk.Spinbox(grid_setting_panel2, from_=1, to=10, increment=1, width=7, textvariable=y_intVar)
        label3.pack()
        y_spin.pack()
        grid_setting_panel2.pack(side='right')
        
        grid_setting_panel.pack()
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        execute_panel = tk.Frame(side_panel, borderwidth = 2, relief = tk.SUNKEN)
        
        execute_button = tk.Button(execute_panel, text = "実行", width=15)
        execute_button.pack()
        
        execute_panel.pack(side="bottom")
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        side_panel.pack(side = tk.RIGHT, fill = tk.Y)
        


if __name__ == "__main__":
    root = tk.Tk()
    app = Application(master = root)
    app.mainloop()