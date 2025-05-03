import time
import sys
import os
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import subprocess

class FileChangeHandler(FileSystemEventHandler):
    def __init__(self, script_path):
        self.script_path = os.path.normpath(script_path)
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def on_modified(self, event):
        if event.src_path.endswith("input.geojson"):
            self.logger.info(f"Файл змінено: {event.src_path}")
            try:
                # Використовуємо список для уникнення shell-ін'єкцій
                result = subprocess.run(
                    [sys.executable, self.script_path],
                    shell=False,
                    cwd=os.path.dirname(self.script_path),
                    check=True,
                    capture_output=True,
                    text=True
                )
                self.logger.info("Обробка успішно завершена")
            except subprocess.CalledProcessError as e:
                self.logger.error(f"Помилка обробки: {e}\nВивід: {e.output}")


if __name__ == "__main__":
    base_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    path_to_watch = os.path.normpath(os.path.join(base_dir, "data"))
    script_to_run = os.path.normpath(os.path.join(base_dir, "qgis_processor.py"))

    event_handler = FileChangeHandler(script_to_run)
    observer = Observer()
    observer.schedule(event_handler, path=path_to_watch, recursive=False)
    observer.start()

    logging.info(f"Відстеження змін у {path_to_watch}")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        logging.info("Відстеження зупинено")
    observer.join()