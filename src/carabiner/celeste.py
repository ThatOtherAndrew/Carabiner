import zipfile
from os import PathLike

import yaml


class Mod:
    def __init__(self, name: str, version: str):
        self.name = name
        self.version = version

    @classmethod
    def from_zip(cls, zip_path: str | PathLike[str]):
        path = zipfile.Path(zip_path)
        if (path / 'everest.yaml').is_file():
            yaml_path = path / 'everest.yaml'
        elif (path / 'everest.yml').is_file():
            yaml_path = path / 'everest.yml'
        else:
            raise FileNotFoundError('everest.yaml file not found')

        with yaml_path.open(encoding='utf-8-sig') as file:
            manifest_data = yaml.safe_load(file)[0]

        return cls(name=manifest_data['Name'], version=str(manifest_data['Version']))

    def __repr__(self):
        return f"<Mod '{self.name}' v{self.version}>"
