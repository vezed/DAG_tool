import numpy as np
from enum import Enum


def un_boolean(matrix):
    """ 将布尔值转为0和1
        :return 0 if False, 1 if True
    """
    return (matrix > 0) + 0


def matrixPow(matrix, n):
    """ 计算matrix的乘方
        :return matrix^n
    """
    for _ in range(n):
        matrix = np.matmul(matrix, matrix)
    return matrix


def maxProduct(matrix, v):
    new_v = np.empty_like(v)
    for i in range(len(v)):
        new_v[i] = max(matrix[i] * v)
    return new_v


def maxProductPow(matrix, wc, n):
    v = np.zeros_like(wc)
    for _ in range(n):
        v = maxProduct(matrix, v + wc)
    return v


def is_duplicated(matrix, m_set):
    """ 判断matrix是否在matrixSet中已经存在
        :return true if duplicated, otherwise false
    """
    for m in m_set:
        if not ((matrix == m) - 1).sum():  # matrix == m
            return True
    return False


def get_wc(instances):
    """ :return array of wc """
    return np.array([instance.task.wc for instance in instances])


def get_bc(instances):
    """ :return array of bc """
    return np.array([instance.task.bc for instance in instances])


# def set_matrix(matrix, x_begin, x_end, y_begin, y_end, matrix_xy, matrix_yx):
#     matrix[x_begin: x_end + 1, y_begin: y_end + 1] = matrix_xy
#     matrix[y_begin: y_end + 1, x_begin: x_end + 1] = matrix_yx
#
#
# def reset_matrix(matrix, x_begin, x_end, y_begin, y_end):
#     matrix[x_begin: x_end + 1, y_begin: y_end + 1] = 0
#     matrix[y_begin: y_end + 1, x_begin: x_end + 1] = 0


def set_matrix(matrix_xy, matrix_yx, x_begin, x_end, y_begin, y_end, xy, yx):
    matrix_xy[x_begin: x_end + 1, y_begin: y_end + 1] = xy
    matrix_yx[y_begin: y_end + 1, x_begin: x_end + 1] = yx


def reset_matrix(matrix_xy, matrix_yx, x_begin, x_end, y_begin, y_end):
    matrix_xy[x_begin: x_end + 1, y_begin: y_end + 1] = 0
    matrix_yx[y_begin: y_end + 1, x_begin: x_end + 1] = 0


class Type(Enum):
    task = 1
    synchro = 2
    dummy = 3
