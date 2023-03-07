import subprocess
import os
from PIL import Image, ImageDraw, ImageFont
import sys
from concurrent.futures import ThreadPoolExecutor
import keyboard
import time
import configparser
import traceback
import json
import time


class ProgressBar:
    """プログレスバーを表示するクラス。インスタンス化を行う際、処理総数を入れる必要がある。
    """

    def __init__(self, processes: int) -> None:
        """処理総数を引数に取る。

        Args:
            processes (int): for文が回る回数を入れる。
        """
        self.processes = processes  # 処理総数
        self.current_progress = 0  # 現在完了した数
        self.start_time = time.time()
        self.process_time = self.start_time
        self.time_sum = 0

    def progressbar(self) -> None:
        """プログレスバーの表示を行う。
        """
        remaining_processes = self.processes - self.current_progress
        now_progress = int((self.current_progress / self.processes) * 30)
        progress = "#"*(now_progress) + " "*(30 - now_progress)
        print('\r[{}] {:02}/{} 残り時間: {:04.1f}s'.format(progress, self.current_progress,
              self.processes, self.get_time()*remaining_processes), end='')

    def update(self) -> None:
        """プログレスバーを一つ進める。
        """
        self.current_progress += 1
        # ここの処理でもしfor文の外でupdateが呼び出された場合クラスを削除する。
        if self.current_progress > self.processes:
            self.__del__(True)
            return
        self.progressbar()

    def get_time(self) -> float:
        """for文一回当たりの時間を計測し、平均時間を取る。

        Returns:
            float: 処理に掛かる平均時間。
        """
        current_time = time.time() - self.process_time
        self.process_time = time.time()
        self.time_sum += current_time
        ave = self.time_sum / self.current_progress
        return ave

    def __del__(self, no_message: bool = False) -> None:
        """クラス削除

        Args:
            no_message (bool, optional): 終了時メッセージを表示するかの選択をする.

            Defaults to False.
        """
        if no_message:
            return
        else:
            print('\r')
            print("かかった時間: {:03.1f}s".format(time.time()-self.start_time))


# ━━━━━グローバル変数━━━━━
width = 960
height = 540
xgrid = 4
ygrid = 4
thumbnail_savepath = ".\\"
gridsize = xgrid * ygrid
ffmpeg_exe = "ffmpeg"
ffprobe_exe = "ffprobe"
running = True
# ━━━━━━━━━━━━━━━━━


def section_check() -> None:
    """-C もしくは --config引数があるかを調べる。存在する場合一つ後ろのものをキーとしてinitializeへ与える。
    """
    section = "DEFAULT"
    if len(sys.argv) > 1:
        for i, arg in enumerate(sys.argv):
            if arg in ['-C', '--config']:
                section = sys.argv[i+1]
                del sys.argv[i]
                sys.argv.remove(section)
    initialize(section)


def initialize(section: str = 'DEFAULT') -> None:
    """
    初期設定を行う。
    """
    global thumbnail_savepath
    # 実行ファイルが存在するディレクトリのパスを取得する
    if getattr(sys, 'frozen', False):
        application_path = os.path.dirname(sys.executable)
    else:
        application_path = os.path.dirname(os.path.abspath(__file__))

    thumbnail_savepath = os.path.join(application_path, 'save')
    # 設定ファイル (config.ini) を読み込む (結果出力)
    if read_ini(application_path, section):
        print('Successfully loaded config.ini.')
    else:
        print('Failed to load config.ini.')
    # サムネイル画像のサイズ (結果出力)
    print(
        f'一枚の横幅: {width}px, 一枚の高さ: {height}px, 横の枚数: {xgrid}枚, 縦の枚数: {ygrid}枚, 指定セクション: {section}\
            \nffmpegの位置: {ffmpeg_exe}, サムネイルの保存先: {thumbnail_savepath}')

    # サムネイル画像の保存先ディレクトリを作成する
    os.makedirs(thumbnail_savepath, exist_ok=True)


def read_ini(application_path: str, section: str) -> bool:
    """config.iniファイルを読み込む。その後各グローバル変数へ代入。

    Args:
        application_path (str): この実行ファイルがある場所
        section (str): ユーザーが設定したconfigのセクション

    Returns:
        bool: config.iniファイルの読み込みに成功した場合True, 失敗した場合False
    """
    global width, height, xgrid, ygrid, gridsize
    # config.ini のパスを取得する
    config_ini_path = os.path.join(application_path, "config.ini")
    # ファイルが存在するか確認しエラーハンドリングを行います。
    if not os.path.exists(config_ini_path):
        print('Do not exist config.ini!')
        create_ini(config_ini_path)
    # ini ファイルを読み込んで、必要な設定値を取得します。
    ini = configparser.ConfigParser()
    ini.read(config_ini_path, 'UTF-8')
    try:
        width = int(ini[section]['width'])
        height = int(ini[section]['height'])
        xgrid = int(ini[section]['xgrid'])
        ygrid = int(ini[section]['ygrid'])
        ffmpeg_path = ini[section]['ffmpeg_path']
        save_path = ini[section]['thumbnail_savepath']
        gridsize = xgrid * ygrid
    except KeyError:
        # キーが見つからない場合（値の取得に失敗した場合）はエラーとして処理します。
        e = traceback.format_exc()
        print(e)
        return False
    get_ff_exe(ffmpeg_path)
    define_thumbnail_savepath(save_path)
    return True


def create_ini(config_ini_path: str) -> None:
    """config.iniを作成する

    Args:
        config_ini_path (str): config.iniを作成する場所
    """
    config = configparser.ConfigParser()
    default_setting = {'width': '960', 'height': '540',
                       'xgrid': '4', 'ygrid': '4', 'ffmpeg_path': '', 'thumbnail_savepath': ''}
    config['DEFAULT'] = default_setting
    with open(config_ini_path, 'w') as configfile:
        # 指定したconfigファイルを書き込み
        config.write(configfile)


def get_ff_exe(ffmpeg_path: str) -> None:
    """ffmpeg.exe, ffprobe.exeが存在するディレクトリのパスを貰い、ffmpeg_exe, ffprobe_exeを決定する。\n
    ffmpeg_pathが空欄の場合は環境変数を設定しているものとみてなにも設定を行わずに終了。

    Args:
        ffmpeg_path (str): ffmpeg.exe, ffprobe.exeが存在するディレクトリのパスを記述してください

    Raises:
        FileNotFoundError: config.iniで与えられたパスに存在していない場合このエラーを吐きます。
    """
    global ffmpeg_exe, ffprobe_exe
    if ffmpeg_path == "":
        return
    temp = os.path.join(ffmpeg_path, 'ffmpeg.exe')
    ffmpeg_exe = temp if os.path.exists(temp) else None
    temp = os.path.join(ffmpeg_path, 'ffprobe.exe')
    ffprobe_exe = temp if os.path.exists(temp) else None
    if ffmpeg_exe is None:
        raise FileNotFoundError('ffmpeg is not exists!')
    if ffprobe_exe is None:
        raise FileNotFoundError('ffprobe is not exists!')


def define_thumbnail_savepath(save_path: str) -> bool:
    """グローバル変数、thumbnail_savepathを設定する。保存したい場所のディレクトリが存在しない場合\n
    thumbnail_savepathはデフォルトである実行ファイルのディレクトリ上のsaveフォルダになる。
    空欄の場合も同様。

    Args:
        save_path (str): 保存したい場所のディレクトリ

    Returns:
        bool: 成功したらTrue, 失敗したらFalse
    """
    global thumbnail_savepath
    if not save_path:
        return True
    elif os.path.exists(save_path):
        thumbnail_savepath = save_path
        return True
    else:
        print(f'{save_path} is not found')
        return False
# --------------------------------------------


def secToHour(second: float) -> str:
    """秒数をHH:MM:SS形式の文字型にします

    Args:
        second (float): 秒数

    Returns:
        str: HH:MM:SS
    """
    H = int(second / 3600)
    M = int((second % 3600) / 60)
    S = int(second % 60)
    return "{:02}:{:02}:{:02}".format(H, M, S)


def human_readable_size(size: int) -> str:
    """バイト表示のものを単位を付けて返します。

    Args:
        size (int): バイト表示

    Returns:
        str: 数字に単位をつけたもの
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} TB"


def keyinput() -> None:
    """qキーが入力されたとき、プログラムを終了する。
    """
    global running
    while running:
        time.sleep(0.05)
        if keyboard.is_pressed('q'):
            print()
            print('\r{}'.format("処理を中断しました。"), end='')
            os._exit(0)
# --------------------------------------------


def get_video_info(video_path: str) -> str:
    """ffprobeを用いて動画の情報を得る。その後加工して文字列として渡す。

    Args:
        video_path (str): 動画ファイルのパス

    Returns:
        str: 動画情報を書き込んだ文
    """
    # 動画ファイルのファイル名を取得する
    video_name = os.path.basename(video_path)
    # ビデオストリームとオーディオストリームに関する情報を取得する
    video_info, audio_info = get_streams(video_path)
    try:
        # キーエラーが発生した場合を想定して、各種情報を取得する
        video_fps = video_info['r_frame_rate']
        video_width = video_info['width']
        video_height = video_info['height']
        video_codec = video_info['codec_name']
        audio_codec = audio_info['codec_name']
        sample_rate = audio_info['sample_rate']
        channel_layout = audio_info['channel_layout']
    except KeyError:
        # キーエラーが発生した場合は、エラー内容を表示する
        print(traceback.format_exc())
    # ファイルサイズ、再生時間、ビデオコーデック、音声コーデック、チャンネル数、サンプリング周波数、解像度、フレームレート等の情報を、フォーマットされた文字列として保存する
    video_format = get_format(video_path)
    duration = float(video_format['duration'])
    videobitrate = int(video_format['bit_rate'])
    videosize = int(video_format['size'])
    try:
        fps = float(video_fps.split('/')[0]) / float(video_fps.split('/')[1])
    except:
        fps = -1
    resulttext = f'File: {video_name}\
    \nSize: {videosize} bytes ({human_readable_size(videosize)}), duration: {secToHour(duration)}, avg.bitrate: {human_readable_size(videobitrate)}/s\
    \nAudio: {audio_codec}, {sample_rate} Hz, {channel_layout}\
    \nVideo: {video_codec}, {video_width}x{video_height}, {fps:.2f}fps'
    return resulttext


def get_streams(video_path: str) -> tuple[dict, dict]:
    """動画ファイルを与えるとffprobeで各ストリームと取り出す

    Args:
        filename (str): 動画ファイル

    Returns:
        tuple: 動画ストリームと音声ストリームのタプル
    """
    # ffprobeコマンドの実行(引数：メッセージ少なく、JSON形式で出力、全ストリーム情報表示)
    cmd = [ffprobe_exe, '-v', 'quiet', '-print_format',
           'json', '-show_streams', video_path]
    output = subprocess.check_output(cmd)
    data = json.loads(output)

    # ストリーム情報からビデオとオーディオの情報を抜き出す
    video_stream = None
    audio_stream = None
    image_stream = None

    for stream in data['streams']:
        if stream['codec_name'] == 'png':
            image_stream = stream
            continue
        if stream['codec_type'] == 'video':
            video_stream = stream
        elif stream['codec_type'] == 'audio':
            audio_stream = stream

    # ビデオ情報を辞書型で保存(video_streamが存在していれば)
    video_info = {
        'codec_name': video_stream.get('codec_name', ''),
        'width': video_stream.get('width', 0),
        'height': video_stream.get('height', 0),
        'r_frame_rate': video_stream.get('r_frame_rate', ''),
    } if video_stream is not None else {}

    # オーディオ情報を辞書型で保存(audio_streamが存在していれば)
    audio_info = {
        'codec_name': audio_stream.get('codec_name', ''),
        'sample_rate': audio_stream.get('sample_rate', ''),
        'channel_layout': audio_stream.get('channel_layout', '')
    } if audio_stream is not None else {}

    return video_info, audio_info


def get_format(video_path: str) -> dict:
    """与えられた動画のフォーマット情報を返す。

    Args:
        video_path (str): 動画のパス

    Returns:
        dict: 動画情報が載った辞書
    """
    cmd = [ffprobe_exe, '-v', 'quiet', '-print_format',
           'json', '-show_format', video_path]
    output = subprocess.check_output(cmd)
    video_format = json.loads(output)['format']
    return video_format


def drawTime(image: Image.Image, second: float) -> Image:
    """渡された画像ファイルに与えられた時刻を書き込む。
    
    Args:
        image (Image.Image): Pillowで取得した画像
        second (float): その画像が切り取られた時間 秒数

    Returns:
        Image: 秒数を書き込んだPillow画像
    """
    global width, height
    fontsize = int(width / 16)  # 文字のサイズ
    postextX = width / 2       # 文字を書き込む位置 x座標 （真ん中）
    postextY = height - fontsize  # 文字を書き込む位置 y座標 （一番下）
    font = ImageFont.truetype(f'C:\Windows\Fonts\HGRSMP.TTF', fontsize)
    font_color = (255, 255, 255, 150)
    edge_color = (0, 0, 0, 200)

    temp_img = image.convert('RGBA')    # アルファ値を追加
    img_size = temp_img.size

    a = Image.new('RGBA', img_size)
    draw_img = ImageDraw.Draw(a)
    draw_img.text(
        (postextX, postextY),
        secToHour(second),
        font=font,
        fill=font_color,
        stroke_width=3,
        stroke_fill=edge_color,
        anchor='ma'
    )

    out_img = Image.alpha_composite(temp_img, a)
    return out_img


def grid_picture(images: list[Image.Image], video_name: str, videoinfo: str) -> None:
    """リストで渡された画像をグリッド上に配置する。
    また、動画情報を書き込むために上部に空白を開けて書き込む。

    Args:
        images (list[Image.Image]): Pillowで得た画像をリストで管理したもの。
        video_name (str): 動画の名前(拡張子を除く)
        videoinfo (str): get_video_infoで得た動画情報
    """
    global width, height, xgrid, ygrid, thumbnail_savepath
    margin = 0  # 画像間の隙間を表す変数。
    widthmargin = 10  # 端の画像の隙間を表す変数。
    information_margin = 200  # 情報を書き込む空白を決める変数。
    fontsize = int(width/24)  # 情報を書き込む文字のサイズ横幅によって決まる。

    # 一つの画像に合成する
    result_image = Image.new('RGB', ((width + margin) * xgrid - margin + widthmargin * 2,
                             (height + margin) * ygrid - margin + information_margin + 10), (128, 128, 128))
    for i, image in enumerate(images):
        x = i % xgrid
        y = i // xgrid
        offset_x = x * (width + margin) + widthmargin
        offset_y = y * (height + margin) + information_margin
        result_image.paste(image, (offset_x, offset_y))

    font = ImageFont.truetype(f'C:\Windows\Fonts\HGRSMP.TTF', fontsize)
    draw = ImageDraw.Draw(result_image)
    draw.multiline_text(
        (widthmargin, widthmargin),
        videoinfo,  # 書き込むテキストを指定
        font=font,
        fill='white',
        stroke_width=3,
        stroke_fill='black',
    )

    # 保存する
    print(
        f'Successfully created {video_name}.jpg in the "{thumbnail_savepath}\\"')
    savepath = os.path.join(thumbnail_savepath, video_name + ".jpg")
    result_image.save(savepath)


def get_image_list(durationlist: list[float], video_path: str) -> list[Image.Image]:
    """"並列で処理を行う
    """
    with ThreadPoolExecutor(max_workers=3) as executor:
        executor.submit(keyinput)
        future = executor.submit(cut_video, durationlist, video_path)
    images = future.result()
    return images


def cut_video(durationlist: list[float], video_path: str) -> list[Image.Image]:
    """ffmpegでリストの中に格納された時間のフレームを抜き取り画像へ変換する。
        また抜き取った時間を画像に書き込む。
        その後、変換した画像をリストに格納する。

    Args:
        durationlist (list[float]): 秒数をリストで管理したもの。
        video_path (str): 動画のパス

    Returns:
        list[Image.Image]: 画像をPillowのリストで管理したもの。
    """
    global width, height, running, thumbnail_savepath
    running = True
    size = str(width) + "*" + str(height)
    images = []  # ffmpegで生成した画像を格納するリスト
    progress_bar = ProgressBar(len(durationlist))
    for i, now in enumerate(durationlist):
        progress_bar.update()
        filename = os.path.basename(video_path)
        filename_without, etc = os.path.splitext(filename)
        save = filename_without + '_TG_' + str(i) + '.jpg'  # 一時的に保存するための変数。
        save = os.path.join(thumbnail_savepath, save)
        subprocess.call([ffmpeg_exe, '-hwaccel', 'cuda', '-loglevel', 'quiet', '-ss', str(now),
                        '-y', '-i', video_path, '-vframes', '1', '-q:v', '1', '-s', size, '-f', 'image2', save])
        image = Image.open(save)
        out_img = drawTime(image, float(now))
        images.append(out_img)
        os.remove(save)  # 追加した後はいらないので削除する。
    print('\r', end='')
    running = False
    return images


def create_thumbnail(video_path: str) -> None:
    """このメソッドにサムネイルを作りたい動画のパスを渡すと生成される。
    """
    global gridsize
    try:
        filename = os.path.basename(video_path)
        filename_without, etc = os.path.splitext(filename)
        video_format = get_format(video_path)
        duration = float(video_format['duration'])
        frame = (duration / gridsize)-1
        videoinfo = get_video_info(video_path)
        durationlist = [frame * (i+1) for i in range(gridsize)]
        images = get_image_list(durationlist, video_path)
        grid_picture(images, filename_without, videoinfo)
    except Exception:
        print(traceback.format_exc())
        print(f'{video_path} is not video file!')


if __name__ == '__main__':
    section_check()
    if len(sys.argv) > 1:
        for arg in sys.argv:
            if arg == sys.argv[0]:
                continue
            create_thumbnail(arg)
    else:
        print('使い方:このファイルに動画をドラッグアンドドロップするか、コマンドラインで直接動画のパスを渡してください。')
        os.system('PAUSE')
