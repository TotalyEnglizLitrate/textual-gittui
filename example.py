from collections.abc import Callable

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Footer


def include_bindings[T: Screen | App](field: str) -> Callable[[type[T]], type[T]]:
    # build a bindings list from settings, hardcoded it for testing
    bindings = [Binding("w", "quit", "Quit", show=True)]

    def wrapper(cls: type[T]) -> type[T]:

        NewClass = type(
            cls.__name__,
            (cls,),
            {
                "BINDINGS": bindings,
                "__module__": cls.__module__,
                "__qualname__": cls.__qualname__,
            },
        )

        return NewClass

    return wrapper


@include_bindings("")
class Test(App):
    def compose(self) -> ComposeResult:
        yield Footer()

    def on_mount(self):
        self.notify(str(self.active_bindings.keys()))


if __name__ == "__main__":
    Test().run()
