from enum import Enum


class Shape(Enum):
    """
    Different shapes for representing aspects. The values are obtained from the ReactFlow library from
    https://reactflow.dev/examples/nodes/shapes
    """
    ROUND_RECTANGLE = 'round-rectangle'
    CIRCLE = 'circle'
    DIAMOND = 'diamond'
    HEXAGON = 'hexagon'
    RECTANGLE = 'rectangle'
    ARROW_RECTANGLE = 'arrow-rectangle'
    CYLINDER = 'cylinder'
    PARALLELOGRAM = 'parallelogram'
    TRIANGLE = 'triangle'
    PLUS = 'plus'


