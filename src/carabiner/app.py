import json
import zipfile
from os import getenv, PathLike
from pathlib import Path
from typing import ClassVar, Any

import yaml
from textual import containers, widgets
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widget import Widget


class ModTile(containers.Horizontal):
    def __init__(self, mod_zip_path: str | PathLike[str], *children: Widget):
        super().__init__(*children)

        self.path = Path(mod_zip_path).resolve()

        manifest = self._get_mod_manifest()
        self.mod_name: str = manifest['Name']
        self.mod_version = str(manifest['Version'])

    def _get_mod_manifest(self) -> dict[str, Any]:
        path = zipfile.Path(self.path)
        if (path / 'everest.yaml').is_file():
            yaml_path = path / 'everest.yaml'
        elif (path / 'everest.yml').is_file():
            yaml_path = path / 'everest.yml'
        else:
            raise FileNotFoundError('everest.y[a]ml file not found')

        with yaml_path.open(encoding='utf-8-sig') as file:
            manifest_data = yaml.safe_load(file)[0]

        return manifest_data

    def compose(self) -> ComposeResult:
        yield widgets.Switch(animate=False)
        yield widgets.Static(f'[green]{self.mod_name}[/] [dim]{self.mod_version}')

    def on_click(self) -> None:
        self.query_one(widgets.Switch).toggle()

class CelesteInstance(containers.VerticalScroll):
    def __init__(self, path: str | PathLike[str], *children: Widget):
        super().__init__(*children)
        self.path = Path(path).resolve()

    def compose(self) -> ComposeResult:
        with widgets.Collapsible(title='Installation', collapsed=False):
            yield widgets.Pretty(self.path)

        with widgets.Collapsible(title='Mods', collapsed=False):
            with containers.Grid():
                for mod in (self.path / 'Mods').glob('*.zip'):
                    yield ModTile(mod)


class Carabiner(App):
    TITLE = 'Carabiner'
    SUB_TITLE = 'Celeste mod preset manager'
    CSS_PATH = 'app.tcss'
    BINDINGS: ClassVar[list[Binding]] = [
        Binding('ctrl+c', action='quit', description='quit', priority=True),
    ]

    def compose(self) -> ComposeResult:
        yield widgets.TabbedContent()
        yield widgets.Footer()

    def on_ready(self):
        with (Path(getenv('LOCALAPPDATA')) / 'Olympus' / 'config.json').open() as file:
            olympus_config = json.load(file)

        tabbed_content = self.query_exactly_one(widgets.TabbedContent)
        for install in olympus_config['installs']:
            pane = widgets.TabPane(install['name'], CelesteInstance(path=install['path']))
            tabbed_content.add_pane(pane)
