import numpy as np


def cross_normal(v1, v2):
    """
    Computes the normal direction of two vectors.

    Parameters
    ----------
    v1 : array_like
        The first vector(s).
    v2 : array_like
        The second vector(s).
    """
    c = np.cross(v1, v2)
    return c / np.linalg.norm(c, axis=-1, keepdims=True)
