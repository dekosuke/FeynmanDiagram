#!/usr/bin/env python
# coding=utf-8

#ファインマンダイアグラムの描画
#ファインマンダイアグラムについては、fetter-waleckaの本を参照
#
#内容
#・ファインマンダイアグラムの計算（文字情報。\latex形式に出力可能）
#・計算したダイアグラムデータのベクトル画像化（ベクトル画像情報。できれば.ai形式に）
#・ベクトル画像化したダイアグラムデータのpng(gif?)画像化
#ぐらい

#必要な非標準モジュール
#・psyco(なくても構わない）

#必要な環境
#SVGが閲覧できるブラウザ(firefoxなど。IEもプラグインを導入すれば見られる)

#改良案：
#・ダイアグラム生成アルゴリズムの改良（あまり速度には貢献しないが・・・）
#・svg->png変換→batikなるものが。いずれにしろ面倒なので後回し
##・proper/improperで分類
##・いろいろな近似(partial sum)に対応
#・いくつかの関数(getdiagramとgetBigDiagramみたいな)は統一すべし
#巨大svgファイルのオプションについて

HEIGHT_DEF=300
FRAMEHEIGHT_DEF=50
FRAMEWIDTH_DEF=50
ALLHEIGHT_DEF=HEIGHT_DEF+FRAMEHEIGHT_DEF*2
#ALLWIDTH_DEF=WIDTH_DEF+FRAMEWIDTH_DEF*2
#WIDTHが非確定なのは大きな問題だ・・・

#始点か終点か判定
#２文字目がfなら始点、tなら終点
def isEnd(astr):
 if astr[1]=="f":
  return False
 elif astr[1]=="t":
  return True
 else:
  print "unexpected string :",astr
  return
def isStart(astr):
 if astr[1]=="f":
  return True
 elif astr[1]=="t":
  return False
 else:
  print "unexpected string :",astr
  return

#ブロック生成
def createBlock(n):
 n=str(n)
 ret=[]
 ret.append("xf" +n)
 ret.append("xt" +n)
 ret.append("xfd"+n)
 ret.append("xtd"+n)
 return ret
#ブロック生成(終点無し版)
def createBlockf(n):
 n=str(n)
 ret=[]
 ret.append("xf" +n)
 ret.append("xfd"+n)
 ret.append("xtd"+n)
 return ret
#ブロック生成(始点無し版)
def createBlockt(n):
 n=str(n)
 ret=[]
 ret.append("xt" +n)
 ret.append("xfd"+n)
 ret.append("xtd"+n)
 return ret
  
#項(線)のlatexの数学記号化
#iG^0(y^\prime_1,x)
#みたいな
def toLatex(aline):
 rstart=aline[0][0]
 if len(aline[0])>2:
  if aline[0][2]=="d":
   rstart+="^\prime"
  rstart+="_"+aline[0][-1]
 rend=aline[1][0]
 if len(aline[1])>2:
  if aline[1][2]=="d":
   rend+="^\prime"
  rend+="_"+aline[1][-1]
 return "iG^0("+rend+","+rstart+")"

#t(終点)からf(始点)に
import string
def TToFconv(astr):
 return string.replace(astr,"t","f")

#
#ファインマンダイアグラム作成（視覚化）
#

#ダイアグラムをメインライン(y->x)とループのリストに分解
def decompose(nodes, alines, wavelines=[]):
 lines=[]
 #alinesの記号からt,fを抜いたものがlines
 for i in range(len(alines)):
  #lines.append([])
  a=string.replace(alines[i][0],"f","")
  a=string.replace(a,"t","")
  b=string.replace(alines[i][1],"f","")
  b=string.replace(b,"t","")
  lines.append([a,b])
 #print alines,lines
 #まず、yからxへの経路を検出
 mainpath=[]
 nowNode=lines[0][0] #yf
 mainpath.append(nowNode)
 if nowNode!="y":
  print "unexpected start node!",lines
  return
 while nowNode!="x":
  for i in range(len(lines)):
   if lines[i][0]==nowNode: #線が見つかった
    mainpath.append(lines[i][1])
    nowNode=lines[i][1]
    del(lines[i])
    break
  else: #線が切れている場合
   print "disconnected main line",lines
   return
 #次に各ループを検出
 if len(lines)==0: #ループ無し
  return (mainpath, [])
 loops=[]
 loops.append([])
 #print "lines=",lines
 loopStart=lines[0][0] #ループ始点
 nowNode=lines[0][0]
 while True: #線が残っている場合
  for i in range(len(lines)):
   if lines[i][0]==nowNode:
    loops[-1].append(nowNode)
    nowNode=lines[i][1]
    del(lines[i])
    if nowNode==loopStart: #ループが閉じた
     if len(lines)>0:
      loopStart=lines[0][0]
      nowNode=loopStart
      loops.append([])
     else:
      return (mainpath, loops) 
    break
 print "unexpected end"

#
#ある記号と共役な記号を返す
#ようするにx1の共役はxd1（逆も然り）で、xの共役はy
#xとyを除く共役な２点はwavy lineで結ばれる
def conjugate(aline):
 #print aline
 if aline=="x":
  return "y"
 elif aline=="y":
  return "x"
 elif aline[1]=="d":
  return aline[0]+aline[2]
 elif len(aline)==2:
  return aline[0]+"d"+aline[1]
 else:
  print "unexpected symbol in conjugate()",aline

def mean(a,b):
 return (a+b)/2
def bigger(a,b):
 if a>b:
  return a
 else:
  return b
def slide(aline, n):
 return aline[n:]+aline[:n]
def revslide(aline, n):
 return aline[-n:]+aline[:-n]

#位置クラス。xとyのみ
class Pos:
 def __init__(self, x,y):
  self.x=x
  self.y=y
 def __add__(self, arg):
  #新しい位置インスタンスを作成して返す
  if isinstance(arg, Pos):
   ret=Pos( arg.x+self.x, arg.y+self.y )
   return ret
  elif isinstance(arg, tuple):
   ret=Pos( self.x+arg[0], self.y+arg[1] )
   return ret
  else:
   #print arg
   raise PositionError,"Unexpected type for __add__ operation.",arg #例外出す
 def __radd__(self, arg):
  #print "self=",self
  #print "arg=",arg
  return self.__add__(arg)
 def __iadd__(self, arg):
  self.x+=arg.x
  self.y+=arg.y
  return self
 def __mul__(self, arg):
  ret=Pos( self.x*arg, self.y*arg ) #スカラー倍
  return ret
 def __div__(self, arg):
  ret=Pos( self.x/arg, self.y/arg )
  return ret
 def __imul__(self, arg):
  if isinstance(arg, float) or isinstance(arg,int): #スカラー倍
   self.x*=arg
   self.y*=arg
  else:
   raise PositionError,"Unexpected type for __imul__ operation." #例外出す
 def __idiv__(self, arg):
  if isinstance(arg, float) or isinstance(arg,int): #スカラー倍
   self.x/=arg
   self.y/=arg
  else:
   raise PositionError,"Unexpected type for __imul__ operation." #例外出す
 def __repr__(self):
  return "Pos"+str( (self.x, self.y) )
 def distance(self, apos):
  d2=(self.x-apos.x)**2+(self.y-apos.y)**2
  return d2**0.5

OBJ_LINE=0
OBJ_CIRCLE=1
OBJ_POINT=2
OBJ_DLINE=3
OBJ_WLINE=4
OBJ_WCIRCLE=5
#placeの戻り値で描画する画像の単位なクラス
#x,y型の位置にはPos型を利用
#型それぞれで継承したほうがいいとかいうことはキニシナイ
class VecObj:
 def __init__(self, *args):
  self.type=args[0]
  if self.type==OBJ_LINE:
   self.f=copy.deepcopy(args[1])
   self.t=copy.deepcopy(args[2])
  elif self.type==OBJ_CIRCLE:
   self.x=copy.deepcopy(args[1]) #中心位置
   self.rad=args[2] #半径
   self.args=copy.deepcopy(args[3]) #左のargsは(円の中の点の)角度で、右のargsは引数(笑)
  elif self.type==OBJ_POINT:
   self.x=copy.deepcopy(args[1])
   self.symbol=args[2] #記号。yとかxとかx2とかx3dとかの文字列。
  elif self.type==OBJ_DLINE:
   pass #未実装
  elif self.type==OBJ_WLINE: #データ構造的には普通の線と同じ
   self.f=copy.deepcopy(args[1])
   self.t=copy.deepcopy(args[2])  
  elif self.type==OBJ_WCIRCLE:
   #２点を結ぶ破線
   #データ構造的には普通の線と同じ→右周りか左周りかの情報をつけるようになった  
   self.f=copy.deepcopy(args[1])
   self.t=copy.deepcopy(args[2])
   if len(args)>3: #回る方向。初期化後の代入でもいい
    self.rightRot=copy.deepcopy(args[3])
 def __repr__(self):
  if self.type==OBJ_LINE:
   typeStr="LINEOBJECT "   
  elif self.type==OBJ_CIRCLE:
   typeStr="CIRCLEOBJECT "
  elif self.type==OBJ_POINT:
   typeStr="POINTOBJECT "
  elif self.type==OBJ_DLINE:
   typeStr="DLINEOBJECT "
  elif self.type==OBJ_WLINE:
   typeStr="WAVYLINEOBJECT "
  elif self.type==OBJ_WCIRCLE:
   typeStr="WAVYCIRCLEOBJECT "
  return typeStr+str( vars(self) )
 def translate(self, m ): #mはPos型
  #print "self=",self
  #print "m=",m
  if hasattr(self, "f"):
   self.f+=m
  if hasattr(self, "t"):
   self.t+=m
  if hasattr(self,"x"):
   self.x+=m
 def lineartransform(mat):
  #線形変換
  if hasattr(self, "f"):
   self.f.x,self.f.y=mat[0][0]*self.f.x+mat[0][1]*self.f.y,mat[1][0]*self.f.x+mat[1][1]*self.f.y
  if hasattr(self, "t"):
   self.t.x,self.t.y=mat[0][0]*self.t.x+mat[0][1]*self.t.y,mat[1][0]*self.t.x+mat[1][1]*self.t.y
  if hasattr(self,"x"):
   self.x,self.y=mat[0][0]*self.x+mat[0][1]*self.y,mat[1][0]*self.x+mat[1][1]*self.y
 def rotate(arg):
  #位置情報の回転だけじゃなく、circleの場合は角度も変える必要があるな・・・
  pass
 def positions():
  #円専用。構成している点の座標のリストを(argsから計算して)返す
  pass
 def __str__(self):
  return self.__repr__()

import math
circleRatio=0.7/math.pi #ダイアグラムの円（１－ループの大きさ）の、単位線に対する大きさの比
distanceRatio=0.5 #円を作成するときの左側との間隔（の単位線に対する大きさの比）
oneSizeLoopRatio=0.7 #１つだけの円の大きさにかける係数
#circSizeRatio=0.7 #出現部分参照
#ダイアグラムの各要素の描画位置（と大きさ）を決定
#縦の長さ(height)は固定、横の長さは固定されていない
#返り値はheight, width, objects
def place(lineAndLoops, height=HEIGHT_DEF, frameHeight=FRAMEHEIGHT_DEF*2, frameWidth=FRAMEWIDTH_DEF*2):
 global circleRatio
 objects=[] #返り値
 mainline=lineAndLoops[0]
 loops=lineAndLoops[1]
 #positionsは位置のハッシュ
 positions={}
 #ループのほうは各点の位置の他に、円の情報が必要
 circleSpec=[]
 #mainlineの各点の位置設定
 for i in range(len(mainline)):
  elem=mainline[i]
  positions[elem]=Pos( frameWidth/2, height*(len(mainline)-i-1)/(len(mainline)-1) + frameHeight/2 )
 #メイン線を追加
 num=len(mainline)-1 #メイン線の分割数
 for i in range(num):
  objects.append( VecObj(OBJ_LINE, Pos(frameWidth/2,height*(i+1)/float(num)+frameHeight/2), Pos(frameWidth/2,height*i/float(num)+frameHeight/2) ) )  
 maincomp=copy.deepcopy(mainline)  #mainline+既に位置の決定されたループ（後で追加）の連結成分
 #基準とする大きさ。mainlineの一つの線の長さ
 unitLine=height/(len(mainline)-1)
 #それぞれのループの位置を決定していく
 for i in range(len(loops)):
  #最初にループの各点に対する共役点がmaincompに存在するかどうか探す
  mainMatchList=[]
  for elem in loops[i]:
   cond=conjugate(elem)
   #print "cond=",cond
   if cond in maincomp: 
    #mainloop中に見つかった
    mainMatchList.append(elem)
  mainMatchNum=len(mainMatchList)
  #ループの位置と形を決定する。
  #ループの要素数とmaincompとの共役点の数の組で場合分けして処理する
  loopSize=len(loops[i])
  if loopSize==1:
   if mainMatchNum==1:
    cond=conjugate(loops[i][0])
    basePos=positions[cond]
    positions[loops[i][0]]=basePos+Pos(unitLine*distanceRatio, 0) #1-loop円のポジションは円の左端
    circRad=unitLine*circleRatio*oneSizeLoopRatio
    circleSpec.append( ([math.pi,], basePos+Pos(unitLine*(distanceRatio)+circRad,0)\
, circRad) ) #円の形指定。(円を構成するループ各点の角度、中心座標、半径)のタプル
    #maincomp.append(loops[i][0])
   else: #ダイアグラム生成のアルゴリズム上たぶんありえない筈だが・・・
    print "error: disconnected loop!"
    return
  elif loopSize==2:
   if mainMatchNum==2: #2-2ループ
    cond1=conjugate(loops[i][0])
    cond2=conjugate(loops[i][1])    
    basePoses=[]
    basePoses.append(positions[cond1])
    basePoses.append(positions[cond2])
    if basePoses[0].y<basePoses[1].y:
     upper=0 #上にある点
    else:
     upper=1
    if basePoses[0].x>basePoses[1].x:
     right=0 #右にある点
    else:
     right=1    
    circRad=abs(basePoses[1].y-basePoses[0].y)/2
    positions[loops[i][0]]=Pos(basePoses[right].x+unitLine*distanceRatio+circRad, basePoses[0].y)
    positions[loops[i][1]]=Pos(basePoses[right].x+unitLine*distanceRatio+circRad, basePoses[1].y)
    if upper==0:
     args=[math.pi/2,3*math.pi/2]
    else:
     args=[3*math.pi/2,math.pi/2] #普通こっちの筈
    circleSpec.append( (args, Pos(positions[loops[i][0]].x, (basePoses[0].y+basePoses[1].y)/2),\
 circRad) )#円の形指定。(円を構成するループ各点の角度、中心座標、半径)のタプル
   elif mainMatchNum==1: #2-1ループ
    cond1=conjugate(loops[i][0])
    positions[loops[i][0]]=positions[cond1]+Pos(unitLine*distanceRatio, 0)
    positions[loops[i][1]]=positions[cond1]+Pos( unitLine*(distanceRatio+2*circleRatio),0 )
    args=[math.pi,0.0]
    #Pos( (positions[loops[i][0]].x+positions[loops[i][1]].x)/2, positions[loops[i][0]].y)\ #下の行の変更前
    circleSpec.append( (args, (positions[loops[i][0]]+positions[loops[i][1]])/2.0\
,  unitLine*circleRatio) )#円の形指定。(円を構成するループ各点の角度、中心座標、半径)のタプル
   else: #ダイアグラム生成のアルゴリズム上たぶんありえない筈だが・・・
    print "error: disconnected loop!"
    return
  else: #一般的な場合。個別の場合以外の処理
   if mainMatchNum==1:
    basePos=positions[conjugate(mainMatchList[0])] #基準点
    circRad=unitLine*circleRatio*(loopSize-2) #円の半径
    circCenter=basePos+Pos(unitLine*distanceRatio+circRad,0) #中心点
    cpIndex=loops[i].index(mainMatchList[0]) #連結点の番号
    newLoop=slide(loops[i],cpIndex)
    #連結される点は180度の位置に行くが、他の点は90度から-90度に均等に配置
    args=[]
    for j in range(loopSize-1):
     args.append( math.asin(1-2.0*j/(loopSize-2)) )
    argList=[math.pi,]+copy.deepcopy(args)
    #回転
    argList=revslide(argList,cpIndex)
    positions[mainMatchList[0]]=circCenter+Pos( circRad*math.cos(math.pi), -circRad*math.sin(math.pi) )
    for j in range(len(args)):
     positions[newLoop[j+1]]=circCenter+Pos( circRad*math.cos(args[j]),-circRad*math.sin(args[j]) )
    circleSpec.append( (argList, circCenter, circRad) )
   elif mainMatchNum>1:
    #その他。最も一般的なパターンだが、３次以上の高次の項にて出てくる
    #1/1,2/1,2/2,n/1以外は全てこれに
    #メイン部分との結合がある点の中で、最も低い位置と最も高い位置にいる点を探す（円の大きさを決定するのに必要）
    lowest=height+frameHeight #初期化
    lowref=0 #一番上の点
    highest=0 
    right=0 #最も右側
    for elem in mainMatchList:
     #elem=mainMatchList[j]
     cond=conjugate(elem)
     if positions[cond].y<lowest:
      lowest=positions[cond].y
      lowref=loops[i].index(elem) #elemの番号
     if positions[cond].y>highest:
      highest=positions[cond].y
     if positions[cond].x>right:
      right=positions[cond].x
    #円の位置の決定
    #basePos=right+unitLine*distanceRatio,mean(lowest,highest) #円左端
    circRad=bigger( (highest-lowest)/2.0 , unitLine*(loopSize-mainMatchNum-1)/2 )#半径
    circCenter=Pos( right+unitLine*distanceRatio+circRad,mean(lowest,highest) ) #中心
    #一番上の点を上端（90度）にあわせて、残りを適当に配置
    argDif=2*math.pi/loopSize
    #ループを円順にずらす（９０度の点が最初になるようにする）
    newloop=slide(loops[i],lowref)
    #print "newloop=",newloop
    args=[]
    argList={}
    for j in range(loopSize):
     args.append(math.pi/2-argDif*j)
     argList[newloop[j]]=args[-1]
     positions[newloop[j]]=circCenter+Pos( circRad*math.cos(args[-1]), -circRad*math.sin(args[-1]) )
    newArgs=[]
    for j in range(loopSize):
     newArgs.append(argList[loops[i][j]])
    circleSpec.append( ( newArgs, circCenter, circRad) )
    pass
   else: #ダイアグラム生成のアルゴリズム上たぶんありえない筈だが・・・
    print "error: disconnected loop!"
    return
  for elem in loops[i]:
   maincomp.append(elem) #ループを連結リストに追加
 for j in range(len(circleSpec)):
  objects.append( VecObj(OBJ_CIRCLE, circleSpec[j][1],circleSpec[j][2], circleSpec[j][0]) ) #円を追加
 for point in maincomp:
  objects.append( VecObj(OBJ_POINT, positions[point],point) ) #点を追加
 width=100
 for j in range(len(circleSpec)): #横の大きさ検出
  #print circleSpec
  if circleSpec[j][1].x+circleSpec[j][2] > width:
   width=circleSpec[j][1].x+circleSpec[j][2]
 #波線を追加
 for key in positions.keys():
  if len(key)==3:
   if (key in mainline) and (conjugate(key) in mainline):
    #両方ともメイン線上にあるとメイン線とかぶるので曲線になる
    objects.append( VecObj(OBJ_WCIRCLE, positions[conjugate(key)],positions[key]) )
   else:
    objects.append( VecObj(OBJ_WLINE, positions[conjugate(key)],positions[key]) )


 #波半円の左右の並べ方アルゴリズム
 #衝突の少ない側（同じ衝突数なら右）に並ぶ
 def iscoll(aobj, bobj):
  bigs=[]
  smls=[]
  bigs.append( max(aobj.f.y,aobj.t.y) )
  smls.append( min(aobj.f.y,aobj.t.y) )
  bigs.append( max(bobj.f.y,bobj.t.y) )
  smls.append( min(bobj.f.y,bobj.t.y) )
  if bigs[0]>bigs[1]:
   bigger=0
   smaller=1
  else:
   bigger=1
   smaller=0
  if smls[bigger]<bigs[smaller] and smls[bigger]>smls[smaller]:
   return True
  else:
   return False
 #波半円が右回りか左回りかの決定
 wcobjects=[] #全波半円オブジェクトのリスト
 wcMaxSize=0 #左半円オブジェクトの最大半径
 for object in objects:
  if object.type==OBJ_WCIRCLE:
   wcobjects.append(object)
 rightList=[] #右半円のリスト
 leftList=[]  #左半円のリスト     
 if len(wcobjects)!=0: 
  rightList.append(wcobjects[0]) #最初のオブジェクトは右に配置
  wcobjects[0].rightRot=True
  for i in range(1,len(wcobjects)):
   leftColl=rightColl=0 #左と右の衝突数
   for elem in rightList:
    if iscoll(wcobjects[i],elem):
     rightColl+=1
   for elem in leftList:
    if iscoll(wcobjects[i],elem):
     leftColl+=1
   if rightColl<=leftColl:
    print "right"
    rightList.append(wcobjects[i])
    wcobjects[i].rightRot=True
   else:
    print "left"
    leftList.append(wcobjects[i])
    wcobjects[i].rightRot=False
    rad=abs(wcobjects[i].f.y-wcobjects[i].t.y)/2
    if rad > wcMaxSize:
     wcMaxSize=rad
  #左半円のぶんだけ全体を右にずらす
  for object in objects:
   object.translate(Pos(wcMaxSize,0))
  width+=wcMaxSize
 return (height+frameHeight, width+frameWidth, objects)

def lower(aPos,bPos):
 if aPos.y<bPos.y:
  return aPos
 else:
  return bPos
def higher(aPos,bPos):
 if aPos.y>bPos.y:
  return aPos
 else:
  return bPos

import webbrowser
#画像の描画
#直線と点と円と波線と矢印が描ける
#SVG形式(ベクタ画像)にする
import os
def drawGraphInSVG(height,width, objects,  savefile=('','test','svg'),\
 browserView=False, fontDraw=True, arrowDraw=True, wavyLinePosAdj=True):
 print "args=",height,width,objects,"AAAA",savefile,browserView,fontDraw,arrowDraw,wavyLinePosAdj
 strokeWidth=1.5#2.5
 wavRatio=1.0 #0.5#波の横方向の大きさ。
 waveVertSize=5.0 #3.0#波の縦方向の大きさ
 #waveHolSize=1.0 #波の横方向の大きさ。未実装
 waveStrokeRatio=0.9 #波線の線の太さ（の通常線に対する比）
 fontSize=12 #フォントの大きさ
 fontDist=(-20,-10) #各記号の元の点からの位置
 font="Verdana" #フォントの種類
 arrowSize=5
 arrowStrokeRatio=0.7
 #y=a sin(kx) where a=strokeWidth*2 b= waveRatio
 xmlStr=[]
 xmlStr.append('<?xml version="1.0" standalone="no"?>\n')
 xmlStr.append('<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" \n\
  "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">\n')
 xmlStr.append('<svg width="'+str(width)+'" height="'+str(height)+'"\n      xmlns="http://www.w3.org/2000/svg" version="1.1">\n')
 nowwc=0 #現在何番目の波線か（偶数番目の波線は左に回す）
 #各オブジェクトを順番に描画する
 #オブジェクトの形式
 for object in objects:
  if object.type==OBJ_LINE:
   #直線を描画 attr1=from attr2=to (from, toはタプル)
   #draw.line((object[1],object[2]), fill=(0,0,0), width=10)
   xmlStr.append('<line x1="'+str(object.f.x)+'" y1="'+str(object.f.y)+'"\
 x2="'+str(object.t.x)+'" y2="'+str(object.t.y)+'" stroke="black" stroke-width="'+str(strokeWidth)+'"/>\n')
   if arrowDraw:
    #矢印を描画
    #直線は縦方向であることを仮定
    theta=math.pi
    P0=Pos(math.cos(theta+3*math.pi/2), -math.sin(theta+3*math.pi/2) )*arrowSize
    P1=Pos(math.cos(theta+  math.pi/6), -math.sin(theta+  math.pi/6) )*arrowSize
    P2=Pos(math.cos(theta+5*math.pi/6), -math.sin(theta+5*math.pi/6) )*arrowSize
    mx,my=mean(object.f.x,object.t.x), mean(object.f.y,object.t.y) #中点
    xmlStr.append('<line x1="'+str(mx+P1.x)+'" y1="'+str(my++P1.y)+'"\
  x2="'+str(mx+P0.x)+'" y2="'+str(my++P0.y)+'" stroke="black" stroke-width="'+str(strokeWidth*arrowStrokeRatio)+'"/>\n')   
    xmlStr.append('<line x1="'+str(mx+P2.x)+'" y1="'+str(my++P2.y)+'"\
  x2="'+str(mx+P0.x)+'" y2="'+str(my++P0.y)+'" stroke="black" stroke-width="'+str(strokeWidth*arrowStrokeRatio)+'"/>\n')   
  elif object.type==OBJ_DLINE:
   #破線を描画 attrは直線と同じ                    
   pass
  elif object.type==OBJ_WLINE or object.type==OBJ_WCIRCLE: #波線・波半円
  #WCIRCLEはメイン線上じゃないと問題が起こるかも
   mode=object.type
   #print object
   #波線を描画 attrは直線と同じ
   #最初に直線の中間点を導出
   Tx=math.pi/wavRatio
   if mode==OBJ_WLINE:
    startPos=object.f
    endPos=object.t
    length=math.sqrt( (object.t.x-object.f.x)**2 + (object.t.y-object.f.y)**2 )    
    iPointNum=int(length/Tx) #中間点の数
    #print "iPointNum =",iPointNum
   else: #OBJ_WCIRCLE
    nowwc+=1
    if wavyLinePosAdj:
     if object.rightRot: #右に回す
      startPos=higher(object.f,object.t)
      endPos=lower(object.f,object.t)
     else: #左に回す
      startPos=lower(object.f,object.t)
      endPos=higher(object.f,object.t)     
    else:
     startPos=object.f
     endPos=object.t
    length=math.sqrt( (endPos.x-startPos.x)**2 + (endPos.y-startPos.y)**2 )*math.pi/2    
    iPointNum=int(length/Tx) #中間点の数    
    #print "iPointNum =",iPointNum
    iPoints=[] #中間点の導出。ただし中間点には始点も含む
    center=Pos( (startPos.x+endPos.x)/2.0, (startPos.y+endPos.y)/2.0)
    radius=(endPos.y-startPos.y)/2.0
    for i in xrange(iPointNum+1):
     theta=math.pi*float(i)/iPointNum
     x=center.x-radius*math.sin(theta)
     y=center.y+radius*math.cos(theta)
     iPoints.append( (x,y) )
   #各ベジェ曲線の作成
   (x1,y1)=0,0  #(x1,y1)-(x4,y4)は基準点
   (x2,y2)=math.pi/2-0.3,1.33*waveVertSize
   (x3,y3)=math.pi/2+0.3,1.33*waveVertSize
   (x4,y4)=math.pi,0
   #アフィン変換して各点を作成
   #arg=math.atan2(object[2][1]-object[1][1],object[2][0]-object[1][0]) #回転角   
   #size=float(length)/iPointNum
   #奇数の形（上側の波）はoが、偶数の形はeが最後についてる
   if mode==OBJ_WLINE:
    a=(endPos.x-startPos.x)/float(iPointNum)/math.pi
    b=(endPos.y-startPos.y)/float(iPointNum)/math.pi
    (x2do, y2do)=x2*a-y2*b,x2*b+y2*a
    (x3do, y3do)=x3*a-y3*b,x3*b+y3*a
    (x2de, y2de)=x2*a+y2*b,x2*b-y2*a
    (x3de, y3de)=x3*a+y3*b,x3*b-y3*a
    (x4,y4)=(endPos.x-startPos.x)/float(iPointNum),(endPos.y-startPos.y)/float(iPointNum) 
    xmlStr.append('<path\n')
    xmlStr.append(' fill="none" fill-opacity="1" fill-rule="evenodd"\
 stroke="black" stroke-width="'+str(strokeWidth*waveStrokeRatio)+'"\n')
    xmlStr.append('d=" M '+str(startPos.x)+','+str(startPos.y)+' \n')
    #各点を作成
    for i in range(iPointNum):
     if i%2==0:
      xmlStr.append(' c '+str(x2do)+','+str(y2do)+' '+str(x3do)+','+str(y3do)+' '+str(x4)+','+str(y4)+' \n')
     else:
      xmlStr.append(' c '+str(x2de)+','+str(y2de)+' '+str(x3de)+','+str(y3de)+' '+str(x4)+','+str(y4)+' \n')
    xmlStr.append('" />\n')
   else: #OBJ_WCIRCLE
    xmlStr.append('<path\n')
    xmlStr.append(' fill="none" fill-opacity="1"\
 fill-rule="evenodd" stroke="black" stroke-width="'+str(strokeWidth*waveStrokeRatio)+'"\n')
    xmlStr.append('d="\n')
    for i in xrange(iPointNum):
     #波線。注意すべきはこっちは相対座標じゃなくて絶対座標な点
     a=(iPoints[i+1][0]-iPoints[i][0])/math.pi
     b=(iPoints[i+1][1]-iPoints[i][1])/math.pi
     if i%2==0:
      x2d,y2d=x2*a-y2*b+iPoints[i][0],x2*b+y2*a+iPoints[i][1]
      x3d,y3d=x3*a-y3*b+iPoints[i][0],x3*b+y3*a+iPoints[i][1]
     else:
      x2d,y2d=x2*a+y2*b+iPoints[i][0],x2*b-y2*a+iPoints[i][1]
      x3d,y3d=x3*a+y3*b+iPoints[i][0],x3*b-y3*a+iPoints[i][1]
     x4d,y4d=iPoints[i+1][0],iPoints[i+1][1]
     xmlStr.append('M '+str(iPoints[i][0])+','+str(iPoints[i][1])+' C '+str(x2d)+','+str(y2d)+' '+str(x3d)+','+str(y3d)+' '+str(x4d)+','+str(y4d)+' \n')
    xmlStr.append('" />\n')
  elif object.type==OBJ_CIRCLE:
   #円を描画 attr1=center, attr2=radius
   xmlStr.append('<circle cx="'+str(object.x.x)+'" cy="'+str(object.x.y)+'"\
 r="'+str(object.rad)+'" stroke="black"  fill="none" fill-opacity="1" stroke-width="'+str(strokeWidth)+'"/>\n')
   #rightArrow=(Pos(0,0),Pos(-arrowSize,-arrowSize),Pos(-arrowSize,+arrowSize))
   #leftArrow =(Pos(0,0),Pos( arrowSize,-arrowSize),Pos( arrowSize,+arrowSize)) 
   if arrowDraw:
    #円上の矢印を描画
    args=object.args
    Base=Pos(0,0) #矢印の見た目調整用
    #print "args=",args
    if len(args)==1: #1点だけの円
     mPos=object.x+Pos(object.rad,0)#+Pos(math.cos(math.pi),-math.sin(math.pi))*object.rad
     mPos+=Base
     #print "mPos=",mPos
     theta=0
     P0=Pos(math.cos(theta+3*math.pi/2), -math.sin(theta+3*math.pi/2) )*arrowSize
     P1=Pos(math.cos(theta+  math.pi/6), -math.sin(theta+  math.pi/6) )*arrowSize
     P2=Pos(math.cos(theta+5*math.pi/6), -math.sin(theta+5*math.pi/6) )*arrowSize
     arrow=(mPos+P0, mPos+P1, mPos+P2 )
     #print arrow
     xmlStr.append('<line x1="'+str(arrow[1].x)+'" y1="'+str(arrow[1].y)+'"\
  x2="'+str(arrow[0].x)+'" y2="'+str(arrow[0].y)+'" stroke="black" stroke-width="'+str(strokeWidth*arrowStrokeRatio)+'"/>\n')   
     xmlStr.append('<line x1="'+str(arrow[2].x)+'" y1="'+str(arrow[2].y)+'"\
  x2="'+str(arrow[0].x)+'" y2="'+str(arrow[0].y)+'" stroke="black" stroke-width="'+str(strokeWidth*arrowStrokeRatio)+'"/>\n')       
    else: #2点以上の円。右回り。
     for i in range(len(args)):
      arg=args[i]
      if i==0:
       argb=args[-1]
      else:
       argb=args[i-1]
      if arg>argb:
       theta=mean(arg,argb)-math.pi
      else:
       theta=mean(arg,argb)
      P0=Pos(math.cos(theta+3*math.pi/2), -math.sin(theta+3*math.pi/2) )*arrowSize
      P1=Pos(math.cos(theta+  math.pi/6), -math.sin(theta+  math.pi/6) )*arrowSize
      P2=Pos(math.cos(theta+5*math.pi/6), -math.sin(theta+5*math.pi/6) )*arrowSize
      arrow=(Base+P0, Base+P1, Base+P2)
      mPos=object.x+Pos(math.cos(theta),-math.sin(theta))*object.rad
      arrow=(arrow[0]+mPos, arrow[1]+mPos, arrow[2]+mPos)
      xmlStr.append('<line x1="'+str(arrow[1].x)+'" y1="'+str(arrow[1].y)+'"\
   x2="'+str(arrow[0].x)+'" y2="'+str(arrow[0].y)+'" stroke="black" stroke-width="'+str(strokeWidth*arrowStrokeRatio)+'"/>\n')   
      xmlStr.append('<line x1="'+str(arrow[2].x)+'" y1="'+str(arrow[2].y)+'"\
   x2="'+str(arrow[0].x)+'" y2="'+str(arrow[0].y)+'" stroke="black" stroke-width="'+str(strokeWidth*arrowStrokeRatio)+'"/>\n')   
   
  elif object.type==OBJ_POINT:
   #点を描画 attr1=point
   xmlStr.append('<circle cx="'+str(object.x.x)+'" cy="'+str(object.x.y)+'"\
 r="'+str(strokeWidth*1.5)+'" fill="black" stroke="black" stroke-width="'+str(strokeWidth)+'"/>\n')
   #文字を描画 attr2=その場所の記号
   if fontDraw:
    pointName=object.symbol.replace("d","'")
    xmlStr.append('<text x="'+str(object.x.x+fontDist[0])+'" y="'+str(object.x.y+fontDist[1])+'"\
 fill="black" font-family="'+font+'" font-size="'+str(fontSize)+'" >'+pointName+'</text>\n')
  else:
   print "unexpected object!",object
   #return
 #img.show() #PNGファイルで保存
 #img.save(savefile, 'PNG', dpi=(72,72)) #PNGファイルで保存
 #del draw
 xmlStr.append("</svg>")
 filename=os.path.join( os.curdir, savefile[0], (savefile[1]+"."+savefile[2]) )
 #ディレクトリが存在するかどうかのチェック(存在しなかったら作る）
 if savefile[0]!="" and not savefile[0] in os.listdir(os.curdir):
  print "create directory",savefile[0]
  os.mkdir( os.path.join(os.curdir,savefile[0]) )
 print "save to "+filename
 fileobj=file(filename,"w")
 fileobj.writelines(xmlStr)
 fileobj.close()
 if browserView:
  webbrowser.open(filename)
 
#ファインマンダイアグラム計算
#
#データ構造
#再帰するメイン部分
#便利のため
STR=0
WAV=1
import copy; 
def getDiagramr(allNodes, unusedNodes, lines, unusedContainers):
 rets=[] #戻り値
 #print "func_getDiagramr called",unusedNodes,lines,unusedContainers
 if len(unusedNodes)==0:
  if len(unusedContainers)==0:
   #終了
   return [lines,]
  else:
   #コンテナが残っているのにノードを使い切った場合
   #非連結グラフになってしまう
   #print "disconnected graph!",lines
   return []

 #一本線引いて再帰。線を引きうる場所が２箇所以上ある場合は分岐。
 if allNodes[0]=="xt":
  #ありえない頂点の残り方
  print 'unexpected state : only "xt" node left'
 else:
  if isStart(unusedNodes[0]):
   #使われてない最初の点が線の始点に
   lineStart=unusedNodes[0]
   unusedNodes=unusedNodes[1:] #始点削除
   #終点候補を探る
   for elem in unusedNodes:
    if isEnd(elem): #終点なら
     #再帰
     newLines=copy.deepcopy(lines)
     #線追加
     newLines.append((lineStart, elem))
     #unusedNodesから終点削除
     newUnusedNodes=copy.deepcopy(unusedNodes)
     newUnusedNodes.remove(elem)
     #newUnusedContainers=copy.deepcopy(unusedContainers) #これ要らないかも
     rets+=getDiagramr(allNodes, newUnusedNodes, newLines, unusedContainers) #再帰
   if len(unusedContainers)!=0:
    #新しいコンテナを開ける
    #ノードリストでxtを最後にしておくことに注意
    newLines=copy.deepcopy(lines)    
    newLines.append( (lineStart,"xt"+str(unusedContainers[0])) )
    newUnusedNodes=copy.deepcopy(unusedNodes)
    newUnusedNodes=newUnusedNodes[:-1]+createBlockf(unusedContainers[0])+[newUnusedNodes[-1],]
    newUnusedContainers=copy.deepcopy(unusedContainers)
    newUnusedContainers=newUnusedContainers[1:]
    #print "open new container",unusedContainers[0]
    rets+=getDiagramr(allNodes, newUnusedNodes, newLines, newUnusedContainers) #再帰
  else:
   #使われてない最初の点が線の終点に
   lineEnd=unusedNodes[0]
   unusedNodes=unusedNodes[1:] #終点削除
   #終点候補を探る
   for elem in unusedNodes:
    if isStart(elem): #始点なら
     #再帰する
     newLines=copy.deepcopy(lines)
     #線追加
     newLines.append((elem, lineEnd))
     #unusedNodesから始点削除
     newUnusedNodes=copy.deepcopy(unusedNodes)
     newUnusedNodes.remove(elem)
     #newUnusedContainers=copy.deepcopy(unusedContainers) #これ要らないかも
     rets+=getDiagramr(allNodes, newUnusedNodes, newLines, unusedContainers) #再帰
   if len(unusedContainers)!=0:
    #新しいコンテナを開ける
    #ノードリストでxtを最後にしておくことに注意
    newLines=copy.deepcopy(lines)    
    newLines.append( ("xf"+str(unusedContainers[0]), lineEnd))
    newUnusedNodes=copy.deepcopy(unusedNodes)
    newUnusedNodes=newUnusedNodes[:-1]+createBlockt(unusedContainers[0])+[newUnusedNodes[-1],]
    newUnusedContainers=copy.deepcopy(unusedContainers)
    newUnusedContainers=newUnusedContainers[1:]
    #print "open new container",unusedContainers[0]
    rets+=getDiagramr(allNodes, newUnusedNodes, newLines, newUnusedContainers) #再帰
 #print "func_getDiagramr end",unusedNodes,lines,unusedContainers
 return rets
    
def getDiagram(size, browser=False, texOutPut=False,\
 fontDraw=True, arrowDraw=True, wavyLinePosAdj=True, saveDir=""):
 allNodes=[]
 allNodes.append("yf")
 for i in range(1,size):
  #ブロック追加
  allNodes+=createBlock(i)
 allNodes.append("xt")
 #未使用ノード集には順番が重要
 #一点も使われていないブロックはunusedCotainersに格納されている
 unusedNodes=["yf","xt"]
 #直線
 StrLines=[]
 #波線
 waveLines=[]
 lines=[]
 #使われていないコンテナ(xfN, xtN, xfdN, xtdNのブロックのリスト)
 unusedContainers=range(1,size+1)
 diagrams=getDiagramr(allNodes, unusedNodes, lines, unusedContainers)
 if texOutPut: #texの数式で出力モード
  filename="test"+str(size)+".tex"
  #print "outPut :",filename
  fileobj=file(filename, "w")
  fileobj.write( r"""\documentclass{jsarticle}
\begin{document}""")
  for lineAndLoops in diagrams:
   #print lineAndLoops
   texLines=""
   for aline in lineAndLoops:
    texLines+=toLatex(aline)+" "
   fileobj.write(r"\[")
   fileobj.write(texLines)
   fileobj.write("\\]\n")
   #print "mainline and loops :", decompose(allNodes, lines)
  fileobj.write("\\end{document}\n")
  return
 i=0
 for lineAndLoops in diagrams:
  i+=1
  print "line and loops",lineAndLoops
  decon=decompose(allNodes, lineAndLoops)
  #print decon
  rets=place(decon)
  #print rets
  if rets:
   drawGraphInSVG(rets[0],rets[1],rets[2], (saveDir,"test"+str(i), "svg"), browserView=browser, fontDraw=fontDraw , arrowDraw=arrowDraw, wavyLinePosAdj=wavyLinePosAdj)
  else:
   print "unimplemented",lineAndLoops

def getBigDiagram(size, vertical=True, browser=False,\
 fontDraw=True, arrowDraw=True, wavyLinePosAdj=True, saveDir=""):
 #<<ダイアグラム作成、ただし一つの巨大なsvgファイルに>>みたいなっ！
 #縦の長さは確定しているので、とりあえず横長のsvg画像を作成
 allNodes=[]
 allNodes.append("yf")
 for i in range(1,size):
  #ブロック追加
  allNodes+=createBlock(i)
 allNodes.append("xt")
 #未使用ノード集には順番が重要
 #一点も使われていないブロックはunusedCotainersに格納されている
 unusedNodes=["yf","xt"]
 #直線
 StrLines=[]
 #波線
 waveLines=[]
 lines=[]
 #使われていないコンテナ(xfN, xtN, xfdN, xtdNのブロックのリスト)
 unusedContainers=range(1,size+1)
# print r"""\documentclass{jsarticle}
#\begin{document}"""
 diagrams=getDiagramr(allNodes, unusedNodes, lines, unusedContainers)
 i=0
 #graphics=[] #placeの戻り値のリスト
 newObjects=[]
 #画像を順番にずらす
 if vertical:
  height=0
  widthMax=0
 else:
  height=0 #horizontal 複数行表示
  holizontalNum=5
  width=0
  widthMax=0
  nowHolNum=0
 for lineAndLoops in diagrams:
  i+=1
  print "line and loops",lineAndLoops
  decon=decompose(allNodes, lineAndLoops)
  #print decon
  agraph=place(decon)
  #def place :return (height+frameHeight, width+frameWidth, objects)
  #placeの戻り値はsvg画像に（ほぼ）一対一対応している
  if agraph[1] > widthMax:
   widthMax=agraph[1]
  else: #horizontal
   if nowHolNum==holizontalNum:
    nowHolNum=0
    height+=HEIGHT_DEF+FRAMEHEIGHT_DEF
    width=0
  for object in agraph[2]:
   #print "object=",object
   if vertical:
    object.translate( Pos(0,height) )
   else:
    object.translate( Pos(width,height) )
   #print "object'=",object
   newObjects.append(copy.copy(object) )
  if vertical:
   height+=agraph[0]
  else: #horizontal
   width+=agraph[1]
   if width > widthMax:
    widthMax=width
   nowHolNum+=1
 #print "newObjects =",newObjects
 if vertical:
  drawGraphInSVG(height, widthMax, newObjects, (saveDir,"testBig"+str(size), "svg"), browserView=browser, \
fontDraw=fontDraw , arrowDraw=arrowDraw, wavyLinePosAdj=wavyLinePosAdj)   
 else: #horizontal
  drawGraphInSVG(height+ALLHEIGHT_DEF, widthMax, newObjects, (saveDir,"testBig"+str(size), "svg"), \
browserView=browser , fontDraw=fontDraw  , arrowDraw=arrowDraw, wavyLinePosAdj=wavyLinePosAdj) 

def writeHtml(n):
  f=file("display.html", "w")
  astr=''
  astr="<h1>There are "+str(n)+" diagrams.</h1>"
  for i in range(1,n+1):
    astr += '<h2>diagram '+str(i)+'</h2>'
    astr += '<object data="test'+str(i)+'.svg" type="image/svg+xml">diagram'+str(i)+'</object><br>'
  f.write(astr)

if __name__=='__main__':
 import sys
 from optparse import OptionParser #コマンドライン解析の標準ライブラリ
 usage = """
Usage: %prog [options] arg\n\n 
Calculate and Draw all One-particle Feynman Diagrams of degree s (s is determined by option -s).
Outputs are SVG files(SVG is vector graphics format).

Term Nums of Feynman Diagrams:
degree 1 -      2 terms
degree 2 -     10 terms
degree 3 -     74 terms
degree 4 -    706 terms
degree 5 -   8162 terms
degree 6 - 110410 terms
-s(size option) more than 5 takes much time!!!

For questions , requests and bugs , report to elbreth<elb.phys@gmail.com>"""

 parser = OptionParser(usage)
 parser.add_option("-s" , "--size" , type="int", dest="size", \
default=1, help="size(degree) of diagram to calculate. default is 1")
 parser.add_option("-f" , "--folder", "--directory" , type="string", dest="saveDir", \
default="", help='specify directory to save files. for example, "-f test" will save files to "./test/"')
 parser.add_option("-d" , "--disp", action="store_true", dest="browser", \
default=False, help="redirect to browser.") 
 parser.add_option("-t" , "--tex", action="store_true", dest="texout", \
default=False, help="output in tex file (for development)") 
 parser.add_option("-b" , "--big" ,  action="store_true", dest="is_big", \
default=False, help="output is integrated into one big file")
 parser.add_option("--bh" , "--bighorizontal", action="store_true", dest="is_big_vertical", \
default=False) 
 parser.add_option("-p" , "--psyco", action="store_true", dest="usepsyco", \
 help="use psyco to boost program speed") 
 parser.add_option("--np" , "--nopsyco", action="store_false", dest="usepsyco", \
default=False, help="don't use psyco. for enviroment without psyco (default)") 
 parser.add_option("--nf" , "--noFont", action="store_false", dest="usefont", \
default=True, help="don't draw font") 
 parser.add_option("--na" , "--noArrow", action="store_false", dest="usearrow", \
default=True, help="don't draw arrow") 
 parser.add_option("--nwa" , "--noWavLinePosAdj", action="store_false", dest="usewlpa", \
default=True, help="don't adjust position of wavy line  (for development)") 
 parser.add_option("--nl" , "--noLimit", "--noSizeLimit", action="store_false", dest="isLimit", \
default=True, help="unlimit the size limit") 

 
 (options, args) = parser.parse_args()
 size=options.size
 if options.isLimit:
  if options.browser:
   if size>2:
    print "size too big (you will open more than 50 windows!!).\
\nrun with smaller size, or use option --nl to lift this limit." 
    sys.exit()
  else: 
   if size>4:
    print "size too big (it may take too much time).\
\nrun with smaller size, or use option --nl to lift this limit."
    sys.exit()
 if options.usepsyco:
  print "using psyco"
  import psyco
  psyco.full()
 if options.is_big:
  getBigDiagram( size, browser=options.browser, fontDraw=options.usefont, \
arrowDraw=options.usearrow, wavyLinePosAdj=options.usewlpa, saveDir=saveDir)
 elif options.is_big_vertical:
  getBigDiagram( size, vertical=False, browser=options.browser , fontDraw=options.usefont, \
arrowDraw=options.usearrow, wavyLinePosAdj=options.usewlpa, saveDir=options.saveDir)
 else:
  getDiagram( size, browser=options.browser ,texOutPut=options.texout , fontDraw=options.usefont, \
arrowDraw=options.usearrow, wavyLinePosAdj=options.usewlpa, saveDir=options.saveDir)

termNum={1:2, 2:10, 3:74, 4:706, 5:8162, 6:110410}
writeHtml(termNum[size])
