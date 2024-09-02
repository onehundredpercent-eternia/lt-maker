from pathlib import Path
from app.data.serialization.command import SCommand, SerializeCommand
from app.editor.file_manager.file_manager import FileManager

class SerializationFileManager():
    def __init__(self, root_dir: Path):
        self.root_dir = root_dir
        self.file_manager = FileManager(root_dir)

    def process_serialization_command(self, cmd: SerializeCommand):
        if cmd.action == SCommand.WRITE:
            self.file_manager.save(cmd.path, cmd.contents, True)
        pass