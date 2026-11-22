"""Small metadata-free marching-squares outline tracer for designated artwork."""

import numpy as np


def simplify(points, tolerance):
    if len(points) <= 2:
        return points
    segment = points[-1] - points[0]
    relative = points[1:-1] - points[0]
    distance = np.abs(segment[0] * relative[:, 1] - segment[1] * relative[:, 0]) / np.linalg.norm(segment)
    split = int(np.argmax(distance)) + 1
    if distance[split - 1] <= tolerance:
        return points[[0, -1]]
    return np.concatenate((simplify(points[:split + 1], tolerance)[:-1], simplify(points[split:], tolerance)))


def trace(gray, threshold=127.5, tolerance=0.13):
    height, width = gray.shape
    pixels = np.pad(gray.astype(float), 1, constant_values=255)
    cases = {
        1: [(0, 3)], 2: [(0, 1)], 3: [(1, 3)], 4: [(1, 2)],
        5: [(0, 3), (1, 2)], 6: [(0, 2)], 7: [(2, 3)], 8: [(2, 3)],
        9: [(0, 2)], 10: [(0, 1), (2, 3)], 11: [(1, 2)],
        12: [(1, 3)], 13: [(0, 1)], 14: [(0, 3)],
    }
    neighbors = {}
    for y in range(height + 1):
        for x in range(width + 1):
            values = [pixels[y, x], pixels[y, x + 1], pixels[y + 1, x + 1], pixels[y + 1, x]]
            case = sum((value < threshold) << index for index, value in enumerate(values))
            if case not in cases:
                continue
            corners = np.array([[x - 1, y - 1], [x, y - 1], [x, y], [x - 1, y]])
            intersections = {}
            for edge in set(edge for pair in cases[case] for edge in pair):
                following = (edge + 1) % 4
                fraction = (threshold - values[edge]) / (values[following] - values[edge])
                point = corners[edge] + fraction * (corners[following] - corners[edge])
                intersections[edge] = tuple(np.round(point, 6))
            for a, b in cases[case]:
                a, b = intersections[a], intersections[b]
                neighbors.setdefault(a, []).append(b)
                neighbors.setdefault(b, []).append(a)
    assert all(len(points) == 2 for points in neighbors.values()), "Trace contains an open or ambiguous boundary."
    contours = []
    remaining = set(neighbors)
    while remaining:
        start = min(remaining)
        points = [start]
        previous, current = None, start
        while True:
            following = next(point for point in neighbors[current] if point != previous)
            if following == start:
                break
            points.append(following)
            previous, current = current, following
        remaining.difference_update(points)
        points = np.array(points)
        following = np.roll(points, -1, axis=0)
        smoothed = np.stack((points * 0.875 + following * 0.125,
                             points * 0.125 + following * 0.875), axis=1).reshape(-1, 2)
        middle = len(smoothed) // 2
        contours.append(np.concatenate((simplify(smoothed[:middle + 1], tolerance)[:-1],
                                        simplify(np.concatenate((smoothed[middle:], smoothed[:1])), tolerance)[:-1])))
    return contours


def path_data(contours):
    return " ".join("M" + " L".join(f"{x:.4f},{y:.4f}" for x, y in contour) + " Z" for contour in contours)


def rasterize(contours, shape):
    yy, xx = np.mgrid[:shape[0], :shape[1]]
    mask = np.zeros(shape, dtype=bool)
    for contour in contours:
        inside = np.zeros_like(mask)
        for (ax, ay), (bx, by) in zip(contour, np.roll(contour, -1, axis=0)):
            if by != ay:
                inside ^= ((ay > yy) != (by > yy)) & (xx < ax + (yy - ay) * (bx - ax) / (by - ay))
        mask ^= inside
    return mask
