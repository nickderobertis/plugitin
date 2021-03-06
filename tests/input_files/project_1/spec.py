from typing import Tuple, Dict

from plugin import PluginSpec, ChainPlugin


class MyPluginSpec(PluginSpec):

    def on_single_arg(self, value: float) -> float:
        pass

    def on_two_args(self, value: float, value2: float) -> Tuple[float, float]:
        pass

    def on_kwargs(self, value: float = 10) -> Dict[str, float]:
        pass

    def on_args_and_kwargs(self, value: float, value2: float = 10) -> Tuple[float, Dict[str, float]]:
        pass

    def on_nothing(self):
        pass


class MyChainPlugin(ChainPlugin):

    def on_single_arg(self, value: float) -> float:
        return self.execute('on_single_arg', (value,))

    def on_two_args(self, value: float, value2: float) -> Tuple[float, float]:
        return self.execute('on_two_args', (value, value2))

    def on_kwargs(self, value: float = 10) -> Dict[str, float]:
        return self.execute('on_kwargs', kwargs=dict(value=value))

    def on_args_and_kwargs(self, value: float, value2: float = 10) -> Tuple[float, Dict[str, float]]:
        return self.execute('on_args_and_kwargs', (value,), kwargs=dict(value2=value2))

    def on_nothing(self):
        return self.execute('on_nothing')


