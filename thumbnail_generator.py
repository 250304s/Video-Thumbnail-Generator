#!python3.10
import ffmpeg
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

# ━━━━━グローバル変数━━━━━
width = 960
height = 540
xgrid = 4
ygrid = 4
save_thumbnail_path = ".\\"
gridsize = xgrid * ygrid
running = True
# ━━━━━━━━━━━━━━━━━


def initialize() -> None:
    """
    初期設定を行う。
    """
    global save_thumbnail_path

    # 実行ファイルが存在するディレクトリのパスを取得する
    if getattr(sys, 'frozen', False):
        application_path = os.path.dirname(sys.executable)
    else:
        application_path = os.path.dirname(os.path.abspath(__file__))

    # 設定ファイル (config.ini) を読み込む (結果出力)
    if read_ini(application_path):
        print('Successfully loaded config.ini.')
    else:
        print('Failed to load config.ini.')
    # サムネイル画像のサイズ (結果出力)
    print(
        f'一枚の横幅: {width}px, 一枚の高さ: {height}px, 横の枚数: {xgrid}枚, 縦の枚数: {ygrid}枚')

    # サムネイル画像の保存先ディレクトリを作成する
    save_thumbnail_path = os.path.join(application_path, 'save')
    os.makedirs(save_thumbnail_path, exist_ok=True)


def read_ini(application_path) -> bool:
    global width, height, xgrid, ygrid
    # config.ini のパスを取得する
    config_ini_path = os.path.join(application_path, "config.ini")
    # ファイルが存在するか確認しエラーハンドリングを行います。
    if not os.path.exists(config_ini_path):
        print('Do not exist config.ini!')
        return False
    # ini ファイルを読み込んで、必要な設定値を取得します。
    ini = configparser.ConfigParser()
    ini.read(config_ini_path, 'UTF-8')
    try:
        width = int(ini['DEFAULT']['width'])
        height = int(ini['DEFAULT']['height'])
        xgrid = int(ini['DEFAULT']['xgrid'])
        ygrid = int(ini['DEFAULT']['ygrid'])
    except KeyError:
        # キーが見つからない場合（値の取得に失敗した場合）はエラーとして処理します。
        e = traceback.format_exc()
        print(e)
        return False
    return True

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


def guruguru() -> None:
    """現在のインデックスに応じて表示を行う
    """
    number = 0
    while running:
        number += 1
        time.sleep(0.25)
        if number % 4 == 0:
            print('\r{}'.format("|"), end='')
        elif number % 4 == 1:
            print('\r{}'.format("/"), end='')
        elif number % 4 == 2:
            print('\r{}'.format("-"), end='')
        else:
            print('\r{}'.format("\\"), end='')
            """if number > 60:
                break"""
    print('\r', end='')


def keyinput() -> None:
    """
    qキーが入力されたとき、プログラムを終了する。
    """
    global running
    while running:
        time.sleep(0.05)
        if keyboard.is_pressed('q'):
            print('\r{}'.format("処理を中断しました。"), end='')
            os._exit(0)
# --------------------------------------------


def get_video_info(videofile: str) -> str:
    """ffprobeを用いて動画の情報を得る。その後加工して文字列として渡す。
    """
    # ffprobeを用いて、動画ファイルについての詳細情報を取得する
    probe = ffmpeg.probe(videofile)
    # 動画ファイルのファイル名を取得する
    videoname = os.path.basename(videofile)
    # ビデオストリームとオーディオストリームに関する情報を取得する
    video_info, audio_info = get_streams(videofile)
    try:
        # キーエラーが発生した場合を想定して、各種情報を取得する
        videofps = video_info['r_frame_rate']
        videowidth = video_info['width']
        videoheight = video_info['height']
        videocodec = video_info['codec_name']
        audiocodec = audio_info['codec_name']
        samplerate = audio_info['sample_rate']
        channellayout = audio_info['channel_layout']
    except KeyError:
        # キーエラーが発生した場合は、エラー内容を表示する
        print(traceback.format_exc())
    # ファイルサイズ、再生時間、ビデオコーデック、音声コーデック、チャンネル数、サンプリング周波数、解像度、フレームレート等の情報を、フォーマットされた文字列として保存する
    duration = float(probe['format']['duration'])
    videobitrate = int(probe['format']['bit_rate'])
    videosize = int(probe['format']['size'])
    try:
        fps = float(videofps.split('/')[0]) / float(videofps.split('/')[1])
    except:
        fps = -1
    resulttext = 'File: {}\nSize: {} bytes ({}), duration: {}, avg.bitrate: {}/s\nAudio: {}, {} Hz, {}\nVideo: {}, {}x{}, {:.2f}fps'.format(
        videoname,
        videosize, human_readable_size(videosize), secToHour(
            duration), human_readable_size(videobitrate),
        audiocodec, samplerate, channellayout,
        videocodec, videowidth, videoheight, fps)
    return resulttext


def get_streams(videofile: str) -> tuple(dict, dict):
    """動画ファイルを与えるとffprobeで各ストリームと取り出す

    Args:
        filename (str): 動画ファイル

    Returns:
        tuple: 動画ストリームと音声ストリームのタプル
    """
    # ffprobeコマンドの実行(引数：メッセージ少なく、JSON形式で出力、全ストリーム情報表示)
    cmd = ['ffprobe', '-v', 'quiet', '-print_format',
           'json', '-show_streams', videofile]
    output = subprocess.check_output(cmd)
    data = json.loads(output)

    # ストリーム情報からビデオとオーディオの情報を抜き出す
    video_stream = None
    audio_stream = None

    for stream in data['streams']:
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


def drawTime(image, second: float) -> Image:
    """渡された画像ファイルとその時刻を書き込む。
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


def grid_picture(images, videoname, videoinfo: str) -> None:
    """リストで渡された画像をグリッド上に配置する。
    また、動画情報を書き込むために上部に空白を開けて書き込む。
    """
    global width, height, xgrid, ygrid, save_thumbnail_path
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
        f'Successfully created {videoname}.jpg in the "{save_thumbnail_path}\\"!')
    savepath = os.path.join(save_thumbnail_path, videoname + ".jpg")
    result_image.save(savepath)


def get_image_list(durationlist, videopath) -> list:
    """"並列で処理を行う
    """
    with ThreadPoolExecutor(max_workers=3) as executor:
        executor.submit(keyinput)
        future = executor.submit(cut_video, durationlist, videopath)
        executor.submit(guruguru)
    images = future.result()
    return images


def cut_video(durationlist, videopath) -> list:
    """ffmpegでリストの中に格納された時間のフレームを抜き取り画像へ変換する。
        また抜き取った時間を画像に書き込む。
        その後、変換した画像をリストに格納する。
    """
    global width, height, running, save_thumbnail_path
    running = True
    size = str(width) + "*" + str(height)
    images = []  # ffmpegで生成した画像を格納するリスト
    for i, now in enumerate(durationlist):
        filename = os.path.basename(videopath)
        filename_without, etc = os.path.splitext(filename)
        save = filename_without + '_TG_' + str(i) + '.jpg'  # 一時的に保存するための変数。
        save = os.path.join(save_thumbnail_path, save)
        subprocess.call(['ffmpeg', '-hwaccel', 'cuda', '-loglevel', 'quiet', '-ss', str(now), '-y', '-i', videopath, '-vframes',
                        '1', '-q:v', '1', '-s', size, '-f', 'image2', save])
        image = Image.open(save)
        out_img = drawTime(image, float(now))
        images.append(out_img)
        os.remove(save)  # 追加した後はいらないので削除する。
    print('\r', end='')
    running = False
    return images


def create_thumbnail(videopath) -> None:
    """このメソッドにサムネイルを作りたい動画のパスを渡すと生成される。
    """
    global gridsize
    try:
        filename = os.path.basename(videopath)
        filename_without, etc = os.path.splitext(filename)
        probe = ffmpeg.probe(videopath)
        duration = float(probe['format']['duration'])
        frame = (duration / gridsize)-1
        videoinfo = get_video_info(videopath)
        durationlist = [frame * (i+1) for i in range(gridsize)]
        images = get_image_list(durationlist, videopath)
        grid_picture(images, filename_without, videoinfo)
    except Exception:
        print(traceback.format_exc())
        print(f'{videopath} is not video file!')


if __name__ == '__main__':
    initialize()
    if len(sys.argv) > 1:
        for i in sys.argv:
            if i == sys.argv[0]:
                continue
            create_thumbnail(i)
    else:
        print('使い方:このファイルに動画をドラッグアンドドロップするか、コマンドラインで直接動画のパスを渡してください。')
        os.system('PAUSE')
