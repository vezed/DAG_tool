from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QLabel


def resize_graph(graph: QPixmap, label: QLabel) -> QPixmap:
    width = graph.width()
    height = graph.height()
    if width / label.width() >= height / label.height():
        ratio = width / label.width()
    else:
        ratio = height / label.height()
    new_width = int(width / ratio)
    new_height = int(height / ratio)
    new_graph = graph.scaled(new_width, new_height)
    return new_graph
