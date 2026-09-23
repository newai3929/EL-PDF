import sys
from pathlib import Path
from PySide6.QtCore import Qt, QRectF, QSize, Signal
from PySide6.QtGui import QAction, QIcon, QImage, QPainter, QPixmap, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QLabel,
    QMainWindow,
    QScrollArea,
    QSlider,
    QSpinBox,
    QStatusBar,
    QToolBar,
    QVBoxLayout,
    QWidget,
)
import pymupdf as fitz
class PDFPageWidget(QLabel):
    """单页 PDF 渲染组件"""
    def __init__(self, page: fitz.Page, dpi: int = 150, parent=None):
        super().__init__(parent)
        self.page = page
        self.dpi = dpi
        self.setAlignment(Qt.AlignCenter)
        self.setScaledContents(False)
        self.render()
    def render(self):
        zoom = self.dpi / 72.0
        mat = fitz.Matrix(zoom, zoom)
        pix = self.page.get_pixmap(matrix=mat, alpha=False)
        img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888)
        self.setPixmap(QPixmap.fromImage(img))
        self.setFixedSize(pix.width, pix.height)
    def set_dpi(self, dpi: int):
        self.dpi = dpi
        self.render()
class PDFViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("EL-PDF Viewer")
        self.resize(1024, 768)
        self.doc: fitz.Document | None = None
        self.page_widgets: list[PDFPageWidget] = []
        self.current_dpi = 150
        self._setup_ui()
        self._setup_shortcuts()
    def _setup_ui(self):
        # 中央滚动区域
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.container = QWidget()
        self.layout = QVBoxLayout(self.container)
        self.layout.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        self.layout.setSpacing(8)
        self.layout.setContentsMargins(16, 16, 16, 16)
        self.scroll_area.setWidget(self.container)
        self.setCentralWidget(self.scroll_area)
        # 工具栏
        toolbar = QToolBar("主工具栏")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        # 打开文件
        act_open = QAction("打开", self)
        act_open.setShortcut(QKeySequence.StandardKey.Open)
        act_open.triggered.connect(self.open_file)
        toolbar.addAction(act_open)
        toolbar.addSeparator()
        # 缩放控制
        toolbar.addWidget(QLabel("缩放:"))
        self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setRange(50, 400)
        self.zoom_slider.setValue(self.current_dpi)
        self.zoom_slider.setFixedWidth(150)
        self.zoom_slider.valueChanged.connect(self.on_zoom_changed)
        toolbar.addWidget(self.zoom_slider)
        self.zoom_spin = QSpinBox()
        self.zoom_spin.setRange(50, 400)
        self.zoom_spin.setValue(self.current_dpi)
        self.zoom_spin.setSuffix("%")
        self.zoom_spin.valueChanged.connect(self.zoom_slider.setValue)
        toolbar.addWidget(self.zoom_spin)
        toolbar.addSeparator()
        # 页码跳转
        toolbar.addWidget(QLabel("页码:"))
        self.page_spin = QSpinBox()
        self.page_spin.setRange(1, 1)
        self.page_spin.valueChanged.connect(self.go_to_page)
        toolbar.addWidget(self.page_spin)
        self.page_label = QLabel("/ 0")
        toolbar.addWidget(self.page_label)
        # 状态栏
        self.status = QStatusBar()
        self.setStatusBar(self.status)
    def _setup_shortcuts(self):
        # 滚动快捷键
        QAction("向上", self, shortcut=QKeySequence(Qt.Key_Up), triggered=lambda: self.scroll_area.verticalScrollBar().triggerAction(self.scroll_area.verticalScrollBar().SliderSingleStepSub))
        QAction("向下", self, shortcut=QKeySequence(Qt.Key_Down), triggered=lambda: self.scroll_area.verticalScrollBar().triggerAction(self.scroll_area.verticalScrollBar().SliderSingleStepAdd))
        QAction("翻页上", self, shortcut=QKeySequence(Qt.Key_PageUp), triggered=self.prev_page)
        QAction("翻页下", self, shortcut=QKeySequence(Qt.Key_PageDown), triggered=self.next_page)
    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "打开 PDF", "", "PDF 文件 (*.pdf)")
        if not path:
            return
        self.load_document(path)
    def load_document(self, path: str):
        try:
            if self.doc:
                self.doc.close()
        except Exception:
            pass
        self.doc = fitz.open(path)
        self.setWindowTitle(f"EL-PDF Viewer - {Path(path).name}")
        # 清空旧页面
        for w in self.page_widgets:
            w.deleteLater()
        self.page_widgets.clear()
        self.layout.takeAt(0)  # 清空布局（简单粗暴）
        # 重建页面
        for i, page in enumerate(self.doc):
            widget = PDFPageWidget(page, self.current_dpi)
            self.page_widgets.append(widget)
            self.layout.addWidget(widget)
        self.page_spin.setRange(1, len(self.doc))
        self.page_spin.setValue(1)
        self.page_label.setText(f"/ {len(self.doc)}")
        self.status.showMessage(f"已加载: {len(self.doc)} 页", 3000)
    def on_zoom_changed(self, dpi: int):
        self.current_dpi = dpi
        self.zoom_spin.blockSignals(True)
        self.zoom_spin.setValue(dpi)
        self.zoom_spin.blockSignals(False)
        for w in self.page_widgets:
            w.set_dpi(dpi)
    def go_to_page(self, page_num: int):
        if not self.page_widgets:
            return
        widget = self.page_widgets[page_num - 1]
        self.scroll_area.ensureWidgetVisible(widget, 0, 50)
    def prev_page(self):
        if self.page_spin.value() > 1:
            self.page_spin.setValue(self.page_spin.value() - 1)
    def next_page(self):
        if self.page_spin.value() < self.page_spin.maximum():
            self.page_spin.setValue(self.page_spin.value() + 1)
    def closeEvent(self, event):
        if self.doc:
            self.doc.close()
        super().closeEvent(event)
def main():
    app = QApplication(sys.argv)
    app.setApplicationName("EL-PDF Viewer")
    viewer = PDFViewer()
    viewer.show()
    sys.exit(app.exec())
if __name__ == "__main__":
    main()