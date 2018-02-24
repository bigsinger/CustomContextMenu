### star -- Python常用功能库
- 在构建流程的时候无需重新实现某函数的功能，直接信手拈来，快速解决问题！仅限Python27！

### 使用方法
- 1、在Python安装目录的lib文件夹下（如D:\Python27\Lib），直接gitclone地址：https://github.com/bigsinger/star.git
- 2、在你的任何Python工程中import star后，即可使用。
```
import star
from star.APK import APK
from star.ZIP import ZIP
from star.AXML import AXML
```

### 说明文档
- 见[《说明文档》](https://github.com/pythonstar/star/wiki/%E8%AF%B4%E6%98%8E%E6%96%87%E6%A1%A3)

### 编写规则
- 尽量函数式编程，如无必要不用类。
- star下的函数名一律全小写，其他类与类函数不要求。
- 不考虑导入库的冗余性，旨在快速使用并解决问题。
