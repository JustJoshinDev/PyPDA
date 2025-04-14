import sys
import os
import json
import subprocess
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QWidget, QVBoxLayout,
    QLabel, QFileDialog, QStackedWidget, QGridLayout, QToolButton,
    QTreeView, QFileSystemModel, QPlainTextEdit, QListWidget, QLineEdit
)
from PySide6.QtCore import Qt, QDir, QEvent, QSize
from PySide6.QtGui import QKeySequence, QFont, QPalette, QColor, QIcon

APP_DATA_PATH = os.path.expanduser("~/.pypda")
EXTENSIONS_JSON = os.path.join(APP_DATA_PATH, "extensions.json")

# ------------------ Retro Theme ------------------
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

# ------------------ Extension Class ------------------
class Extension:
    def __init__(self, name, icon_path, widget_cls):
        self.name = name
        self.icon_path = icon_path
        self.widget_cls = widget_cls

# ------------------ Extensions ------------------
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

class Calculator(QWidget):
    def __init__(self, parent):
        super().__init__()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("[ Calculator ]"))

        self.display = QLineEdit()
        self.display.setReadOnly(True)
        self.display.setAlignment(Qt.AlignRight)
        self.display.setFixedHeight(40)
        layout.addWidget(self.display)

        grid = QGridLayout()
        buttons = [
            ['7', '8', '9', '÷'],
            ['4', '5', '6', '×'],
            ['1', '2', '3', '-'],
            ['C', '0', '=', '+']
        ]

        for row, row_vals in enumerate(buttons):
            for col, val in enumerate(row_vals):
                btn = QPushButton(val)
                btn.setFixedSize(60, 40)
                btn.clicked.connect(lambda _, v=val: self.on_button_click(v))
                grid.addWidget(btn, row, col)

        layout.addLayout(grid)

        btn_home = QPushButton("Return to Main Menu")
        btn_home.clicked.connect(lambda: parent.set_view("home"))
        layout.addWidget(btn_home)

        self.setLayout(layout)
        self.current_input = ""

    def on_button_click(self, value):
        if value == 'C':
            self.current_input = ""
            self.display.setText("")
        elif value == '=':
            try:
                expression = self.current_input.replace('×', '*').replace('÷', '/')
                result = str(eval(expression))
                self.display.setText(result)
                self.current_input = result
            except Exception:
                self.display.setText("Error")
                self.current_input = ""
        else:
            self.current_input += value
            self.display.setText(self.current_input)


class ExtensionManager(QWidget):
    def __init__(self, parent):
        super().__init__()
        layout = QVBoxLayout()
        self.list_widget = QListWidget()
        layout.addWidget(QLabel("[ Installed Extensions ]"))
        layout.addWidget(self.list_widget)

        btn_add = QPushButton("Install New Extension")
        btn_add.clicked.connect(parent.add_extension)
        btn_home = QPushButton("Return to Main Menu")
        btn_home.clicked.connect(lambda: parent.set_view("home"))
        layout.addWidget(btn_add)
        layout.addWidget(btn_home)

        self.setLayout(layout)
        self.load_extensions()

    def load_extensions(self):
        self.list_widget.clear()
        if os.path.exists(EXTENSIONS_JSON):
            with open(EXTENSIONS_JSON, "r") as f:
                exts = json.load(f)
            for ext in exts:
                self.list_widget.addItem(ext["name"])

# ------------------ Home Grid ------------------
class HomeScreen(QWidget):
    def __init__(self, parent, extensions):
        super().__init__()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("[ PyPDA v0.1 ]"))

        grid = QGridLayout()
        max_columns = 3
        for i, ext in enumerate(extensions):
            btn = QToolButton()
            btn.setText(ext.name)
            btn.setIcon(QIcon(ext.icon_path))
            btn.setIconSize(QSize(48, 48))
            btn.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
            btn.clicked.connect(lambda _, e=ext: parent.launch_extension(e))
            grid.addWidget(btn, i // max_columns, i % max_columns)

        layout.addLayout(grid)
        layout.addStretch()
        self.setLayout(layout)

# ------------------ Main Window ------------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyPDA v0.1")
        self.showFullScreen()
        self.stack = QStackedWidget()

        # Define extensions
        self.extensions = [
            Extension("File Explorer", "icons/folder.png", lambda: FileExplorer(self)),
            Extension("Terminal", "icons/terminal.png", lambda: Terminal(self)),
            Extension("Extensions", "icons/install.png", lambda: ExtensionManager(self)),
            Extension("Calculator", "icons/calc.png", lambda: Calculator(self)),

        ]

        self.home = HomeScreen(self, self.extensions)
        self.stack.addWidget(self.home)
        self.setCentralWidget(self.stack)

    def set_view(self, view_name):
        if view_name == "home":
            self.stack.setCurrentIndex(0)

    def launch_extension(self, extension):
        widget = extension.widget_cls()
        self.stack.addWidget(widget)
        self.stack.setCurrentWidget(widget)

    def add_extension(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Python Extension", os.path.expanduser("~"), "Python Files (*.py)")
        if file_path:
            ext_name = os.path.basename(file_path)
            os.makedirs(APP_DATA_PATH, exist_ok=True)
            if os.path.exists(EXTENSIONS_JSON):
                with open(EXTENSIONS_JSON, "r") as f:
                    exts = json.load(f)
            else:
                exts = []
            exts.append({"name": ext_name, "path": file_path})
            with open(EXTENSIONS_JSON, "w") as f:
                json.dump(exts, f, indent=2)
            # Refresh manager if open
            for i in range(self.stack.count()):
                widget = self.stack.widget(i)
                if isinstance(widget, ExtensionManager):
                    widget.load_extensions()

# ------------------ Boot ------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    apply_retro_style(app)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
