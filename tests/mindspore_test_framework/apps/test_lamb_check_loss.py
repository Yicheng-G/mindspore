# Copyright 2020 Huawei Technologies Co., Ltd
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ============================================================================

"""Checking lamb loss."""

from mindspore import context
from mindspore.nn.optim import Lamb
from ..mindspore_test import mindspore_test
from ..pipeline.gradient.check_training import pipeline_for_check_model_loss_for_case_by_case_config
from ..utils.model_util import Linreg
from ..utils.model_util import SquaredLoss

network = Linreg(2)
num_epochs = 1000

verification_set = [
    ('Linreg', {
        'block': {
            'model': network,
            'loss': SquaredLoss(),
            'opt': Lamb(network.trainable_params(), decay_steps=num_epochs, warmup_steps=10, weight_decay=0.01),
            'num_epochs': num_epochs,
            'loss_upper_bound': 0.3,
        },
        'desc_inputs': {
            'true_params': ([2, -3.4], 4.2),
            'num_samples': 100,
            'batch_size': 20,
        }
    })
]


@mindspore_test(pipeline_for_check_model_loss_for_case_by_case_config)
def test_lamb_loss():
    context.set_context(mode=context.GRAPH_MODE)
    return verification_set
