import torch
from phase_space_reconstruction.modeling import ImageDataset, ImageDataset3D


def run_quad_scan(
        beam,
        lattice,
        screen,
        ks,
        scan_quad_id = 0,
        save_as = None
        ):
    
    """
    Runs virtual quad scan and returns image data from the
    screen downstream.

    Parameters
    ----------
    beam : bmadx.Beam
        ground truth beam
    lattice: bmadx TorchLattice
        diagnostics lattice
    screen: ImageDiagnostic
        diagnostic screen
    ks: Tensor
        quadrupole strengths. 
        shape: n_quad_strengths x n_images_per_quad_strength x 1
    save_as : str
        filename to store output dataset. Default: None.

    Returns
    -------
        dset: ImageDataset
            output image dataset
    """

    # tracking though diagnostics lattice
    diagnostics_lattice = lattice.copy()
    diagnostics_lattice.elements[scan_quad_id].K1.data = ks
    output_beam = diagnostics_lattice(beam)

    # histograms at screen
    images = screen(output_beam)

    # create image dataset
    dset = ImageDataset(ks, images)
    
    # save scan data if wanted
    if save_as is not None:
        torch.save(dset, save_as)
        print(f"dataset saved as '{save_as}'")

    return dset


def run_sextupole_scan(
        beam,
        lattice,
        screen,
        ks,
        scan_quad_id=0,
        save_as=None
):
    """
    Runs virtual quad scan and returns image data from the
    screen downstream.

    Parameters
    ----------
    beam : bmadx.Beam
        ground truth beam
    lattice: bmadx TorchLattice
        diagnostics lattice
    screen: ImageDiagnostic
        diagnostic screen
    ks: Tensor
        quadrupole strengths.
        shape: n_quad_strengths x n_images_per_quad_strength x 1
    save_as : str
        filename to store output dataset. Default: None.

    Returns
    -------
        dset: ImageDataset
            output image dataset
    """

    # tracking though diagnostics lattice
    diagnostics_lattice = lattice.copy()
    diagnostics_lattice.elements[scan_quad_id].K2.data = ks
    print(list(diagnostics_lattice.named_parameters()))
    output_beam = diagnostics_lattice(beam)

    # histograms at screen
    images = screen(output_beam)

    # create image dataset
    dset = ImageDataset(ks, images)

    # save scan data if wanted
    if save_as is not None:
        torch.save(dset, save_as)
        print(f"dataset saved as '{save_as}'")

    return dset

def run_3d_scan(
        beam,
        lattice,
        screen,
        ks,
        vs,
        gs,
        ids = [0, 2, 4],
        save_as = None
        ):
    
    """
    Runs virtual quad + transverse deflecting cavity 2d scan and returns
    image data from the screen downstream.

    Parameters
    ----------
    beam : bmadx.Beam
        ground truth beam
    lattice: bmadx TorchLattice
        diagnostics lattice
    screen: ImageDiagnostic
        diagnostic screen
    quad_ks: Tensor
        quadrupole strengths. 
        shape: n_quad_strengths
    quad_id: int
        id of quad lattice element used for scan.
    tdc_vs: Tensor
        Transverse deflecting cavity voltages. 
        shape: n_tdc_voltages
    tdc_id: int
        id of tdc lattice element.
    save_as : str
        filename to store output dataset. Default: None.

    Returns
    -------
    dset: ImageDataset
        output image dataset
    """

    # base lattice
    diagnostics_lattice = lattice.copy()
    # params:
    params = torch.meshgrid(ks, vs, gs, indexing='ij')
    params = torch.stack(params, dim=-1).reshape((-1,3)).unsqueeze(-1)
    diagnostics_lattice.elements[ids[0]].K1.data = params[:,0].unsqueeze(-1)
    diagnostics_lattice.elements[ids[1]].VOLTAGE.data = params[:,1].unsqueeze(-1)
    diagnostics_lattice.elements[ids[2]].G.data = params[:,2].unsqueeze(-1)

    # track through lattice
    output_beam = diagnostics_lattice(beam)

    # histograms at screen
    images = screen(output_beam)

    # create image dataset
    dset = ImageDataset3D(params, images)
    
    # save scan data if wanted
    if save_as is not None:
        torch.save(dset, save_as)
        print(f"dataset saved as '{save_as}'")

    return dset

def run_t_scan(
        beam,
        lattice,
        screen,
        ks,
        vs,
        gs,
        ids = [0, 2, 4],
        save_as = None
        ):
    
    """
    Runs virtual quad + transverse deflecting cavity 2d scan and returns
    image data from the screen downstream.

    Parameters
    ----------
    beam : bmadx.Beam
        ground truth beam
    lattice: bmadx TorchLattice
        diagnostics lattice
    screen: ImageDiagnostic
        diagnostic screen
    quad_ks: Tensor
        quadrupole strengths. 
        shape: n_quad_strengths
    quad_id: int
        id of quad lattice element used for scan.
    tdc_vs: Tensor
        Transverse deflecting cavity voltages. 
        shape: n_tdc_voltages
    tdc_id: int
        id of tdc lattice element.
    save_as : str
        filename to store output dataset. Default: None.

    Returns
    -------
    dset: ImageDataset
        output image dataset
    """

    # base lattice
    diagnostics_lattice = lattice.copy()
    # params:
    # params = torch.meshgrid(ks, vs, gs, indexing='ij')
    # params = torch.stack(params, dim=-1).reshape((-1,3)).unsqueeze(-1)
    # allowed = torch.tensor([0, 4, 8, 9, 10, 11, 12, 16])
    n_ks = len(ks)
    params = torch.zeros((n_ks+3, 3, 1))
    for i in range(n_ks):
        params[i, 0, 0] = ks[i]
        params[i, 1, 0] = vs[0]
        params[i, 2, 0] = gs[0]

    params[n_ks, 0, 0] = torch.tensor(0.0)
    params[n_ks, 1, 0] = vs[0]
    params[n_ks, 2, 0] = gs[1]

    params[n_ks+1, 0, 0] = torch.tensor(0.0)
    params[n_ks+1, 1, 0] = vs[1]
    params[n_ks+1, 2, 0] = gs[0]

    params[n_ks+2, 0, 0] = torch.tensor(0.0)
    params[n_ks+2, 1, 0] = vs[1]
    params[n_ks+2, 2, 0] = gs[1]

    print(params.shape)
    print(params[:,:,0])
    diagnostics_lattice.elements[ids[0]].K1.data = params[:,0].unsqueeze(-1)
    diagnostics_lattice.elements[ids[1]].VOLTAGE.data = params[:,1].unsqueeze(-1)
    diagnostics_lattice.elements[ids[2]].G.data = params[:,2].unsqueeze(-1)

    # track through lattice
    output_beam = diagnostics_lattice(beam)

    # histograms at screen
    images = screen(output_beam)

    # create image dataset
    dset = ImageDataset3D(params, images)
    
    # save scan data if wanted
    if save_as is not None:
        torch.save(dset, save_as)
        print(f"dataset saved as '{save_as}'")

    return dset

#### TEST ##################################################################################
def run_3d_scan_2screens(
        beam,
        lattice,
        screen0,
        screen1,
        ks,
        vs,
        gs,
        n_imgs_per_param = 1,
        ids = [0, 2, 4],
        save_as = None
        ):
    
    """
    Runs virtual quad + transverse deflecting cavity 2d scan and returns
    image data from the screen downstream.

    Parameters
    ----------
    beam : bmadx.Beam
        ground truth beam
    lattice: bmadx TorchLattice
        diagnostics lattice
    screen: ImageDiagnostic
        diagnostic screen
    ids: array like
        ids of lattice elements to scan in this order: [quad_id, tdc_id, dipole_id]
    save_as : str
        filename to store output dataset. Default: None.

    Returns
    -------
    dset: ImageDataset
        output image dataset
    """

    # base lattices 
    params = torch.meshgrid(gs, ks, vs, indexing='ij')
    params = torch.stack(params, dim=-1)

    params0 = params[0].reshape((len(ks)*len(vs),3)).unsqueeze(-1)
    diagnostics_lattice0 = lattice.copy()
    diagnostics_lattice0.elements[ids[2]].G.data = params0[:,0].unsqueeze(-1)
    diagnostics_lattice0.elements[ids[0]].K1.data = params0[:,1].unsqueeze(-1)
    diagnostics_lattice0.elements[ids[1]].VOLTAGE.data = params0[:,2].unsqueeze(-1)

    params1 = params[1].reshape((len(ks)*len(vs),3)).unsqueeze(-1)
    diagnostics_lattice1 = lattice.copy()
    diagnostics_lattice1.elements[ids[2]].G.data = params1[:,0].unsqueeze(-1)
    diagnostics_lattice1.elements[ids[0]].K1.data = params1[:,1].unsqueeze(-1)
    diagnostics_lattice1.elements[ids[1]].VOLTAGE.data = params1[:,2].unsqueeze(-1)

    # track through lattice
    output_beam0 = diagnostics_lattice0(beam)
    output_beam1 = diagnostics_lattice1(beam)

    # histograms at screen
    images0 = screen0(output_beam0).squeeze()
    images1 = screen1(output_beam1).squeeze()
    images_stack = torch.stack((images0, images1), dim=1)
    params_stack = torch.stack((params0, params1), dim=1)

    # create image dataset
    copied_images = torch.stack([images_stack]*n_imgs_per_param, dim=2)
    dset = ImageDataset3D(params_stack, copied_images)
    
    # save scan data if wanted
    if save_as is not None:
        torch.save(dset, save_as)
        print(f"dataset0 saved as '{save_as}'")

    return dset