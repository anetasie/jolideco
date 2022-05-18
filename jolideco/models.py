import torch.nn as nn
from .utils.torch import convolve_fft_torch


class SimpleNPredModel(nn.Module):
    """Simple npred model

    Parameters
    ----------
    flux_init : `~torch.Tensor`
        Initial flux tensor
    use_log_flux : bool
        Use log scaling for flux
    upsampling_factor : None
        Upsampling factor for the flux

    """

    def __init__(self, flux_init, use_log_flux=True, upsampling_factor=None):
        super().__init__()

        if use_log_flux:
            flux_init = torch.log(flux_init)

        self._flux = nn.Parameter(flux_init)
        self._use_log_flux = use_log_flux
        self.upsampling_factor = upsampling_factor

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

    def forward(self, psf, background, exposure):
        """Forward folding model evaluation.

        Parameters
        ----------
        psf : `~torch.Tensor`
            Point spread function
        background : `~torch.Tensor`
            Background tensor
        exposure : `~torch.Tensor`
            Exposure tensor

        Returns
        -------
        npred : `~torch.Tensor`
            Predicetd number of counts
        """
        npred = (self.flux + background) * exposure
        npred = convolve_fft_torch(npred, psf)

        if self.upsampling_factor:
            npred = F.avg_pool2d(
                npred, kernel_size=self.upsampling_factor, divisor_override=1
            )

        return npred
