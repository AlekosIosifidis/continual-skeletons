from typing import Tuple

import torch
from ride.utils.logging import getLogger
from torch import Tensor

from .utils import FillMode

State = Tuple[Tensor, int]

logger = getLogger(__name__)


class Delay(torch.nn.Module):
    def __init__(
        self,
        delay: int,
        temporal_fill: FillMode = "replicate",
    ):
        assert delay > 0
        assert temporal_fill in {"zeros", "replicate"}
        self.delay = delay
        self.make_padding = {"zeros": torch.zeros_like, "replicate": torch.clone}[
            temporal_fill
        ]

        super(Delay, self).__init__()
        # state is initialised in self.forward

    def init_state(
        self,
        first_output: Tensor,
    ) -> State:
        padding = self.make_padding(first_output)
        state_buffer = torch.stack([padding for _ in range(self.delay)], dim=0)
        state_index = 0
        if not hasattr(self, "state_buffer"):
            self.register_buffer("state_buffer", state_buffer, persistent=False)
        return state_buffer, state_index

    def clean_state(self):
        self.state_buffer = None
        self.state_index = None

    def get_state(self):
        if (
            hasattr(self, "state_buffer")
            and self.state_buffer is not None
            and hasattr(self, "state_index")
            and self.state_buffer is not None
        ):
            return (self.state_buffer, self.state_index)
        else:
            return None

    def forward_regular(self, input: Tensor) -> Tensor:
        # Pass into delay line, but discard output
        self.forward(input)

        # No delay during forward_regular
        return input

    def forward(self, input: Tensor) -> Tensor:
        output, (self.state_buffer, self.state_index) = self._forward(
            input, self.get_state()
        )
        return output

    def _forward(self, input: Tensor, prev_state: State) -> Tuple[Tensor, State]:
        if prev_state is None:
            buffer, index = self.init_state(input)
        else:
            buffer, index = prev_state

        # Get output
        output = buffer[index].clone()

        # Update state
        buffer[index] = input
        new_index = (index + 1) % self.delay

        return output, (buffer, new_index)
