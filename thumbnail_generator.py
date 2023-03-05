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
import errno
import json

could_readed = True
# 実行ファイルが存在するディレクトリのパスを取得する
if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
else:
    application_path = os.path.dirname(os.path.abspath(__file__))

# iniファイルのパスを設定する
config_ini_path = os.path.join(application_path, "config.ini")

# iniファイルを読み込む
ini = configparser.ConfigParser()
if not os.path.exists(config_ini_path):
    could_readed = False
ini.read(config_ini_path, 'UTF-8')

width = int(ini['DEFAULT']['width']) if could_readed else 960
height = int(ini['DEFAULT']['height']) if could_readed else 540
xgrid = int(ini['DEFAULT']['xgrid']) if could_readed else 3
ygrid = int(ini['DEFAULT']['ygrid']) if could_readed else 5
gridsize = xgrid * ygrid
running = True

try:
    savepath = ini['USER']['savepath'] if ini['USER']['savepath'] != '' or could_readed else ''
except:
    savepath = ''

if savepath == '':
    save_thumbnail_path = os.path.join(application_path, 'save')
else:
    save_thumbnail_path = savepath
os.makedirs(save_thumbnail_path, exist_ok=True)

# --------------------------------------------
def secToHour(second: float) -> str:
    """秒数で渡されたものをHH:MM:SSの形に直す
    """
    H = int(second / 3600)
    M = int((second % 3600) / 60)
    S = int(second % 60)
    return "{:02}:{:02}:{:02}".format(H, M, S)


def human_readable_size(size) -> str:
    """ファイルサイズを見やすい形に加工する
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


def keyinput():
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

def get_video_info(videofile) -> str:
    """ffprobeを用いて動画の情報を得る。その後加工して文字列として渡す。
    """
    probe = ffmpeg.probe(videofile)
    videoname = os.path.basename(videofile)
    video_info, audio_info = get_streams(videofile)
    videofps = video_info['r_frame_rate']
    videowidth = video_info['width']
    videoheight = video_info['height']
    videocodec = video_info['codec_name']
    audiocodec = audio_info['codec_name']
    samplerate = audio_info['sample_rate']
    channellayout = audio_info['channel_layout']
    duration = float(probe['format']['duration'])
    videobitrate = int(probe['format']['bit_rate'])
    videosize = int(probe['format']['size'])
    fps = float(videofps.split('/')[0]) / float(videofps.split('/')[1])
    resulttext = 'File: {}\nSize: {} bytes ({}), duration: {}, avg.bitrate: {}/s\nAudio: {}, {} Hz, {}\nVideo: {}, {}x{}, {:.2f}fps'.format(
        videoname,
        videosize, human_readable_size(videosize), secToHour(
            duration), human_readable_size(videobitrate),
        audiocodec, samplerate, channellayout,
        videocodec, videowidth, videoheight, fps)
    return resulttext

def get_streams(filename) -> dict:
    cmd = ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_streams', filename]
    output = subprocess.check_output(cmd)
    data = json.loads(output)
    
    video_stream = None
    audio_stream = None
    
    for stream in data['streams']:
        if stream['codec_type'] == 'video':
            video_stream = stream
        elif stream['codec_type'] == 'audio':
            audio_stream = stream
    
    video_info = {
        'codec_name': video_stream.get('codec_name', ''),
        'width': video_stream.get('width', 0),
        'height': video_stream.get('height', 0),
        'r_frame_rate': video_stream.get('r_frame_rate', ''),
    } if video_stream is not None else {}
    
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


def grid_picture(images, filepath, videoinfo: str) -> None:
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
    savepath = os.path.join(save_thumbnail_path, filepath + ".jpg")
    result_image.save(savepath)
    
    
def get_image_list(durationlist, videopath):
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


def create_thumbnail(videopath):
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
    except Exception as e:
        print(e)
        print(f'{videopath} is not video file!')


if __name__ == '__main__':
    if len(sys.argv) > 1:
        for i in sys.argv:
            if i == sys.argv[0]:
                continue
            create_thumbnail(i)
    else:
        print('使い方:このファイルに動画をドラッグアンドドロップするか、コマンドラインで直接動画のパスを渡してください。')
        os.system('PAUSE')
