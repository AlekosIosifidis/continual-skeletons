from enum import Enum
from functools import wraps
from typing import Callable, Tuple

from torch import Tensor
from torch.nn import Module


class TensorPlaceholder:
    shape: Tuple[int]

    def __init__(self, shape: Tuple[int]):
        self.shape = shape

    def size(self):
        return self.shape


class FillMode(Enum):
    REPLICATE = "replicate"
    ZEROS = "zeros"


def unsqueezed(instance: Module, dim: int = 2):
    def decorator(func: Callable[[Tensor], Tensor]):
        @wraps(func)
        def call(x: Tensor) -> Tensor:
            x = x.unsqueeze(dim)
            x = func(x)
            x = x.squeeze(dim)
            return x

        return call

    instance.forward_regular = instance.forward
    instance.forward = decorator(instance.forward)

    return instance
