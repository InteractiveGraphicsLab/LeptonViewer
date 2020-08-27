実行方法

1. Visual studio runtimeのインストール
・LeptonViewer\SDK\Lepton-SDK_PureThermal_Windows10_1.0.2\Redistributables\VC_redist.x64.exeをダブルクリック
・すでに新しいバージョンがインストール済み，の表示があればキャンセルして良い

2. dllの利用許可
・LeptonViewer\src\x64下のすべてのdllファイルを右クリックしてプロパティを開く
・「このファイルは他のコンピューターから取得したものです...」の表示があれば「ブロックの解除」をチェック
※なければ何もしなくて良い

3. 実行環境の構築
・pythonをインストール（python 3.7とanaconda1.5.1で開発）
・Pycharm (コミュニティ)をインストール
・PycharmでLeptonViewerプロジェクトを開く
    1. pycharmのOpenProject から LeptonViewerフォルダを選択して開く
    2. ソースコードをプロジェクトへ追加 :
        プロジェクトを開いてもpythonプログラムファイルは表示されないので以下の手順を踏む必要がある
        File > Settings > Project: プロジェクト名※ > Project Structure > add content root
        srcフォルダを選択(mark as sourcesを指定) > OK
        -->　Project windowにsrcフォルダが配置される

・Interpreterを追加：
	File > Settings > Project: プロジェクト名※ > Project Interpreter >
	ギアマーク(右上)をクリック > Add >
	(virtual environmentが初めから選択されているはず) >  New environmentを選択 > OKをクリック
・パッケージをインストール：
	File > Settings > Project: プロジェクト名※ > Project Interpreter >
	プラスマークをクリック > 以下3項目をそれぞれ検索してInstall Packageを押す：
		- opencv-python（自動でnumpyもインストールされるはず）
		- Pillow
		- pythonnet

4. 実行
・viewer.pyを右クリック > Run

5. exeファイル化
・パッケージをインストールと同様にPyInstallerをインストール
・PycharmのTerminalを開く
・.\venv\Scripts\pyinstaller.exe -w .\viewer.spec
・(あるいは .\venv\Scripts\pyinstaller.exe -F -w --hidden-import=clr -i .\src\logo.ico .\src\viewer.py)
・ビルド結果が.\distに生成される
・実行時に必要なファイル（x64, x86, config.ini, default.ini, logo.ico）をコピーすれば他のwindowsマシンで実行可能


以下のCC0ライセンスのアラームを利用しています．
219244__zyrytsounds__alarm-clock-short.wav
https://freesound.org/people/ZyryTSounds/sounds/219244/
238390__amorralteixe__alarmclock.wav
https://freesound.org/people/amorralteixe/sounds/238390/
265769__richerlandtv__alarmclock.wav
https://freesound.org/people/RICHERlandTV/sounds/265769/
