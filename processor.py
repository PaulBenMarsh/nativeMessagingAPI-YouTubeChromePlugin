
from nativemessaging import MessageProcessor

from PyQt5.QtCore import QObject, pyqtSignal

from pytube import YouTube


class ProcessorSignals(QObject):

    downloadBegin = pyqtSignal(YouTube)

    def __init__(self):

        super(ProcessorSignals, self).__init__()


class DownloadProcessor(MessageProcessor):

    def __init__(self):

        super(DownloadProcessor, self).__init__()

        self.signals = ProcessorSignals()

        self.download_directory = "C:/users/studio/desktop/pytube videos"

    def process(self, message):

        import re

        video_url = message.data["text"]

        pattern = "https://www\\.youtube\\.com/watch\\?v=[^&]+"
        match = re.match(pattern, video_url)

        if match is None:
            return

        video_url = match.group()

        youtube = YouTube(url=video_url)

        if youtube is None:
            return

        stream_query = youtube.streams.filter(progressive=True, file_extension="mp4")
        stream = stream_query.order_by("resolution").desc().first()

        self.signals.downloadBegin.emit(youtube)

        stream.download(self.download_directory)
