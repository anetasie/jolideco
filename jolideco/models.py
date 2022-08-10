import torch
import torch.nn as nn
import torch.nn.functional as F
from .utils.torch import convolve_fft_torch


class FluxComponent(nn.Module):
    """Flux component

    Parameters
    ----------
    flux_init : `~torch.Tensor`
        Initial flux tensor
    use_log_flux : bool
        Use log scaling for flux
    """

    def __init__(self, flux_init, use_log_flux=True):
        super().__init__()

        if use_log_flux:
            flux_init = torch.log(flux_init)

        self._flux = nn.Parameter(flux_init)
        self._use_log_flux = use_log_flux

    @property
    def use_log_flux(self):
        """Use log flux (`bool`)"""
        return self._use_log_flux

    @property
    def flux(self):
        """Flux (`torch.Tensor`)"""
        if self.use_log_flux:
            return torch.exp(self._flux)
        else:
            return self._flux


class NPredModel(nn.Module):
    """Predicted counts model with mutiple components

    Attributes
    ----------
    components : list of `FluxModel`
        List of flux model components
    upsampling_factor : None
        Spatial upsampling factor for the flux

    """

    def __init__(self, components, upsampling_factor=None):
        super().__init__()
        self.components = nn.ModuleList(components)
        self.upsampling_factor = upsampling_factor

    def forward(self, background, exposure, psf=None, rmf=None):
        """Forward folding model evaluation.

        Parameters
        ----------
        background : `~torch.Tensor`
            Background tensor
        exposure : `~torch.Tensor`
            Exposure tensor
        psf : `~torch.Tensor`
            Point spread function
        rmf : `~torch.Tensor`
            Energy redistribution matrix.

        Returns
        -------
        npred : `~torch.Tensor`
            Predicted number of counts
        """
        flux = torch.zeros(exposure.shape)

        for component in self.components:
            flux += component.flux

        npred = (flux + background) * exposure

        if psf is not None:
            npred = convolve_fft_torch(npred, psf)

        if self.upsampling_factor:
            npred = F.avg_pool2d(
                npred, kernel_size=self.upsampling_factor, divisor_override=1
            )

        if rmf is not None:
            # TODO: simplify if possible
            npred = torch.matmul(npred[0].T, rmf).T[None]

        return npred
