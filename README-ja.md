# はじめに
`gtgascript` は GrADS2gt で複数の GTOOL3 ファイルをまとめて
オープンするスクリプトを生成するツールです．

# 使い方
`gtgascript` の引数にオープンしたいファイルへのパスを指定して下さい．

```shell
$ gtgascript T u v q z Ps T2 olr osr
Writing a script to GLON256-GGLA128-ECMANLP37-744hr-X256-Y128-Z37.gs ... done
```
生成されるファイルには `X軸名-Y軸名-Z軸名-時間ステップ-X軸サイズ-Y軸サイズ-Y軸サイズ.gs`
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
データファイルのパスに `y[0-9][0-9][0-9][0-9]` のパターンが含まれ，
かつそのパターンにマッチする別のパスが存在する場合，
GrADS のテンプレート機能を用いてオープンします．

```shell
$ ls -d pictl/y????
pictl/y1600 pictl/y1601 pictl/y1602 ...
$ gtgascript pictl/y1600
Writing a script to GLON256-GGLA128-ECMANLP37-744hr-X256-Y128-Z37.gs ... done
Writing a script to GLON256-GGLA128-GLEVC6-744hr-X256-Y128-Z6.gs ... done
Writing a script to OCLONTPT360-OCLATTPT256-OCDEPT63-744hr-X360-Y256-Z63.gs ... done
```

この例では，y1600, y1601, ... と `y[0-9][0-9][0-9][0-9]` のパターンに
複数のディレクトリがマッチしているため，これらのパスはテンプレート化の対象となります．

以下のように，変数 `tmpl` に GrADS のテンプレートパターンである `%y4` が
使用されています．

```shell
$ cat GLON256-GGLA128-ECMANLP37-744hr-X256-Y128-Z37.gs
****  GrADS script (gtopen/vgtopen)

dir0 = "/data/01/user/pictl/y1600"
tmpl = "/data/01/user/pictl/y%y4"

* tsize: The size of T-axis (fix if incorrect).
tsize = 1752

*          Var     Zlev    Title
* --------------------------------------------------------------
*            z       37    geopotential height [m]
*            v       37    v-velocity [m/s]
*            u       37    u-velocity [m/s]
(略)

' gtopen ' dir0'/ATM/z ' tmpl'/ATM/z ' tsize
'vgtopen ' dir0'/ATM/v ' tmpl'/ATM/v ' tsize
'vgtopen ' dir0'/ATM/u ' tmpl'/ATM/u ' tsize
(略)
```

パスに `run[0-9]+`  のパターンが含まれている場合は，アンサンブル
だと解釈され，テンプレートパターンとして `%e` が使用されます．

```
****  GrADS script (gtopen/vgtopen)

dir0 = "/proj/cmip6/DECK/historical/run01/y1850"
tmpl = "/proj/cmip6/DECK/historical/run%e/y%y4"

* tsize: The size of T-axis (fix if incorrect).
tsize = 1980

* The number of ensembles: 50
'gtoptions edef 50 %02d'

*          Var     Zlev    Title
* --------------------------------------------------------------
*            z       38    geopotential height [m]
(略)

' gtopen ' dir0'/ATM/z ' tmpl'/ATM/z ' tsize
'vgtopen ' dir0'/ATM/v ' tmpl'/ATM/v ' tsize
(略)
```
