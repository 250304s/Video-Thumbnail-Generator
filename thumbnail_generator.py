import glob
import ffmpeg
import subprocess
import os
from PIL import Image, ImageDraw, ImageFont
import sys


width = 960
height = 540

xgrid = 3
ygrid = 5
gridsize = xgrid * ygrid


def secToHour(second: float) -> str:
    H = int(second / 3600)
    M = int((second % 3600) / 60)
    S = int(second % 60)
    return "{:02}:{:02}:{:02}".format(H, M, S)


def human_readable_size(size):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} TB"


def write_video_info(videofile) -> str:
    probe = ffmpeg.probe(videofile)
    videoname = os.path.basename(videofile)
    vstreams = probe['streams'][0]
    astreams = probe['streams'][1]
    # --- 動画情報 ---
    videosize = int(probe['format']['size'])
    videowidth = vstreams['width']
    videoheight = vstreams['height']
    videofps = vstreams['r_frame_rate']
    videobitrate = int(vstreams['bit_rate'])
    duration = float(vstreams['duration'])
    videocodec = vstreams['codec_name']
    fps = float(videofps.split('/')[0]) / float(videofps.split('/')[1])
    # --------------
    # --- 音声情報 ---
    audiocodec = astreams['codec_name']
    samplerate = astreams['sample_rate']
    channellayout = astreams['channel_layout']
    # --------------
    resulttext = 'File: {}\nSize: {} bytes ({}), duration: {}, avg.bitrate: {}/s\nAudio: {}, {} Hz, {}\nVideo: {}, {}x{}, {:.2f}fps'.format(
        videoname,
        videosize, human_readable_size(videosize), secToHour(
            duration), human_readable_size(videobitrate),
        audiocodec, samplerate, channellayout,
        videocodec, videowidth, videoheight, fps)
    return resulttext


def drawTime(image, second: float):
    global width, height
    fontsize = int(width / 16)
    postextX = width / 2
    postextY = height - fontsize
    font = ImageFont.truetype(f'C:\Windows\Fonts\HGRSMP.TTF', fontsize)
    font_color = (255, 255, 255, 150)
    edge_color = (0, 0, 0, 200)

    temp_img = image.convert('RGBA')
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


def grid_picture(images, filepath, videoinfo: str):
    global width, height, xgrid, ygrid
    margin = 0
    widthmargin = 10
    information_margin = 200
    fontsize = int(width/24)

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
    result_image.save(filepath + ".jpg")
    
def guruguru(number: int):
    if number % 4 == 0:
        print('{}{}'.format("|" ,"\u001B[1A"))
    elif number % 4 == 1:
        print('{}{}'.format("/" ,"\u001B[1A"))
    elif number % 4 == 2:
        print('{}{}'.format("ー" ,"\u001B[1A"))
    else:
        print('{}{}'.format("\\" ,"\u001B[1A"))


def cut_video(durationlist, video):
    global width
    global height
    size = str(width) + "*" + str(height)
    images = []
    videoindo = write_video_info(video)
    for i, now in enumerate(durationlist):
        filename = os.path.basename(video)

        filename_without, etc = os.path.splitext(filename)
        save = str(i) + '.jpg'
        guruguru(i)
        subprocess.call(['ffmpeg', '-hwaccel', 'cuda', '-loglevel', 'quiet', '-ss', str(now), '-i', video, '-vframes',
                        '1', '-q:v', '1', '-s', size, '-f', 'image2', save])
        image = Image.open(save).resize((width, height))
        out_img = drawTime(image, float(now))
        images.append(out_img)
        os.remove(save)
    grid_picture(images, filename_without, videoindo)

def create_thumbnail(filepath):
    global gridsize
    try:
        probe = ffmpeg.probe(filepath)
        duration = float(probe['format']['duration'])
        frame = (duration / gridsize)-1
        durationlist = [frame * (i+1) for i in range(gridsize)]
        cut_video(durationlist, filepath)
    except:
        print('this is not video file!')


if __name__ == '__main__':
    if len(sys.argv) > 1:
        for i in sys.argv:
            if i == sys.argv[0]:
                continue
            create_thumbnail(i)
    else:
        print('使い方:このファイルに動画をドラッグアンドドロップするか、コマンドラインで直接動画のパスを渡してください。')
        input('終了するには何かキーを押してください...')
