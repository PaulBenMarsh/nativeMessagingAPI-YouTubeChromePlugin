
def main(argv):

    from PyQt5.QtWidgets import QApplication

    from mainwindow import MainWindow

    application = QApplication(argv)
    window = MainWindow()

    window.show()
    window.exec()

    return application.exec()


if __name__ == "__main__":
    import sys

    def excepthook(exctype, value, traceback):
        # import winsound
        # winsound.Beep(440, 500)
        sys.__excepthook__(exctype, value, traceback)

    sys.excepthook = excepthook

    sys.exit(main(sys.argv))
