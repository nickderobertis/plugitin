from typing import *
from plugin import ChainPlugin, AggregatePlugin


class MyPluginChain(ChainPlugin):
    def on_single_arg(self, value: float) -> float:
        return self.execute("on_single_arg", value)

    def on_two_args(self, value: float, value2: float) -> Tuple[float, float]:
        return self.execute("on_two_args", value, value2)

    def on_kwargs(self, value: float = 10) -> Dict[str, float]:
        return self.execute("on_kwargs", value=value)

    def on_args_and_kwargs(
        self, value: float, value2: float = 10
    ) -> Tuple[float, Dict[str, float]]:
        return self.execute("on_args_and_kwargs", value, value2=value2)

    def on_nothing(self):
        return self.execute("on_nothing")


class MyPluginAggregate(AggregatePlugin):
    def on_single_arg(self, value: float) -> List[float]:
        return self.execute("on_single_arg", value)

    def on_two_args(self, value: float, value2: float) -> List[Tuple[float, float]]:
        return self.execute("on_two_args", value, value2)

    def on_kwargs(self, value: float = 10) -> List[Dict[str, float]]:
        return self.execute("on_kwargs", value=value)

    def on_args_and_kwargs(
        self, value: float, value2: float = 10
    ) -> List[Tuple[float, Dict[str, float]]]:
        return self.execute("on_args_and_kwargs", value, value2=value2)

    def on_nothing(self):
        return self.execute("on_nothing")
