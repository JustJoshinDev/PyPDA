import sys
import os
import json
import subprocess
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QWidget, QVBoxLayout,
    QLabel, QFileDialog, QStackedWidget, QListWidget, QHBoxLayout, QTreeView, QFileSystemModel, QPlainTextEdit
)
from PySide6.QtCore import Qt, QDir, QEvent
from PySide6.QtGui import QKeySequence, QFont, QPalette, QColor

APP_DATA_PATH = os.path.expanduser("~/.pipda")
APPS_JSON = os.path.join(APP_DATA_PATH, "apps.json")

# Apply late-90s PDA style globally
def apply_retro_style(app):
    font = QFont("Courier New", 10)
    app.setFont(font)

    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(192, 192, 192))
    palette.setColor(QPalette.Button, QColor(160, 160, 160))
    palette.setColor(QPalette.ButtonText, Qt.black)
    palette.setColor(QPalette.Base, QColor(255, 255, 255))
    palette.setColor(QPalette.Text, Qt.black)
    palette.setColor(QPalette.WindowText, Qt.black)
    app.setPalette(palette)

class HomeScreen(QWidget):
    def __init__(self, parent):
        super().__init__()
        layout = QVBoxLayout()

        header = QLabel("[ PiPDA OS Booted ]")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)

        layout.addSpacing(10)

        btn_file = QPushButton("File Manager")
        btn_term = QPushButton("Terminal")
        btn_apps = QPushButton("Installed Apps")
        btn_add = QPushButton("Install New App")

        for btn in [btn_file, btn_term, btn_apps, btn_add]:
            btn.setFixedHeight(30)
            btn.setStyleSheet("QPushButton { border: 2px outset gray; background-color: silver; }")

        btn_file.clicked.connect(lambda: parent.set_view("file"))
        btn_term.clicked.connect(lambda: parent.set_view("term"))
        btn_apps.clicked.connect(lambda: parent.set_view("apps"))
        btn_add.clicked.connect(parent.add_app)

        layout.addWidget(btn_file)
        layout.addWidget(btn_term)
        layout.addWidget(btn_apps)
        layout.addWidget(btn_add)
        layout.addStretch()

        self.setLayout(layout)

class FileExplorer(QWidget):
    def __init__(self, parent):
        super().__init__()
        layout = QVBoxLayout()

        self.model = QFileSystemModel()
        self.model.setRootPath(QDir.rootPath())

        self.tree = QTreeView()
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(QDir.rootPath()))
        self.tree.setColumnHidden(1, True)
        self.tree.setColumnHidden(2, True)

        btn_home = QPushButton("Return to Main Menu")
        btn_home.clicked.connect(lambda: parent.set_view("home"))

        layout.addWidget(QLabel("[ File Explorer ]"))
        layout.addWidget(self.tree)
        layout.addWidget(btn_home)

        self.setLayout(layout)

class Terminal(QWidget):
    def __init__(self, parent):
        super().__init__()
        layout = QVBoxLayout()

        self.terminal_output = QPlainTextEdit()
        self.terminal_output.setReadOnly(True)
        self.terminal_output.setPlaceholderText("-- Terminal Boot --")

        self.terminal_input = QPlainTextEdit()
        self.terminal_input.setPlaceholderText("Enter Command...")
        self.terminal_input.setFixedHeight(60)

        self.terminal_input.installEventFilter(self)

        btn_home = QPushButton("Return to Main Menu")
        btn_home.clicked.connect(lambda: parent.set_view("home"))

        layout.addWidget(QLabel("[ Terminal Interface ]"))
        layout.addWidget(self.terminal_output)
        layout.addWidget(self.terminal_input)
        layout.addWidget(btn_home)

        self.setLayout(layout)

        self.show_current_directory()

    def eventFilter(self, source, event):
        if source == self.terminal_input and event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
                self.execute_command()
                return True
        return super().eventFilter(source, event)

    def show_current_directory(self):
        current_dir = os.getcwd()
        self.terminal_output.appendPlainText(f"DIR: {current_dir}")

    def execute_command(self):
        command = self.terminal_input.toPlainText().strip()
        if not command:
            return

        self.terminal_output.appendPlainText(f"> {command}")

        if sys.platform.startswith('linux') or sys.platform.startswith('win'):
            process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=os.getcwd())
        else:
            self.terminal_output.appendPlainText("! Unsupported platform.")
            return

        stdout, stderr = process.communicate()

        if stdout:
            self.terminal_output.appendPlainText(stdout.decode('utf-8'))
        if stderr:
            self.terminal_output.appendPlainText(stderr.decode('utf-8'))

        self.show_current_directory()
        self.terminal_input.clear()

class AppMenu(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.layout = QVBoxLayout()
        self.app_list = QListWidget()
        btn_home = QPushButton("Return to Main Menu")
        btn_home.clicked.connect(lambda: parent.set_view("home"))

        self.layout.addWidget(QLabel("[ Installed Applications ]"))
        self.layout.addWidget(self.app_list)
        self.layout.addWidget(btn_home)
        self.setLayout(self.layout)
        self.load_apps()

    def load_apps(self):
        self.app_list.clear()
        if os.path.exists(APPS_JSON):
            with open(APPS_JSON, "r") as f:
                apps = json.load(f)
            for app in apps:
                self.app_list.addItem(app["name"])

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("JoshPDA Rev 1")
        self.showFullScreen()

        self.stack = QStackedWidget()
        self.home = HomeScreen(self)
        self.file_explorer = FileExplorer(self)
        self.terminal = Terminal(self)
        self.app_menu = AppMenu(self)

        self.stack.addWidget(self.home)
        self.stack.addWidget(self.file_explorer)
        self.stack.addWidget(self.terminal)
        self.stack.addWidget(self.app_menu)

        self.setCentralWidget(self.stack)

    def set_view(self, view_name):
        views = {"home": 0, "file": 1, "term": 2, "apps": 3}
        self.stack.setCurrentIndex(views.get(view_name, 0))

    def add_app(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Python App", os.path.expanduser("~"), "Python Files (*.py)")
        if file_path:
            app_name = os.path.basename(file_path)
            os.makedirs(APP_DATA_PATH, exist_ok=True)
            if os.path.exists(APPS_JSON):
                with open(APPS_JSON, "r") as f:
                    apps = json.load(f)
            else:
                apps = []
            apps.append({"name": app_name, "path": file_path})
            with open(APPS_JSON, "w") as f:
                json.dump(apps, f, indent=2)
            self.app_menu.load_apps()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    apply_retro_style(app)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
