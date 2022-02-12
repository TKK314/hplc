# hplc
実際に動くアプリは[herokuapp](https://hplcapp.herokuapp.com/)で公開しています

# 概要
このアプリはHPLC（高速液体クロマトグラフィー）のデータを簡便にpdf化します。
txtファイル→pdfファイルへの変換を行います。

# 実際の動作
![HPLCAppデモ](https://user-images.githubusercontent.com/75611809/153698119-27c63495-f048-4be4-8110-fbc0ca0b92bc.gif)
# 使用方法

1. `wiki/sample.txt`ファイルを選択し、出力ボタンを押します
2. 各パラメータ（後述）を任意の値に変更し、Enterボタンで確定します
3. 目的のグラフが描画されたらpdfとして出力ボタンを押し保存します

# パラメータ
### 分
x軸の設定<br>
HPLCのリテンションタイム描画範囲を設定します<br>
デフォルトでは0分〜txtファイルの最大値

### UV
左y軸の設定<br>
HPLCのUVチャート（灰色）の描画範囲を設定します<br>
デフォルトではtxtファイルの最小値〜最大値

### RI
右y軸の設定<br>
HPLCのRIチャート（灰色）の描画範囲を設定します<br>
デフォルトではtxtファイルの最小値〜最大値
