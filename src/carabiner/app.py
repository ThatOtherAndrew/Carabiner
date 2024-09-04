import json
import zipfile
from os import getenv, PathLike
from pathlib import Path
from typing import ClassVar, Any

import yaml
from textual import containers, widgets
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Switch


class ModTile(containers.Horizontal):
    class Toggled(Message):
        def __init__(self, mod_name: str, file_name: str, is_enabled: bool) -> None:
            super().__init__()
            self.mod_name = mod_name
            self.file_name = file_name
            self.is_enabled = is_enabled

    is_enabled = reactive(False)

    def __init__(self, mod_zip_path: str | PathLike[str], is_enabled: bool, *children: Widget):
        super().__init__(*children)

        self.path = Path(mod_zip_path).resolve()

        manifest = self._get_mod_manifest()
        self.mod_name: str = manifest['Name']
        self.mod_version = str(manifest['Version'])
        self.set_reactive(ModTile.is_enabled, is_enabled)

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
        yield widgets.Switch(value=self.is_enabled)
        yield widgets.Static(f'[green]{self.mod_name}[/] [dim]{self.mod_version}')

    def watch_is_enabled(self, _, value: bool) -> None:
        self.query_one(Switch).value = value
        self.post_message(self.Toggled(mod_name=self.mod_name, file_name=self.path.name, is_enabled=value))

    def on_click(self) -> None:
        self.query_one(widgets.Switch).toggle()

    def on_switch_changed(self, event: widgets.Switch.Changed) -> None:
        self.is_enabled = not self.is_enabled

class CelesteInstance(containers.VerticalScroll):
    def __init__(self, path: str | PathLike[str], *children: Widget):
        super().__init__(*children)
        self.path = Path(path).resolve()
        self.mods_enabled: dict[str, bool] = {}
        self.blacklist_file = self.path / 'Mods' / 'blacklist.txt'

    def get_blacklist_enabled(self, mod_file_name: str):
        return mod_file_name not in [
            line.strip()
            for line in self.blacklist_file.read_text().splitlines()
            if not line.startswith('#')
        ]

    def set_blacklist(self, mod_file_name: str, enabled: bool):
        lines = self.blacklist_file.read_text().splitlines()

        if enabled:
            for i, line in enumerate(lines):
                if line.strip() == mod_file_name:
                    lines[i] = '# ' + mod_file_name
                    break
        else:
            exists = False
            for i, line in enumerate(lines):
                if line.lstrip('# ').rstrip() == mod_file_name:
                    lines[i] = mod_file_name
                    exists = True
                    break
            if not exists:
                lines.append(mod_file_name)

        self.blacklist_file.write_text('\n'.join(lines))


    def compose(self) -> ComposeResult:
        with widgets.Collapsible(title='Installation', collapsed=False):
            yield widgets.Pretty(self.path)

        with widgets.Collapsible(title='Mods', collapsed=False):
            with containers.Grid():
                for mod in (self.path / 'Mods').glob('*.zip'):
                    mod_tile = ModTile(mod, is_enabled=self.get_blacklist_enabled(mod.name))
                    self.mods_enabled[mod_tile.mod_name] = mod_tile.is_enabled
                    yield mod_tile

    def on_mod_tile_toggled(self, message: ModTile.Toggled) -> None:
        self.set_blacklist(message.file_name, message.is_enabled)

        if message.is_enabled:
            self.notify(f'[green]Enabled[/] {message.mod_name}', severity='information')
        else:
            self.notify(f'[red]Disabled[/] {message.mod_name}', severity='error')


class Carabiner(App):
    TITLE = 'Carabiner'
    SUB_TITLE = 'Celeste mod preset manager'
    CSS_PATH = 'app.tcss'
    BINDINGS: ClassVar[list[Binding]] = [
        Binding('ctrl+c', action='quit', description='quit', priority=True),
    ]

    def compose(self) -> ComposeResult:
        yield widgets.Header(icon='🍓')
        yield widgets.TabbedContent()
        yield widgets.Footer()

    def on_ready(self):
        with (Path(getenv('LOCALAPPDATA')) / 'Olympus' / 'config.json').open() as file:
            olympus_config = json.load(file)

        tabbed_content = self.query_exactly_one(widgets.TabbedContent)
        for install in olympus_config['installs']:
            pane = widgets.TabPane(install['name'], CelesteInstance(path=install['path']))
            tabbed_content.add_pane(pane)
