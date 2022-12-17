from src.client.CallScheduler import *
from src.client.CallGenerator import *


class Main:
    def __init__(self):
        self.scheduler = SchedulerMainWindow(self)
        self.generator = GeneratorMainWindow(self)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main = Main()
    main.generator.show()
    sys.exit(app.exec_())
