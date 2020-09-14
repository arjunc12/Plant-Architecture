from scipy.spatial.distance import euclidean
import numpy as np

DIMENSION_COORD = {'x' : 0, 'y' : 1, 'z' : 2}

def angleBetweenVectors(v1, v2):
    numerator = np.dot(v1, v2)

    m1 = np.sqrt(np.dot(v1, v1))
    m2 = np.sqrt(np.dot(v2, v2))
    denominator = m1 * m2

    return np.arccos(numerator / denominator)

def rotationAngle(v, dim='y'):
    pass

def translateToOrigin(p0, p1, q):
    assert len(p0) == len(p1) == len(q)

    p0_shift = p0[:]
    p1_shift = p1[:]
    q_shift = q[:]

    for i, coord in enumerate(p0):
        for point in [p0Shift, p1Shift, qShift]:
            point[i] -= coord

    return p0Shift, p1Shirt, qShift

def optimalMidpointApprox(p0, p1, q, alpha):
    assert len(p0) == len(p1) == len(q)

    p0 = np.array(p0)
    p1 = np.array(p1)
    q = np.array(q)

    m = p1 - p0

    delta = 0.01
    bestCost = None
    bestMidpoint = None
    for t in np.arange(0, 1 + delta, delta):
        midpoint = p0 + m * t
        wiring =  pylab.euclidean(midpoint, q)
        delay = pylab.euclidean(midpoint, q) + pylab.euclidean(p0, midpoint)
        cost = (alpha * wiring) + ((1 - alpha) * delay)

        if bestCost == None or cost < bestCost:
            bestCost = cost
            bestMidpoint = midpoint

