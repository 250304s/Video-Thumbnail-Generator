# Video-Thumbnail-Generator
動画からサムネイルを生成するスクリプトです。 
# ━━━━ 必要な環境 ━━━━  
windows10, ffmpeg(パスを通す必要あり), Nvida製のグラフィックボード
# ━━━━  使い方  ━━━━  
exeファイル上に動画をドラッグアンドドロップすることでexeファイルのあるディレクトリにsaveファイルが生成される。saveフォルダ上にサムネイルを生成する。
```console
python thumbnail_generator.py video.mp4
```
## config.iniの説明
```
[DEFAULT]
width = 960
height = 540
xgrid = 4
ygrid = 4
ffmpeg_path = 
save_thumbnail_path = 
```
- width: 画像一枚当たりの横幅
- height: 画像一枚当たりの高さ
- xgrid: サムネイルを作成するとき画像を横に何枚並べるか
- ygrid: サムネイルを作成するとき画像を縦に何枚並べるか
- ffmpeg_path: ffmpeg.exeとffprobe.exeが存在するディレクトリを指定する。空欄であった場合環境変数を設定しているものとみなす。
- save_thumbnail_path: 画像の保存先を設定する。