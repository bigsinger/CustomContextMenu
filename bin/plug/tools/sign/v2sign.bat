set dir=%~dp0
set apk=%~1

cd /d %dir%

java -jar apksigner.jar -notupdate -appname 测试 -keystore debug.keystore -alias androiddebugkey -pswd android -aliaspswd android -v1 false -v2 true "%apk%"

::参数说明：
::-appname：待签名的应用程序名，可选，但建议不同的APP填上对应的app名（可以为中文），有助于【加速】 
::-keystore：后跟.keystore签名文件
::-alias：后跟签名别名
::-pswd：后跟对应签名的密码，例如这里是：android 可选，如果不填，则签名的时候需要手动输入
::最后跟待签名的apk路径或者目录路径，如果跟的是目录则是批量签名。

