from ..ising_core import IsingCore
from .ising_interface import IsingInterface
from typing import Union
import torch
import numpy as np


class SpinPolynomial(IsingInterface):

    def __init__(self, matrix: Union[torch.Tensor, np.ndarray], vector: Union[torch.Tensor, np.ndarray, None] = None, constant: Union[float, int, None] = None,
                dtype: torch.dtype=torch.float32, device: str = 'cpu') -> None:
        super().__init__(matrix, vector, constant, [-1, 1], dtype, device)

    def to_ising(self) -> IsingCore:
        return IsingCore(-2 * self.matrix, self.vector, self.dtype, self.device)

    def from_ising(self, ising: IsingCore) -> torch.Tensor:
        return ising.ground_state
