import dataclasses


@dataclasses.dataclass
class FolderPath:
    path: str


@dataclasses.dataclass
class FilePath:
    path_to_folder: FolderPath
    name: str
    is_json: bool

    def full_path(self):
        return self.path_to_folder.path + self.name


PATH_TO_FOLDER_SYSTEM_DATA = FolderPath('SystemData/')
PATH_TO_JSON_FILE_OFFERS_CACHE = FilePath(PATH_TO_FOLDER_SYSTEM_DATA, 'offers_info_cache.json', True)
