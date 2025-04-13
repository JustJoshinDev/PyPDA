import sys
import os
import json
import subprocess
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QWidget, QVBoxLayout,
    QLabel, QFileDialog, QStackedWidget, QListWidget, QHBoxLayout, QTreeView, QFileSystemModel, QPlainTextEdit
)
from PySide6.QtCore import Qt, QDir, QEvent
from PySide6.QtGui import QKeySequence

APP_DATA_PATH = os.path.expanduser("~/.pipda")
APPS_JSON = os.path.join(APP_DATA_PATH, "apps.json")

class HomeScreen(QWidget):
    def __init__(self, parent):
        super().__init__()
        layout = QVBoxLayout()

        header = QLabel("Welcome to PiPDA!")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)

        layout.addSpacing(10)  # Add some space before buttons

        btn_file = QPushButton("File Explorer")
        btn_term = QPushButton("Terminal")
        btn_apps = QPushButton("All Apps")
        btn_add = QPushButton("Add App")

        btn_file.clicked.connect(lambda: parent.set_view("file"))
        btn_term.clicked.connect(lambda: parent.set_view("term"))
        btn_apps.clicked.connect(lambda: parent.set_view("apps"))
        btn_add.clicked.connect(parent.add_app)

        layout.addWidget(btn_file)
        layout.addWidget(btn_term)
        layout.addWidget(btn_apps)
        layout.addWidget(btn_add)

        layout.addStretch()  # Add stretch to push the buttons to the top

        self.setLayout(layout)

class FileExplorer(QWidget):
    def __init__(self, parent):
        super().__init__()
        layout = QVBoxLayout()

        self.model = QFileSystemModel()
        self.model.setRootPath(QDir.rootPath())  # Set the root directory

        self.tree = QTreeView()
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(QDir.rootPath()))
        self.tree.setColumnHidden(1, True)  # Hide size column
        self.tree.setColumnHidden(2, True)  # Hide type column

        btn_home = QPushButton("Exit to Home")
        btn_home.clicked.connect(lambda: parent.set_view("home"))

        layout.addWidget(QLabel("File Explorer"))
        layout.addWidget(self.tree)
        layout.addWidget(btn_home)  # Add exit button to this screen

        self.setLayout(layout)

class Terminal(QWidget):
    def __init__(self, parent):
        super().__init__()
        layout = QVBoxLayout()

        # Create a text area for terminal output and input
        self.terminal_output = QPlainTextEdit()
        self.terminal_output.setReadOnly(True)  # Make it read-only to simulate terminal
        self.terminal_output.setPlaceholderText("Terminal Output Here...")

        self.terminal_input = QPlainTextEdit()
        self.terminal_input.setPlaceholderText("Enter command here...")
        self.terminal_input.setFixedHeight(60)

        # Add the input field's event filter
        self.terminal_input.installEventFilter(self)

        btn_home = QPushButton("Exit to Home")
        btn_home.clicked.connect(lambda: parent.set_view("home"))

        layout.addWidget(QLabel("[ Terminal ]"))
        layout.addWidget(self.terminal_output)
        layout.addWidget(self.terminal_input)
        layout.addWidget(btn_home)  # Add exit button to this screen

        self.setLayout(layout)

        # Display the initial directory
        self.show_current_directory()

    def eventFilter(self, source, event):
        # Detect the Enter key press on the terminal input field
        if source == self.terminal_input and event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
                self.execute_command()
                return True  # Return True to indicate the event is handled

        return super().eventFilter(source, event)  # Pass the event to the default handler

    def show_current_directory(self):
        """Display the current directory in the terminal output."""
        current_dir = os.getcwd()
        self.terminal_output.appendPlainText(f"Current Directory: {current_dir}")

    def execute_command(self):
        command = self.terminal_input.toPlainText().strip()
        if not command:
            return

        # Display the command in the terminal output window
        self.terminal_output.appendPlainText(f"$ {command}")

        # Execute the command in the system shell (depending on the OS)
        if sys.platform.startswith('linux'):
            process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=os.getcwd())
        elif sys.platform.startswith('win'):
            process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=os.getcwd())

        else:
            self.terminal_output.appendPlainText("Unsupported platform for terminal commands.")
            return

        # Collect the output and error streams
        stdout, stderr = process.communicate()

        # Display the output
        if stdout:
            self.terminal_output.appendPlainText(stdout.decode('utf-8'))
        if stderr:
            self.terminal_output.appendPlainText(stderr.decode('utf-8'))

        # Show the current directory after executing the command
        self.show_current_directory()

        # Clear input after execution
        self.terminal_input.clear()

class AppMenu(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.layout = QVBoxLayout()
        self.app_list = QListWidget()
        btn_home = QPushButton("Exit to Home")
        btn_home.clicked.connect(lambda: parent.set_view("home"))

        self.layout.addWidget(QLabel("Installed Apps:"))
        self.layout.addWidget(self.app_list)
        self.layout.addWidget(btn_home)  # Add exit button to this screen
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
        self.showFullScreen()  # Full screen mode

        self.stack = QStackedWidget()
        self.home = HomeScreen(self)
        self.file_explorer = FileExplorer(self)
        self.terminal = Terminal(self)
        self.app_menu = AppMenu(self)

        self.stack.addWidget(self.home)      # Index 0
        self.stack.addWidget(self.file_explorer)  # 1
        self.stack.addWidget(self.terminal)  # 2
        self.stack.addWidget(self.app_menu)  # 3

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
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
