import time
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import subprocess

class FileChangeHandler(FileSystemEventHandler):
    def __init__(self, script_path):
        self.script_path = script_path

    def on_modified(self, event):
        if event.src_path.endswith("input.geojson"):
            print(f"{event.src_path} було змінено. Запуск обробки...")
            try:
                # Запуск QGIS-скрипта
                subprocess.run(
                    ["python", self.script_path],
                    shell=True,
                    cwd=os.path.dirname(self.script_path),
                    check=True
                )
                print("✅ Обробка завершена успішно.")
            except subprocess.CalledProcessError as e:
                print(f"❌ Помилка під час запуску: {e}")


if __name__ == "__main__":
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    path_to_watch = os.path.join(base_dir, "data")
    script_to_run = os.path.join(base_dir, "qgis_processor.py")

    event_handler = FileChangeHandler(script_to_run)
    observer = Observer()
    observer.schedule(event_handler, path=path_to_watch, recursive=False)
    observer.start()

    print(f"Відстеження змін у {path_to_watch}. Натисніть Ctrl+C для зупинки.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()