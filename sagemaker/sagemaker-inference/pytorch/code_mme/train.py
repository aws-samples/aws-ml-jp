import argparse
import json
import logging
import os
import sys
import shutil
import subprocess
from distutils.dir_util import copy_tree
from tempfile import TemporaryDirectory
import torch
import torch.distributed as dist
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
import torch.utils.data
import torch.utils.data.distributed
from torchvision import datasets, transforms
from model import Net
from packaging import version as pkgversion
from sagemaker_pytorch_serving_container import handler_service as default_handler_service

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler(sys.stdout))

def enable_sm_oneclick_deploy(model_dir):
    """Copy current running source code folder to model_dir, to enable Estimator.deploy()
    PyTorch framework containers will load custom inference code if:
    - The code exists in a top-level code/ folder in the model.tar.gz
    - The entry point argument matches an existing file
    ...So to make one-click estimator.deploy() work (without creating a PyTorchModel first), we need
    to:
    - Copy the current working directory to model_dir/code
    - `from inference import *` because "train.py" will still be the entry point (same as the training job)
    """
    code_path = os.path.join(model_dir, "code")
    logger.info(f"Copying working folder to {code_path}")
    for currpath, dirs, files in os.walk("."):
        for file in files:
            # Skip any filenames starting with dot:
            if file.startswith("."):
                continue
            filepath = os.path.join(currpath, file)
            # Skip any pycache or dot folders:
            if ((os.path.sep + ".") in filepath) or ("__pycache__" in filepath):
                continue
            relpath = filepath[len(".") :]
            if relpath.startswith(os.path.sep):
                relpath = relpath[1:]
            outpath = os.path.join(code_path, relpath)
            logger.info(f"Copying {filepath} to {outpath}")
            os.makedirs(outpath.rpartition(os.path.sep)[0], exist_ok=True)
            shutil.copy2(filepath, outpath)
    return code_path

def enable_torchserve_multi_model(model_dir, handler_service_file=default_handler_service.__file__):
    """Package the contents of model_dir as a TorchServe model archive
    SageMaker framework serving containers for PyTorch versions >=1.6 use TorchServe, for consistency with
    the PyTorch ecosystem. TorchServe expects particular 'model archive' packaging around models.

    On single-model endpoints, the SageMaker container can transparently package your model.tar.gz for
    TorchServe at start-up. On multi-model endpoints though, as models are loaded and unloaded dynamically,
    this is not (currently?) supported.

    ...So to make your training jobs produce model.tar.gz's which are already compatible with TorchServe
    (and therefore SageMaker Multi-Model-Endpoints, on PyTorch >=1.6), you can do something like this.

    Check out the PyTorch Inference Toolkit (used by SageMaker PyTorch containers) for more details:
    https://github.com/aws/sagemaker-pytorch-inference-toolkit

    For running single-model endpoints, or MMEs on PyTorch<1.6, this function is not necessary.

    If you use the SageMaker PyTorch framework containers, you won't need to change `handler_service_file`
    unless you already know about the topic :-)  The default handler will already support `model_fn`, etc.
    """
    if pkgversion.parse(torch.__version__) >= pkgversion.parse("1.6"):
        logger.info(f"Packaging {model_dir} for use with TorchServe")
        # torch-model-archiver creates a subdirectory per `model-name` within `export-path`, but we want the
        # contents to end up in `model_dir`'s root - so will use a temp dir and copy back:
        with TemporaryDirectory() as temp_dir:
            ts_model_name = "model"  # Just a placeholder, doesn't really matter for our purposes
            subprocess.check_call(
                [
                    "torch-model-archiver",
                    "--model-name",
                    ts_model_name,
                    "--version",
                    "1",
                    "--handler",
                    handler_service_file,
                    "--extra-files",
                    model_dir,
                    "--archive-format",
                    "no-archive",
                    "--export-path",
                    temp_dir,
                ]
            )
            copy_tree(os.path.join(temp_dir, ts_model_name), model_dir)
    else:
        logger.info(f"Skipping TorchServe repackage: PyTorch version {torch.__version__} < 1.6")


def _get_train_data_loader(batch_size, training_dir, is_distributed, **kwargs):
    logger.info("Get train data loader")
    train_tensor = torch.load(os.path.join(training_dir, 'training.pt'))
    dataset = torch.utils.data.TensorDataset(train_tensor[0], train_tensor[1])

    train_sampler = torch.utils.data.distributed.DistributedSampler(dataset) if is_distributed else None
    return torch.utils.data.DataLoader(dataset, batch_size=batch_size, shuffle=train_sampler is None,
                                       sampler=train_sampler, **kwargs)

def _get_test_data_loader(test_batch_size, training_dir, **kwargs):
    logger.info("Get test data loader")
    test_tensor = torch.load(os.path.join(training_dir, 'test.pt'))
    dataset = torch.utils.data.TensorDataset(test_tensor[0], test_tensor[1])
    return torch.utils.data.DataLoader(
        dataset,
        batch_size=test_batch_size,
        shuffle=True, **kwargs)


def _average_gradients(model):
    # Gradient averaging.
    size = float(dist.get_world_size())
    for param in model.parameters():
        dist.all_reduce(param.grad.data, op=dist.reduce_op.SUM)
        param.grad.data /= size


def train(args):
    is_distributed = len(args.hosts) > 1 and args.backend is not None
    logger.debug("Distributed training - {}".format(is_distributed))
    use_cuda = args.num_gpus > 0
    logger.debug("Number of gpus available - {}".format(args.num_gpus))
    kwargs = {'num_workers': 1, 'pin_memory': True} if use_cuda else {}
    device = torch.device("cuda" if use_cuda else "cpu")

    if is_distributed:
        # Initialize the distributed environment.
        world_size = len(args.hosts)
        os.environ['WORLD_SIZE'] = str(world_size)
        host_rank = args.hosts.index(args.current_host)
        os.environ['RANK'] = str(host_rank)
        dist.init_process_group(backend=args.backend, rank=host_rank, world_size=world_size)
        logger.info('Initialized the distributed environment: \'{}\' backend on {} nodes. '.format(
            args.backend, dist.get_world_size()) + 'Current host rank is {}. Number of gpus: {}'.format(
            dist.get_rank(), args.num_gpus))

    # set the seed for generating random numbers
    torch.manual_seed(args.seed)
    if use_cuda:
        torch.cuda.manual_seed(args.seed)

    train_loader = _get_train_data_loader(args.batch_size, args.data_dir, is_distributed, **kwargs)
    test_loader = _get_test_data_loader(args.test_batch_size, args.data_dir, **kwargs)

    logger.debug("Processes {}/{} ({:.0f}%) of train data".format(
        len(train_loader.sampler), len(train_loader.dataset),
        100. * len(train_loader.sampler) / len(train_loader.dataset)
    ))

    logger.debug("Processes {}/{} ({:.0f}%) of test data".format(
        len(test_loader.sampler), len(test_loader.dataset),
        100. * len(test_loader.sampler) / len(test_loader.dataset)
    ))

    model = Net().to(device)
    if is_distributed and use_cuda:
        # multi-machine multi-gpu case
        model = torch.nn.parallel.DistributedDataParallel(model)
    else:
        # single-machine multi-gpu case or single-machine or multi-machine cpu case
        model = torch.nn.DataParallel(model)

    optimizer = optim.SGD(model.parameters(), lr=args.lr, momentum=args.momentum)

    for epoch in range(1, args.epochs + 1):
        model.train()
        for batch_idx, (data, target) in enumerate(train_loader, 1):
            data, target = data.to(device), target.to(device)
            optimizer.zero_grad()
            output = model(data)
            loss = F.nll_loss(output, target)
            loss.backward()
            if is_distributed and not use_cuda:
                # average gradients manually for multi-machine cpu case only
                _average_gradients(model)
            optimizer.step()
            if batch_idx % args.log_interval == 0:
                logger.info('Train Epoch: {} [{}/{} ({:.0f}%)] Loss: {:.6f}'.format(
                    epoch, batch_idx * len(data), len(train_loader.sampler),
                    100. * batch_idx / len(train_loader), loss.item()))
        test(model, test_loader, device)
    save_model(model, args.model_dir)


def test(model, test_loader, device):
    model.eval()
    test_loss = 0
    correct = 0
    with torch.no_grad():
        for data, target in test_loader:
            data, target = data.to(device), target.to(device)
            output = model(data)
            test_loss += F.nll_loss(output, target, size_average=False).item()  # sum up batch loss
            pred = output.max(1, keepdim=True)[1]  # get the index of the max log-probability
            correct += pred.eq(target.view_as(pred)).sum().item()

    test_loss /= len(test_loader.dataset)
    logger.info('Test set: Average loss: {:.4f}, Accuracy: {}/{} ({:.0f}%)\n'.format(
        test_loss, correct, len(test_loader.dataset),
        100. * correct / len(test_loader.dataset)))


def save_model(model, model_dir):
    logger.info("Saving the model.")
    path = os.path.join(model_dir, 'model.pth')
    # recommended way from http://pytorch.org/docs/master/notes/serialization.html
    torch.save(model.cpu().state_dict(), path)
    enable_sm_oneclick_deploy(model_dir) # added to use multi model endpoint
    enable_torchserve_multi_model(model_dir) # added to use multi model endpoint


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    # Data and model checkpoints directories
    parser.add_argument('--batch-size', type=int, default=64, metavar='N',
                        help='input batch size for training (default: 64)')
    parser.add_argument('--test-batch-size', type=int, default=1000, metavar='N',
                        help='input batch size for testing (default: 1000)')
    parser.add_argument('--epochs', type=int, default=10, metavar='N',
                        help='number of epochs to train (default: 10)')
    parser.add_argument('--lr', type=float, default=0.01, metavar='LR',
                        help='learning rate (default: 0.01)')
    parser.add_argument('--momentum', type=float, default=0.5, metavar='M',
                        help='SGD momentum (default: 0.5)')
    parser.add_argument('--seed', type=int, default=1, metavar='S',
                        help='random seed (default: 1)')
    parser.add_argument('--log-interval', type=int, default=100, metavar='N',
                        help='how many batches to wait before logging training status')
    parser.add_argument('--backend', type=str, default=None,
                        help='backend for distributed training (tcp, gloo on cpu and gloo, nccl on gpu)')

    # Container environment
    parser.add_argument('--hosts', type=list, default=json.loads(os.environ['SM_HOSTS']))
    parser.add_argument('--current-host', type=str, default=os.environ['SM_CURRENT_HOST'])
    parser.add_argument('--model-dir', type=str, default=os.environ['SM_MODEL_DIR'])
    parser.add_argument('--data-dir', type=str, default=os.environ['SM_CHANNEL_TRAINING'])
    parser.add_argument('--num-gpus', type=int, default=os.environ['SM_NUM_GPUS'])

    train(parser.parse_args())