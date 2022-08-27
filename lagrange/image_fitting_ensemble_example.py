import logging
import os

import sys

import torch

from lagrange.custom_snapshot_regressor import CustomSnapshotRegressor
from torch.autograd import grad
from torch.nn import Parameter
from torch.nn.functional import mse_loss
from torch.utils.data import DataLoader, random_split, Subset
from torchensemble import SnapshotEnsembleRegressor
from utils import kl_div

sys.path.append("../../")

from modeling import (
    ImageDataset,
    Imager,
    InitialBeam,
    MaxEntropyQuadScan,
    NonparametricTransform,
    QuadScanTransport,
)

logging.basicConfig(level=logging.INFO)


class CustomLoss(torch.nn.MSELoss):
    def __init__(self, l0, model):
        super().__init__()
        self.loss_record = []
        self.register_parameter("lambda_", Parameter(l0))
        #self.model = model

    def forward(self, input_data, target):
        image_loss = kl_div(target, input_data[0]).sum()
        entropy_loss = -input_data[1]
        # print(entropy_loss.data, image_loss.data, self.lambda_.data)

        # attempt to maximize the entropy loss while constraining on the image loss
        # using lagrange multipliers see:
        # https://en.wikipedia.org/wiki/Lagrange_multiplier

        unconstrained_loss = entropy_loss + self.lambda_ * image_loss
        #z = grad(
        #    unconstrained_loss,
        #    list(self.model.beam_generator.parameters()) + [self.lambda_],
        #    create_graph=True,
        #)
        #grad_loss = torch.norm(
        #    torch.cat([ele.flatten().unsqueeze(1) for ele in z], dim=0)
        #)
        self.loss_record.append(
            [image_loss, entropy_loss, input_data[2], self.lambda_.data]
        )

        return unconstrained_loss


def create_ensemble(bins, bandwidth):
    defaults = {
        "s": torch.tensor(0.0).float(),
        "p0c": torch.tensor(10.0e6).float(),
        "mc2": torch.tensor(0.511e6).float(),
    }

    transformer = NonparametricTransform(4, 50, 0.0, torch.nn.Tanh())
    base_dist = torch.distributions.MultivariateNormal(torch.zeros(6), torch.eye(6))

    module_kwargs = {
        "initial_beam": InitialBeam(100000, transformer, base_dist, **defaults),
        "transport": QuadScanTransport(torch.tensor(0.1), torch.tensor(1.0), 1),
        "imager": Imager(bins, bandwidth),
        "condition": False,
    }

    ensemble = CustomSnapshotRegressor(
        estimator=MaxEntropyQuadScan,
        estimator_args=module_kwargs,
        n_estimators=5,
    )

    ensemble.create_estimator()
    return ensemble


def get_data(folder):
    all_k = torch.load(folder + "kappa.pt").float()
    all_images = torch.load(folder + "train_images.pt").float()
    xx = torch.load(folder + "xx.pt")
    bins = xx[0].T[0]

    if torch.cuda.is_available():
        all_k = all_k.cuda()
        all_images = all_images.cuda()

    print(all_images.shape)
    print(all_k.shape)
    print(bins.shape)

    return all_k, all_images, bins, xx


def get_datasets(all_k, all_images, save_dir):
    train_dset = ImageDataset(all_k[::2], all_images[::2])
    test_dset = ImageDataset(all_k[1::2], all_images[1::2])
    torch.save(train_dset, save_dir + "/train.dset")
    torch.save(test_dset, save_dir + "/test.dset")

    return train_dset, test_dset


if __name__ == "__main__":
    folder = "../test_case_4/"

    save_dir = "alpha_1e-3_snapshot_lr_01"
    if not os.path.isdir(save_dir):
        os.mkdir(save_dir)

    all_k, all_images, bins, xx = get_data(folder)
    train_dset, test_dset = get_datasets(all_k, all_images, save_dir)
    print(len(train_dset))

    train_dataloader = DataLoader(train_dset, batch_size=5, shuffle=True)
    test_dataloader = DataLoader(test_dset, shuffle=True)

    bin_width = bins[1] - bins[0]
    bandwidth = bin_width / 2
    ensemble = create_ensemble(bins, bandwidth)

    criterion = GradientSquaredLoss(torch.tensor(100.0).to(all_k), ensemble.estimator)
    ensemble.set_criterion(criterion)

    n_epochs = 1000
    optim = torch.optim.Adam(
        list(ensemble.estimator.beam_generator.parameters()),# + [criterion.lambda_],
        lr=0.01,
    )
    ensemble.set_optimizer(optim)

    # with torch.autograd.detect_anomaly():
    ensemble.fit(
        train_dataloader, epochs=n_epochs, save_dir=save_dir, lr_clip=[0.0001, 10]
    )
    torch.save(criterion.loss_record, save_dir + "/loss_log.pt")
