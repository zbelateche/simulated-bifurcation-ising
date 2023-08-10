import torch
from tqdm import tqdm
from typing import Tuple


class StopWindow:

    """
    Optimization tool to monitor spins bifurcation and convergence
    for the Simulated Bifurcation (SB) algorithm.
    Allows an early stopping of the iterations and saves computation time.
    """

    def __init__(self, n_spins: int, n_agents: int, convergence_threshold: int, dtype: torch.dtype, device: str, verbose: bool) -> None:
        self.n_spins = n_spins
        self.n_agents = n_agents
        self.convergence_threshold = convergence_threshold
        self.dtype = dtype
        self.device = device
        self.__init_tensors()
        self.current_spins = self.__init_spins()
        self.final_spins = self.__init_spins()
        self.progress = self.__init_progress_bar(verbose)

    @property
    def shape(self) -> Tuple[int, int]:
        return (self.n_spins, self.n_agents)
    
    def __init_progress_bar(self, verbose: bool) -> tqdm:
        return tqdm(
            total=self.n_agents,
            desc='Bifurcated agents',
            disable=not verbose,
            smoothing=0,
        )
    
    def __init_tensor(self, dtype: torch.dtype) -> torch.Tensor:
        return torch.zeros(self.n_agents, device=self.device, dtype=dtype)

    def __init_tensors(self) -> None:
        self.stability = self.__init_tensor(self.dtype)
        self.newly_bifurcated = self.__init_tensor(bool)
        self.previously_bifurcated = self.__init_tensor(bool)
        self.bifurcated = self.__init_tensor(bool)
        self.equal = self.__init_tensor(bool)

    def __init_spins(self) -> torch.Tensor:
        return torch.zeros(size=self.shape, dtype=self.dtype, device=self.device)

    def __update_final_spins(self, sampled_spins) -> None:
        self.final_spins[:, self.newly_bifurcated] = torch.sign(
            sampled_spins[:, self.newly_bifurcated]
        )

    def __set_previously_bifurcated_spins(self) -> None:
        self.previously_bifurcated = self.bifurcated * 1.

    def __set_newly_bifurcated_spins(self) -> None:
        torch.logical_xor(
            self.bifurcated,
            self.previously_bifurcated,
            out=self.newly_bifurcated
        )

    def __update_bifurcated_spins(self) -> None:
        torch.eq(
            self.stability,
            self.convergence_threshold - 1,
            out=self.bifurcated
        )

    def __update_stability_streak(self) -> None:
        self.stability[torch.logical_and(self.equal, self.not_bifurcated)] += 1
        self.stability[torch.logical_and(self.not_equal, self.not_bifurcated)] = 0

    @property
    def not_equal(self) -> torch.Tensor:
        return torch.logical_not(self.equal)

    @property
    def not_bifurcated(self) -> torch.Tensor:
        return torch.logical_not(self.bifurcated)

    def __compare_spins(self, sampled_spins: torch.Tensor) -> None:
        torch.eq(
            torch.einsum('ik, ik -> k', self.current_spins, sampled_spins),
            self.n_spins,
            out=self.equal
        )

    def __store_spins(self, sampled_spins: torch.Tensor) -> None:
        torch.sign(sampled_spins, out=self.current_spins)

    def __get_number_newly_bifurcated_agents(self) -> int:
        return self.newly_bifurcated.sum().item()
    
    def update(self, sampled_spins: torch.Tensor):
        self.__compare_spins(sampled_spins)
        self.__update_stability_streak()
        self.__update_bifurcated_spins()
        self.__set_newly_bifurcated_spins()
        self.__set_previously_bifurcated_spins()
        self.__update_final_spins(sampled_spins)
        self.__store_spins(sampled_spins)
        self.progress.update(self.__get_number_newly_bifurcated_agents())
    
    def must_continue(self) -> bool:
        return torch.any(self.stability < self.convergence_threshold - 1)
    
    def has_bifurcated_spins(self) -> bool:
        return torch.any(self.bifurcated)

    def get_bifurcated_spins(self) -> torch.Tensor:
        return self.final_spins[:, self.bifurcated]