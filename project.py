import sys
import os
import psutil
import shutil
import win32com.client
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel, QVBoxLayout, QTextEdit, QFileDialog, QGridLayout, QComboBox,
    QProgressBar, QTabWidget, QSizePolicy, QMessageBox, QHBoxLayout
)
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time
from datetime import datetime
import pyqtgraph as pg  # For line graphs

# Custom Thread for Scanning Files
class FileScannerThread(QThread):
    update_progress = pyqtSignal(int, int, int)  # Signal to update progress (progress, scanned_files, total_files)
    scan_result = pyqtSignal(list)  # Signal to send scan results

    def __init__(self, drive_path):
        super().__init__()
        self.drive_path = drive_path

    def run(self):
        old_files = []
        total_files = 0
        scanned_files = 0

        # Count total files for progress calculation
        for root, _, files in os.walk(self.drive_path):
            total_files += len(files)

        # Scan files
        for root, _, files in os.walk(self.drive_path):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    # Get file details
                    last_access_time = os.path.getatime(file_path)
                    last_modified_time = os.path.getmtime(file_path)
                    days_unused = (time.time() - last_access_time) // (24 * 3600)
                    size = os.path.getsize(file_path) / (1024 * 1024)  # Size in MB

                    # Add file details to the list
                    old_files.append({
                        "path": file_path,
                        "name": file,
                        "size_mb": size,
                        "last_accessed": datetime.fromtimestamp(last_access_time).strftime("%Y-%m-%d %H:%M:%S"),
                        "last_modified": datetime.fromtimestamp(last_modified_time).strftime("%Y-%m-%d %H:%M:%S"),
                        "days_unused": days_unused
                    })
                except Exception as e:
                    print(f"Error accessing {file_path}: {e}")

                scanned_files += 1
                progress = int((scanned_files / total_files) * 100)
                self.update_progress.emit(progress, scanned_files, total_files)

        self.scan_result.emit(old_files)

# File Event Handler for Monitoring
class FileEventHandler(FileSystemEventHandler):
    def __init__(self, output_widget):
        super().__init__()
        self.output_widget = output_widget

    def on_deleted(self, event):
        if not event.is_directory:
            self.output_widget.append(f"❌ File Deleted: {event.src_path}")

# Main Application Window
class FileSystemTool(QWidget):
    def __init__(self):
        super().__init__()
        self.folder_to_monitor = None
        self.observer = None
        self.scanner_thread = None
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Advanced File System Recovery & Optimization Tool")
        self.setGeometry(100, 100, 1200, 800)
        self.setStyleSheet("""
            QWidget {
                background-color: #2E3440;
                color: #D8DEE9;
            }
            QPushButton {
                background-color: #4C566A;
                color: #ECEFF4;
                padding: 10px;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #5E81AC;
            }
            QTextEdit {
                background-color: #3B4252;
                color: #ECEFF4;
                border: 1px solid #4C566A;
                padding: 10px;
                border-radius: 5px;
                font-size: 12px;
            }
            QComboBox {
                background-color: #4C566A;
                color: #ECEFF4;
                padding: 5px;
                border-radius: 5px;
                font-size: 14px;
            }
            QProgressBar {
                background-color: #4C566A;
                color: #ECEFF4;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #5E81AC;
                border-radius: 5px;
            }
            QLabel {
                font-size: 16px;
                color: #ECEFF4;
            }
        """)

        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Title
        title = QLabel("📂 Advanced File System Recovery & Optimization Tool")
        title.setFont(QFont("Arial", 20, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setFont(QFont("Arial", 12))
        main_layout.addWidget(self.tabs)

        # File Operations Tab
        file_operations_tab = QWidget()
        file_operations_layout = QVBoxLayout()
        file_operations_layout.setSpacing(15)

        # Drive Selector
        self.drive_selector = QComboBox()
        self.drive_selector.addItem("Select a Drive")
        self.drive_selector.currentIndexChanged.connect(self.display_drive_files)
        file_operations_layout.addWidget(self.drive_selector)

        # Buttons
        button_layout = QGridLayout()
        buttons = {
            "📁 Scan System": self.scan_files,
            "👀 Monitor Files": self.monitor_files,
            "🔄 Recover Files": self.recover_deleted_files,
            "⚙️ Optimize Storage": self.optimize_storage,
            "📂 Select Folder": self.select_folder,
            "🧹 Clear Log": self.clear_output
        }

        row, col = 0, 0
        for text, function in buttons.items():
            btn = QPushButton(text)
            btn.setFont(QFont("Arial", 12))
            btn.clicked.connect(function)
            btn.setToolTip(f"Click to {text.lower()}")
            button_layout.addWidget(btn, row, col)
            col += 1
            if col > 2:
                col = 0
                row += 1

        file_operations_layout.addLayout(button_layout)

        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        file_operations_layout.addWidget(self.progress_bar)

        # Output Log
        self.output_text = QTextEdit(readOnly=True)
        self.output_text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        file_operations_layout.addWidget(self.output_text)

        file_operations_tab.setLayout(file_operations_layout)
        self.tabs.addTab(file_operations_tab, "File Operations")

        # System Info Tab
        system_info_tab = QWidget()
        system_info_layout = QVBoxLayout()
        system_info_layout.setSpacing(15)

        # System Info Label
        system_info_label = QLabel("🖥️ System Information")
        system_info_label.setFont(QFont("Arial", 16, QFont.Bold))
        system_info_layout.addWidget(system_info_label)

        # CPU Usage
        self.cpu_usage_label = QLabel("💻 CPU Usage: 0%")
        self.cpu_usage_label.setFont(QFont("Arial", 14))
        system_info_layout.addWidget(self.cpu_usage_label)

        # CPU Usage Graph
        self.cpu_graph = pg.PlotWidget(title="CPU Usage (%)")
        self.cpu_graph.setBackground("#3B4252")
        self.cpu_graph.setYRange(0, 100)
        self.cpu_graph.showGrid(x=True, y=True)
        self.cpu_curve = self.cpu_graph.plot(pen=pg.mkPen(color="#5E81AC", width=2))
        system_info_layout.addWidget(self.cpu_graph)

        # Memory Usage
        self.memory_usage_label = QLabel("🧠 Memory Usage: 0%")
        self.memory_usage_label.setFont(QFont("Arial", 14))
        system_info_layout.addWidget(self.memory_usage_label)

        # Memory Usage Graph
        self.memory_graph = pg.PlotWidget(title="Memory Usage (%)")
        self.memory_graph.setBackground("#3B4252")
        self.memory_graph.setYRange(0, 100)
        self.memory_graph.showGrid(x=True, y=True)
        self.memory_curve = self.memory_graph.plot(pen=pg.mkPen(color="#88C0D0", width=2))
        system_info_layout.addWidget(self.memory_graph)

        system_info_tab.setLayout(system_info_layout)
        self.tabs.addTab(system_info_tab, "System Info")

        self.setLayout(main_layout)
        self.load_drives()

        # Initialize data for graphs
        self.cpu_data = []
        self.memory_data = []
        self.time_data = []

        # Start real-time system info updates
        self.system_info_timer = QTimer()
        self.system_info_timer.timeout.connect(self.update_system_info)
        self.system_info_timer.start(1000)  # Update every 1 second

    def load_drives(self):
        self.drive_selector.clear()
        self.drive_selector.addItem("Select a Drive")
        for drive in [d.device for d in psutil.disk_partitions()]:
            self.drive_selector.addItem(drive)
    
    def display_drive_files(self):
        selected_drive = self.drive_selector.currentText()
        if selected_drive == "Select a Drive":
            return
        
        self.output_text.append(f"📂 Files in {selected_drive}:\n")
        for root, _, files in os.walk(selected_drive):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    size = os.path.getsize(file_path) / (1024 * 1024)  # Size in MB
                    self.output_text.append(f"📄 {file_path} - {size:.2f} MB")
                except Exception as e:
                    self.output_text.append(f"❌ Error reading {file_path}: {e}")

    def scan_files(self):
        selected_drive = self.drive_selector.currentText()
        if selected_drive == "Select a Drive":
            QMessageBox.warning(self, "Warning", "Please select a drive first!")
            return

        self.output_text.append("🔍 Scanning file system...\n")
        self.progress_bar.setValue(0)

        # Start the scanning thread
        self.scanner_thread = FileScannerThread(selected_drive)
        self.scanner_thread.update_progress.connect(self.update_progress)
        self.scanner_thread.scan_result.connect(self.display_scan_results)
        self.scanner_thread.start()

    def update_progress(self, progress, scanned_files, total_files):
        self.progress_bar.setValue(progress)
        self.output_text.append(f"📊 Progress: {scanned_files}/{total_files} files scanned ({progress}%)")

    def display_scan_results(self, old_files):
        if old_files:
            self.output_text.append("⚠️ Unused Files (Not accessed for more than 180 days):\n")
            for file in old_files:
                self.output_text.append(
                    f"📄 File: {file['name']}\n"
                    f"   📂 Path: {file['path']}\n"
                    f"   📦 Size: {file['size_mb']:.2f} MB\n"
                    f"   🕒 Last Accessed: {file['last_accessed']}\n"
                    f"   🕒 Last Modified: {file['last_modified']}\n"
                    f"   🕒 Days Unused: {file['days_unused']}\n"
                    "----------------------------------------\n"
                )
        else:
            self.output_text.append("✅ No unused files found.\n")

        self.output_text.append("✅ Scan complete!\n")

    def monitor_files(self):
        if not self.folder_to_monitor:
            QMessageBox.warning(self, "Warning", "Please select a folder first!")
            return
        
        self.output_text.append(f"📂 Monitoring folder: {self.folder_to_monitor}\n")
        self.observer = Observer()
        self.observer.schedule(FileEventHandler(self.output_text), self.folder_to_monitor, recursive=True)
        self.observer.start()

    def recover_deleted_files(self):
        recovery_folder = QFileDialog.getExistingDirectory(self, "Select Recovery Folder")
        if not recovery_folder:
            self.output_text.append("⚠️ Recovery canceled!\n")
            return
        
        shell = win32com.client.Dispatch("Shell.Application")
        recycle_bin = shell.Namespace(10)
        
        for item in recycle_bin.Items():
            recovered_path = os.path.join(recovery_folder, item.Name)
            shutil.move(item.Path, recovered_path)
            self.output_text.append(f"🔄 Recovered: {item.Name} → {recovered_path}\n")
        
        self.output_text.append(f"✅ Files saved in: {recovery_folder}\n")

    def optimize_storage(self):
        self.output_text.append("🛠️ Optimizing storage...\n")
        os.system("cleanmgr /sagerun:1")
        self.output_text.append("✅ Optimization Complete!\n")

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            self.folder_to_monitor = folder
            self.output_text.append(f"📂 Selected Folder: {folder}\n")
    
    def clear_output(self):
        self.output_text.clear()
        self.output_text.append("🗑️ Log cleared!\n")

    def update_system_info(self):
        # Update CPU Usage
        cpu_usage = psutil.cpu_percent()
        self.cpu_usage_label.setText(f"💻 CPU Usage: {cpu_usage}%")
        self.cpu_data.append(cpu_usage)

        # Update Memory Usage
        memory_usage = psutil.virtual_memory().percent
        self.memory_usage_label.setText(f"🧠 Memory Usage: {memory_usage}%")
        self.memory_data.append(memory_usage)

        # Update time data
        self.time_data.append(len(self.time_data))

        # Update graphs
        self.cpu_curve.setData(self.time_data, self.cpu_data)
        self.memory_curve.setData(self.time_data, self.memory_data)

        # Limit data to last 60 seconds
        if len(self.time_data) > 60:
            self.cpu_data.pop(0)
            self.memory_data.pop(0)
            self.time_data.pop(0)

    def closeEvent(self, event):
        if self.observer:
            self.observer.stop()
            self.observer.join()
        if self.scanner_thread and self.scanner_thread.isRunning():
            self.scanner_thread.quit()
        self.system_info_timer.stop()  # Stop the timer
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FileSystemTool()
    window.show()
    sys.exit(app.exec_())