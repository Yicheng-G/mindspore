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
# ==============================================================================

import numpy as np
import time

import mindspore.dataset as ds


# This UT test tests the following cases

# 1. padding: input_shape=[x] output_shape=[y] where y > x
# 2. padding in one dimension and truncate in the other. input_shape=[x1,x2] output_shape=[y1,y2] y1>x1 and y2<x2
# 3. automatic padding for a specific column
# 4. default setting for all columns
# 5. test None in different places

# this generator function yield two columns
# col1d: [0],[1], [2], [3]
# col2d: [[100],[200]], [[101],[201]], [102],[202]], [103],[203]]
def gen_2cols(num):
    for i in range(num):
        yield (np.array([i]), np.array([[i + 100], [i + 200]]))


# this generator function yield one column of variable shapes
# col: [0], [0,1], [0,1,2], [0,1,2,3]
def gen_var_col(num):
    for i in range(num):
        yield (np.array([j for j in range(i + 1)]),)


# this generator function yield two columns of variable shapes
# col1: [0], [0,1], [0,1,2], [0,1,2,3]
# col2: [100], [100,101], [100,101,102], [100,110,102,103]
def gen_var_cols(num):
    for i in range(num):
        yield (np.array([j for j in range(i + 1)]), np.array([100 + j for j in range(i + 1)]))


# this generator function yield two columns of variable shapes
# col1: [[0]], [[0,1]], [[0,1,2]], [[0,1,2,3]]
# col2: [[100]], [[100,101]], [[100,101,102]], [[100,110,102,103]]
def gen_var_cols_2d(num):
    for i in range(num):
        yield (np.array([[j for j in range(i + 1)]]), np.array([[100 + j for j in range(i + 1)]]))


def test_batch_padding_01():
    data1 = ds.GeneratorDataset((lambda: gen_2cols(2)), ["col1d", "col2d"])
    data1 = data1.batch(batch_size=2, drop_remainder=False, pad_info={"col2d": ([2, 2], -2), "col1d": ([2], -1)})
    data1 = data1.repeat(2)
    for data in data1.create_dict_iterator():
        assert np.array_equal([[0, -1], [1, -1]], data["col1d"])
        assert np.array_equal([[[100, -2], [200, -2]], [[101, -2], [201, -2]]], data["col2d"])


def test_batch_padding_02():
    data1 = ds.GeneratorDataset((lambda: gen_2cols(2)), ["col1d", "col2d"])
    data1 = data1.batch(batch_size=2, drop_remainder=False, pad_info={"col2d": ([1, 2], -2)})
    data1 = data1.repeat(2)
    for data in data1.create_dict_iterator():
        assert np.array_equal([[0], [1]], data["col1d"])
        assert np.array_equal([[[100, -2]], [[101, -2]]], data["col2d"])


def test_batch_padding_03():
    data1 = ds.GeneratorDataset((lambda: gen_var_col(4)), ["col"])
    data1 = data1.batch(batch_size=2, drop_remainder=False, pad_info={"col": (None, -1)})  # pad automatically
    data1 = data1.repeat(2)
    res = dict()
    for ind, data in enumerate(data1.create_dict_iterator()):
        res[ind] = data["col"].copy()
    assert np.array_equal(res[0], [[0, -1], [0, 1]])
    assert np.array_equal(res[1], [[0, 1, 2, -1], [0, 1, 2, 3]])
    assert np.array_equal(res[2], [[0, -1], [0, 1]])
    assert np.array_equal(res[3], [[0, 1, 2, -1], [0, 1, 2, 3]])


def test_batch_padding_04():
    data1 = ds.GeneratorDataset((lambda: gen_var_cols(2)), ["col1", "col2"])
    data1 = data1.batch(batch_size=2, drop_remainder=False, pad_info={})  # pad automatically
    data1 = data1.repeat(2)
    for data in data1.create_dict_iterator():
        assert np.array_equal(data["col1"], [[0, 0], [0, 1]])
        assert np.array_equal(data["col2"], [[100, 0], [100, 101]])


def test_batch_padding_05():
    data1 = ds.GeneratorDataset((lambda: gen_var_cols_2d(3)), ["col1", "col2"])
    data1 = data1.batch(batch_size=3, drop_remainder=False,
                        pad_info={"col2": ([2, None], -2), "col1": (None, -1)})  # pad automatically
    for data in data1.create_dict_iterator():
        assert np.array_equal(data["col1"], [[[0, -1, -1]], [[0, 1, -1]], [[0, 1, 2]]])
        assert np.array_equal(data["col2"], [[[100, -2, -2], [-2, -2, -2]], [[100, 101, -2], [-2, -2, -2]],
                                             [[100, 101, 102], [-2, -2, -2]]])


def batch_padding_performance_3d():
    cifar10_dir = "../data/dataset/testCifar10Data"
    data1 = ds.Cifar10Dataset(cifar10_dir, shuffle=False)  # shape = [32,32,3]
    data1 = data1.repeat(24)
    pad_info = {"image": ([36, 36, 3], 0)}
    # pad_info = None
    data1 = data1.batch(batch_size=24, drop_remainder=True, pad_info=pad_info)
    start_time = time.time()
    num_batches = 0
    ret = []
    for data in data1.create_dict_iterator():
        num_batches += 1
    res = "total number of batch:" + str(num_batches) + " time elapsed:" + str(time.time() - start_time)
    # print(res)


def batch_padding_performance_1d():
    cifar10_dir = "../data/dataset/testCifar10Data"
    data1 = ds.Cifar10Dataset(cifar10_dir, shuffle=False)  # shape = [32,32,3]
    data1 = data1.repeat(24)
    data1 = data1.map(input_columns="image", operations=(lambda x: x.reshape(-1)))
    pad_info = {"image": ([3888], 0)}  # 3888 =36*36*3
    # pad_info = None
    data1 = data1.batch(batch_size=24, drop_remainder=True, pad_info=pad_info)
    start_time = time.time()
    num_batches = 0
    for data in data1.create_dict_iterator():
        num_batches += 1
    res = "total number of batch:" + str(num_batches) + " time elapsed:" + str(time.time() - start_time)
    # print(res)


def batch_pyfunc_padding_3d():
    cifar10_dir = "../data/dataset/testCifar10Data"
    data1 = ds.Cifar10Dataset(cifar10_dir, shuffle=False)  # shape = [32,32,3]
    data1 = data1.repeat(24)
    # pad_info = {"image": ([36, 36, 3], 0)}
    data1 = data1.map(input_columns="image", operations=(lambda x: np.pad(x, ((0, 4), (0, 4), (0, 0)))),
                      python_multiprocessing=False)
    data1 = data1.batch(batch_size=24, drop_remainder=True)
    start_time = time.time()
    num_batches = 0
    for data in data1.create_dict_iterator():
        num_batches += 1
    res = "total number of batch:" + str(num_batches) + " time elapsed:" + str(time.time() - start_time)
    # print(res)


def batch_pyfunc_padding_1d():
    cifar10_dir = "../data/dataset/testCifar10Data"
    data1 = ds.Cifar10Dataset(cifar10_dir, shuffle=False)  # shape = [32,32,3]
    data1 = data1.repeat(24)
    data1 = data1.map(input_columns="image", operations=(lambda x: x.reshape(-1)))
    data1 = data1.map(input_columns="image", operations=(lambda x: np.pad(x, (0, 816))), python_multiprocessing=False)
    data1 = data1.batch(batch_size=24, drop_remainder=True)
    start_time = time.time()
    num_batches = 0
    for data in data1.create_dict_iterator():
        num_batches += 1
    res = "total number of batch:" + str(num_batches) + " time elapsed:" + str(time.time() - start_time)
    # print(res)


# this function runs pad_batch and numpy.pad then compare the results
def test_pad_via_map():
    cifar10_dir = "../data/dataset/testCifar10Data"

    def pad_map_config():
        data1 = ds.Cifar10Dataset(cifar10_dir, shuffle=False, num_samples=1000)  # shape = [32,32,3]
        data1 = data1.map(input_columns="image", operations=(lambda x: x.reshape(-1)))  # reshape to 1d
        data1 = data1.map(input_columns="image", operations=(lambda x: np.pad(x, (0, 816))))
        data1 = data1.batch(batch_size=25, drop_remainder=True)
        res = []
        for data in data1.create_dict_iterator():
            res.append(data["image"])
        return res

    def pad_batch_config():
        data2 = ds.Cifar10Dataset(cifar10_dir, shuffle=False, num_samples=1000)  # shape = [32,32,3]
        data2 = data2.map(input_columns="image", operations=(lambda x: x.reshape(-1)))  # reshape to 1d
        data2 = data2.batch(batch_size=25, drop_remainder=True, pad_info={"image": ([3888], 0)})
        res = []
        for data in data2.create_dict_iterator():
            res.append(data["image"])
        return res

    res_from_map = pad_map_config()
    res_from_batch = pad_batch_config()
    assert len(res_from_batch) == len(res_from_batch)
    for i in range(len(res_from_map)):
        assert np.array_equal(res_from_map[i], res_from_batch[i])


if __name__ == '__main__':
    test_batch_padding_01()
    test_batch_padding_02()
    test_batch_padding_03()
    test_batch_padding_04()
    test_batch_padding_05()
    # batch_padding_performance_3d()
    # batch_padding_performance_1d()
    # batch_pyfunc_padding_3d()
    # batch_pyfunc_padding_1d()
    test_pad_via_map()
