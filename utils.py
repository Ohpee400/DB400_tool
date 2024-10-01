import os
import sys
from PySide6.QtCore import QCoreApplication

# 確保程序完全退出
def force_quit():
    QCoreApplication.quit()
    sys.exit(0)

jt400_path = "/Users/clark/Desktop/DDSC/Clark文件/13-JavaCode/jt400.jar"
if not os.path.exists(jt400_path):
    print(f"錯誤：jt400.jar 文件未找到：{jt400_path}")
    sys.exit(1)

java_home = "/Library/Java/JavaVirtualMachines/jdk-22.jdk/Contents/Home"
os.environ["JAVA_HOME"] = java_home
os.environ["PATH"] = f"{java_home}/bin:{os.environ.get('PATH', '')}"
os.environ["CLASSPATH"] = f"{jt400_path}:{os.environ.get('CLASSPATH', '')}"