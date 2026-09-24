import sys  # 导入系统模块，用于访问命令行参数和退出程序
from pathlib import Path  # 导入路径处理工具，用于获取文件名等操作
from PySide6.QtCore import Qt, QRectF, QSize, Signal  # 导入Qt核心模块：对齐标志、矩形、尺寸、信号机制
from PySide6.QtGui import QAction, QIcon, QImage, QPainter, QPixmap, QKeySequence, QFont, QColor, QFontMetrics  # 导入Qt GUI模块：动作、图标、图像、绘图、像素图、快捷键、字体、颜色、字体度量
from PySide6.QtWidgets import (  # 导入Qt控件模块的开始
    QApplication,  # 应用程序对象，Qt应用的入口
    QFileDialog,  # 文件选择对话框
    QLabel,  # 标签控件，用于显示文本或图片
    QMainWindow,  # 主窗口类，提供工具栏、状态栏等框架
    QScrollArea,  # 滚动区域控件，支持内容滚动
    QSlider,  # 滑块控件，用于数值调节
    QSpinBox,  # 数字输入框，带上下箭头按钮
    QSizePolicy,  # 尺寸策略，控制控件的伸缩行为
    QStatusBar,  # 状态栏控件，显示提示信息
    QToolBar,  # 工具栏控件，放置常用按钮
    QVBoxLayout,  # 垂直布局管理器，控件从上到下排列
    QWidget,  # 所有控件的基类
)
import pymupdf as fitz  # 导入PyMuPDF库（别名fitz），用于PDF解析和渲染


class WelcomeWidget(QWidget):  # 定义欢迎页面组件类，继承自QWidget
    def __init__(self, parent=None):  # 构造函数：接收父控件（可选）
        super().__init__(parent)  # 调用父类QWidget的构造函数，传入父控件
        self.setAttribute(Qt.WA_StyledBackground, True)  # 启用样式表背景绘制（否则setStyleSheet背景不生效）
        self.setStyleSheet("background-color: white;")  # 设置背景颜色为白色
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  # 设置尺寸策略为水平和垂直方向都可扩展（填满可用空间）

    def paintEvent(self, event):  # 绘制事件回调：每次需要重绘时自动调用
        painter = QPainter(self)  # 创建QPainter绘图对象，绑定到当前控件
        painter.setRenderHint(QPainter.Antialiasing)  # 开启抗锯齿，使图形边缘更平滑
        painter.setRenderHint(QPainter.TextAntialiasing)  # 开启文字抗锯齿，使文字边缘更平滑

        w = self.width()  # 获取控件当前宽度（像素）
        h = self.height()  # 获取控件当前高度（像素）

        title_y = int(h * 0.30)  # 大标题的Y坐标：距顶部30%高度处（作为文字基线位置）
        max_title_font = min(w // 6, h // 4)  # 大标题字号：取宽度的1/6和高度的1/4中较小者，保证窗口缩放时自适应且不溢出
        title_font = QFont("Microsoft YaHei", max_title_font, QFont.Bold)  # 创建大标题字体：微软雅黑、自适应字号、粗体
        title_font.setLetterSpacing(QFont.AbsoluteSpacing, 8)  # 设置字间距为8像素（固定值），让标题更舒展
        painter.setFont(title_font)  # 将大标题字体设为当前绘图字体
        title_color = QColor(0, 0, 0, int(255 * 0.40))  # 创建颜色：黑色（RGB 0,0,0），Alpha=102即40%不透明度
        painter.setPen(title_color)  # 设置画笔颜色为40%透明度的黑色

        title_text = "EL-PDF"  # 大标题文本内容
        fm = QFontMetrics(title_font)  # 获取大标题字体的度量对象（用于测量文字宽度）
        title_x = (w - fm.horizontalAdvance(title_text)) // 2  # 计算X坐标：用（总宽-文字宽）/2 实现水平居中
        painter.drawText(title_x, title_y, title_text)  # 在计算好的位置绘制大标题文字

        subtitle_y = int(h * 0.50)  # 副标题的Y坐标：距顶部50%高度处
        max_sub_font = min(w // 24, h // 18)  # 副标题字号：取宽度的1/24和高度的1/18中较小者，明显小于大标题
        sub_font = QFont("Microsoft YaHei", max_sub_font, QFont.Normal)  # 创建副标题字体：微软雅黑、自适应字号、常规字重
        painter.setFont(sub_font)  # 将副标题字体设为当前绘图字体
        sub_color = QColor(0, 0, 0, 255)  # 创建颜色：黑色，Alpha=255即完全不透明（100%）
        painter.setPen(sub_color)  # 设置画笔颜色为不透明黑色

        sub_text = "让我们现在开始，打开，编辑，或是查看"  # 副标题文本内容
        fm_sub = QFontMetrics(sub_font)  # 获取副标题字体的度量对象（用于测量文字宽度）
        sub_x = (w - fm_sub.horizontalAdvance(sub_text)) // 2  # 计算X坐标：用（总宽-文字宽）/2 实现水平居中
        painter.drawText(sub_x, subtitle_y, sub_text)  # 在计算好的位置绘制副标题文字

    def resizeEvent(self, event):  # 控件大小变化事件回调
        self.update()  # 标记控件需要重绘（触发paintEvent，使文字按新尺寸重新计算位置和字号）
        super().resizeEvent(event)  # 调用父类的resizeEvent，完成默认处理


class PDFPageWidget(QLabel):  # 定义PDF页面组件类，继承自QLabel（标签控件）
    def __init__(self, page: fitz.Page, dpi: int = 150, parent=None):  # 构造函数：接收PDF页面对象、DPI（默认150）、父控件
        super().__init__(parent)  # 调用父类QLabel的构造函数，传入父控件
        self.page = page  # 保存传入的PDF页面对象引用
        self.dpi = dpi  # 保存当前渲染分辨率（每英寸像素数）
        self.setAlignment(Qt.AlignCenter)  # 设置标签内容居中对齐
        self.setScaledContents(False)  # 关闭自动缩放像素图，由代码手动控制尺寸
        self.render()  # 首次渲染，绘制PDF页面到标签上

    def render(self):  # 渲染方法：将PDF页面绘制为位图并显示
        zoom = self.dpi / 72.0  # 计算缩放比例：PDF标准分辨率为72DPI，除以72得到缩放倍数
        mat = fitz.Matrix(zoom, zoom)  # 构建2D变换矩阵，水平和垂直方向按zoom倍缩放
        pix = self.page.get_pixmap(matrix=mat, alpha=False)  # 将PDF页面按矩阵渲染为像素图（不含透明通道）
        img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888)  # 将PyMuPDF的原始像素数据包装为Qt的QImage对象（RGB888格式）
        self.setPixmap(QPixmap.fromImage(img))  # 将QImage转换为QPixmap并设置到标签上显示
        self.setFixedSize(pix.width, pix.height)  # 将标签尺寸固定为渲染出的图片尺寸

    def set_dpi(self, dpi: int):  # 修改渲染分辨率的方法
        self.dpi = dpi  # 更新DPI值
        self.render()  # 用新的DPI重新渲染当前页面


class PDFViewer(QMainWindow):  # 定义PDF查看器主窗口类，继承自QMainWindow（提供工具栏/状态栏框架）
    def __init__(self):  # 构造函数
        super().__init__()  # 调用父类QMainWindow的构造函数
        self.setWindowTitle("EL-PDF Viewer")  # 设置窗口标题
        self.resize(1024, 768)  # 设置窗口初始尺寸为1024x768像素
        self.doc: fitz.Document | None = None  # 初始化PDF文档对象为None（类型注解：文档或None）
        self.page_widgets: list[PDFPageWidget] = []  # 初始化页面组件列表（存储所有已渲染的页面控件）
        self.current_dpi = 150  # 初始化当前缩放分辨率为150 DPI
        self._setup_ui()  # 调用UI初始化方法，构建界面控件
        self._setup_shortcuts()  # 调用快捷键初始化方法，绑定键盘操作
        self._show_welcome()  # 启动时显示欢迎页

    def _setup_ui(self):  # UI初始化方法：创建并布局所有界面控件
        self.scroll_area = QScrollArea()  # 创建滚动区域，作为中央控件的容器
        self.scroll_area.setWidgetResizable(True)  # 允许内部控件随滚动区域自动调整大小
        self.scroll_area.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)  # 设置内部控件水平和垂直居中
        self.container = QWidget()  # 创建容器控件，作为所有PDF页面的父容器
        self.layout = QVBoxLayout(self.container)  # 在容器上创建垂直布局管理器（页面从上到下排列）
        self.layout.setAlignment(Qt.AlignHCenter | Qt.AlignTop)  # 设置布局中的控件水平居中、顶部对齐
        self.layout.setSpacing(8)  # 设置页面之间的间距为8像素
        self.layout.setContentsMargins(16, 16, 16, 16)  # 设置布局四周边距各为16像素
        self.scroll_area.setWidget(self.container)  # 将容器设置为滚动区域的可滚动内容
        self.setCentralWidget(self.scroll_area)  # 将滚动区域设置为主窗口的中央控件

        toolbar = QToolBar("主工具栏")  # 创建工具栏对象
        toolbar.setMovable(False)  # 禁止用户拖动工具栏（固定位置）
        self.addToolBar(toolbar)  # 将工具栏添加到主窗口顶部

        act_open = QAction("打开", self)  # 创建"打开"动作，父对象为主窗口
        act_open.setShortcut(QKeySequence.StandardKey.Open)  # 绑定系统标准快捷键 Ctrl+O
        act_open.triggered.connect(self.open_file)  # 点击动作时触发open_file方法
        toolbar.addAction(act_open)  # 将"打开"按钮添加到工具栏

        act_close = QAction("关闭", self)  # 创建"关闭"动作，父对象为主窗口
        act_close.setShortcut(QKeySequence.StandardKey.Close)  # 绑定系统标准快捷键 Ctrl+W
        act_close.triggered.connect(self.close_document)  # 点击动作时触发close_document方法（关闭文档返回欢迎页）
        toolbar.addAction(act_close)  # 将"关闭"按钮添加到工具栏

        toolbar.addSeparator()  # 在工具栏中添加一条竖直分隔线

        toolbar.addWidget(QLabel("缩放:"))  # 在工具栏添加"缩放:"文本标签
        self.zoom_slider = QSlider(Qt.Horizontal)  # 创建水平方向的缩放滑块
        self.zoom_slider.setRange(50, 400)  # 设置滑块范围为50%到400%
        self.zoom_slider.setValue(self.current_dpi)  # 设置滑块初始值为当前DPI（150）
        self.zoom_slider.setFixedWidth(150)  # 固定滑块宽度为150像素
        self.zoom_slider.valueChanged.connect(self.on_zoom_changed)  # 滑块值变化时触发on_zoom_changed方法
        toolbar.addWidget(self.zoom_slider)  # 将滑块添加到工具栏

        self.zoom_spin = QSpinBox()  # 创建数字输入框，用于精确输入缩放值
        self.zoom_spin.setRange(50, 400)  # 设置输入框范围为50到400
        self.zoom_spin.setValue(self.current_dpi)  # 设置输入框初始值为当前DPI
        self.zoom_spin.setSuffix("%")  # 设置输入框数值后缀为百分号
        self.zoom_spin.valueChanged.connect(self.zoom_slider.setValue)  # 输入框值变化时同步更新滑块（双向联动）
        toolbar.addWidget(self.zoom_spin)  # 将输入框添加到工具栏

        toolbar.addSeparator()  # 添加分隔线

        toolbar.addWidget(QLabel("页码:"))  # 在工具栏添加"页码:"文本标签
        self.page_spin = QSpinBox()  # 创建页码数字输入框
        self.page_spin.setRange(1, 1)  # 初始范围为1到1（加载文档后会更新）
        self.page_spin.valueChanged.connect(self.go_to_page)  # 页码变化时触发跳转方法
        toolbar.addWidget(self.page_spin)  # 将页码输入框添加到工具栏
        self.page_label = QLabel("/ 0")  # 创建显示总页数的标签，初始为"/ 0"
        toolbar.addWidget(self.page_label)  # 将总页数标签添加到工具栏

        self.status = QStatusBar()  # 创建状态栏对象
        self.setStatusBar(self.status)  # 将状态栏设置到主窗口底部

    def _setup_shortcuts(self):  # 快捷键初始化方法：绑定键盘导航操作
        QAction("向上", self, shortcut=QKeySequence(Qt.Key_Up), triggered=lambda: self.scroll_area.verticalScrollBar().triggerAction(self.scroll_area.verticalScrollBar().SliderSingleStepSub))  # 绑定↑键：垂直滚动条向上滚动一步
        QAction("向下", self, shortcut=QKeySequence(Qt.Key_Down), triggered=lambda: self.scroll_area.verticalScrollBar().triggerAction(self.scroll_area.verticalScrollBar().SliderSingleStepAdd))  # 绑定↓键：垂直滚动条向下滚动一步
        QAction("翻页上", self, shortcut=QKeySequence(Qt.Key_PageUp), triggered=self.prev_page)  # 绑定PgUp键：跳转到上一页
        QAction("翻页下", self, shortcut=QKeySequence(Qt.Key_PageDown), triggered=self.next_page)  # 绑定PgDn键：跳转到下一页

    def _show_welcome(self):  # 显示欢迎页面的方法：清空布局后添加欢迎页组件
        if not hasattr(self, 'welcome_widget'):  # 如果欢迎页组件尚未创建（首次调用）
            self.welcome_widget = WelcomeWidget()  # 创建欢迎页组件实例
        for w in self.page_widgets:  # 遍历所有已有的PDF页面组件
            w.deleteLater()  # 标记为待删除（Qt事件循环中安全销毁）
        self.page_widgets.clear()  # 清空页面组件列表
        while self.layout.count():  # 循环移除布局中所有剩余控件（直到布局为空）
            item = self.layout.takeAt(0)  # 从布局中移除第一个项
            if item.widget():  # 如果该项是控件
                item.widget().deleteLater()  # 标记该控件为待删除
        self.layout.addWidget(self.welcome_widget, 1)  # 将欢迎页添加到布局，stretch=1使其占满剩余空间居中显示
        self.page_spin.setRange(1, 1)  # 页码范围重置为1到1（无文档）
        self.page_spin.setValue(1)  # 页码重置为1
        self.page_label.setText("/ 0")  # 总页数标签重置为"/ 0"

    def _hide_welcome(self):  # 隐藏欢迎页面的方法：从布局中移除欢迎页
        if hasattr(self, 'welcome_widget') and self.welcome_widget:  # 如果欢迎页组件存在且未被销毁
            self.layout.removeWidget(self.welcome_widget)  # 从布局中移除欢迎页组件
            self.welcome_widget.hide()  # 隐藏欢迎页组件
            self.welcome_widget = None  # 将引用置为None（下次需要时会重新创建）

    def close_document(self):  # 关闭当前文档的方法：返回欢迎页
        if self.doc:  # 如果有打开的PDF文档
            self.doc.close()  # 关闭文档，释放文件句柄和内存
            self.doc = None  # 将文档引用置为None
        self._show_welcome()  # 显示欢迎页
        self.status.showMessage("已关闭文档", 2000)  # 在状态栏显示提示信息，2秒后自动消失

    def open_file(self):  # 打开文件方法：弹出文件选择对话框
        path, _ = QFileDialog.getOpenFileName(self, "打开 PDF", "", "PDF 文件 (*.pdf)")  # 弹出文件对话框，只显示PDF文件，返回选中的文件路径
        if not path:  # 如果用户取消选择（路径为空）
            return  # 直接返回，不做任何处理
        self.load_document(path)  # 否则调用load_document加载所选PDF

    def load_document(self, path: str):  # 加载PDF文档方法：接收文件路径
        try:  # 尝试执行以下代码（异常安全）
            if self.doc:  # 如果已有打开的文档
                self.doc.close()  # 关闭旧文档，释放文件句柄
        except Exception:  # 关闭旧文档时出现任何异常
            pass  # 忽略异常，继续执行
        self._hide_welcome()  # 隐藏欢迎页（加载文档时不显示欢迎页）
        self.doc = fitz.open(path)  # 打开新的PDF文档
        self.setWindowTitle(f"EL-PDF Viewer - {Path(path).name}")  # 更新窗口标题，显示当前打开的文件名
        for w in self.page_widgets:  # 遍历所有旧的页面组件
            w.deleteLater()  # 标记为待删除（Qt事件循环中安全销毁）
        self.page_widgets.clear()  # 清空页面组件列表
        self.layout.takeAt(0)  # 清空布局中的第一个项（移除残留控件）
        for i, page in enumerate(self.doc):  # 遍历PDF文档中的每一页（带索引）
            widget = PDFPageWidget(page, self.current_dpi)  # 为每页创建渲染组件
            self.page_widgets.append(widget)  # 将组件加入列表
            self.layout.addWidget(widget)  # 将组件加入垂直布局（页面依次排列）
        self.page_spin.setRange(1, len(self.doc))  # 更新页码输入框范围为1到总页数
        self.page_spin.setValue(1)  # 将页码重置为第1页
        self.page_label.setText(f"/ {len(self.doc)}")  # 更新总页数标签为实际页数
        self.status.showMessage(f"已加载: {len(self.doc)} 页", 3000)  # 在状态栏显示加载信息，3秒后自动消失

    def on_zoom_changed(self, dpi: int):  # 缩放变化回调方法
        self.current_dpi = dpi  # 更新当前DPI值
        self.zoom_spin.blockSignals(True)  # 暂时阻断输入框的信号（防止递归触发）
        self.zoom_spin.setValue(dpi)  # 同步输入框的数值
        self.zoom_spin.blockSignals(False)  # 恢复输入框的信号发送
        for w in self.page_widgets:  # 遍历所有页面组件
            w.set_dpi(dpi)  # 用新的DPI重新渲染每个页面

    def go_to_page(self, page_num: int):  # 跳转到指定页码的方法
        if not self.page_widgets:  # 如果没有页面组件（文档未加载）
            return  # 直接返回
        widget = self.page_widgets[page_num - 1]  # 获取目标页码对应的组件（页码从1开始，列表从0开始）
        self.scroll_area.ensureWidgetVisible(widget, 0, 50)  # 滚动使目标页面可见（垂直边距50像素）

    def prev_page(self):  # 跳转到上一页的方法
        if self.page_spin.value() > 1:  # 如果当前页码大于1（还有上一页）
            self.page_spin.setValue(self.page_spin.value() - 1)  # 页码减1，触发go_to_page跳转

    def next_page(self):  # 跳转到下一页的方法
        if self.page_spin.value() < self.page_spin.maximum():  # 如果当前页码小于最大页码（还有下一页）
            self.page_spin.setValue(self.page_spin.value() + 1)  # 页码加1，触发go_to_page跳转

    def closeEvent(self, event):  # 窗口关闭事件回调
        if self.doc:  # 如果有打开的PDF文档
            self.doc.close()  # 关闭文档，释放文件句柄和内存
        super().closeEvent(event)  # 调用父类的closeEvent，完成默认关闭流程


def main():  # 程序主入口函数
    app = QApplication(sys.argv)  # 创建Qt应用程序对象，传入命令行参数
    app.setApplicationName("EL-PDF Viewer")  # 设置应用程序名称（显示在任务栏等）
    viewer = PDFViewer()  # 创建PDF查看器主窗口实例
    viewer.show()  # 显示主窗口
    sys.exit(app.exec())  # 进入Qt事件循环，程序退出时返回退出码


if __name__ == "__main__":  # 判断是否直接运行此脚本（而非被导入）
    main()  # 调用主函数启动程序