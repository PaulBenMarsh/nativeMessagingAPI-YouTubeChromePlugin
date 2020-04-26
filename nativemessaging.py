
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QThread
from abc import ABC, abstractmethod


class Message:

        def __init__(self):
            self.data = {}

        def from_string(self, string):

            import json

            self.data = json.loads(string)

        def from_dict(self, data):
            self.data = data


class MessageReceivingThread(QThread):

        terminated = pyqtSignal()
        messageReceived = pyqtSignal(Message)

        def __init__(self):

            super(MessageReceivingThread, self).__init__()

        def __del__(self):
            self.wait()

        def run(self):

            import sys
            import struct

            while True:
                message_length_bytes = sys.stdin.buffer.read(4)
                if len(message_length_bytes) == 0:
                    break
                message = Message()
                message_length = struct.unpack("i", message_length_bytes)[0]
                message_string = sys.stdin.buffer.read(message_length).decode("utf-8")
                message.from_string(message_string)

                self.messageReceived.emit(message)
            self.terminated.emit()


class QueuePollThread(QThread):

    def __init__(self, queue, message_processor, terminate_event):

        super(QueuePollThread, self).__init__()

        self.queue = queue
        self.message_processor = message_processor

        self.is_running = True

        terminate_event.connect(self.on_partner_terminate)

    def __del__(self):
        self.wait()

    @pyqtSlot()
    def on_partner_terminate(self):
        self.is_running = False

    def run(self):

        import time

        while self.is_running:
            while not self.queue.empty():
                message = self.queue.get_nowait()
                self.message_processor.process(message)
            time.sleep(0.1)


class MessageProcessor(ABC):

        def __init__(self):

            super(MessageProcessor, self).__init__()

        @abstractmethod
        def process(self, message):
            raise NotImplementedError()


class NativeMessagingHost(QObject):

    def __init__(self, message_processor):

        import sys
        import os
        import msvcrt

        from queue import Queue

        super(NativeMessagingHost, self).__init__()

        msvcrt.setmode(sys.stdin.buffer.fileno(), os.O_BINARY)
        msvcrt.setmode(sys.stdout.buffer.fileno(), os.O_BINARY)

        self.message_processor = message_processor

        self.queue = Queue()

        self.message_receiving_thread = MessageReceivingThread()
        self.message_receiving_thread.messageReceived.connect(self.on_message_received)
        # self.message_receiving_thread.terminated.connect(self.on_thread_terminated)

        terminate_event = self.message_receiving_thread.terminated
        self.queue_poll_thread = QueuePollThread(
            self.queue,
            self.message_processor,
            terminate_event
        )

    @pyqtSlot(Message)
    def on_message_received(self, message):
        self.queue.put(message)

    def send_message(self, message):

        import sys
        import struct
        import json

        message_bytes = json.dumps(message.data, ensure_ascii=False).encode()

        message_length_bytes = struct.pack("I", len(message_bytes))
        sys.stdout.buffer.write(message_length_bytes)
        sys.stdout.buffer.write(message_bytes)
        sys.stdout.buffer.flush()

    def exec(self):

        self.message_receiving_thread.start()
        self.queue_poll_thread.start()
