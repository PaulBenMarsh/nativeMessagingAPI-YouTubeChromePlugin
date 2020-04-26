
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QMainWindow, QListWidgetItem
from pytube import YouTube


class MainWindow(QMainWindow):

    def __init__(self):

        from PyQt5 import uic
        from PyQt5.QtCore import Qt
        from PyQt5.QtWidgets import QProgressBar, QWidget, QHBoxLayout

        from processor import DownloadProcessor
        from nativemessaging import NativeMessagingHost

        super(MainWindow, self).__init__()

        ui_file_path = "mainwindow.ui"
        uic.loadUi(ui_file_path, self)

        self.list_widget.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.list_widget.setTextElideMode(Qt.ElideRight)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p%")
        self.progress_bar.setAlignment(Qt.AlignCenter)

        layout = QHBoxLayout()
        layout.addWidget(self.progress_bar)

        widget = QWidget()
        widget.setLayout(layout)

        self.status_bar.addPermanentWidget(widget, 2)
        self.status_bar.setStyleSheet("QStatusBar::item {border: none;}")

        self.setWindowFlag(Qt.MSWindowsFixedSizeDialogHint)
        self.status_bar.setSizeGripEnabled(False)

        self.message_processor = DownloadProcessor()
        self.message_processor.signals.downloadBegin.connect(self.on_download_begin)
        self.native_messaging_host = NativeMessagingHost(self.message_processor)

    @pyqtSlot(YouTube)
    def on_download_begin(self, youtube):

        thumbnail_url = youtube.thumbnail_url
        title = youtube.title

        item = VideoItem()
        item.setText(title)
        item.setThumbnailFromUrl(thumbnail_url)
        item.setStatus(VideoItem.Status.Downloading)

        youtube.register_on_progress_callback(self.on_download_progress)
        youtube.register_on_complete_callback(item.on_download_complete)

    def on_download_progress(self, stream, chunk, file_handle, bytes_remaining):
        value = (float(bytes_remaining) / float(stream.file_size)) * 100.0
        self.progress_bar.setValue(value)

    def exec(self):
        self.native_messaging_host.exec()


class VideoItem(QListWidgetItem):

    from enum import Enum

    class Status(Enum):
        Pending = "#adb9c5"
        Downloading = "#abce9e"
        Completed = "#66b266"

    def __init__(self):
        from PyQt5.QtNetwork import QNetworkAccessManager

        super(VideoItem, self).__init__()

        self.network_manager = QNetworkAccessManager()

        self.setStatus(VideoItem.Status.Pending)

    def setStatus(self, status):

        from PyQt5.Qt import QColor

        self.status = status
        self.setBackground(QColor(self.status.value))

    def setThumbnailFromUrl(self, thumbnail_url):

        from PyQt5.QtNetwork import QNetworkRequest, QNetworkReply
        from PyQt5.QtCore import Qt, QUrl
        from PyQt5.Qt import QPixmap, QSize

        reply = self.network_manager.get(QNetworkRequest(QUrl(thumbnail_url)))

        if reply.error() == QNetworkReply.NoError:
            image_bytes = reply.readAll()
            pixmap = QPixmap()
            pixmap.loadFromData(image_bytes)
        else:
            pixmap = QPixmap("missing.jpg")

        pixmap = pixmap.scaled(QSize(120, 90), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        self.setData(Qt.DecorationRole, pixmap)

    @pyqtSlot()
    def on_download_complete(self, stream, file_handle):
        self.setStatus(VideoItem.Status.Completed)
