# Lepton Viewer 
サーモカメラ Lepton 3.5 の可視化ツールです．  
サーモグラフィ画像表示，閾値以上の画素のハイライト，閾値以上の画素が検出された際のアラーム音提示機能を持ちます．  
Windows PC用です．
  
![LeptonViewer](https://github.com/InteractiveGraphicsLab/LeptonViewer/blob/dev_bellalarm/imgs/leptonviewer.gif "LeptonViewer")
  
  
  
## 実行方法 (exeファイルを利用)
- Lepton 3.5 または Lepton 3.0 がUSB接続されたWindows PCを用意してください
- このリポジトリのリリースより，最新版のzipファイルをダウンロードし，展開してください  
- Visual studio runtimeのインストール
  - 展開したフォルダ内のInstallフォルダを開きVC_redist.x64.exeをダブルクリックしてください
  - すでに新しいバージョンがインストール済み，の表示があればインストール不要です
- dllファイルのアクセス許可
  - 展開したフォルダ内のx64フォルダを開いてください
  - フォルダ内dllを右クリックしプロパティを開いてください
  - 「このファイルは他のコンピューターから取得したものです...」の表示があれば「ブロックの解除」をチェックしてください
  - すべてのdllファイルにこの処理を行ってください
  - ※なければ何もしなくて良いです
- 展開したフォルダ内のLeptonViewer.exeをダブルクリックするとLeptonViewerが起動します．
  
  
  
## 実行方法（Pythonを利用する方法，開発者向け）

LocalのPythonを利用する場合は以下の手順に従ってください．  
インストール不要なものについては随時読み飛ばしてください．  

### 1. Visual studio runtimeのインストール  
- LeptonViewer\SDK\Lepton-SDK_PureThermal_Windows10_1.0.2\Redistributables\VC_redist.x64.exeをダブルクリック  
- すでに新しいバージョンがインストール済み，の表示があればキャンセルして良い  

### 2. dllの利用許可
- LeptonViewer\src\x64下のすべてのdllファイルを右クリックしてプロパティを開く
- 「このファイルは他のコンピューターから取得したものです...」の表示があれば「ブロックの解除」をチェック
- ※なければ何もしなくて良い

### 3. 実行環境の構築
- pythonをインストール（python 3.7とanaconda1.5.1で開発）
- Pycharm (コミュニティ)をインストール
- PycharmでLeptonViewerプロジェクトを開く
- Interpreterを追加：
    - File > Settings > Project: LeptonViewer > Project Interpreter > ギアマーク
    - Add > New environment > (virtual environmentが初めから選択されているはず) > OK
- パッケージをインストール：
  - File > Settings > Project: LeptonViewer > Project Interpreter > プラスマーク
  - それぞれを検索してInstall Packageを押す：
    - opencv-python（自動でnumpyもインストールされるはず）
    - Pillow
    - pythonnet

- ソースコードをプロジェクトへ追加 :
  - File > Settings > Project: プロジェクト名※ > Project Structure > add content root
  - srcフォルダを選択(mark as sourcesを指定) > OK
  - -->　Project windowにsrcフォルダが配置される
  
  
  
#### 4. 実行
- viewer.pyを右クリック > Run
  
  
  
### 5. exeファイル化
- パッケージをインストールと同様にPyInstallerをインストール
- PycharmのTerminalを開く
- .\venv\Scripts\pyinstaller.exe -w .\viewer.spec
- (あるいは .\venv\Scripts\pyinstaller.exe -F -w --hidden-import=clr -i .\src\logo.ico .\src\viewer.py)
- ビルド結果が.\distに生成される
- 実行時に必要なファイル（x64, x86, config.ini, default.ini, logo.ico）をコピーすれば他のwindowsマシンで実行可能
  
  
  
  
  
