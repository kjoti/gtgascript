# はじめに
`gtgascript` は GrADS2gt で複数の GTOOL3 ファイルをまとめて
オープンするスクリプトを生成するツールです．

# 使い方
`gtgascript` の引数にオープンしたいファイルへのパスを指定して下さい．

```shell
$ gtgascript T u v q z Ps T2 olr osr
Writing a script to GLON256-GGLA128-ECMANLP37-744hr-X256-Y128-Z37.gs ... done
```
生成されるファイルには `X軸名-Y軸名-Z軸名-時間ステップ-X軸サイズ-Y軸サイズ-Z軸サイズ.gs`
という名前がつきます．
自動的に生成されるファイル名が衝突しないためにこのような長い名前をついています．
実際に使う際には，不便だと思いますので，使いやすいように適宜リネームしてお使いください．

引数にはディレクトリを指定することもできます．その場合は，
そのディレクトリ以下すべてのファイルを指定したことになります．

GrADS2gt の `run` コマンドでこのスクリプトを実行してください．
```
ga-> run GLON256-GGLA128-ECMANLP37-744hr-X256-Y128-Z37.gs
```

## テンプレート機能
データファイルのパスに特定のパターンが含まれている場合，
そのパスに対して GrADS のテンプレート機能が有効になります
（これはデフォルトの振る舞いです．テンプレート機能が不要の場合は
`gtgascript` の起動時にオプション `-s` を指定して下さい）．


| パス内のパターン（正規表現）| 使用するGrADS のテンプレート| 意味         |
| ---                         | ---                         | ---          |
|y[0-9]{4}                    | %y4                         | 年（4桁）    |
|m[0-1][0-9]                  | %m2                         | 月（2桁）    |
|run[0-9]+                    | %e                          | アンサンブル |
|ens[0-9]+                    | %e                          | アンサンブル |

アンサンブルを表す数字部分の桁数は任意ですが，桁数がそろっている必要があります．
例えば，run1, run2, ..., run10, run11 では期待通りになりません．
run01, run001 のようにゼロでパディングして桁数をそろえておく必要があります．

`gtgascript` の引数にはテンプレートのパターンにマッチする
最初のパスだけを指定して下さい．

例えば，
```shell
$ gtgascript historical/run01/y1850
```
すると `gtgascript` は `run02` や `y1851` にマッチするパスを探し，
複数のパスが存在するようであれば，テンプレート機能を有効にします．

生成されたスクリプトには変数 `tmpl` がテンプレート化されたデータパス，
変数 `tsize` には時間ステップ数，
またアンサンブル数などが自動で設定されます．

以下は，テンプレートが有効になった場合のスクリプトの一例です．
```
****  GrADS script (gtopen/vgtopen)

dir0 = "/絶対パス/historical/run01/y1850"
tmpl = "/絶対パス/historical/run%e/y%y4"

* tsize: The size of T-axis (fix if incorrect).
tsize = 1980

* The number of ensembles: 50
'gtoptions edef 50 %02d'

*          Var     Zlev    Title
* --------------------------------------------------------------
*            z       38    geopotential height [m]
(略)

' gtopen ' dir0'/ATM/z ' tmpl'/ATM/z ' tsize
'vgtopen ' dir0'/ATM/u ' tmpl'/ATM/u ' tsize
'vgtopen ' dir0'/ATM/v ' tmpl'/ATM/v ' tsize
(略)
```
