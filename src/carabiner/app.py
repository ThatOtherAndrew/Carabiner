import json
from os import getenv, PathLike
from pathlib import Path
from typing import ClassVar

from textual import containers, widgets
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widget import Widget

from . import celeste


class ModTile(Widget):
    def __init__(self, mod: celeste.Mod, *children: Widget):
        self.mod = mod
        super().__init__(*children)

    def compose(self) -> ComposeResult:
        yield widgets.Pretty(self.mod)

class CelesteInstance(containers.VerticalScroll):
    def __init__(self, path: str | PathLike[str], *children: Widget):
        super().__init__(*children)
        self.path = Path(path).resolve()

    def compose(self) -> ComposeResult:
        with widgets.Collapsible(title='Installation'):
            yield widgets.Pretty(self.path)

        with widgets.Collapsible(title='Mods'):
            with containers.Grid():
                for mod in (self.path / 'Mods').glob('*.zip'):
                    yield ModTile(mod=celeste.Mod.from_zip(mod))


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
